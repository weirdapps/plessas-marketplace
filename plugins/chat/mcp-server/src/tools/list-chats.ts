import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const listChatsTool: Tool = {
  name: 'teams_list_chats',
  description: 'List my chats (1:1, group, meeting). Returns recently-active chats with members and last message preview.',
  inputSchema: {
    type: 'object',
    properties: {
      top: { type: 'integer', minimum: 1, maximum: 100, description: 'Max chats to return.' },
    },
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['list-chats'];
    if (args.top) cliArgs.push('--top', String(args.top));
    return runTeamsCli(cliArgs);
  },
};
