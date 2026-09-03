import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const listMessagesTool: Tool = {
  name: 'teams_list_messages',
  description: 'List messages in a chat OR channel. For chats, pass chat_id. For channels, pass team_id + channel_id.',
  inputSchema: {
    type: 'object',
    properties: {
      chat_id: { type: 'string', description: 'Chat ID (for 1:1/group chats).' },
      team_id: { type: 'string', description: 'Team ID (for channel messages, with channel_id).' },
      channel_id: { type: 'string', description: 'Channel ID (with team_id).' },
      top: { type: 'integer', minimum: 1, maximum: 100, description: 'Max messages to return.' },
      since: { type: 'string', description: 'ISO-8601 UTC timestamp — only messages after this.' },
    },
    additionalProperties: false,
  },
  handler: async (args) => {
    // Flag names must match teams-access/src/cli.ts:133-136 exactly: --chat,
    // --team, --channel, --page-size. These were --chat-id / --team-id /
    // --channel-id / --top / --since, none of which commander accepts (there is
    // no allowUnknownOption), so every call failed on argument parsing.
    // --since has no CLI equivalent at all and is dropped rather than faked.
    const cliArgs = ['list-messages'];
    if (args.chat_id) cliArgs.push('--chat', args.chat_id);
    if (args.team_id) cliArgs.push('--team', args.team_id);
    if (args.channel_id) cliArgs.push('--channel', args.channel_id);
    if (args.top) cliArgs.push('--page-size', String(args.top));
    return runTeamsCli(cliArgs);
  },
};
