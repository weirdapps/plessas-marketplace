// src/tools/doctor.ts
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Tool } from '../tool.js';
import { getResolvedCli } from '../subprocess.js';
import { checkAuth } from '../auth-guard.js';
import pkg from '../../package.json' with { type: 'json' };

// The server is started from two different depths: dist/tools/doctor.js (the
// tsc output) and bundle/server.mjs (the committed esbuild bundle). A fixed
// join(__dirname, '..', '..') is correct for at most one of them. From the
// bundle it resolved to plugins/<plugin>/ rather than the server root, and from
// a copy of the bundle in a temp directory it produced the suggestion
// "cd /private && npm install" and would have written .last-startup.json to a
// path nothing reads. Walk up instead, and accept only the directory whose
// package.json is this server's own, so a failure to find it is null rather
// than a plausible-looking wrong path.
export function findServerRoot(startDir: string): string | null {
  let dir = startDir;
  for (let hops = 0; hops < 8; hops++) {
    try {
      const found = JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8')) as { name?: string };
      if (found.name === pkg.name) return dir;
    } catch {
      // No package.json here, or it is unreadable or not JSON: keep walking.
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

const SERVER_ROOT = findServerRoot(dirname(fileURLToPath(import.meta.url)));
const STATUS_FILE = SERVER_ROOT === null ? null : join(SERVER_ROOT, '.last-startup.json');

interface LastStartup {
  ts: string;
  status: 'ok' | 'fail';
  error: string | null;
  node: string;
}

function readLastStartup(): LastStartup | null {
  if (STATUS_FILE === null) return null;
  try {
    return JSON.parse(readFileSync(STATUS_FILE, 'utf8'));
  } catch {
    return null;
  }
}

function buildSuggestion(opts: {
  cliMode: 'bundled' | 'path';
  authStatus: string;
  lastStartupStatus: 'ok' | 'fail' | 'unknown';
  lastStartupError: string | null;
  serverRoot: string | null;
}): string {
  if (opts.lastStartupStatus === 'fail') {
    return `Last MCP startup FAILED: ${opts.lastStartupError ?? 'unknown'}. Check stderr from Claude or run 'bash mcp-server/run.sh' manually to see the error.`;
  }
  if (opts.cliMode === 'path') {
    // Keep this command identical in shape to the one run.sh prints. A bare
    // `npm install` here would pull several hundred MB of Playwright browsers
    // that the bundled CLI does not need at install time.
    if (opts.serverRoot === null) {
      return 'teams-cli not bundled in mcp-server/node_modules. The MCP is using a global teams-cli on PATH. To get the bundled (more robust) install, run PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci in the plugin\'s mcp-server directory (this server could not locate its own package root, so there is no path to print).';
    }
    return `teams-cli not bundled in mcp-server/node_modules. The MCP is using a global teams-cli on PATH. To get the bundled (more robust) install, run: cd ${opts.serverRoot} && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci`;
  }
  if (opts.authStatus === 'missing' || opts.authStatus === 'expired') {
    return 'Auth missing/expired. Run: teams-cli login';
  }
  return 'All systems green.';
}

export const doctorTool: Tool = {
  name: 'teams_doctor',
  description: 'Diagnose the teams-bridge MCP: node binary, CLI install mode, CLI version, MCP server version, auth status, last startup, and a single-line next-step suggestion. Call this first when something is broken.',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  handler: async () => {
    const cli = getResolvedCli();
    // Same JSON import server.ts uses. The old runtime `_require('../../package.json')`
    // resolved relative to the emitted file, so it reported the version correctly
    // only from dist/tools/ and read 'unknown' from anywhere else.
    const mcpVersion = pkg.version;

    let auth: { status: string; hoursRemaining?: number; account?: { upn: string; displayName?: string } } | { status: string; error: string };
    try {
      auth = await checkAuth();
    } catch (e) {
      auth = { status: 'error', error: (e as Error).message };
    }

    const lastStartup = readLastStartup();
    const lastStartupStatus = lastStartup?.status ?? 'unknown';

    const suggestion = buildSuggestion({
      cliMode: cli.mode,
      authStatus: auth.status,
      lastStartupStatus,
      lastStartupError: lastStartup?.error ?? null,
      serverRoot: SERVER_ROOT,
    });

    return {
      mcpServer: { name: 'teams-bridge', version: mcpVersion },
      node: { path: cli.nodeBin, version: process.version },
      cli: { mode: cli.mode, path: cli.path, version: cli.cliVersion },
      // Reported so the anchor is visible rather than inferred: a wrong
      // serverRoot is what made the old suggestion nonsense from a bundle.
      serverRoot: SERVER_ROOT,
      auth,
      lastStartup,
      suggestion,
    };
  },
};
