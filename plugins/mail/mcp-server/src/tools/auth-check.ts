// src/tools/auth-check.ts
import type { Tool } from '../tool.js';
import { checkAuth } from '../auth-guard.js';

export const authCheckTool: Tool = {
  name: 'outlook_auth_check',
  description: 'Check whether the cached outlook-cli session is still valid. Returns {status, hoursRemaining, account}.',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  handler: () => checkAuth(),
};
