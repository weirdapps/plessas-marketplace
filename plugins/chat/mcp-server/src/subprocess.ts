import { spawn as nodeSpawn } from 'node:child_process';
import type { ChildProcessWithoutNullStreams } from 'node:child_process';
import { createRequire } from 'node:module';

// Resolve teams-cli to an absolute path at module load.
// Bundled as a github dep in package.json — npm install puts it in node_modules.
// If resolution fails (e.g. legacy install with global `npm link`), fall back to
// PATH lookup of `teams-cli` so we don't break existing setups.
const _require = createRequire(import.meta.url);
let CLI_ABS_PATH: string | null = null;
try {
  CLI_ABS_PATH = _require.resolve('teams-cli/dist/cli.js');
} catch {
  CLI_ABS_PATH = null;
}

/** Diagnostic accessor for the doctor tool. */
export function getResolvedCli(): { mode: 'bundled' | 'path'; path: string; nodeBin: string; cliVersion: string | null } {
  let cliVersion: string | null = null;
  if (CLI_ABS_PATH) {
    try {
      const pkg = _require('teams-cli/package.json') as { version?: string };
      cliVersion = pkg.version ?? null;
    } catch { /* swallow */ }
  }
  return CLI_ABS_PATH
    ? { mode: 'bundled', path: CLI_ABS_PATH, nodeBin: process.execPath, cliVersion }
    : { mode: 'path', path: 'teams-cli', nodeBin: process.execPath, cliVersion: null };
}

export type TeamsCliErrorCode =
  | 'invalid_input'
  | 'config_error'
  | 'auth_required'
  | 'upstream'
  | 'io'
  | 'internal';

export class TeamsCliError extends Error {
  constructor(
    public readonly code: TeamsCliErrorCode,
    public readonly exitCode: number,
    public readonly stderr: string,
    public readonly retryable: boolean,
    public readonly remediation?: string,
  ) {
    super(`teams-cli ${code} (exit ${exitCode}): ${stderr}`);
    this.name = 'TeamsCliError';
  }
}

const EXIT_CODE_MAP: Record<number, { code: TeamsCliErrorCode; retryable: boolean }> = {
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

export type SpawnLike = (
  command: string,
  args: readonly string[],
  options: { stdio: ['ignore', 'pipe', 'pipe'] },
) => ChildProcessWithoutNullStreams;

let spawnImpl: SpawnLike = nodeSpawn as unknown as SpawnLike;

export function __setSpawnForTests(impl: SpawnLike | undefined): void {
  spawnImpl = (impl ?? (nodeSpawn as unknown as SpawnLike));
}

function spawnOnce(args: string[], timeoutMs: number): Promise<SpawnResult> {
  return new Promise((resolve, reject) => {
    const isWindows = process.platform === 'win32';
    // Use absolute paths (current node + bundled CLI) when available — survives
    // PATH stripping in launchd/GUI launches and fnm session-bin rotation.
    // Fall back to bare command name if teams-cli isn't installed as a dep.
    const cmd = CLI_ABS_PATH ? process.execPath : 'teams-cli';
    const finalArgs = CLI_ABS_PATH ? [CLI_ABS_PATH, ...args] : args;
    const child = spawnImpl(cmd, finalArgs, { stdio: ['ignore', 'pipe', 'pipe'], ...(isWindows && { shell: true }) } as any);
    let stdout = '', stderr = '';
    child.stdout.on('data', (b: Buffer) => { stdout += b.toString(); });
    child.stderr.on('data', (b: Buffer) => { stderr += b.toString(); });
    const timer = setTimeout(() => {
      child.kill('SIGTERM');
      reject(new Error(`teams-cli timed out after ${timeoutMs}ms`));
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

export interface RunTeamsCliOpts {
  timeoutMs?: number;
  noAutoReauth?: boolean;
}

export async function runTeamsCli<T = unknown>(
  args: string[],
  opts: RunTeamsCliOpts = {},
): Promise<T> {
  const finalArgs = [...args];
  if (opts.noAutoReauth !== false && !finalArgs.includes('--no-auto-reauth')) {
    finalArgs.push('--no-auto-reauth');
  }
  const timeoutMs = opts.timeoutMs ?? 60_000;

  for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
    const result = await spawnOnce(finalArgs, timeoutMs);

    if (result.exitCode === 0) {
      try { return JSON.parse(result.stdout) as T; }
      catch (e) {
        throw new TeamsCliError('internal', 0,
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
      ? 'Run `teams-cli login` then retry.'
      : undefined;

    throw new TeamsCliError(mapping.code, result.exitCode, result.stderr, mapping.retryable, remediation);
  }

  throw new TeamsCliError('upstream', 5, 'Retries exhausted', true);
}
