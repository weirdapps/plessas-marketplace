// src/tools/list-folders.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const listFoldersTool: Tool = {
  name: 'outlook_list_folders',
  description: 'List mail folders with TotalItemCount. Set recursive:true to walk the whole tree.',
  inputSchema: {
    type: 'object',
    properties: { recursive: { type: 'boolean', default: false } },
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['list-folders'];
    if (args.recursive) cliArgs.push('--recursive');
    return runOutlookCli(cliArgs);
  },
};
