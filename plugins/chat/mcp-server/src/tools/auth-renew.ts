import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const authRenewTool: Tool = {
  name: 'teams_auth_renew',
  description: 'Silently renew the Teams Bearer using the persisted browser profile (headless).',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  handler: async () => runTeamsCli(['auth-renew']),
};
