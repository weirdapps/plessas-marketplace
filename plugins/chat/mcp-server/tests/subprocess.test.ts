// tests/subprocess.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EventEmitter } from 'node:events';
import {
  runTeamsCli,
  TeamsCliError,
  shouldUseShell,
  __setSpawnForTests,
  type SpawnLike,
} from '../src/subprocess.js';

/** Returns a factory that builds a deferred fake child each time it's called. */
function makeChildFactory(opts: { stdout?: string; stderr?: string; exitCode: number }): () => any {
  return () => {
    const stdout = new EventEmitter();
    const stderr = new EventEmitter();
    const child = new EventEmitter() as any;
    child.stdout = stdout;
    child.stderr = stderr;
    child.kill = () => {};

    // Defer emission until after the caller (spawnOnce) has attached its listeners.
    setImmediate(() => {
      if (opts.stdout) stdout.emit('data', Buffer.from(opts.stdout));
      if (opts.stderr) stderr.emit('data', Buffer.from(opts.stderr));
      child.emit('close', opts.exitCode);
    });

    return child;
  };
}

function sequenceSpawn(...factories: Array<() => any>): SpawnLike {
  let i = 0;
  return ((_cmd: string, _args: readonly string[], _options: any) => {
    const factory = factories[i] ?? factories[factories.length - 1];
    i++;
    return factory();
  }) as SpawnLike;
}

describe('runTeamsCli', () => {
  beforeEach(() => {
    __setSpawnForTests(undefined); // reset to real spawn
  });
  afterEach(() => {
    __setSpawnForTests(undefined);
  });

  it('parses JSON stdout on exit code 0', async () => {
    __setSpawnForTests(sequenceSpawn(
      makeChildFactory({ stdout: '[{"id":"x"}]', exitCode: 0 }),
    ));
    const result = await runTeamsCli<Array<{ id: string }>>(['list-chats', '--top', '1']);
    expect(result).toEqual([{ id: 'x' }]);
  });

  it('throws TeamsCliError with auth_required on exit code 4', async () => {
    __setSpawnForTests(sequenceSpawn(
      makeChildFactory({ stderr: '{"code":"AUTH_EXPIRED"}', exitCode: 4 }),
    ));
    await expect(runTeamsCli(['list-chats'])).rejects.toMatchObject({
      name: 'TeamsCliError',
      code: 'auth_required',
      exitCode: 4,
      retryable: false,
    });
  });

  it('retries on exit code 5 then succeeds', async () => {
    __setSpawnForTests(sequenceSpawn(
      makeChildFactory({ stderr: '{"code":"timeout"}', exitCode: 5 }),
      makeChildFactory({ stderr: '{"code":"timeout"}', exitCode: 5 }),
      makeChildFactory({ stdout: '{"ok":true}', exitCode: 0 }),
    ));
    const result = await runTeamsCli<{ ok: boolean }>(['list-chats']);
    expect(result).toEqual({ ok: true });
  }, 15_000);

  it('throws invalid_input on exit code 2 without retry', async () => {
    __setSpawnForTests(sequenceSpawn(
      makeChildFactory({ stderr: 'bad args', exitCode: 2 }),
    ));
    await expect(runTeamsCli(['bogus'])).rejects.toMatchObject({
      code: 'invalid_input',
      exitCode: 2,
    });
  });

  it('appends --no-auto-reauth but never --json', async () => {
    // teams-cli defines no --json global option (teams-access/src/cli.ts), unlike
    // outlook-cli. Adding one would make commander reject every call.
    let capturedArgs: readonly string[] = [];
    __setSpawnForTests(((_cmd: string, args: readonly string[]) => {
      capturedArgs = args;
      return makeChildFactory({ stdout: '{}', exitCode: 0 })();
    }) as SpawnLike);
    await runTeamsCli(['list-chats']);
    expect(capturedArgs).toContain('--no-auto-reauth');
    expect(capturedArgs).not.toContain('--json');
  });

  it('does not duplicate --no-auto-reauth when the caller already passed it', async () => {
    let capturedArgs: readonly string[] = [];
    __setSpawnForTests(((_cmd: string, args: readonly string[]) => {
      capturedArgs = args;
      return makeChildFactory({ stdout: '{}', exitCode: 0 })();
    }) as SpawnLike);
    await runTeamsCli(['list-chats', '--no-auto-reauth']);
    expect(capturedArgs.filter(a => a === '--no-auto-reauth')).toHaveLength(1);
  });
});

