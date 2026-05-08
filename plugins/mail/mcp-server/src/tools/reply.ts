// src/tools/reply.ts
//
// Wrappers for `outlook-cli reply` and `reply-all`. Both default to
// draft-first (creates draft + activates Outlook). signature_file optional —
// defaults to ~/.outlook-cli/signature.html.

import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

interface ReplyArgs {
  message_id: string;
  html_body?: string;
  text_body?: string;
  html_file?: string;
  text_file?: string;
  signature_file?: string;
  no_signature?: boolean;
  no_cc_self?: boolean;
  send_now?: boolean;
  no_open?: boolean;
  dry_run?: boolean;
}

const REPLY_SCHEMA = {
  type: 'object',
  properties: {
    message_id: { type: 'string', minLength: 1 },
    html_body: { type: 'string' },
    text_body: { type: 'string' },
    html_file: { type: 'string' },
    text_file: { type: 'string' },
    signature_file: { type: 'string' },
    no_signature: { type: 'boolean', default: false },
    no_cc_self: {
      type: 'boolean',
      default: false,
      description: 'Suppress automatic CC to authenticated user (default: CC-self ON).',
    },
    send_now: { type: 'boolean', default: false },
    no_open: { type: 'boolean', default: false },
    dry_run: { type: 'boolean', default: false },
  },
  required: ['message_id'],
  additionalProperties: false,
} as const;

async function buildReplyCliArgs(
  command: 'reply' | 'reply-all',
  args: ReplyArgs,
): Promise<{ cliArgs: string[]; cleanup: string[] }> {
  const cliArgs: string[] = [command, args.message_id];
  const cleanup: string[] = [];
  const fs = await import('node:fs/promises');
  const path = await import('node:path');
  const os = await import('node:os');

  if (typeof args.html_file === 'string') {
    cliArgs.push('--html', args.html_file);
  } else if (typeof args.html_body === 'string') {
    const p = path.join(os.tmpdir(), `outlook-cli-reply-${Date.now()}-${Math.random().toString(36).slice(2)}.html`);
    await fs.writeFile(p, args.html_body, 'utf-8');
    cliArgs.push('--html', p);
    cleanup.push(p);
  } else if (typeof args.text_file === 'string') {
    cliArgs.push('--text', args.text_file);
  } else if (typeof args.text_body === 'string') {
    const p = path.join(os.tmpdir(), `outlook-cli-reply-${Date.now()}-${Math.random().toString(36).slice(2)}.txt`);
    await fs.writeFile(p, args.text_body, 'utf-8');
    cliArgs.push('--text', p);
    cleanup.push(p);
  }

  if (typeof args.signature_file === 'string') {
    cliArgs.push('--signature', args.signature_file);
  }
  if (args.no_signature === true) cliArgs.push('--no-signature');
  if (args.no_cc_self === true) cliArgs.push('--no-cc-self');
  if (args.send_now === true) cliArgs.push('--send-now');
  if (args.no_open === true) cliArgs.push('--no-open');
  if (args.dry_run === true) cliArgs.push('--dry-run');

  return { cliArgs, cleanup };
}

async function cleanupTemp(paths: string[]): Promise<void> {
  if (paths.length === 0) return;
  const fs = await import('node:fs/promises');
  await Promise.all(paths.map((p) => fs.unlink(p).catch(() => undefined)));
}

export const replyTool: Tool = {
  name: 'outlook_reply',
  description:
    'Reply to a message via outlook-cli. Default: creates draft (with auto-quoted ' +
    'original + signature) and activates Outlook desktop. Set send_now:true to dispatch.',
  inputSchema: REPLY_SCHEMA,
  handler: async (args: ReplyArgs) => {
    const { cliArgs, cleanup } = await buildReplyCliArgs('reply', args);
    try {
      return await runOutlookCli(cliArgs);
    } finally {
      await cleanupTemp(cleanup);
    }
  },
};

export const replyAllTool: Tool = {
  name: 'outlook_reply_all',
  description:
    'Reply-all to a message via outlook-cli. Recipients (To+Cc) pre-populated by ' +
    'M365 from the original. Same draft-first default as outlook_reply.',
  inputSchema: REPLY_SCHEMA,
  handler: async (args: ReplyArgs) => {
    const { cliArgs, cleanup } = await buildReplyCliArgs('reply-all', args);
    try {
      return await runOutlookCli(cliArgs);
    } finally {
      await cleanupTemp(cleanup);
    }
  },
};
