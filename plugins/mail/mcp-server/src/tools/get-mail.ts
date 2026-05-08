// src/tools/get-mail.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const getMailTool: Tool = {
  name: 'outlook_get_mail',
  description: 'Retrieve a single message by Id with body + attachments metadata.',
  inputSchema: {
    type: 'object',
    properties: {
      id: { type: 'string' },
      body: { type: 'string', enum: ['html', 'text', 'none'], default: 'html' },
    },
    required: ['id'],
    additionalProperties: false,
  },
  handler: async (args) => {
    return runOutlookCli(['get-mail', args.id, '--body', args.body ?? 'html']);
  },
};
