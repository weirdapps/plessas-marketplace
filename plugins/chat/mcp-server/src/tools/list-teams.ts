import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const listTeamsTool: Tool = {
  name: 'teams_list_teams',
  description: 'List teams I belong to.',
  inputSchema: { type: 'object', properties: {}, additionalProperties: false },
  handler: async () => runTeamsCli(['list-teams']),
};
