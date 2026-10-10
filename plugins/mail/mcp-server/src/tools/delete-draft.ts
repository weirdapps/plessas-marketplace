// src/tools/delete-draft.ts
import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

/**
 * Deletes unsent drafts and nothing else. The CLI fetches every id and refuses
 * any message whose server-side IsDraft is not true, before issuing a DELETE,
 * so this tool cannot clear received or sent mail. That is why it needs no
 * folder argument and why outlook_move_mail can keep refusing Deleted Items.
 * Exchange keeps a deleted draft in Deleted Items.
 */
export const deleteDraftTool: Tool = {
  name: 'outlook_delete_draft',
  description: 'Delete unsent drafts by id (from outlook_list_mail folder:"Drafts"). Refuses any message that is not a draft. Deleted drafts go to Deleted Items. ids[] up to 20 per call.',
  inputSchema: {
    type: 'object',
    properties: {
      ids: { type: 'array', items: { type: 'string' }, minItems: 1, maxItems: 20 },
      continueOnError: { type: 'boolean', default: true },
    },
    required: ['ids'],
    additionalProperties: false,
  },
  handler: async (args) => {
    const cliArgs = ['delete-draft', ...args.ids];
    const continueOnError = args.continueOnError !== false;
    if (continueOnError) cliArgs.push('--continue-on-error');
    // Like move-mail: not idempotent (a deleted id is gone), and with
    // --continue-on-error the CLI prints the payload then exits 5 to flag failed[].
    return runOutlookCli(cliArgs, { idempotent: false, payloadExitCodes: continueOnError ? [5] : [] });
  },
};
