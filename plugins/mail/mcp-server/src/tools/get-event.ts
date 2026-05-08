// src/tools/get-event.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const getEventTool: Tool = {
  name: 'outlook_get_event',
  description: 'Retrieve a single calendar event by Id.',
  inputSchema: {
    type: 'object',
    properties: { id: { type: 'string' } },
    required: ['id'],
    additionalProperties: false,
  },
  handler: async (args) => runOutlookCli(['get-event', args.id]),
};
