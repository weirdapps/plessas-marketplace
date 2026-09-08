---
description: "Review inbox with briefing, insights, action recommendations, and draft replies"
argument-hint: "[inbox|archive|both] [--count N] [--briefing-only]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep, mcp__plugin_mail_outlook-bridge__*, mcp__second-brain__*
---

> Path conventions: `<TEMP_DIR>` resolves to the OS temp directory (`$TMPDIR` or `/tmp` on macOS/Linux, `$env:TEMP` on Windows). Resolve before passing to tools.

<objective>
Read emails via the outlook-bridge MCP wrapper around `outlook-cli`, provide a comprehensive briefing with insights, recommend actions, and draft replies matching the user's communication style (defined in `${CLAUDE_PLUGIN_ROOT}/shared/style-guide.md`).

**Architecture**: outlook-bridge MCP for reading AND sending (Microsoft Graph via `outlook-cli`). New mail goes through `/send-mail` (creates a draft via `mcp__plugin_mail_outlook-bridge__outlook_send_mail`). Replies are drafted as text in the conversation; the user pastes manually into Outlook Reply so they retain final review and signature/threading control.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 0. Learn from Previous Drafts (AUTOMATIC, runs silently every time)

The draft-vs-actual comparison is specified once, in `${CLAUDE_PLUGIN_ROOT}/commands/draft-review.md`. Read that file and run its comparison before anything else: match pending drafts in `~/.claude/drafts/pending/` against what was actually sent, classify each as SENT_AS_IS / MODIFIED / REWRITTEN / NOT_SENT, update the style guide, and move processed drafts to `reviewed/`.

Three differences apply when running under `/mail-review`:

- Run it silently. Emit one line, `LEARNING: Processed N drafts, accuracy X/10`, rather than the full delta report; `/draft-review` is the command for the formal report.
- **First run**: if the `~/.claude/drafts/` directory structure does not exist, create it automatically. If no `inbox-state.json` exists, treat all emails as NEW.
- If `~/.claude/drafts/pending/` is empty, skip the whole step without comment.

Do NOT restate the comparison specification here. If the two ever disagree, `draft-review.md` wins.

### 1. Load Context

- Read the communication style guide from `${CLAUDE_PLUGIN_ROOT}/shared/style-guide.md`
- Read `~/.claude/drafts/inbox-state.json` to know which emails were seen in the previous run

### 2-6. Read, classify, recommend, and present the briefing

Call `mcp__plugin_mail_outlook-bridge__outlook_auth_check` first; if `status != "ok"`, surface the auth flow before continuing.

These five steps are specified once, in `${CLAUDE_PLUGIN_ROOT}/commands/inbox-briefing.md`, sections 2 through 6. Read that file and follow it exactly: reading messages via `outlook_list_mail` / `outlook_get_mail`, attachment extraction, NEW vs PREVIOUSLY SEEN classification, the action taxonomy, gist generation, and the briefing output format.

Two differences apply when running under `/mail-review`:

- Default to `top: 50`. Drafting needs a wider sweep than a plain briefing.
- More than one action may apply to a single email (for example URGENT + REPLY). Keep every action that fits, because the drafting step below keys off them.

Do NOT restate the briefing specification here. If the two ever disagree, `inbox-briefing.md` wins.

### 6b. (OPTIONAL) Enrich drafts with knowledge-store context

> **Only run this step if second-brain tools are available in your environment**, that is, if your tool list contains tools whose names begin with `mcp__second-brain__`. The `second-brain` MCP server is available via the optional `mail-pro` plugin in the [`plessas-lab`](https://github.com/weirdapps/plessas-lab) marketplace (requires the `weirdapps/plessas-second-brain` knowledge store). If no such tool is listed, **skip this entire section**; the `mail` plugin is fully functional without it, drafts will just lean on the email thread itself + the style guide.

If `second-brain` is available, query it to enrich draft context. The style guide tells you HOW to write; second-brain tells you WHAT to say.

**For each email marked REPLY, DELEGATE, FOLLOW-UP, or FORWARD, run in parallel:**

1. `mcp__second-brain__search_emails`: search by subject keywords to find thread history and prior decisions
2. `mcp__second-brain__topic_context`: get broader topic context (related threads, key people, open actions)
3. `mcp__second-brain__person_context`: for senders/recipients where relationship context would sharpen the draft
4. `mcp__second-brain__query_decisions`: if the thread involves a pending decision or approval
5. `mcp__second-brain__query_emails`: filter by person + date range for recent exchanges on the topic

**Use the gathered context to:**

- Reference specific facts, numbers, or prior decisions in the draft
- Route delegations to the correct person/team (not just a name)
- Add productive pressure by citing deadlines, audit findings, or commitments
- Avoid re-asking questions that were already answered in the thread

**Keep drafts BRIEF**: context makes them sharper, not longer. A 10-word draft that references the right fact beats a 50-word draft that's vague.

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
2. **Copy to clipboard as rich text** (justified alignment preserved), platform-aware:
   - **macOS**: `printf '<html>…</html>' | textutil -stdin -format html -convert rtf -stdout | pbcopy`
   - **Windows**: `Get-Content file.html | Set-Clipboard` (PowerShell) or `clip < file.html` (plain HTML)
   - **Linux**: `xclip -selection clipboard -t text/html < file.html`

   **macOS:**

   ```bash
   printf '<html><body style="font-family: &quot;Aptos Light&quot;, Aptos, sans-serif; font-size: 12pt; color: #404040; text-align: justify;">Draft body here</body></html>' \
     | textutil -stdin -format html -convert rtf -stdout | pbcopy
   ```

   **Windows (PowerShell):**

   ```powershell
   $html = '<html><body style="font-family: &quot;Aptos Light&quot;, Aptos, sans-serif; font-size: 12pt; color: #404040; text-align: justify;">Draft body here</body></html>'
   $html | Set-Clipboard -AsHtml
   ```

   **Linux (X11 with xclip):**

   ```bash
   printf '<html><body style="font-family: &quot;Aptos Light&quot;, Aptos, sans-serif; font-size: 12pt; color: #404040; text-align: justify;">Draft body here</body></html>' \
     | xclip -selection clipboard -t text/html
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

### Full workflow: briefing + drafts (auto-learns first)

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

### Learning mode only: process pending drafts

```
/mail-review --learn
```

</examples>
