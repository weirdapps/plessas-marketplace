// src/tools/move-mail.ts
import type { Tool } from '../tool.js';
import { runOutlookCli, OutlookCliError } from '../subprocess.js';

/**
 * Leaf folder names this tool refuses to move mail into.
 *
 * Compared with spaces stripped and case folded, so the display form ("Deleted
 * Items") and the well-known alias the CLI documents ("DeletedItems") are both
 * caught. Matching only the display form would leave the canonical spelling as
 * a hole, which is worse than no check.
 */
const BLOCKED_DESTINATIONS = new Set([
  'deleteditems', 'junkemail', 'junk', 'trash', 'recoverableitems',
]);

/**
 * Best-effort, BY NAME ONLY. `--to` also accepts `id:<raw>`, and no string check
 * can tell which folder a raw id points at, so a caller determined to reach
 * Deleted Items still can. This stops the accidental bulk move, not a deliberate
 * one, and should not be described as a complete guarantee.
 */
export function isBlockedDestination(to: string): boolean {
  const leaf = to.split(/[/\\]/).pop() ?? '';
  return BLOCKED_DESTINATIONS.has(leaf.replace(/\s+/g, '').toLowerCase());
}

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
    if (isBlockedDestination(String(args.to))) {
      const refusal = new OutlookCliError(
        'invalid_input', 2,
        `destination '${args.to}' is not allowed`, false,
        'This tool does not move mail into Deleted Items, Junk or Trash. Delete from Outlook directly if that is really what you want.',
      );
      // The constructor prefixes "outlook-cli ... (exit 2)", which would credit the
      // refusal to a CLI that was never spawned. Say who actually refused.
      refusal.message = `outlook-bridge refused this move: destination '${args.to}' is not allowed (outlook-cli was not called)`;
      throw refusal;
    }
    const cliArgs = ['move-mail', ...args.ids, '--to', args.to];
    const continueOnError = args.continueOnError !== false;
    if (continueOnError) cliArgs.push('--continue-on-error');
    // Not idempotent: the source ids are gone once a move lands, so a retry
    // reports failure for messages that did move. With --continue-on-error the
    // CLI prints the payload and then exits 5 to flag failed[] (cli.js emits the
    // result before setting process.exitCode = 5), so take the payload: it is
    // the only place the caller learns WHICH ids failed.
    return runOutlookCli(cliArgs, { idempotent: false, payloadExitCodes: continueOnError ? [5] : [] });
  },
};