/** Spawn stub that answers every attempt identically and counts the attempts. */
function countingSpawn(opts: { stdout?: string; stderr?: string; exitCode: number }): { spawn: SpawnLike; calls: () => number } {
  let calls = 0;
  const spawn = ((_cmd: string, _args: readonly string[], _options: any) => {
    calls++;
    return makeChildFactory(opts)();
  }) as SpawnLike;
  return { spawn, calls: () => calls };
}

describe('retry policy on exit 5', () => {
  afterEach(() => __setSpawnForTests(undefined));

  it('retries an idempotent read three times before giving up', async () => {
    const { spawn, calls } = countingSpawn({ stderr: '{"code":"timeout"}', exitCode: 5 });
    __setSpawnForTests(spawn);
    await expect(runTeamsCli(['list-chats'])).rejects.toMatchObject({ code: 'upstream' });
    expect(calls()).toBe(4); // initial attempt + 3 retries
  }, 15_000);

  it('never retries a non-idempotent write, so a lost response cannot post twice', async () => {
    const { spawn, calls } = countingSpawn({ stderr: '{"code":"timeout"}', exitCode: 5 });
    __setSpawnForTests(spawn);
    await expect(runTeamsCli(['send-message'], { idempotent: false })).rejects.toMatchObject({
      code: 'upstream',
      retryable: false,
    });
    expect(calls()).toBe(1);
  });

  it('tells the caller the upstream state is unknown rather than reporting a clean failure', async () => {
    __setSpawnForTests(countingSpawn({ stderr: 'timeout', exitCode: 5 }).spawn);
    const err = (await runTeamsCli(['send-message'], { idempotent: false })
      .catch((e: unknown) => e)) as TeamsCliError;
    expect(err.remediation).toMatch(/NOT retried/);
    expect(err.remediation).toMatch(/may or may not have completed/);
  });
});

describe('shouldUseShell', () => {
  // process.platform cannot be varied per spawn, so the Windows combinations are
  // pinned on the pure helper that spawnOnce calls.
  it('never uses a shell off Windows', () => {
    expect(shouldUseShell('darwin', '/abs/node_modules/teams-cli/dist/cli.js')).toBe(false);
    expect(shouldUseShell('darwin', null)).toBe(false);
    expect(shouldUseShell('linux', '/abs/node_modules/teams-cli/dist/cli.js')).toBe(false);
    expect(shouldUseShell('linux', null)).toBe(false);
  });

  it('never uses a shell for the bundled CLI, even on Windows', () => {
    // Bundled means spawning process.execPath, a real .exe: no cmd.exe, so
    // metacharacters in a message body stay inert.
    expect(shouldUseShell('win32', 'C:\\repo\\node_modules\\teams-cli\\dist\\cli.js')).toBe(false);
  });

  it('uses a shell only for the Windows PATH fallback', () => {
    expect(shouldUseShell('win32', null)).toBe(true);
  });
});

describe('spawn options', () => {
  afterEach(() => __setSpawnForTests(undefined));

  it.skipIf(process.platform === 'win32')('sets no shell option on this platform', async () => {
    let capturedOptions: Record<string, unknown> = {};
    __setSpawnForTests(((_cmd: string, _args: readonly string[], options: any) => {
      capturedOptions = options;
      return makeChildFactory({ stdout: '{}', exitCode: 0 })();
    }) as SpawnLike);
    await runTeamsCli(['list-chats']);
    expect(capturedOptions.stdio).toEqual(['ignore', 'pipe', 'pipe']);
    expect(capturedOptions.shell).toBeFalsy();
    expect(Object.hasOwn(capturedOptions, 'shell')).toBe(false);
  });
});

describe('TeamsCliError', () => {
  it('constructs with code, exit code, stderr, and remediation', () => {
    const err = new TeamsCliError('auth_required', 4, 'expired', false, 'Run login');
    expect(err.name).toBe('TeamsCliError');
    expect(err.code).toBe('auth_required');
    expect(err.exitCode).toBe(4);
    expect(err.remediation).toBe('Run login');
  });
});
