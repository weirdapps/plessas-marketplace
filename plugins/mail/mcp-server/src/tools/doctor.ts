// src/tools/doctor.ts
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import type { Tool } from '../tool.js';
import { getResolvedCli } from '../subprocess.js';
import { checkAuth } from '../auth-guard.js';

const _require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));
const SERVER_ROOT = join(__dirname, '..', '..');
const STATUS_FILE = join(SERVER_ROOT, '.last-startup.json');

interface LastStartup {
  ts: string;
  status: 'ok' | 'fail';
  error: string | null;
  node: string;
}

function readLastStartup(): LastStartup | null {
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
}): string {
  if (opts.lastStartupStatus === 'fail') {
    return `Last MCP startup FAILED: ${opts.lastStartupError ?? 'unknown'}. Check stderr from Claude or run 'bash mcp-server/run.sh' manually to see the error.`;
  }
  if (opts.cliMode === 'path') {
    return `outlook-tool not bundled in mcp-server/node_modules. The MCP is using a global outlook-cli on PATH. To get the bundled (more robust) install, run: cd ${SERVER_ROOT} && npm install`;
  }
  if (opts.authStatus === 'missing' || opts.authStatus === 'expired') {
    return 'Auth missing/expired. Run: outlook-cli login --sharepoint-host groupnbg.sharepoint.com';
  }
  return 'All systems green.';
}

export const doctorTool: Tool = {
  name: 'outlook_doctor',
  description: 'Diagnose the outlook-bridge MCP: node binary, CLI install mode, CLI version, MCP server version, auth status, last startup, and a single-line next-step suggestion. Call this first when something is broken.',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  handler: async () => {
    const cli = getResolvedCli();
    let mcpVersion = 'unknown';
    try {
      const pkg = _require('../../package.json') as { version?: string };
      mcpVersion = pkg.version ?? 'unknown';
    } catch { /* ignore */ }

    let auth: { status: string; hoursRemaining?: number; account?: { upn: string } } | { status: string; error: string };
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
    });

    return {
      mcpServer: { name: 'outlook-bridge', version: mcpVersion },
      node: { path: cli.nodeBin, version: process.version },
      cli: { mode: cli.mode, path: cli.path, version: cli.cliVersion },
      auth,
      lastStartup,
      suggestion,
    };
  },
};
