import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const sendMessageTool: Tool = {
  name: 'teams_send_message',
  description: 'Send a message to a chat (Graph). Channel sends are NOT supported (scope missing). Draft-only by design — confirm before sending.',
  inputSchema: {
    type: 'object',
    properties: {
      chat_id: { type: 'string', description: 'Chat ID to send to.' },
      body: { type: 'string', description: 'Message body (HTML or plain text).' },
    },
    required: ['chat_id', 'body'],
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['send-message', '--chat-id', args.chat_id, '--body', args.body];
    return runTeamsCli(cliArgs);
  },
};
