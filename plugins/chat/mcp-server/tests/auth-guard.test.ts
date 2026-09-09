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

  it('returns ok with hoursRemaining when teams-cli reports ok status', async () => {
    const expiresAt = new Date(Date.now() + 8 * 3600_000).toISOString();
    __setSpawnForTests(fakeSpawnReturning({
      stdout: JSON.stringify({
        status: 'ok',
        tokenExpiresAt: expiresAt,
        account: { upn: 'user@example.com', displayName: 'A User' },
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

  it('returns expired when the CLI reports a non-ok status', async () => {
    __setSpawnForTests(fakeSpawnReturning({
      stdout: JSON.stringify({ status: 'expired' }),
      exitCode: 0,
    }));
    const result = await checkAuth();
    expect(result.status).toBe('expired');
  });

  it('reports hoursRemaining 0 when the CLI omits tokenExpiresAt', async () => {
    __setSpawnForTests(fakeSpawnReturning({
      stdout: JSON.stringify({ status: 'ok' }),
      exitCode: 0,
    }));
    const result = await checkAuth();
    expect(result.status).toBe('ok');
    expect(result.hoursRemaining).toBe(0);
  });

  it('rethrows non-auth errors instead of masking them as missing', async () => {
    __setSpawnForTests(fakeSpawnReturning({
      stderr: 'bad args',
      exitCode: 2,
    }));
    await expect(checkAuth()).rejects.toMatchObject({ code: 'invalid_input' });
  });
});
