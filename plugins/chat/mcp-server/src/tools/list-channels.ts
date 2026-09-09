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
    // The CLI needs one of the two modes (teams-access/src/cli.ts:101-102):
    // --team-id for a single team, --all-teams to flatten across every team.
    // Sending neither exited 2, so the "Omit for all teams" the schema advertises
    // was unreachable. Wire the flag rather than withdraw the mode.
    const cliArgs = ['list-channels'];
    if (args.team_id) cliArgs.push('--team-id', args.team_id);
    else cliArgs.push('--all-teams');
    return runTeamsCli(cliArgs);
  },
};
