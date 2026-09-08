// src/subprocess.ts
import { spawn as nodeSpawn } from 'node:child_process';
import type { ChildProcessWithoutNullStreams } from 'node:child_process';
import { createRequire } from 'node:module';

// Resolve outlook-tool CLI to an absolute path at module load.
// Bundled as a github dep in package.json — npm install puts it in node_modules.
// If resolution fails (e.g. legacy install with global `npm link`), fall back to
// PATH lookup of `outlook-cli` so we don't break existing setups.
const _require = createRequire(import.meta.url);
let CLI_ABS_PATH: string | null = null;
try {
  CLI_ABS_PATH = _require.resolve('outlook-tool/dist/cli.js');
} catch {
  CLI_ABS_PATH = null;
}

/** Diagnostic accessor for the doctor tool. */
export function getResolvedCli(): { mode: 'bundled' | 'path'; path: string; nodeBin: string; cliVersion: string | null } {
  let cliVersion: string | null = null;
  if (CLI_ABS_PATH) {
    try {
      const pkg = _require('outlook-tool/package.json') as { version?: string };
      cliVersion = pkg.version ?? null;
    } catch { /* swallow */ }
  }
  return CLI_ABS_PATH
    ? { mode: 'bundled', path: CLI_ABS_PATH, nodeBin: process.execPath, cliVersion }
    : { mode: 'path', path: 'outlook-cli', nodeBin: process.execPath, cliVersion: null };
}

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

// A shell is needed only for the Windows PATH fallback, where the target is the
// `outlook-cli` .cmd shim that Node >= 20.12.2 refuses to spawn without one.
// The bundled path runs process.execPath, a real .exe, so it needs no shell: with
// one, every argument goes through cmd.exe and user-controlled mail subjects,
// bodies, recipients and search queries become shell metacharacters.
export function shouldUseShell(platform: string, cliAbsPath: string | null): boolean {
  return platform === 'win32' && cliAbsPath === null;
}

function spawnOnce(args: string[], timeoutMs: number): Promise<SpawnResult> {
  return new Promise((resolve, reject) => {
    const useShell = shouldUseShell(process.platform, CLI_ABS_PATH);
    // Use absolute paths (current node + bundled CLI) when available — survives
    // PATH stripping in launchd/GUI launches and fnm session-bin rotation.
    // Fall back to bare command name if outlook-tool isn't installed as a dep.
    // That fallback is the one remaining shell-exposed path, reached only by a
    // legacy `npm link` install on Windows.
    const cmd = CLI_ABS_PATH ? process.execPath : 'outlook-cli';
    const finalArgs = CLI_ABS_PATH ? [CLI_ABS_PATH, ...args] : args;
    const child = spawnImpl(cmd, finalArgs, { stdio: ['ignore', 'pipe', 'pipe'], ...(useShell && { shell: true }) } as any);
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
  /**
   * Default true. Exit 5 covers "response lost" as well as "call failed", so a
   * timed-out send-mail may already have been delivered. Retrying it delivers it
   * again. Set false on every non-idempotent write: the caller then gets one
   * error saying the upstream state is unknown instead of up to four sends.
   */
  idempotent?: boolean;
  /**
   * Exit codes whose stdout still carries a payload the caller wants. Several CLI
   * commands print their result and only THEN set a non-zero exit to flag a bad
   * state (move-mail sets 5 for a non-empty failed[]). Throwing that away loses
   * the only report of what actually happened. Empty by default; a code listed
   * here still falls through to the error path if stdout does not parse.
   */
  payloadExitCodes?: number[];
}

export async function runOutlookCli<T = unknown>(
  args: string[],
  opts: RunOutlookCliOpts = {},
): Promise<T> {
  const idempotent = opts.idempotent !== false;
  const payloadExitCodes = opts.payloadExitCodes ?? [];
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

    // Non-zero exit that still carries a report: the payload is already on stdout
    // and is the only place the caller learns what happened. Throwing it away and
    // retrying the whole batch would re-move the ids that already moved.
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
      remediation = 'Run `outlook-cli login` then retry.';
    } else if (mapping.code === 'upstream' && !idempotent) {
      remediation = 'NOT retried, because this operation is not idempotent and exit 5 covers a lost response as well as a failed call: '
        + 'the upstream state is unknown and the operation may or may not have completed. '
        + 'Check Drafts, Sent Items or the target folder before repeating it.';
    }

    throw new OutlookCliError(mapping.code, result.exitCode, result.stderr, retryable, remediation);
  }

  throw new OutlookCliError('upstream', 5, 'Retries exhausted', true);
}
