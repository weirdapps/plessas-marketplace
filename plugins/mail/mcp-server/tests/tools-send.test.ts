// tests/tools-send.test.ts
//
// Behavioral tests for the v0.2.0 write-side tool wrappers — verify the
// arg arrays passed to runOutlookCli match what the underlying CLI expects.

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EventEmitter } from 'node:events';
import os from 'node:os';
import { __setSpawnForTests, type SpawnLike } from '../src/subprocess.js';

const tmpDir = os.tmpdir();
import {
  sendMailTool,
  replyTool,
  replyAllTool,
  forwardTool,
  captureSignatureTool,
} from '../src/tools/index.js';

let capturedArgs: string[] = [];

/**
 * Strip the absolute CLI script path prefix from spawn args.
 *
 * subprocess.ts spawns via `spawn(NODE_BIN, [CLI_PATH, ...meaningfulArgs])` when
 * outlook-tool is bundled as a dep, or via `spawn('outlook-cli', meaningfulArgs)`
 * when falling back to PATH. Tests assert on the meaningful args regardless.
 */
function meaningfulArgs(args: readonly string[]): string[] {
  const first = args[0] ?? '';
  const looksLikeCliPath = first.endsWith('cli.js') || first.endsWith('cli.cjs') || first.endsWith('cli.mjs');
  return looksLikeCliPath ? [...args.slice(1)] : [...args];
}

function captureSpawn(stdoutJson: unknown): SpawnLike {
  return ((_cmd: string, args: readonly string[]) => {
    capturedArgs = meaningfulArgs(args);
    const stdout = new EventEmitter();
    const stderr = new EventEmitter();
    const child = new EventEmitter() as any;
    child.stdout = stdout;
    child.stderr = stderr;
    child.kill = () => {};
    setImmediate(() => {
      stdout.emit('data', Buffer.from(JSON.stringify(stdoutJson)));
      child.emit('close', 0);
    });
    return child;
  }) as SpawnLike;
}

beforeEach(() => {
  capturedArgs = [];
  __setSpawnForTests(captureSpawn({ ok: true }));
});
afterEach(() => {
  __setSpawnForTests(undefined);
});

describe('outlook_send_mail', () => {
  it('builds: send-mail --subject S --to a --to b --html FILE', async () => {
    await sendMailTool.handler({
      to: ['a@x.com', 'b@y.com'],
      subject: 'hello',
      html_file: `${tmpDir}/body.html`,
    });
    expect(capturedArgs[0]).toBe('send-mail');
    expect(capturedArgs).toContain('--subject');
    expect(capturedArgs).toContain('hello');
    expect(capturedArgs.filter((a) => a === '--to')).toHaveLength(2);
    expect(capturedArgs).toContain('a@x.com');
    expect(capturedArgs).toContain('b@y.com');
    expect(capturedArgs).toContain('--html');
    expect(capturedArgs).toContain(`${tmpDir}/body.html`);
  });

  it('passes through --send-now / --no-cc-self / --no-save-sent / --dry-run flags', async () => {
    await sendMailTool.handler({
      to: ['x@y.com'],
      subject: 's',
      html_file: `${tmpDir}/b.html`,
      send_now: true,
      no_cc_self: true,
      no_save_sent: true,
      dry_run: true,
    });
    expect(capturedArgs).toContain('--send-now');
    expect(capturedArgs).toContain('--no-cc-self');
    expect(capturedArgs).toContain('--no-save-sent');
    expect(capturedArgs).toContain('--dry-run');
  });

  it('inline html_body materializes to a tmp file and cleans up', async () => {
    const fs = await import('node:fs/promises');
    let tmpPathSeen = '';
    __setSpawnForTests(((_cmd: string, args: readonly string[]) => {
      capturedArgs = meaningfulArgs(args);
      const idx = capturedArgs.indexOf('--html');
      if (idx >= 0) tmpPathSeen = capturedArgs[idx + 1] as string;
      const stdout = new EventEmitter();
      const stderr = new EventEmitter();
      const child = new EventEmitter() as any;
      child.stdout = stdout;
      child.stderr = stderr;
      child.kill = () => {};
      setImmediate(() => {
        stdout.emit('data', Buffer.from('{}'));
        child.emit('close', 0);
      });
      return child;
    }) as SpawnLike);

    await sendMailTool.handler({
      to: ['x@y.com'],
      subject: 's',
      html_body: '<p>hi inline</p>',
    });
    // tmp path was used during the call
    expect(tmpPathSeen).toMatch(/outlook-cli-body-.*\.html$/);
    // and is cleaned up after
    await expect(fs.access(tmpPathSeen)).rejects.toThrow();
  });

  it('attach[] expands to repeated --attach', async () => {
    await sendMailTool.handler({
      to: ['x@y.com'],
      subject: 's',
      html_file: `${tmpDir}/b.html`,
      attach: [`${tmpDir}/a.pdf`, `${tmpDir}/b.pdf`],
    });
    expect(capturedArgs.filter((a) => a === '--attach')).toHaveLength(2);
    expect(capturedArgs).toContain(`${tmpDir}/a.pdf`);
    expect(capturedArgs).toContain(`${tmpDir}/b.pdf`);
  });
});

