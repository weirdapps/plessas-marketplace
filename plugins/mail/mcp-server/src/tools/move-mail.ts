// src/tools/move-mail.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const moveMailTool: Tool = {
  name: 'outlook_move_mail',
  description: 'Move messages to a folder. ids[] up to 20 per call. continue_on_error:true reports failures without aborting.',
  inputSchema: {
    type: 'object',
    properties: {
      ids: { type: 'array', items: { type: 'string' }, minItems: 1, maxItems: 20 },
      to: { type: 'string', description: 'Folder path, alias, or "id:<raw>"' },
      continueOnError: { type: 'boolean', default: true },
    },
    required: ['ids', 'to'],
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['move-mail', ...args.ids, '--to', args.to];
    if (args.continueOnError !== false) cliArgs.push('--continue-on-error');
    return runOutlookCli(cliArgs);
  },
};
