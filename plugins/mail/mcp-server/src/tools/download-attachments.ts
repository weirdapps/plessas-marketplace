// src/tools/download-attachments.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const downloadAttachmentsTool: Tool = {
  name: 'outlook_download_attachments',
  description: 'Save attachments from a message to a directory. Use include_inline:true for inline images.',
  inputSchema: {
    type: 'object',
    properties: {
      id: { type: 'string' },
      out: { type: 'string', description: 'Absolute path to output directory' },
      includeInline: { type: 'boolean', default: false },
      overwrite: { type: 'boolean', default: false },
    },
    required: ['id', 'out'],
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['download-attachments', args.id, '--out', args.out];
    if (args.includeInline) cliArgs.push('--include-inline');
    if (args.overwrite) cliArgs.push('--overwrite');
    return runOutlookCli(cliArgs);
  },
};
