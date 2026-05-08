// src/tools/send-mail.ts
//
// Wrapper for `outlook-cli send-mail`. Default behavior creates a DRAFT and
// activates Microsoft Outlook desktop. Pass send_now:true to dispatch
// immediately. CC-self is ON by default per CLAUDE.md compliance rule.

import type { Tool } from '../tool.js';
import { runOutlookCli } from '../subprocess.js';

export const sendMailTool: Tool = {
  name: 'outlook_send_mail',
  description:
    'Send a new email via outlook-cli. Default: creates draft + activates Outlook ' +
    'desktop. Set send_now:true to dispatch immediately. CC-self is ON by default.',
  inputSchema: {
    type: 'object',
    properties: {
      to: {
        type: 'array',
        items: { type: 'string' },
        minItems: 1,
        description: 'TO recipients (one or more email addresses)',
      },
      cc: { type: 'array', items: { type: 'string' } },
      bcc: { type: 'array', items: { type: 'string' } },
      subject: { type: 'string', minLength: 1 },
      html_body: {
        type: 'string',
        description: 'HTML body content (preferred for Outlook). Inline OR via html_file.',
      },
      text_body: {
        type: 'string',
        description: 'Plain-text body content. Inline OR via text_file.',
      },
      html_file: { type: 'string', description: 'Path to HTML body file.' },
      text_file: { type: 'string', description: 'Path to text body file.' },
      attach: {
        type: 'array',
        items: { type: 'string' },
        description: 'File paths to attach (combined cap 30 MB).',
      },
      signature_file: {
        type: 'string',
        description: 'Override signature file path (default: ~/.outlook-cli/signature.html). Inline images auto-loaded from sibling signature-assets/ dir.',
      },
      no_signature: {
        type: 'boolean',
        default: false,
        description: 'Suppress automatic signature appending (default: signature ON).',
      },
      no_cc_self: {
        type: 'boolean',
        default: false,
        description: 'Suppress automatic CC to authenticated user.',
      },
      no_save_sent: { type: 'boolean', default: false },
      send_now: {
        type: 'boolean',
        default: false,
        description: 'Skip draft + Outlook activation, send immediately.',
      },
      no_open: {
        type: 'boolean',
        default: false,
        description: 'Do not activate Outlook desktop after creating draft.',
      },
      dry_run: { type: 'boolean', default: false },
    },
    required: ['to', 'subject'],
    additionalProperties: false,
  },
  handler: async (args: any) => {
    const cliArgs = ['send-mail', '--subject', args.subject];

    // Recipients — outlook-cli accepts repeated --to flags
    for (const r of args.to as string[]) cliArgs.push('--to', r);
    if (Array.isArray(args.cc)) for (const r of args.cc) cliArgs.push('--cc', r);
    if (Array.isArray(args.bcc)) for (const r of args.bcc) cliArgs.push('--bcc', r);

    // Body: either inline (write to temp) or file path passthrough
    const bodyFiles = await materializeBodies(args);
    if (bodyFiles.html) cliArgs.push('--html', bodyFiles.html);
    if (bodyFiles.text) cliArgs.push('--text', bodyFiles.text);

    if (Array.isArray(args.attach)) {
      for (const f of args.attach) cliArgs.push('--attach', f);
    }

    if (typeof args.signature_file === 'string' && args.signature_file.length > 0) {
      cliArgs.push('--signature', args.signature_file);
    }
    if (args.no_signature === true) cliArgs.push('--no-signature');
    if (args.no_cc_self === true) cliArgs.push('--no-cc-self');
    if (args.no_save_sent === true) cliArgs.push('--no-save-sent');
    if (args.send_now === true) cliArgs.push('--send-now');
    if (args.no_open === true) cliArgs.push('--no-open');
    if (args.dry_run === true) cliArgs.push('--dry-run');

    try {
      return await runOutlookCli(cliArgs);
    } finally {
      await cleanupTempBodies(bodyFiles);
    }
  },
};

// ---------------------------------------------------------------------------
// Inline body support: writes html_body / text_body to a tmp file so the
// CLI's file-based --html / --text flags can consume them. The tmp file is
// removed in the finally block so failures don't leak.
// ---------------------------------------------------------------------------

interface MaterializedBodies {
  html?: string;
  text?: string;
  /** Tmp paths to delete in cleanup (paths that we created, not user-supplied). */
  cleanup: string[];
}

async function materializeBodies(args: any): Promise<MaterializedBodies> {
  const out: MaterializedBodies = { cleanup: [] };
  const fs = await import('node:fs/promises');
  const path = await import('node:path');
  const os = await import('node:os');

  // HTML
  if (typeof args.html_file === 'string' && args.html_file.length > 0) {
    out.html = args.html_file;
  } else if (typeof args.html_body === 'string' && args.html_body.length > 0) {
    const p = path.join(os.tmpdir(), `outlook-cli-body-${Date.now()}-${Math.random().toString(36).slice(2)}.html`);
    await fs.writeFile(p, args.html_body, 'utf-8');
    out.html = p;
    out.cleanup.push(p);
  }
  // Text
  if (typeof args.text_file === 'string' && args.text_file.length > 0) {
    out.text = args.text_file;
  } else if (typeof args.text_body === 'string' && args.text_body.length > 0) {
    const p = path.join(os.tmpdir(), `outlook-cli-body-${Date.now()}-${Math.random().toString(36).slice(2)}.txt`);
    await fs.writeFile(p, args.text_body, 'utf-8');
    out.text = p;
    out.cleanup.push(p);
  }
  return out;
}

async function cleanupTempBodies(bodies: MaterializedBodies): Promise<void> {
  if (bodies.cleanup.length === 0) return;
  const fs = await import('node:fs/promises');
  await Promise.all(
    bodies.cleanup.map((p) =>
      fs.unlink(p).catch(() => undefined),
    ),
  );
}
