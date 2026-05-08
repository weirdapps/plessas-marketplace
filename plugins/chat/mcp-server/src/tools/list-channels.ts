import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const listChannelsTool: Tool = {
  name: 'teams_list_channels',
  description: 'List channels in a team or across all my teams.',
  inputSchema: {
    type: 'object',
    properties: {
      team_id: { type: 'string', description: 'Team ID to list channels for. Omit for all teams.' },
    },
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['list-channels'];
    if (args.team_id) cliArgs.push('--team-id', args.team_id);
    return runTeamsCli(cliArgs);
  },
};
