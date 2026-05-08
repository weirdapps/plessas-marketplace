// src/tools/forward.ts
//
// Wrapper for `outlook-cli forward`. Required: message_id + to. Same
// draft-first default as send-mail / reply.

import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const forwardTool: Tool = {
  name: 'outlook_forward',
  description:
    'Forward a message via outlook-cli. M365 server auto-quotes the original. ' +
    'to[] is REQUIRED (forward target). Default: creates draft + activates Outlook.',
  inputSchema: {
    type: 'object',
    properties: {
      message_id: { type: 'string', minLength: 1 },
      to: {
        type: 'array',
        items: { type: 'string' },
        minItems: 1,
        description: 'Forward target(s). REQUIRED.',
      },
      cc: { type: 'array', items: { type: 'string' } },
      bcc: { type: 'array', items: { type: 'string' } },
      html_body: { type: 'string' },
      text_body: { type: 'string' },
      html_file: { type: 'string' },
      text_file: { type: 'string' },
      signature_file: { type: 'string' },
      no_signature: { type: 'boolean', default: false },
      no_cc_self: {
        type: 'boolean',
        default: false,
        description: 'Suppress automatic CC to authenticated user.',
      },
      send_now: { type: 'boolean', default: false },
      no_open: { type: 'boolean', default: false },
      dry_run: { type: 'boolean', default: false },
    },
    required: ['message_id', 'to'],
    additionalProperties: false,
  },
  handler: async (args: any) => {
    const cliArgs: string[] = ['forward', args.message_id];
    const cleanup: string[] = [];
    const fs = await import('node:fs/promises');
    const path = await import('node:path');
    const os = await import('node:os');

    for (const r of args.to as string[]) cliArgs.push('--to', r);
    if (Array.isArray(args.cc)) for (const r of args.cc) cliArgs.push('--cc', r);
    if (Array.isArray(args.bcc)) for (const r of args.bcc) cliArgs.push('--bcc', r);

    // Body source — at least one of html_*/text_* is required by the underlying
    // CLI. Forward typically has a one-line note, so html_body inline is common.
    if (typeof args.html_file === 'string') {
      cliArgs.push('--html', args.html_file);
    } else if (typeof args.html_body === 'string') {
      const p = path.join(os.tmpdir(), `outlook-cli-fwd-${Date.now()}-${Math.random().toString(36).slice(2)}.html`);
      await fs.writeFile(p, args.html_body, 'utf-8');
      cliArgs.push('--html', p);
      cleanup.push(p);
    } else if (typeof args.text_file === 'string') {
      cliArgs.push('--text', args.text_file);
    } else if (typeof args.text_body === 'string') {
      const p = path.join(os.tmpdir(), `outlook-cli-fwd-${Date.now()}-${Math.random().toString(36).slice(2)}.txt`);
      await fs.writeFile(p, args.text_body, 'utf-8');
      cliArgs.push('--text', p);
      cleanup.push(p);
    }

    if (typeof args.signature_file === 'string') cliArgs.push('--signature', args.signature_file);
    if (args.no_signature === true) cliArgs.push('--no-signature');
    if (args.no_cc_self === true) cliArgs.push('--no-cc-self');
    if (args.send_now === true) cliArgs.push('--send-now');
    if (args.no_open === true) cliArgs.push('--no-open');
    if (args.dry_run === true) cliArgs.push('--dry-run');

    try {
      return await runOutlookCli(cliArgs);
    } finally {
      if (cleanup.length > 0) {
        await Promise.all(cleanup.map((p) => fs.unlink(p).catch(() => undefined)));
      }
    }
  },
};
