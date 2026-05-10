---
description: "Send a new email via outlook-bridge MCP (draft-first by default)"
argument-hint: "[describe what to send, to whom, subject, and optionally attach files]"
allowed-tools: Bash, Read, Glob, mcp__outlook-bridge__outlook_send_mail
---

<objective>
Compose and send a NEW email (no thread context) via the `outlook-bridge` MCP plugin, which wraps `outlook-cli send-mail` (Microsoft Graph v2.0).

For **replies** to an existing thread (with auto-quote + signature), use `/reply` or `/reply-all`. For **forwards**, use `/forward`. This `/send-mail` skill is for new emails ONLY.

Sender identity (UPN, default CC-self) is configured in `shared/style-guide.md` (Identity section).

User request: $ARGUMENTS
</objective>

<instructions>

## 1. Parse the user's request

Extract:

- **To**: One or more recipient email addresses (REQUIRED)
- **CC**: Optional CC recipients (the user's UPN from `shared/style-guide.md` is automatically CC'd unless `--no-cc-self` is requested)
- **BCC**: Optional BCC recipients
- **Subject**: Email subject line (REQUIRED)
- **Body**: Email body content — convert to HTML for Outlook compatibility
- **Attachments**: File paths to attach (optional). Use Glob to find files if paths are approximate.
- **Send mode**: DEFAULT is draft-first (creates draft, activates Microsoft Outlook desktop, user reviews and sends manually). Pass `send_now: true` ONLY if the user explicitly says "send immediately" or "send now".

If the user hasn't provided required fields (To, Subject), ask before proceeding.

## 2. Prepare the body

- Always send emails in **HTML format** for Outlook rendering
- Convert any markdown content to proper HTML with inline CSS
- Font: **Aptos**, size **12pt**, color **#404040** (Black Text 1 Lighter 25%)
- **NO `<p>` tags** — use `<br>` for line breaks, `<br><br>` for paragraph spacing
- Wrap content in a basic HTML structure:

```html
<html><body style="font-family: Aptos, sans-serif; font-size: 12pt; color: #404040; text-align: justify;">
[content here]
</body></html>
```

**Signature note**: Microsoft Graph send does NOT auto-insert your Outlook signature into the JSON body. The signature gets added when you OPEN the draft in Outlook desktop and edit/send manually. Since draft-first is the default, the user's normal signature handling kicks in. For `send_now: true` calls (rare), the signature will be MISSING — warn the user, or pre-pend the signature HTML manually before invoking the tool.

## 3. Prepare attachments

If attachments are specified:

- Verify each file exists using Glob or Read
- Collect absolute POSIX paths
- If a file doesn't exist, warn the user and ask whether to proceed without it
- Combined attachment size must stay under **30 MB** (M365 `/sendmail` JSON cap)

## 4. Send via the MCP tool

Invoke `mcp__outlook-bridge__outlook_send_mail` with:

```json
{
  "to": ["recipient@example.com"],
  "cc": ["additional-cc@example.com"],
  "bcc": ["bcc@example.com"],
  "subject": "Email subject",
  "html_body": "<html><body style=\"...\">...</body></html>",
  "attach": ["/absolute/path/to/file.pdf"]
}
```

**Default behavior**: creates a DRAFT, returns `{id, webLink}`, activates Microsoft Outlook desktop. User finds the draft in Drafts folder (top of list since just created), reviews, and sends manually. Outlook desktop will add the signature automatically when the user edits/sends.

**Optional flags**:

- `send_now: true` — bypass draft, dispatch immediately. Only use when the user explicitly requested immediate send. **Warning**: signature will be MISSING (no Outlook desktop edit step).
- `no_cc_self: true` — suppress automatic CC to the authenticated user. Only use when the user explicitly requests no self-copy.
- `no_save_sent: true` — don't save to Sent folder (only meaningful with `send_now`).
- `no_open: true` — create draft but don't activate Outlook desktop. Use for scripted scenarios; the `webLink` is still returned for the user to open manually.
- `dry_run: true` — print the would-send payload as JSON without contacting M365. Useful for previewing.

**Body file alternative**: instead of `html_body` inline, you can pass `html_file: "/absolute/path/to/body.html"` if the body content is large or already exists as a file.

## 5. Confirm result

After execution, the tool returns JSON like:

```json
{
  "mode": "draft",
  "id": "AAMk...",
  "webLink": "https://outlook.office365.com/owa/...",
  "to": ["recipient@example.com"],
  "cc": ["your.email@nbg.gr"],
  "subject": "Email subject"
}
```

Report to the user:

- For **draft mode** (default): "Draft created in Outlook Drafts folder — Microsoft Outlook activated. Review and send. (id: `AAMk-...`)"
- For **send_now**: "Email sent to [recipients] with subject [subject]. CC-self: copy in your inbox shortly."
- If error: report the error JSON and suggest fixes (auth issues → run `outlook-cli auth-check`; file not found → check attachment paths).

</instructions>

<rollback>
The previous AppleScript-based version of this skill (using `tell application "Microsoft Outlook" to make new outgoing message`) is preserved in git history before the email-handler send-side migration commit. The current implementation depends on `outlook-bridge` plugin v0.2.0+ and `outlook-cli` v1.3.0+ being present and authenticated.
</rollback>
