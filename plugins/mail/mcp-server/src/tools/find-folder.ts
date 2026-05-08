// src/tools/find-folder.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const findFolderTool: Tool = {
  name: 'outlook_find_folder',
  description: 'Resolve a folder by display-name path (e.g. "Inbox/Projects/Alpha"). Returns folder Id or null.',
  inputSchema: {
    type: 'object',
    properties: { path: { type: 'string' } },
    required: ['path'],
    additionalProperties: false,
  },
  handler: async (args) => runOutlookCli(['find-folder', args.path]),
};
