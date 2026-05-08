// src/tools/capture-signature.ts
//
// Wrapper for `outlook-cli capture-signature` — one-time bootstrap of the
// signature file used by reply/reply-all/forward.

import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const captureSignatureTool: Tool = {
  name: 'outlook_capture_signature',
  description:
    'Extract email signature from a SentItems message and save to ' +
    '~/.outlook-cli/signature.html (default). Heuristic: tries Outlook web ' +
    'wrappers first, falls back to last <hr> or pre-reply-marker block. ' +
    'Hand-edit the output file to refine if the heuristic captures too much.',
  inputSchema: {
    type: 'object',
    properties: {
      from_message: {
        type: 'string',
        description: 'Override: source message id (default: latest in SentItems)',
      },
      out: {
        type: 'string',
        description: 'Override output path (default: ~/.outlook-cli/signature.html)',
      },
    },
    additionalProperties: false,
  },
  handler: async (args: any) => {
    const cliArgs = ['capture-signature'];
    if (typeof args.from_message === 'string' && args.from_message.length > 0) {
      cliArgs.push('--from-message', args.from_message);
    }
    if (typeof args.out === 'string' && args.out.length > 0) {
      cliArgs.push('--out', args.out);
    }
    return runOutlookCli(cliArgs);
  },
};
