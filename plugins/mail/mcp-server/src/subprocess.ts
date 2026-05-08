// src/subprocess.ts
import { spawn as nodeSpawn } from 'node:child_process';
import type { ChildProcessWithoutNullStreams } from 'node:child_process';

export type OutlookCliErrorCode =
  | 'invalid_input'      // exit 2
  | 'config_error'       // exit 3
  | 'auth_required'      // exit 4
  | 'upstream'           // exit 5 (after retries exhausted)
  | 'io'                 // exit 6
  | 'internal';          // exit 1 or any other

export class OutlookCliError extends Error {
  constructor(
    public readonly code: OutlookCliErrorCode,
    public readonly exitCode: number,
    public readonly stderr: string,
    public readonly retryable: boolean,
    public readonly remediation?: string,
  ) {
    super(`outlook-cli ${code} (exit ${exitCode}): ${stderr}`);
    this.name = 'OutlookCliError';
  }
}

const EXIT_CODE_MAP: Record<number, { code: OutlookCliErrorCode; retryable: boolean }> = {
  1: { code: 'internal', retryable: false },
  2: { code: 'invalid_input', retryable: false },
  3: { code: 'config_error', retryable: false },
  4: { code: 'auth_required', retryable: false },
  5: { code: 'upstream', retryable: true },
  6: { code: 'io', retryable: false },
};

const RETRY_DELAYS_MS = [500, 1500, 4000];

function sleep(ms: number): Promise<void> {
  return new Promise(r => setTimeout(r, ms));
}

interface SpawnResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

// Minimal shape of the spawn function we need. Allows tests to inject a fake.
export type SpawnLike = (
  command: string,
  args: readonly string[],
  options: { stdio: ['ignore', 'pipe', 'pipe'] },
) => ChildProcessWithoutNullStreams;

let spawnImpl: SpawnLike = nodeSpawn as unknown as SpawnLike;

/** Test-only: replace the spawn implementation. Pass undefined to reset. */
export function __setSpawnForTests(impl: SpawnLike | undefined): void {
  spawnImpl = (impl ?? (nodeSpawn as unknown as SpawnLike));
}

function spawnOnce(args: string[], timeoutMs: number): Promise<SpawnResult> {
  return new Promise((resolve, reject) => {
    const isWindows = process.platform === 'win32';
    const child = spawnImpl('outlook-cli', args, { stdio: ['ignore', 'pipe', 'pipe'], ...(isWindows && { shell: true }) } as any);
    let stdout = '', stderr = '';
    child.stdout.on('data', (b: Buffer) => { stdout += b.toString(); });
    child.stderr.on('data', (b: Buffer) => { stderr += b.toString(); });
    const timer = setTimeout(() => {
      child.kill('SIGTERM');
      reject(new Error(`outlook-cli timed out after ${timeoutMs}ms`));
    }, timeoutMs);
    child.on('close', (exitCode: number | null) => {
      clearTimeout(timer);
      resolve({ exitCode: exitCode ?? 1, stdout, stderr });
    });
    child.on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });
  });
}

export interface RunOutlookCliOpts {
  timeoutMs?: number;
  noAutoReauth?: boolean;       // default true — MCP wrapper never wants browser pop-up
}

export async function runOutlookCli<T = unknown>(
  args: string[],
  opts: RunOutlookCliOpts = {},
): Promise<T> {
  const finalArgs = [...args];
  if (opts.noAutoReauth !== false && !finalArgs.includes('--no-auto-reauth')) {
    finalArgs.push('--no-auto-reauth');
  }
  if (!finalArgs.includes('--json')) {
    finalArgs.push('--json');
  }
  const timeoutMs = opts.timeoutMs ?? 60_000;

  for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
    const result = await spawnOnce(finalArgs, timeoutMs);

    if (result.exitCode === 0) {
      try { return JSON.parse(result.stdout) as T; }
      catch (e) {
        throw new OutlookCliError('internal', 0,
          `Failed to parse JSON stdout: ${(e as Error).message}; raw="${result.stdout.slice(0, 200)}"`,
          false);
      }
    }

    const mapping = EXIT_CODE_MAP[result.exitCode] ?? { code: 'internal' as const, retryable: false };

    if (mapping.retryable && attempt < RETRY_DELAYS_MS.length) {
      await sleep(RETRY_DELAYS_MS[attempt]);
      continue;
    }

    const remediation = mapping.code === 'auth_required'
      ? 'Run `outlook-cli login` then retry.'
      : undefined;

    throw new OutlookCliError(mapping.code, result.exitCode, result.stderr, mapping.retryable, remediation);
  }

  throw new OutlookCliError('upstream', 5, 'Retries exhausted', true);
}
