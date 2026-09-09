// tests/tools-send.test.ts
//
// Behavioral tests for teams_send_message: verify the arg array passed to
// runTeamsCli matches the flags teams-access/src/cli.ts defines (--chat, --text,
// --html). Commander runs without allowUnknownOption, so a wrong flag name fails
// the send before auth is even consulted.

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EventEmitter } from 'node:events';
import { __setSpawnForTests, type SpawnLike } from '../src/subprocess.js';
import { sendMessageTool, listMessagesTool, listChannelsTool, healthCheckTool } from '../src/tools/index.js';
import { withAttribution, looksLikeHtml, ATTRIBUTION_PREFIX } from '../src/tools/send-message.js';

let capturedArgs: string[] = [];

/**
 * Strip the absolute CLI script path prefix from spawn args.
 *
 * subprocess.ts spawns via `spawn(NODE_BIN, [CLI_PATH, ...meaningfulArgs])` when
 * teams-cli is bundled as a dep, or via `spawn('teams-cli', meaningfulArgs)` when
 * falling back to PATH. Tests assert on the meaningful args regardless.
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

describe('teams_send_message', () => {
  it('builds: send-message --chat <id> --html <body>', async () => {
    await sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body: '<p>[Claude] hi</p>' });
    expect(capturedArgs.slice(0, 5)).toEqual([
      'send-message',
      '--chat',
      '19:abc@thread.v2',
      '--html',
      '<p>[Claude] hi</p>',
    ]);
  });

  it('routes a plain-text body to --text, not --html', async () => {
    await sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body: '[Claude] plain body' });
    expect(capturedArgs).toContain('--text');
    expect(capturedArgs).not.toContain('--html');
  });

  it('passes chat id and body as separate argv entries, never concatenated', async () => {
    const chatId = '19:abc@thread.v2';
    const body = '<p>[Claude] two words</p>';
    await sendMessageTool.handler({ chat_id: chatId, body });
    expect(capturedArgs).toContain(chatId);
    expect(capturedArgs).toContain(body);
    for (const arg of capturedArgs) {
      if (arg !== chatId) expect(arg).not.toContain(chatId);
      if (arg !== body) expect(arg).not.toContain(body);
    }
  });

  it('passes a body containing shell metacharacters through verbatim as one argv entry', async () => {
    // No shell is used (see shouldUseShell), so nothing here needs escaping and
    // nothing may be mangled either: the body must arrive byte-for-byte.
    const body = '<p>[Claude] price is 5 & 6 | ok; "quoted" `tick` $(whoami)</p>';
    await sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body });
    expect(capturedArgs.filter(a => a === body)).toHaveLength(1);
  });

  it('appends --no-auto-reauth and no --json', async () => {
    await sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body: 'hi' });
    expect(capturedArgs).toContain('--no-auto-reauth');
    expect(capturedArgs).not.toContain('--json');
  });
});

describe('teams_list_channels', () => {
  it('sends --team-id when a team is named', async () => {
    await listChannelsTool.handler({ team_id: 'team-1' });
    expect(capturedArgs.slice(0, 3)).toEqual(['list-channels', '--team-id', 'team-1']);
    expect(capturedArgs).not.toContain('--all-teams');
  });

  it('sends --all-teams when team_id is omitted, the mode the schema advertises', async () => {
    await listChannelsTool.handler({});
    expect(capturedArgs.slice(0, 2)).toEqual(['list-channels', '--all-teams']);
    expect(capturedArgs).not.toContain('--team-id');
  });
});

describe('teams_health_check', () => {
  // The CLI writes the report and only then exits 5 (broken) or 1 (degraded).
  const report = {
    overall: 'degraded',
    probes: [{ name: 'graph', ok: true }, { name: 'chatsvc', ok: false }],
  };

  it.each([[1, 'degraded'], [5, 'broken']])(
    'returns the report on exit %i rather than discarding it',
    async (exitCode) => {
      __setSpawnForTests(((_cmd: string, args: readonly string[]) => {
        capturedArgs = meaningfulArgs(args);
        const stdout = new EventEmitter();
        const stderr = new EventEmitter();
        const child = new EventEmitter() as any;
        child.stdout = stdout;
        child.stderr = stderr;
        child.kill = () => {};
        setImmediate(() => {
          stdout.emit('data', Buffer.from(JSON.stringify(report)));
          child.emit('close', exitCode);
        });
        return child;
      }) as SpawnLike);
      await expect(healthCheckTool.handler({})).resolves.toEqual(report);
    },
  );

  it('still throws when a non-zero exit carries no report', async () => {
    __setSpawnForTests(((_cmd: string, args: readonly string[]) => {
      capturedArgs = meaningfulArgs(args);
      const stdout = new EventEmitter();
      const stderr = new EventEmitter();
      const child = new EventEmitter() as any;
      child.stdout = stdout;
      child.stderr = stderr;
      child.kill = () => {};
      setImmediate(() => {
        stderr.emit('data', Buffer.from('session missing'));
        child.emit('close', 4);
      });
      return child;
    }) as SpawnLike);
    await expect(healthCheckTool.handler({})).rejects.toMatchObject({ code: 'auth_required' });
  });
});

describe('html detection', () => {
  it('treats a matched tag pair as HTML', () => {
    expect(looksLikeHtml('<p>hi</p>')).toBe(true);
    expect(looksLikeHtml('some <b>bold</b> text')).toBe(true);
    expect(looksLikeHtml('<div class="x">y</div>')).toBe(true);
  });

  it('treats a void element as HTML', () => {
    expect(looksLikeHtml('line one<br>line two')).toBe(true);
    expect(looksLikeHtml('line one<br/>line two')).toBe(true);
  });

  it('does NOT treat prose with angle brackets as HTML', () => {
    // The old sniff was /<[a-z][\s\S]*>/i, which fired on all of these.
    expect(looksLikeHtml('a<b and c>d')).toBe(false);
    expect(looksLikeHtml('if x<y then y>x')).toBe(false);
    expect(looksLikeHtml('5 < 6 > 3')).toBe(false);
    expect(looksLikeHtml('plain text')).toBe(false);
  });

  it('sends prose with angle brackets as text, not markup', async () => {
    await sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body: 'a<b and c>d' });
    expect(capturedArgs).toContain('--text');
    expect(capturedArgs).not.toContain('--html');
  });

  it('honours an explicit format over the sniff, both ways', async () => {
    await sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body: '<p>markup</p>', format: 'text' });
    expect(capturedArgs).toContain('--text');

    await sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body: 'no tags here', format: 'html' });
    expect(capturedArgs).toContain('--html');
  });

  it('advertises format as an optional enum', () => {
    const schema = sendMessageTool.inputSchema as {
      properties: { format?: { enum?: string[] } };
      required: string[];
    };
    expect(schema.properties.format?.enum).toEqual(['html', 'text']);
    expect(schema.required).not.toContain('format');
  });
});

describe('[Claude] attribution', () => {
  // CodeQL flagged the original single-pass tag strip as incomplete multi-character
  // sanitization. The value never reaches a renderer, so this is not XSS: it decides
  // whether the attribution prefix is already present. Stripping to a fixed point is
  // the accepted remediation and costs one extra comparison. Measured on this regex,
  // the greedy [^>]* means one pass is already stable for every input tried, so the
  // loop is defensive rather than load-bearing. What these tests pin is the property
  // that actually matters: exactly one prefix, whatever the markup looks like.
  it('adds exactly one prefix to malformed markup', () => {
    const once = withAttribution('<<b>>hello');
    expect(once.match(/\[Claude\]/g)).toHaveLength(1);
  });

  it('is idempotent, so a re-send never stacks prefixes', () => {
    for (const body of ['plain', '<p>para</p>', '<<b>>malformed', '  leading space']) {
      const once = withAttribution(body);
      expect(withAttribution(once)).toBe(once);
    }
  });

  it('prepends the prefix to a plain-text body that lacks it', () => {
    expect(withAttribution('running late')).toBe('[Claude] running late');
  });

  it('prepends it inside the first block element, not before it', () => {
    expect(withAttribution('<p>running late</p>')).toBe('<p>[Claude] running late</p>');
    expect(withAttribution('<div><p>nested</p></div>')).toBe('<div><p>[Claude] nested</p></div>');
  });

  it('is idempotent: a body that already carries the prefix is untouched', () => {
    expect(withAttribution('[Claude] already tagged')).toBe('[Claude] already tagged');
    expect(withAttribution('<p>[Claude] already tagged</p>')).toBe('<p>[Claude] already tagged</p>');
    expect(withAttribution(withAttribution('twice'))).toBe('[Claude] twice');
  });

  it('survives a body that starts with whitespace', () => {
    expect(withAttribution('   spaced')).toBe('   [Claude] spaced');
    expect(withAttribution('\n<p>newline first</p>')).toBe('\n<p>[Claude] newline first</p>');
    expect(withAttribution('  <p>[Claude] tagged</p>')).toBe('  <p>[Claude] tagged</p>');
  });

  it('handles a body whose visible text starts before the first tag', () => {
    expect(withAttribution('bold <b>bit</b>')).toBe('[Claude] bold <b>bit</b>');
  });

  it('goes through on every send, so an untagged body reaches the CLI tagged', async () => {
    await sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body: '<p>untagged</p>' });
    expect(capturedArgs).toContain(`<p>${ATTRIBUTION_PREFIX} untagged</p>`);
    expect(capturedArgs).not.toContain('<p>untagged</p>');
  });

  it('does not double-tag a body the caller already prefixed', async () => {
    await sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body: '<p>[Claude] mine</p>' });
    expect(capturedArgs).toContain('<p>[Claude] mine</p>');
    expect(capturedArgs.join(' ')).not.toContain('[Claude] [Claude]');
  });
});

describe('teams_send_message does not retry on exit 5', () => {
  it('spawns the CLI exactly once, so a lost response cannot post twice', async () => {
    let calls = 0;
    __setSpawnForTests(((_cmd: string, _args: readonly string[]) => {
      calls++;
      const stdout = new EventEmitter();
      const stderr = new EventEmitter();
      const child = new EventEmitter() as any;
      child.stdout = stdout;
      child.stderr = stderr;
      child.kill = () => {};
      setImmediate(() => {
        stderr.emit('data', Buffer.from('timeout'));
        child.emit('close', 5);
      });
      return child;
    }) as SpawnLike);
    await expect(sendMessageTool.handler({ chat_id: '19:abc@thread.v2', body: 'hi' }))
      .rejects.toMatchObject({ code: 'upstream', retryable: false });
    expect(calls).toBe(1);
  });
});

describe('teams_list_messages', () => {
  it('builds chat reads as: list-messages --chat <id> --page-size N', async () => {
    await listMessagesTool.handler({ chat_id: '19:abc@thread.v2', top: 25 });
    expect(capturedArgs.slice(0, 3)).toEqual(['list-messages', '--chat', '19:abc@thread.v2']);
    expect(capturedArgs).toContain('--page-size');
    expect(capturedArgs).toContain('25');
  });

  it('builds channel reads as: list-messages --team <id> --channel <id>', async () => {
    await listMessagesTool.handler({ team_id: 'team-1', channel_id: 'chan-1' });
    expect(capturedArgs).toContain('--team');
    expect(capturedArgs).toContain('team-1');
    expect(capturedArgs).toContain('--channel');
    expect(capturedArgs).toContain('chan-1');
    expect(capturedArgs).not.toContain('--chat');
  });

  it('drops the unsupported since filter rather than faking it', async () => {
    await listMessagesTool.handler({ chat_id: '19:abc@thread.v2', since: '2026-01-01T00:00:00Z' });
    expect(capturedArgs).not.toContain('--since');
    expect(capturedArgs).not.toContain('2026-01-01T00:00:00Z');
  });
});
