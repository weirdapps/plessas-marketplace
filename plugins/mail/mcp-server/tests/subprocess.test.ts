// tests/subprocess.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EventEmitter } from 'node:events';
import {
  runOutlookCli,
  OutlookCliError,
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

describe('OutlookCliError', () => {
  it('constructs with code, exit code, stderr, and remediation', () => {
    const err = new OutlookCliError('auth_required', 4, 'expired', false, 'Run login');
    expect(err.name).toBe('OutlookCliError');
    expect(err.code).toBe('auth_required');
    expect(err.exitCode).toBe(4);
    expect(err.remediation).toBe('Run login');
  });
});
