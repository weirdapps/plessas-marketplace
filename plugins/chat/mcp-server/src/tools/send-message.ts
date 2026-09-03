import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

export const sendMessageTool: Tool = {
  name: 'teams_send_message',
  description: 'Send a message to a Teams chat via Graph. Channel sends are not supported (scope missing).',
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
    // Flag names must match teams-access/src/cli.ts:177-181 exactly: --chat,
    // --text, --html. This sent --chat-id and --body, which commander rejects
    // (no allowUnknownOption), so every send through the MCP bridge failed on
    // argument parsing before auth was even consulted. That made it look like
    // another symptom of the 2026-09-02 token outage rather than a separate bug.
    //
    // Route to --html when the body already looks like markup, otherwise --text,
    // so a plain string is not silently rendered as HTML and a crafted <p> block
    // is not escaped. House style for Teams is HTML.
    const body = String(args.body ?? '');
    const bodyFlag = /<[a-z][\s\S]*>/i.test(body) ? '--html' : '--text';
    return runTeamsCli(['send-message', '--chat', args.chat_id, bodyFlag, body]);
  },
};
