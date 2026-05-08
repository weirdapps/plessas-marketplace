---
description: "Read inbox and present a briefing with summaries, action recommendations, and insights — no drafting or replying"
argument-hint: "[inbox|archive|both] [--count N] [--unread]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Read emails via the outlook-bridge MCP wrapper around `outlook-cli` and present a concise inbox briefing with summaries, action recommendations, and strategic insights. This command is read-only — it never drafts, replies, or modifies any email.

**Architecture**: outlook-bridge MCP for both reading (structured JSON from Microsoft Graph via `outlook-cli`) and sending (`/send-mail` uses `mcp__outlook-bridge__outlook_send_mail`, draft-first by default). No AppleScript dependency.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 1. Load Previous State
- Read `~/.claude/drafts/inbox-state.json` (if exists) to know which emails were seen before

### 2. Read Emails via outlook-bridge MCP

Call `mcp__outlook-bridge__outlook_auth_check` first; if `status != "ok"`, surface the auth flow before continuing.

**Reading the inbox:**
```
Tool: mcp__outlook-bridge__outlook_list_mail
Args: {
  "folder": "Inbox",
  "top": N,
  "select": "Id,Subject,From,ToRecipients,CcRecipients,ReceivedDateTime,HasAttachments,IsRead,WebLink,ConversationId"
}
```

**Reading archive:**
```
Tool: mcp__outlook-bridge__outlook_list_mail
Args: {
  "folder": "Archive",
  "top": N,
  "select": "Id,Subject,From,ToRecipients,CcRecipients,ReceivedDateTime,HasAttachments,IsRead,WebLink,ConversationId"
}
```

**Reading full message body** (for important/complex emails):
```
Tool: mcp__outlook-bridge__outlook_get_mail
Args: { "id": "<Id>", "body": "html" }   # use "text" for plain-text extraction
```

**Key points:**
- One `outlook_list_mail` call returns up to 100 messages — use `since` + `all:true` + `max` for larger sweeps
- `select` keeps payloads small; only request body via `outlook_get_mail` when needed
- For `--unread` flag: include `IsRead` in `select` and filter client-side (`IsRead == false`)
- If `{error: "auth_required"}` is returned, run `outlook-cli login` via Bash with user approval and retry

### 2b. Extract Attachment Content (if relevant)

For emails with attachments (PPTX, PDF, DOCX, XLSX), use `markitdown` to extract content for summarization. Save attachments to a temp directory via the MCP wrapper:

```
Tool: mcp__outlook-bridge__outlook_download_attachments
Args: { "id": "<Id>", "out": "/tmp/mail_att", "overwrite": true }
```

The tool returns the absolute paths of saved files. Then convert each saved attachment:
```bash
markitdown "/tmp/mail_att/filename.pptx" | head -200
```

Use the extracted text to include a one-line attachment summary in the briefing gist, e.g.:
- "ATTACHMENT: Q1 Cards Revenue Report — revenue up 12% YoY, 3 action items"
- "ATTACHMENT: Project timeline (Excel) — 15 milestones, next deadline April 3"

Only extract attachments for emails marked REPLY, URGENT, or DELEGATE — skip for MONITOR/SKIP to save time.

### 3. Classify New vs Previously Seen
Compare current inbox against `inbox-state.json`:
- **NEW**: Emails not in the previous state
- **PREVIOUSLY SEEN**: Emails present in a prior run
  - Note if user appears to have acted (email moved to archive, reply sent, etc.)

### 4. Analyze & Recommend Actions
For each email, determine one or more actions:

| Action | When | Symbol |
|--------|------|--------|
| **REPLY** | Needs your direct response (decision, approval, input) | ↩️ |
| **DELEGATE** | Someone on your team should handle this | 👉 |
| **FORWARD** | Needs to be sent to someone outside the thread | ➡️ |
| **MONITOR** | You're CC'd or FYI — no action now but keep an eye | 👀 |
| **URGENT** | Time-sensitive, needs immediate attention | ⚡ |
| **SKIP** | No action needed (newsletter, notification, auto-email) | ⏭️ |
| **FOLLOW-UP** | You already replied but thread needs follow-up check | 🔄 |

### 5. Generate Gist
For each email, write a 1-2 sentence gist:
- What is this about? (substance, not just subject line)
- What does the sender want from you specifically?
- Any context that matters (deadline, escalation, repeat request)

### 6. Present Briefing

```
═══════════════════════════════════════════════
INBOX BRIEFING — [date], [time]
[count] emails in inbox
═══════════════════════════════════════════════

NEW SINCE LAST RUN ([count])
───────────────────────────────────────────────
1. [SENDER] — [Subject]
   GIST: [1-2 sentence summary]
   ACTION: [symbol] [ACTION] — [brief reason]

2. ...

PREVIOUSLY SEEN ([count])
───────────────────────────────────────────────
N. [SENDER] — [Subject]
   GIST: [1-2 sentence summary]
   STATUS: [still in inbox / user replied / updated]
   ACTION: [symbol] [ACTION] — [brief reason]

═══════════════════════════════════════════════
INSIGHTS
═══════════════════════════════════════════════
- [X] emails need your decision/reply
- [Patterns observed, e.g., "3 emails from Cards team about same POS issue"]
- [Urgency flags, e.g., "ΥΦΑΝΤΙΔΗΣ waiting 2 days — no response yet"]
- [Delegation opportunities, e.g., "4 emails could be handled by sector heads"]
- [Thread connections between emails]
- [Suggested priorities for the day]
═══════════════════════════════════════════════
```

### 7. Save Inbox State
Write `~/.claude/drafts/inbox-state.json`:
```json
{
  "last_run": "ISO-8601 timestamp",
  "run_count": N,
  "seen_emails": [
    {
      "from": "sender name",
      "subject": "subject line",
      "timestamp": "email timestamp",
      "action_recommended": "REPLY|DELEGATE|FWD|MONITOR|SKIP|URGENT|FOLLOW-UP",
      "action_taken": "PENDING",
      "gist": "1-line summary"
    }
  ]
}
```
</process>

<specifications>
## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `folder` | No | `inbox` | Which folder to read: `inbox`, `archive`, or `both` |
| `--count` | No | `20` | Number of emails to process (for archive) |
| `--unread` | No | `false` | Only process unread emails |

## Output
- Inbox briefing with new vs previously seen separation
- 1-2 sentence gist per email
- Action recommendations with symbols
- Strategic insights and patterns
- NO drafting, NO replying, NO email modification
</specifications>

<examples>
## Usage Examples

### Quick inbox scan
```
/inbox-briefing
```

### Include archive context
```
/inbox-briefing both
```

### Only unread
```
/inbox-briefing --unread
```

### Deep archive scan
```
/inbox-briefing archive --count 50
```
</examples>
