// src/tools/create-folder.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const createFolderTool: Tool = {
  name: 'outlook_create_folder',
  description: 'Create a folder by path. Idempotent when idempotent:true (no-op if it exists).',
  inputSchema: {
    type: 'object',
    properties: {
      path: { type: 'string' },
      createParents: { type: 'boolean', default: true },
      idempotent: { type: 'boolean', default: true },
    },
    required: ['path'],
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['create-folder', args.path];
    if (args.createParents !== false) cliArgs.push('--create-parents');
    if (args.idempotent !== false) cliArgs.push('--idempotent');
    return runOutlookCli(cliArgs);
  },
};
