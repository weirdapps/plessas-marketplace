// tests/auth-guard.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EventEmitter } from 'node:events';
import { checkAuth } from '../src/auth-guard.js';
import { __setSpawnForTests, type SpawnLike } from '../src/subprocess.js';

function fakeSpawnReturning(opts: { stdout?: string; stderr?: string; exitCode: number }): SpawnLike {
  return ((_cmd: string, _args: readonly string[], _options: any) => {
    const stdout = new EventEmitter();
    const stderr = new EventEmitter();
    const child = new EventEmitter() as any;
    child.stdout = stdout;
    child.stderr = stderr;
    child.kill = () => {};
    setImmediate(() => {
      if (opts.stdout) stdout.emit('data', Buffer.from(opts.stdout));
      if (opts.stderr) stderr.emit('data', Buffer.from(opts.stderr));
      child.emit('close', opts.exitCode);
    });
    return child;
  }) as SpawnLike;
}

describe('checkAuth', () => {
  beforeEach(() => __setSpawnForTests(undefined));
  afterEach(() => __setSpawnForTests(undefined));

  it('returns ok with hoursRemaining when outlook-cli reports ok status', async () => {
    const expiresAt = new Date(Date.now() + 8 * 3600_000).toISOString();
    __setSpawnForTests(fakeSpawnReturning({
      stdout: JSON.stringify({
        status: 'ok',
        tokenExpiresAt: expiresAt,
        account: { upn: 'user@example.com' },
      }),
      exitCode: 0,
    }));
    const result = await checkAuth();
    expect(result.status).toBe('ok');
    expect(result.hoursRemaining).toBeGreaterThanOrEqual(7);
    expect(result.account?.upn).toBe('user@example.com');
    expect(result.tokenExpiresAt).toBe(expiresAt);
  });

  it('returns missing on auth_required error (exit 4)', async () => {
    __setSpawnForTests(fakeSpawnReturning({
      stderr: '{"code":"AUTH_EXPIRED"}',
      exitCode: 4,
    }));
    const result = await checkAuth();
    expect(result.status).toBe('missing');
  });

  it('returns expired when CLI reports non-ok status', async () => {
    __setSpawnForTests(fakeSpawnReturning({
      stdout: JSON.stringify({ status: 'expired' }),
      exitCode: 0,
    }));
    const result = await checkAuth();
    expect(result.status).toBe('expired');
  });
});
