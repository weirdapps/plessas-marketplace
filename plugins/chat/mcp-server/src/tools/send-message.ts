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
 * The prefix goes INSIDE leading formatting tags so it renders as visible text
 * rather than sitting outside the first block element.
 *
 * "Already prefixed" is decided on the raw body, never on a tag-stripped copy.
 * A regex strip is not how HTML parses: `<p title=">[Claude]">Pay</p>` strips to
 * text starting "[Claude]" while the recipient sees only "Pay", and hidden,
 * styled or non-rendering elements hide a prefix that is technically present.
 * So only a run of attribute-free formatting tags may precede an existing prefix;
 * anything else gets a fresh one in front. A plain-text body (isHtml=false) is
 * shown literally, so there nothing may precede it but whitespace.
 */
export function withAttribution(
  body: string,
  prefix: string = ATTRIBUTION_PREFIX,
  isHtml: boolean = true,
): string {
  const leadRe = isHtml ? LEADING_FORMATTING_TAGS : /^\s*/;
  const lead = leadRe.exec(body)?.[0] ?? '';
  if (body.slice(lead.length).startsWith(prefix)) return body;
  return `${lead}${prefix} ${body.slice(lead.length)}`;
}

/** Whitespace and attribute-free opening tags that render their text normally. */
const LEADING_FORMATTING_TAGS =
  /^(?:\s*<(?:p|div|span|b|strong|i|em|u|blockquote|h[1-6])>)*\s*/i;

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
    const body = withAttribution(raw, ATTRIBUTION_PREFIX, isHtml);
    const bodyFlag = isHtml ? '--html' : '--text';
    // Not idempotent: a retried exit 5 posts the same message to the chat again.
    return runTeamsCli(['send-message', '--chat', args.chat_id, bodyFlag, body], { idempotent: false });
  },
};
