---
description: "Review inbox with briefing, insights, action recommendations, and draft replies"
argument-hint: "[inbox|archive|both] [--count N] [--briefing-only]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Read emails via the outlook-bridge MCP wrapper around `outlook-cli`, provide a comprehensive briefing with insights, recommend actions, and draft replies matching the user's communication style (defined in `shared/style-guide.md`).

**Architecture**: outlook-bridge MCP for reading AND sending (Microsoft Graph via `outlook-cli`). New mail goes through `/send-mail` (creates a draft via `mcp__outlook-bridge__outlook_send_mail`). Replies are drafted as text in the conversation — user pastes manually into Outlook Reply so they retain final review and signature/threading control.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 0. Learn from Previous Drafts (AUTOMATIC — runs silently every time)
**First run**: If `~/.claude/drafts/` directory structure doesn't exist, create it automatically. If no `inbox-state.json` exists, treat all emails as NEW. Skip learning if no pending drafts.

Check `~/.claude/drafts/pending/` for unprocessed draft files.
If pending drafts exist:
1. Read Archive via `mcp__outlook-bridge__outlook_list_mail` to find matching sent emails (Archive is the primary source — user regularly empties Sent Items, but all replies are CC'd to self and land in Archive):
   ```
   Tool: mcp__outlook-bridge__outlook_list_mail
   Args: {
     "folder": "Archive",
     "top": 30,
     "select": "Id,Subject,From,ToRecipients,CcRecipients,ReceivedDateTime,ConversationId"
   }
   ```
   Filter client-side to messages where `From.upn` matches the user's UPN. For body content, follow up per-Id with `mcp__outlook-bridge__outlook_get_mail`.
   - Also check Sent Items (`folder: "Sent Items"`) as a supplement for very recent emails (last 1-2 hours) that may not yet be in Archive
   - Match by subject keywords and approximate date (within 72h of draft creation)
2. For each matched draft:
   - Extract the ACTUAL reply text the user sent (strip signature and quoted text)
   - Compare against the `draft_text` from the pending JSON
   - Analyze: length, tone, content, word choice, decision, skip/reply differences
   - Classify: SENT_AS_IS | MODIFIED | REWRITTEN | NOT_SENT
3. **Auto-classify stale drafts**: Any draft in `pending/` older than 72 hours with no matching sent email → NOT_SENT (triage error). Learn: was the email low-priority? Was the recommended action wrong?
4. Scan the last 20 sent items for **organic emails** not matching any draft:
   - New recipients → create profile stub
   - Sentence patterns, question frequency, imperative usage
   - If consistent across 3+ organic emails → apply as style guide update
5. Compute accuracy score: `(SENT_AS_IS + 0.5 * MODIFIED) / total_drafts`
6. If any learnings found:
   - Back up style guide to `~/.claude/drafts/style-guide-backups/`
   - Update `shared/style-guide.md` in the email-handler plugin directory
   - Move processed drafts to `reviewed/` with `delta_type`, `learnings`, `reviewed_date`
   - Append a dated entry to `~/.claude/drafts/learnings.md` with accuracy score
7. Show a brief learning summary:
   ```
   LEARNING: Processed N drafts — accuracy X/10
     SENT_AS_IS: X | MODIFIED: X | REWRITTEN: X | NOT_SENT: X
   Style guide updated: [changes]
   ```
6. Ingest ALL recent sent emails (continuous learning)
   - Read last 20 Archive messages via `mcp__outlook-bridge__outlook_list_mail` (`folder: "Archive", top: 20`), filter client-side to messages where `From.upn` matches the user's UPN
     (Archive is the canonical source — Sent Items gets emptied regularly; user CCs himself on all replies)
   - For each: identify recipient, analyze length, language, tone, greeting, closing
   - Compare against current style guide profiles
   - If actual email deviates from profile consistently, update the profile
   - Log: `"CONTINUOUS LEARNING: Analyzed N organic emails, M style updates applied"`

### 1. Load Context
- Read the communication style guide from `shared/style-guide.md`
- Read `~/.claude/drafts/inbox-state.json` to know which emails were seen in the previous run

### 2. Read Emails via outlook-bridge MCP

Call `mcp__outlook-bridge__outlook_auth_check` first; if `status != "ok"`, surface the auth flow before continuing.

**Reading inbox messages:**
```
Tool: mcp__outlook-bridge__outlook_list_mail
Args: {
  "folder": "Inbox",
  "top": 50,
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

**Reading full message body** (for important/complex emails that need deeper analysis):
```
Tool: mcp__outlook-bridge__outlook_get_mail
Args: { "id": "<Id>", "body": "html" }   # use "text" for plain-text extraction
```

**Key points:**
- One `outlook_list_mail` call returns up to 100 messages — use `since` + `all:true` + `max` for larger sweeps
- Use `select` to keep payloads small; only request body via `outlook_get_mail` when needed
- For `--unread` flag: include `IsRead` in `select` and filter client-side (`IsRead == false`)
- `Id` is a stable identifier for each message
- If `{error: "auth_required"}` is returned, run `outlook-cli login` via Bash with user approval and retry

### 2b. Extract Attachment Content (if relevant)

For emails with attachments (PPTX, PDF, DOCX, XLSX), use `markitdown` to extract content for summarization. Save attachments via the MCP wrapper:

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

Only extract attachments for emails marked REPLY, URGENT, or DELEGATE — skip for MONITOR/SKIP to save time. Clean up temp files after extraction: `rm -rf /tmp/mail_att/*`

### 3. Classify New vs Previously Seen
Compare current inbox against `inbox-state.json`:
- **NEW**: Emails not in the previous state (arrived since last run)
- **PREVIOUSLY SEEN**: Emails that were in inbox during a prior run
  - If previously seen with an action recommendation, note if the user acted on it or not

### 4. Analyze & Recommend Actions
For each email, determine:

| Action | When | Symbol |
|--------|------|--------|
| **REPLY** | Needs your direct response (decision, approval, input) | ↩️ |
| **DELEGATE** | Someone on your team should handle this | 👉 |
| **FORWARD** | Needs to be sent to someone outside the thread | ➡️ |
| **MONITOR** | You're CC'd or FYI — no action now but keep an eye | 👀 |
| **URGENT** | Time-sensitive, needs immediate attention | ⚡ |
| **SKIP** | No action needed (newsletter, notification, auto-email) | ⏭️ |
| **FOLLOW-UP** | You already replied but thread needs follow-up check | 🔄 |

Multiple actions can apply (e.g., URGENT + REPLY).

### 5. Generate Gist
For each email, write a 1-2 sentence gist:
- What is this about? (substance, not just subject)
- What does the sender want from you specifically?
- Any context that matters (deadline, escalation, repeat request)

### 6. Present Inbox Briefing
Present the briefing in this format:

```
═══════════════════════════════════════════════
INBOX BRIEFING — [date], [time]
═══════════════════════════════════════════════

NEW SINCE LAST RUN ([count] emails)
───────────────────────────────────────────────
1. [SENDER] — [Subject]
   GIST: [1-2 sentence summary]
   ACTION: [symbol] [ACTION] — [brief reason]

2. [SENDER] — [Subject]
   GIST: [1-2 sentence summary]
   ACTION: [symbol] [ACTION] — [brief reason]

PREVIOUSLY SEEN ([count] emails)
───────────────────────────────────────────────
3. [SENDER] — [Subject]
   GIST: [1-2 sentence summary]
   STATUS: [still waiting / user replied / updated since last run]
   ACTION: [symbol] [ACTION] — [brief reason]

INSIGHTS
───────────────────────────────────────────────
- [X] emails need your decision/reply
- [Pattern/theme observed, e.g., "Boss escalated same issue twice this week"]
- [Urgency note, e.g., "Sender X waiting since 20:57 — no response yet"]
- [Delegation opportunity, e.g., "3 emails could be handled by your team"]
- [Any thread connections between emails]
═══════════════════════════════════════════════
```

### 6b. Gather Context from Second-Brain (before drafting)

For each email marked REPLY, DELEGATE, FOLLOW-UP, or FORWARD, query the second-brain MCP to enrich the draft with substantive context. The style guide tells you HOW to write; second-brain tells you WHAT to say.

**For each actionable email, run in parallel:**
1. `search_emails` — search by subject keywords to find thread history and prior decisions
2. `topic_context` — get broader topic context (related threads, key people, open actions)
3. `person_context` — for senders/recipients where relationship context would sharpen the draft
4. `query_decisions` — if the thread involves a pending decision or approval
5. `query_emails` — filter by person + date range for recent exchanges on the topic

**Use the gathered context to:**
- Reference specific facts, numbers, or prior decisions in the draft
- Route delegations to the correct person/team (not just a name)
- Add productive pressure by citing deadlines, audit findings, or commitments
- Avoid re-asking questions that were already answered in the thread

**Keep drafts BRIEF** — context makes them sharper, not longer. A 10-word draft that references the right fact beats a 50-word draft that's vague.

**Skip second-brain queries for:**
- SKIP/MONITOR emails (no draft needed)
- Simple acknowledgments ("ευχαριστώ [name]") where no context is needed
- Forwarding with no body text (Type 7)

### 7. Draft Replies
For each email marked REPLY or DELEGATE:
- Generate a reply following the style guide exactly
- Adapt tone per recipient using per-recipient profiles
- Incorporate context from step 6b to make drafts substantively accurate
- For DELEGATE: draft a forwarding message or a reply that assigns ownership

For each email marked FORWARD:
- Suggest who to forward to and draft forwarding text (if any)

### 8. Save State
**Save drafts**: For each draft created, save a JSON file to `~/.claude/drafts/pending/`:
```json
{
  "id": "YYYYMMDD-NNN",
  "created": "ISO-8601 timestamp",
  "subject": "email subject",
  "subject_keywords": ["key", "words"],
  "original_from": "sender name",
  "recipients_to": ["names"],
  "recipients_cc": ["names"],
  "reply_type": "reply | reply_all | forward",
  "draft_text": "exact draft text",
  "draft_style": "BRIEF | FULL",
  "draft_pattern": "Type N (pattern name)",
  "status": "pending"
}
```

**Update inbox state**: Write `~/.claude/drafts/inbox-state.json`:
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
      "action_taken": "DRAFTED|SKIPPED|PENDING",
      "gist": "1-line summary"
    }
  ]
}
```

**Prune stale entries**: Remove `seen_emails` entries older than 14 days to keep the file lean.

### 9. Present Drafts

Present each draft reply as TEXT in the conversation for user review.

Reply drafts are presented as text in the conversation (not auto-injected into Outlook) so the user retains final review before send and so signature/threading is handled by Outlook's native Reply flow on paste.

**For each reply draft:**
1. Display the draft text in the conversation
2. **Copy to clipboard as rich text** (justified alignment preserved) — platform-aware:
   - **macOS**: `printf '<html>…</html>' | textutil -stdin -format html -convert rtf -stdout | pbcopy`
   - **Windows**: `Get-Content file.html | Set-Clipboard` (PowerShell) or `clip < file.html` (plain HTML)
   - **Linux**: `xclip -selection clipboard -t text/html < file.html`
   ```bash
   # macOS example:
   printf '<html><body style="font-family: Aptos, sans-serif; font-size: 12pt; color: #404040; text-align: justify;">Draft body here</body></html>' | textutil -stdin -format html -convert rtf -stdout | pbcopy
   ```
   Use `<br>` for line breaks and `<br><br>` for paragraph spacing in the HTML.
3. Include the clipboard workflow instructions: the user opens the original email in Outlook, clicks Reply/Reply All, and pastes using Ctrl+V (Cmd+V on macOS) (formatting and justified alignment are preserved)
4. For delegation or forwarding emails that don't need the original thread, use `/send-mail` to create a new email via `make new outgoing message`

**After presenting all drafts:** Ask the user which to send, modify, or discard.
</process>

<specifications>
## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `folder` | No | `both` | Which folder to read: `inbox`, `archive`, or `both` |
| `--count` | No | `20` | Number of recent emails to process |
| `--unread` | No | `false` | Only process unread emails |
| `--learn` | No | `false` | Run ONLY learning mode (skip reading new emails) |
| `--briefing-only` | No | `false` | Show briefing and insights only, skip drafting |

## Output
- Learning summary (if pending drafts found)
- Inbox briefing with new vs previously seen separation
- Action recommendations with gists
- Insights and patterns
- Draft reply text for actionable emails (user pastes manually into Outlook Reply)
</specifications>

<examples>
## Usage Examples

### Full workflow — briefing + drafts (auto-learns first)
```
/mail-review
```

### Just the briefing, no drafts
```
/mail-review --briefing-only
```

### Read last 50 from archive
```
/mail-review archive --count 50
```

### Only unread emails
```
/mail-review --unread
```

### Learning mode only — process pending drafts
```
/mail-review --learn
```
</examples>