describe('outlook_reply / outlook_reply_all', () => {
  it('reply builds: reply <id> --html FILE (subprocess adds --no-auto-reauth + --json)', async () => {
    await replyTool.handler({
      message_id: 'AAMk-1',
      html_file: `${tmpDir}/r.html`,
    });
    expect(capturedArgs.slice(0, 4)).toEqual([
      'reply',
      'AAMk-1',
      '--html',
      `${tmpDir}/r.html`,
    ]);
  });

  it('reply-all builds: reply-all <id>', async () => {
    await replyAllTool.handler({
      message_id: 'AAMk-2',
      html_file: `${tmpDir}/r.html`,
    });
    expect(capturedArgs[0]).toBe('reply-all');
    expect(capturedArgs[1]).toBe('AAMk-2');
  });

  it('passes --signature / --no-signature / --send-now', async () => {
    await replyTool.handler({
      message_id: 'AAMk-3',
      html_file: `${tmpDir}/r.html`,
      signature_file: `${tmpDir}/sig.html`,
      send_now: true,
    });
    expect(capturedArgs).toContain('--signature');
    expect(capturedArgs).toContain(`${tmpDir}/sig.html`);
    expect(capturedArgs).toContain('--send-now');
  });

  it('--no-signature flag', async () => {
    await replyTool.handler({
      message_id: 'AAMk-4',
      html_file: `${tmpDir}/r.html`,
      no_signature: true,
    });
    expect(capturedArgs).toContain('--no-signature');
  });
});

describe('outlook_forward', () => {
  it('builds: forward <id> --to a --html FILE', async () => {
    await forwardTool.handler({
      message_id: 'AAMk-5',
      to: ['fwd@x.com'],
      html_file: `${tmpDir}/r.html`,
    });
    expect(capturedArgs[0]).toBe('forward');
    expect(capturedArgs[1]).toBe('AAMk-5');
    expect(capturedArgs).toContain('--to');
    expect(capturedArgs).toContain('fwd@x.com');
  });

  it('expands to[] / cc[] / bcc[] arrays into repeated flags', async () => {
    await forwardTool.handler({
      message_id: 'AAMk-6',
      to: ['t1@x.com', 't2@x.com'],
      cc: ['c@x.com'],
      bcc: ['b@x.com'],
      html_file: `${tmpDir}/r.html`,
    });
    expect(capturedArgs.filter((a) => a === '--to')).toHaveLength(2);
    expect(capturedArgs.filter((a) => a === '--cc')).toHaveLength(1);
    expect(capturedArgs.filter((a) => a === '--bcc')).toHaveLength(1);
  });
});

describe('outlook_capture_signature', () => {
  it('builds: capture-signature (no args = use defaults)', async () => {
    await captureSignatureTool.handler({});
    // subprocess wrapper appends --no-auto-reauth + --json globally
    expect(capturedArgs[0]).toBe('capture-signature');
    expect(capturedArgs).not.toContain('--from-message');
    expect(capturedArgs).not.toContain('--out');
  });

  it('passes --from-message and --out when supplied', async () => {
    await captureSignatureTool.handler({
      from_message: 'AAMk-99',
      out: `${tmpDir}/custom-sig.html`,
    });
    expect(capturedArgs).toContain('--from-message');
    expect(capturedArgs).toContain('AAMk-99');
    expect(capturedArgs).toContain('--out');
    expect(capturedArgs).toContain(`${tmpDir}/custom-sig.html`);
  });
});
