---
description: "Review inbox with briefing, insights, action recommendations, and draft replies"
argument-hint: "[inbox|archive|both] [--count N] [--briefing-only]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep, mcp__plugin_mail_outlook-bridge__*, mcp__second-brain__*
---

> Path conventions: `<TEMP_DIR>` resolves to the OS temp directory (`$TMPDIR` or `/tmp` on macOS/Linux, `$env:TEMP` on Windows). Resolve before passing to tools.

<objective>
Read emails via the outlook-bridge MCP wrapper around `outlook-cli`, provide a comprehensive briefing with insights, recommend actions, and draft replies matching the user's communication style (defined in `${CLAUDE_PLUGIN_DATA}/style-guide.md`).

**Architecture**: outlook-bridge MCP for reading AND sending (Microsoft Graph via `outlook-cli`). New mail goes through `/send-mail` (creates a draft via `mcp__plugin_mail_outlook-bridge__outlook_send_mail`). Replies are drafted as text in the conversation; the user pastes manually into Outlook Reply so they retain final review and signature/threading control.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 0. Learn from Previous Drafts (AUTOMATIC, runs silently every time)

The draft-vs-actual comparison is specified once, in `${CLAUDE_PLUGIN_ROOT}/commands/draft-review.md`. Read that file and run its comparison before anything else: match pending drafts in `~/.claude/drafts/pending/` against what was actually sent, classify each as SENT_AS_IS / MODIFIED / REWRITTEN / NOT_SENT, update the style guide, and move processed drafts to `reviewed/`.

Three differences apply when running under `/mail-review`:

- Run it silently. Emit one line, `LEARNING: Processed N drafts, accuracy X/10`, rather than the full delta report; `/draft-review` is the command for the formal report.
- **First run**: if `~/.claude/drafts/` does not exist, create it with its `pending/`, `reviewed/` and `style-guide-backups/` subdirectories. If `inbox-state.json` is missing or corrupted, treat all emails as NEW and log `FIRST RUN: No previous state found. All emails treated as new.` (first run only).
- If `~/.claude/drafts/pending/` is empty, skip the whole step without comment.

Do NOT restate the comparison specification here. If the two ever disagree, `draft-review.md` wins.

### 1. Load Context

- Read the communication style guide from `${CLAUDE_PLUGIN_DATA}/style-guide.md`. If it is missing (first run), copy `${CLAUDE_PLUGIN_ROOT}/shared/style-guide-example.md` there first and tell the user:

  > "No style guide found. I've created a template at `${CLAUDE_PLUGIN_DATA}/style-guide.md`. Drafts will use generic professional defaults until you run `/style-sync` to analyse your sent email corpus and build a personalized guide."

  Until the guide is personalized, draft with professional defaults: BRIEF format for internal mail, FULL for external, in the sender's language. A populated guide holds the user's identity (name, role, email, signature), core style rules (brevity, format, language, tone), reply patterns by type, per-recipient profiles and anti-patterns.
- Read `~/.claude/drafts/inbox-state.json` to know which emails were seen in the previous run

### 2-6. Read, classify, recommend, and present the briefing

Call `mcp__plugin_mail_outlook-bridge__outlook_auth_check` first; if `status != "ok"`, surface the auth flow before continuing.

These five steps are specified once, in `${CLAUDE_PLUGIN_ROOT}/commands/inbox-briefing.md`, sections 2 through 6. Read that file and follow it exactly: reading messages via `outlook_list_mail` / `outlook_get_mail`, attachment extraction, NEW vs PREVIOUSLY SEEN classification, the action taxonomy, gist generation, and the briefing output format.

Two differences apply when running under `/mail-review`:

- Default to `top: 50`. Drafting needs a wider sweep than a plain briefing.
- More than one action may apply to a single email (for example URGENT + REPLY). Keep every action that fits, because the drafting step below keys off them.
- When `mcp__second-brain__*` tools are available, add a `CONTEXT:` line under each email's GIST: call `mcp__second-brain__person_context` with the sender's address (the name only when the message holds no address; read `resolved_by` and `match_count` before trusting a name match) for frequency, related decisions and open items, plus `query_actions` (`owner=<sender>`, `status="open"`) and `query_decisions` (`topic=<email topic>`) where useful. Without second-brain, omit the line.
- Urgency signals: the boss asking directly (identify the boss from the style guide's per-recipient profiles), urgent words in the subject, repeated follow-ups from the same person, the user in TO rather than CC, customer-facing issues.

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

**SKIP pre-filter (apply BEFORE drafting).** The default action is SKIP. Draft only if ALL of these hold:

1. The user is in TO (not just CC)
2. The sender is asking something specific from the user
3. The email is not a status update, FYI, newsletter or auto-notification
4. There is no recent reply from the user in the thread already

If in doubt, classify as MONITOR, not REPLY.

**Calibration examples.** Before drafting each reply, recall how the user actually replies:

| Scenario | Draft Instinct | What User Actually Did |
|----------|---------------|----------------------|
| Team asks about UNITY entity | 20-word delegation + justification | "θα το κυνηγήσω εγώ" (5 words) |
| External consultant follow-up | "Good to hear from you..." | "Hi T! we are progressing quite fast..." (200 words, showcase) |
| Boss-originated escalation | "I agree this is unacceptable..." | FW only (no body) |
| Scheduling with external | "When works for you?" | "θα οργανωθεί από [assistant name]" |
| Delegated meeting | "I'll attend" | "εγώ optional" |

**Core principles**, all taken from the style guide: match the user's typical reply length and never write more than necessary; follow its BRIEF vs FULL rules; adjust formality per recipient profile; follow its language rules (which language for internal vs external) and its capitalization, punctuation, greeting and closing rules.

For each email marked REPLY or DELEGATE:

1. Identify the recipient and look up their profile in the style guide
2. Determine the reply type (approval, delegation, decision, thank-you, etc.)
3. Draft the reply following the style guide's patterns, with context from step 6b to make it substantively accurate
4. For DELEGATE: draft a forwarding message or a reply that assigns ownership
5. Validate against the style guide's anti-patterns ("NEVER DO" list)

For each email marked FORWARD:

- Suggest who to forward to and draft forwarding text (or none, if it is a plain FW with signature)

**Quality checklist** before presenting a draft:

- [ ] Is it shorter than or equal to what the user would actually write? (check style guide)
- [ ] Does it follow the style guide's capitalization rules?
- [ ] If BRIEF: no greeting, no closing?
- [ ] If FULL: proper format per style guide?
- [ ] Is it in the correct language per style guide rules?
- [ ] Does the tone match the specific recipient's profile?
- [ ] Is the reply type correct (delegation vs. decision vs. approval)?
- [ ] Would the user actually reply to this email, or would they skip it?

**What NOT to do:**

- Don't draft replies for informational/FYI emails
- Don't use formal language where the style guide says to be informal
- Don't write paragraphs; if your draft exceeds 3 sentences, reconsider
- Don't add the signature block; Outlook handles that
- Don't draft in the wrong language for the recipient
- Don't be polite where the user would be direct
- Don't second-guess decisions; be decisive like the user

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
