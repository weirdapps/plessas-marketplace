import type { Tool } from '../tool.js';
import { checkAuth } from '../auth-guard.js';

export const authCheckTool: Tool = {
  name: 'teams_auth_check',
  description: 'Check whether the cached teams-cli session is still valid. Returns {status, hoursRemaining, account}.',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  handler: () => checkAuth(),
};
