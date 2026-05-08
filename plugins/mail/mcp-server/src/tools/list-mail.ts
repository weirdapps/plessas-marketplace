// src/tools/list-mail.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const listMailTool: Tool = {
  name: 'outlook_list_mail',
  description: 'List messages in a folder. Supports --since/--until/--all/--max for incremental sync.',
  inputSchema: {
    type: 'object',
    properties: {
      folder: { type: 'string', default: 'Inbox' },
      folderId: { type: 'string' },
      top: { type: 'integer', minimum: 1, maximum: 100 },
      since: { type: 'string', description: 'ISO-8601 UTC' },
      until: { type: 'string', description: 'ISO-8601 UTC' },
      all: { type: 'boolean', default: false },
      max: { type: 'integer', default: 10000 },
      select: { type: 'string' },
    },
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['list-mail'];
    if (args.folder) cliArgs.push('--folder', args.folder);
    if (args.folderId) cliArgs.push('--folder-id', args.folderId);
    if (args.top) cliArgs.push('--top', String(args.top));
    if (args.since) cliArgs.push('--since', args.since);
    if (args.until) cliArgs.push('--until', args.until);
    if (args.all) cliArgs.push('--all');
    if (args.max) cliArgs.push('--max', String(args.max));
    if (args.select) cliArgs.push('--select', args.select);
    return runOutlookCli(cliArgs);
  },
};
