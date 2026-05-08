// src/tools/list-calendar.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const listCalendarTool: Tool = {
  name: 'outlook_list_calendar',
  description: 'List calendar events in a date window. from/to accept ISO timestamps or expressions like "now", "now + 14d".',
  inputSchema: {
    type: 'object',
    properties: {
      from: { type: 'string', default: 'now' },
      to: { type: 'string', default: 'now + 7d' },
    },
    additionalProperties: false,
  },
  handler: async (args) => {
    return runOutlookCli(['list-calendar', '--from', args.from ?? 'now', '--to', args.to ?? 'now + 7d']);
  },
};
