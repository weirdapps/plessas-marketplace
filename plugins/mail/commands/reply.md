---
description: "Reply (or reply-all) to an email with auto-quote + signature, draft-first"
argument-hint: "[message id or natural language; what you want to say; optionally --reply-all]"
allowed-tools: Bash, Read, mcp__outlook-bridge__outlook_reply, mcp__outlook-bridge__outlook_reply_all, mcp__outlook-bridge__outlook_list_mail, mcp__outlook-bridge__outlook_get_mail
---

<objective>
Reply to an existing email thread via the `outlook-bridge` MCP. M365 server auto-quotes the original; the signature from `~/.outlook-cli/signature.html` is auto-appended.

For NEW emails (no thread context), use `/send-mail`. For forwarding, use `/forward`.

User request: $ARGUMENTS
</objective>

<instructions>

## 1. Identify the source message

Three input forms:

**A. Direct message id**: user gives an `AAMk-...` id → use it as `message_id`.

**B. Natural language reference**: "reply to the latest from Maria" / "reply to the budget thread" → call `mcp__outlook-bridge__outlook_list_mail` with `top: 20` and a sensible folder (Inbox by default), filter results client-side by sender / subject substring, pick the best match. Confirm the choice with the user before sending if there's any ambiguity.

**C. Already in conversation context**: a recent `/mail-review` or `/inbox-briefing` listed the message — re-use that id directly.

If still ambiguous after natural-language matching, ask the user to disambiguate (show top 3 candidates).

## 2. Decide reply vs reply-all

- Default: **reply** (only the original sender).
- Use **reply-all** when the user explicitly says "reply all", "include everyone", or when the original thread has multiple human participants AND the user's reply is informational (not a private response).
- Pass `tool_name: "outlook_reply_all"` if reply-all; otherwise `outlook_reply`.

## 3. Compose the reply body

Prepare the user's NEW reply content as HTML:

- Convert any markdown to HTML
- Aptos Light 12pt #404040, no `<p>` tags, `<br>`/`<br><br>` for spacing
- Keep it brief and on-tone — match the user's style from `shared/style-guide.md`
- The auto-quoted original AND the signature are appended automatically — do NOT include either in your HTML

Example:

```html
<html><body style="font-family: &quot;Aptos Light&quot;, Aptos, sans-serif; font-size: 12pt; color: #404040; text-align: justify;">
Thanks for the update — confirming the timeline works on our end.<br><br>
Will circulate the revised deck tomorrow morning.
</body></html>
```

## 4. Invoke the MCP tool

```json
{
  "message_id": "AAMk-source-message-id",
  "html_body": "<html><body style=\"...\">your reply content</body></html>"
}
```

**Default behavior**: creates a reply DRAFT (with `RE:` subject prefix from M365), patches the body to inject your reply ABOVE the auto-quoted original, appends your signature from `~/.outlook-cli/signature.html`, activates Outlook desktop.

**Optional flags**:

- `send_now: true` — bypass draft, dispatch immediately
- `no_signature: true` — skip signature appending (rarely needed)
- `signature_file: "/path/to/custom-sig.html"` — override default signature
- `no_open: true` — create draft but don't activate Outlook desktop
- `dry_run: true` — preview without contacting M365

## 5. Confirm result

The tool returns:

```json
{
  "kind": "reply",
  "mode": "draft",
  "id": "AAMk-new-draft-id",
  "webLink": "https://outlook.office365.com/owa/...",
  "subject": "RE: original subject",
  "hasQuotedOriginal": true,
  "signatureApplied": true,
  "to": ["original-sender@..."]
}
```

Report:

- "Reply draft created (id `AAMk-...`) — Microsoft Outlook activated. Review and send. Signature applied: ✓ Auto-quote: ✓"
- If `signatureApplied: false` and the user expected one: warn that `~/.outlook-cli/signature.html` is missing — run `outlook-cli capture-signature` (or invoke `mcp__outlook-bridge__outlook_capture_signature`) once.
- If error: report and suggest fixes (auth → `outlook-cli auth-check`; bad message id → re-list).

</instructions>

<notes>
- One-time setup: signature must be captured first via `outlook-cli capture-signature`. Output lives at `~/.outlook-cli/signature.html`. Hand-edit if the heuristic captured too much.
- The auto-quote uses M365's standard reply formatting (the quoted block with sender/date/subject headers).
- Replies preserve `ConversationId` so the thread stays intact in Outlook + on the recipient side.
</notes>
