// tests/subprocess.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EventEmitter } from 'node:events';
import {
  runOutlookCli,
  OutlookCliError,
  shouldUseShell,
  __setSpawnForTests,
  type SpawnLike,
} from '../src/subprocess.js';

/**
 * Build a fake child process that emits the given stdout, stderr, and exit code.
 * The child object exposes `.stdout.on`, `.stderr.on`, `.on`, and `.kill` like a real
 * ChildProcessWithoutNullStreams.
 */
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

describe('runOutlookCli', () => {
  beforeEach(() => {
    __setSpawnForTests(undefined); // reset to real spawn
  });
  afterEach(() => {
    __setSpawnForTests(undefined);
  });

  it('parses JSON stdout on exit code 0', async () => {
    __setSpawnForTests(sequenceSpawn(
      makeChildFactory({ stdout: '[{"Id":"x"}]', exitCode: 0 }),
    ));
    const result = await runOutlookCli<Array<{ Id: string }>>(['list-mail', '--top', '1']);
    expect(result).toEqual([{ Id: 'x' }]);
  });

  it('throws OutlookCliError with auth_required on exit code 4', async () => {
    __setSpawnForTests(sequenceSpawn(
      makeChildFactory({ stderr: '{"code":"AUTH_EXPIRED"}', exitCode: 4 }),
    ));
    await expect(runOutlookCli(['list-mail'])).rejects.toMatchObject({
      name: 'OutlookCliError',
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
    const result = await runOutlookCli<{ ok: boolean }>(['list-mail']);
    expect(result).toEqual({ ok: true });
  }, 15_000);

  it('throws invalid_input on exit code 2 without retry', async () => {
    __setSpawnForTests(sequenceSpawn(
      makeChildFactory({ stderr: 'bad args', exitCode: 2 }),
    ));
    await expect(runOutlookCli(['bogus'])).rejects.toMatchObject({
      code: 'invalid_input',
      exitCode: 2,
    });
  });

  it('appends --json and --no-auto-reauth automatically', async () => {
    let capturedArgs: readonly string[] = [];
    __setSpawnForTests(((_cmd: string, args: readonly string[]) => {
      capturedArgs = args;
      return makeChildFactory({ stdout: '{}', exitCode: 0 })();
    }) as SpawnLike);
    await runOutlookCli(['list-mail']);
    expect(capturedArgs).toContain('--json');
    expect(capturedArgs).toContain('--no-auto-reauth');
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
    await expect(runOutlookCli(['list-mail'])).rejects.toMatchObject({ code: 'upstream' });
    expect(calls()).toBe(4); // initial attempt + 3 retries
  }, 15_000);

  it('never retries a non-idempotent write, so a lost response cannot send twice', async () => {
    const { spawn, calls } = countingSpawn({ stderr: '{"code":"timeout"}', exitCode: 5 });
    __setSpawnForTests(spawn);
    await expect(runOutlookCli(['send-mail'], { idempotent: false })).rejects.toMatchObject({
      code: 'upstream',
      retryable: false,
    });
    expect(calls()).toBe(1);
  });

  it('tells the caller the upstream state is unknown rather than reporting a clean failure', async () => {
    __setSpawnForTests(countingSpawn({ stderr: 'timeout', exitCode: 5 }).spawn);
    const err = (await runOutlookCli(['send-mail'], { idempotent: false })
      .catch((e: unknown) => e)) as OutlookCliError;
    expect(err.remediation).toMatch(/NOT retried/);
    expect(err.remediation).toMatch(/may or may not have completed/);
  });

  it('still retries other calls that do not opt out', async () => {
    const { spawn, calls } = countingSpawn({ stderr: 'timeout', exitCode: 5 });
    __setSpawnForTests(spawn);
    await expect(runOutlookCli(['list-mail'], { idempotent: true })).rejects.toMatchObject({ code: 'upstream' });
    expect(calls()).toBe(4);
  }, 15_000);
});

describe('partial batch failure', () => {
  afterEach(() => __setSpawnForTests(undefined));

  // move-mail --continue-on-error prints the payload and only then sets exit 5
  // (outlook-tool dist/cli.js: emitResult, then process.exitCode = 5).
  const payload = {
    moved: [{ sourceId: 'a', newId: 'a2' }],
    failed: [{ sourceId: 'b', code: 'UPSTREAM_HTTP_404' }],
    summary: { requested: 2, moved: 1, failed: 1 },
  };

  it('returns the payload when the caller opted in', async () => {
    const { spawn, calls } = countingSpawn({ stdout: JSON.stringify(payload), exitCode: 5 });
    __setSpawnForTests(spawn);
    const result = await runOutlookCli(['move-mail'], { idempotent: false, payloadExitCodes: [5] });
    expect(result).toEqual(payload);
    expect(calls()).toBe(1);
  });

  it('throws normally when exit 5 carries no parseable payload', async () => {
    __setSpawnForTests(countingSpawn({ stderr: 'network down', exitCode: 5 }).spawn);
    await expect(runOutlookCli(['move-mail'], { idempotent: false, payloadExitCodes: [5] }))
      .rejects.toMatchObject({ code: 'upstream' });
  });

  it('does not swallow exit 5 for callers that did not opt in', async () => {
    __setSpawnForTests(countingSpawn({ stdout: JSON.stringify(payload), exitCode: 5 }).spawn);
    await expect(runOutlookCli(['move-mail'], { idempotent: false }))
      .rejects.toMatchObject({ code: 'upstream' });
  });
});

describe('shouldUseShell', () => {
  // process.platform cannot be varied per spawn, so the Windows combinations are
  // pinned on the pure helper that spawnOnce calls.
  it('never uses a shell off Windows', () => {
    expect(shouldUseShell('darwin', '/abs/node_modules/outlook-tool/dist/cli.js')).toBe(false);
    expect(shouldUseShell('darwin', null)).toBe(false);
    expect(shouldUseShell('linux', '/abs/node_modules/outlook-tool/dist/cli.js')).toBe(false);
    expect(shouldUseShell('linux', null)).toBe(false);
  });

  it('never uses a shell for the bundled CLI, even on Windows', () => {
    // Bundled means spawning process.execPath, a real .exe: no cmd.exe, so
    // metacharacters in a subject, body or search query stay inert.
    expect(shouldUseShell('win32', 'C:\\repo\\node_modules\\outlook-tool\\dist\\cli.js')).toBe(false);
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
    await runOutlookCli(['list-mail']);
    expect(capturedOptions.stdio).toEqual(['ignore', 'pipe', 'pipe']);
    expect(capturedOptions.shell).toBeFalsy();
    expect(Object.hasOwn(capturedOptions, 'shell')).toBe(false);
  });
});

describe('OutlookCliError', () => {
  it('constructs with code, exit code, stderr, and remediation', () => {
    const err = new OutlookCliError('auth_required', 4, 'expired', false, 'Run login');
    expect(err.name).toBe('OutlookCliError');
    expect(err.code).toBe('auth_required');
    expect(err.exitCode).toBe(4);
    expect(err.remediation).toBe('Run login');
  });
});
