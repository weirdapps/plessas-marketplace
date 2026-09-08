import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const loginTool: Tool = {
  name: 'teams_login',
  description: 'Capture a Teams web session by signing in via Playwright Chrome window. Interactive — opens a browser.',
  inputSchema: {
    type: 'object',
    properties: {
      chrome_channel: { type: 'string', description: 'Playwright Chrome channel (e.g. "chrome", "msedge").' },
    },
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['login'];
    if (args.chrome_channel) cliArgs.push('--chrome-channel', args.chrome_channel);
    // Derived, not rounded: teams-cli's own loginTimeoutMs default is 300_000
    // (src/config/load.ts:18), plus the 15s process-startup allowance used across
    // this server. The old 120_000 killed an interactive sign-in at two minutes,
    // well inside the window a human needs for password plus MFA, and less than
    // half of what the CLI was still waiting on.
    return runTeamsCli(cliArgs, { noAutoReauth: false, timeoutMs: 315_000, idempotent: false });
  },
};
