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
    return runTeamsCli(cliArgs, { noAutoReauth: false, timeoutMs: 120_000 });
  },
};
