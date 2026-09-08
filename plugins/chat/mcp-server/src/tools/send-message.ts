import type { Tool } from '../tool.js';
import { runTeamsCli } from '../subprocess.js';

/** Attribution marker every agent-sent Teams message must carry. */
export const ATTRIBUTION_PREFIX = '[Claude]';

/**
 * Prepend the attribution prefix unless the visible text already starts with it.
 *
 * This is the single chokepoint for every send the bridge makes, so it is the
 * cheapest place to guarantee what the README promises. There is deliberately no
 * argument to disable it: the plugin ships with auto-send as the documented
 * default, and an opt-out is exactly the argument a model can be talked into
 * passing. Prepending, never rejecting: a silently failed send is worse than an
 * attributed one.
 *
 * The prefix goes INSIDE any leading tags so it renders as visible text rather
 * than sitting outside the first block element.
 */
export function withAttribution(body: string, prefix: string = ATTRIBUTION_PREFIX): string {
  const visible = body.replace(/<[^>]*>/g, '').trimStart();
  if (visible.startsWith(prefix)) return body;
  const lead = /^(?:\s*<[^>]+>)*\s*/.exec(body)?.[0] ?? '';
  return `${body.slice(0, lead.length)}${prefix} ${body.slice(lead.length)}`;
}

/** A tag paired with its own closing tag: <p>x</p>, <b>x</b>, <div ...>x</div>. */
const PAIRED_TAG = /<([a-z][a-z0-9]*)\b[^>]*>[\s\S]*<\/\1\s*>/i;
/** Void elements, which never have a closing tag but are still real markup. */
const VOID_TAG = /<(?:br|hr|img|input)\b[^>]*\/?>/i;

/**
 * Fallback when the caller states no format.
 *
 * The old test was `/<[a-z][\s\S]*>/i`, which fires on any `<` followed by a
 * letter with any `>` later in the string, so plain prose like "a<b and c>d"
 * was sent as HTML and rendered wrong. Requiring a matched closing tag, or a
 * recognised void element, keeps the common HTML cases working while leaving
 * prose alone. Callers who know should pass `format` and skip the guessing.
 */
export function looksLikeHtml(body: string): boolean {
  return PAIRED_TAG.test(body) || VOID_TAG.test(body);
}

export const sendMessageTool: Tool = {
  name: 'teams_send_message',
  description: 'Send a message to a Teams chat via Graph. Channel sends are not supported (scope missing). '
    + 'The bridge prepends "[Claude]" to the body unless it already starts with it, so recipients always '
    + 'know the message came from an agent. Do not add a second prefix.',
  inputSchema: {
    type: 'object',
    properties: {
      chat_id: { type: 'string', description: 'Chat ID to send to.' },
      body: { type: 'string', description: 'Message body (HTML or plain text).' },
      format: {
        type: 'string',
        enum: ['html', 'text'],
        description: 'How to send the body. Omit and the bridge guesses from the markup, '
          + 'which it can only do approximately. Pass it whenever you know.',
      },
    },
    required: ['chat_id', 'body'],
    additionalProperties: false,
  },
  handler: async (args) => {
    // Flag names must match teams-access/src/cli.ts:177-181 exactly: --chat,
    // --text, --html. This sent --chat-id and --body, which commander rejects
    // (no allowUnknownOption), so every send through the MCP bridge failed on
    // argument parsing before auth was even consulted. That made it look like
    // another symptom of the 2026-09-02 token outage rather than a separate bug.
    //
    // Route to --html or --text so a plain string is not silently rendered as
    // markup and a crafted <p> block is not escaped. House style for Teams is
    // HTML. An explicit `format` wins; sniffing is only the fallback, and it
    // runs on the raw body so attribution cannot change the verdict.
    const raw = String(args.body ?? '');
    const isHtml = args.format === 'html' || args.format === 'text'
      ? args.format === 'html'
      : looksLikeHtml(raw);
    const body = withAttribution(raw);
    const bodyFlag = isHtml ? '--html' : '--text';
    // Not idempotent: a retried exit 5 posts the same message to the chat again.
    return runTeamsCli(['send-message', '--chat', args.chat_id, bodyFlag, body], { idempotent: false });
  },
};
