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

// A shell is needed only for the Windows PATH fallback, where the target is the
// `teams-cli` .cmd shim that Node >= 20.12.2 refuses to spawn without one.
// The bundled path runs process.execPath, a real .exe, so it needs no shell: with
// one, every argument goes through cmd.exe and the user-controlled message body
// and chat id become shell metacharacters.
export function shouldUseShell(platform: string, cliAbsPath: string | null): boolean {
  return platform === 'win32' && cliAbsPath === null;
}

function spawnOnce(args: string[], timeoutMs: number): Promise<SpawnResult> {
  return new Promise((resolve, reject) => {
    const useShell = shouldUseShell(process.platform, CLI_ABS_PATH);
    // Use absolute paths (current node + bundled CLI) when available — survives
    // PATH stripping in launchd/GUI launches and fnm session-bin rotation.
    // Fall back to bare command name if teams-cli isn't installed as a dep.
    // That fallback is the one remaining shell-exposed path, reached only by a
    // legacy `npm link` install on Windows.
    const cmd = CLI_ABS_PATH ? process.execPath : 'teams-cli';
    const finalArgs = CLI_ABS_PATH ? [CLI_ABS_PATH, ...args] : args;
    const child = spawnImpl(cmd, finalArgs, { stdio: ['ignore', 'pipe', 'pipe'], ...(useShell && { shell: true }) } as any);
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
  /**
   * Default true. Exit 5 covers "response lost" as well as "call failed", so a
   * timed-out send-message may already have been posted. Retrying it posts it
   * again. Set false on every non-idempotent write: the caller then gets one
   * error saying the upstream state is unknown instead of up to four messages.
   */
  idempotent?: boolean;
  /**
   * Exit codes whose stdout still carries a payload the caller wants. Several CLI
   * commands print their result and only THEN set a non-zero exit to flag a bad
   * state (health-check writes its report, then exits 5 for broken or 1 for
   * degraded). Throwing that away loses the only report of what actually
   * happened. Empty by default; a code listed here still falls through to the
   * error path if stdout does not parse.
   */
  payloadExitCodes?: number[];
}

export async function runTeamsCli<T = unknown>(
  args: string[],
  opts: RunTeamsCliOpts = {},
): Promise<T> {
  const idempotent = opts.idempotent !== false;
  const payloadExitCodes = opts.payloadExitCodes ?? [];
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

    // Non-zero exit that still carries a report: the payload is already on stdout
    // and is the only place the caller learns what happened.
    if (payloadExitCodes.includes(result.exitCode) && result.stdout.trim() !== '') {
      try { return JSON.parse(result.stdout) as T; }
      catch { /* not a payload after all: fall through to the normal error path */ }
    }

    const mapping = EXIT_CODE_MAP[result.exitCode] ?? { code: 'internal' as const, retryable: false };
    const retryable = mapping.retryable && idempotent;

    if (retryable && attempt < RETRY_DELAYS_MS.length) {
      await sleep(RETRY_DELAYS_MS[attempt]);
      continue;
    }

    let remediation: string | undefined;
    if (mapping.code === 'auth_required') {
      remediation = 'Run `teams-cli login` then retry.';
    } else if (mapping.code === 'upstream' && !idempotent) {
      remediation = 'NOT retried, because this operation is not idempotent and exit 5 covers a lost response as well as a failed call: '
        + 'the upstream state is unknown and the operation may or may not have completed. '
        + 'Read the chat back before repeating it.';
    }

    throw new TeamsCliError(mapping.code, result.exitCode, result.stderr, retryable, remediation);
  }

  throw new TeamsCliError('upstream', 5, 'Retries exhausted', true);
}
