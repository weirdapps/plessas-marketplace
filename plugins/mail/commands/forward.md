---
description: "Forward an email to new recipient(s), draft-first by default"
argument-hint: "[message id or natural language; recipients; optional note]"
allowed-tools: Bash, Read, mcp__outlook-bridge__outlook_forward, mcp__outlook-bridge__outlook_list_mail, mcp__outlook-bridge__outlook_get_mail
---

<objective>
Forward an existing email to new recipient(s) via the `outlook-bridge` MCP. M365 server auto-quotes the original message; signature appended automatically. Recipients are explicitly required (unlike reply, which uses the original sender).

For new emails (no source thread), use `/send-mail`. For replies, use `/reply`.

User request: $ARGUMENTS
</objective>

<instructions>

## 1. Identify the source message

Same options as `/reply`:
- **A. Direct id**: user provides `AAMk-...` → use as `message_id`.
- **B. Natural language**: "forward Maria's budget email to Alex" → list recent mail, filter by sender/subject substring, confirm the pick.
- **C. Conversation context**: re-use an id from a recent `/mail-review` or `/inbox-briefing`.

If ambiguous, show top 3 candidates and ask.

## 2. Identify forward target(s)

Required: at least one TO recipient. Extract from user request. Validate each address (must contain `@`).

Optional: CC and BCC. CC-self is NOT auto-applied for forwards (the original message stays threaded; you don't need a personal copy).

## 3. Compose the forwarding note (optional)

If the user wants to add context to the forward ("FYI for the Q2 review"), prepare the HTML note:
- Aptos 12pt #404040
- Brief — usually 1-3 lines
- Do NOT include the original (auto-quoted) or the signature (auto-appended)

If the user has nothing to add, use a minimal placeholder like `<p>FYI</p>` or skip the body. The CLI requires at least one of `html_body`/`text_body`/`html_file`/`text_file`.

## 4. Invoke the MCP tool

```json
{
  "message_id": "AAMk-source-message-id",
  "to": ["recipient@example.com"],
  "cc": ["optional-cc@example.com"],
  "html_body": "<html><body style=\"...\">FYI — see below.</body></html>"
}
```

**Default behavior**: creates a forward DRAFT (with `FW:` subject prefix), patches body to inject your note ABOVE the auto-quoted original, sets ToRecipients/CcRecipients/BccRecipients, appends signature from `~/.outlook-cli/signature.html`, activates Outlook desktop.

**Optional flags**:
- `send_now: true` — dispatch immediately, skip draft
- `no_signature: true` — skip signature
- `signature_file: "/path"` — custom signature file
- `no_open: true` — don't activate Outlook
- `dry_run: true` — preview only

## 5. Confirm result

```json
{
  "kind": "forward",
  "mode": "draft",
  "id": "AAMk-fwd-draft-id",
  "webLink": "https://outlook.office365.com/owa/...",
  "subject": "FW: original subject",
  "hasQuotedOriginal": true,
  "signatureApplied": true,
  "to": ["recipient@example.com"]
}
```

Report:
- "Forward draft created (id `AAMk-...`) → [recipients]. Microsoft Outlook activated. Review and send."
- If `signatureApplied: false` and the user expected one: tell them to run `outlook-cli capture-signature` once.
- If error: report and suggest fixes.

</instructions>

<notes>
- Attachments from the original message ARE forwarded automatically by M365 (via `/createForward`). No `--attach` needed for those.
- To attach ADDITIONAL files beyond the originals, use `/send-mail` instead and reference the source message in your note (forward + extra attach is not currently supported via outlook-bridge).
- One-time setup: capture signature once with `outlook-cli capture-signature`.
</notes>
