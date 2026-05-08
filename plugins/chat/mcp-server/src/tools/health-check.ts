import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const healthCheckTool: Tool = {
  name: 'teams_health_check',
  description: 'Probe Graph + chatsvc + chatsvcagg endpoints and report status for each.',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  handler: async () => runTeamsCli(['health-check'], { timeoutMs: 30_000 }),
};
