---
description: "Periodic deep sync — update style guide from new sent emails since last sync"
argument-hint: "[--force] [--dry-run]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Query the knowledge store DB for all sent emails since the last sync, batch-update the style guide with new patterns, and flag any style drift detected.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 1. Load Sync State
Read `~/.claude/drafts/style-sync-state.json` for the last sync timestamp.
If the file doesn't exist, treat this as the first sync and process all sent emails (equivalent to `/style-rebuild`).

```json
{
  "last_sync": "ISO-8601 timestamp",
  "emails_processed": 0,
  "sync_count": 0
}
```

### 2. Query New Sent Emails

**Data source priority:**
1. **Knowledge store DB** (primary) — query for emails since last sync
2. **Archive mailbox** via `mcp__outlook-bridge__outlook_list_mail` (supplementary) — check for very recent sent emails not yet in DB. The user CCs himself on all replies, so sent mail appears in Archive (`folder: "Archive"`); filter client-side to messages where `From.upn` matches the user's UPN.
3. **Sent Items** — NEVER use. The user regularly empties Sent Items.

Fetch sent emails from knowledge store DB since last sync:
```sql
SELECT e.id, e.date_received, e.sender_name, e.sender_address,
       e.subject, e.summary, e.sentiment, e.language, e.content,
       e.in_reply_to, e.conversation_id
FROM emails e
WHERE e.sender_address LIKE '%<USER_EMAIL>%'
  AND e.date_received > '[last_sync_timestamp]'
ORDER BY e.date_received ASC;
```

Optionally supplement with recent Archive emails not yet in DB via the outlook-bridge MCP:
```
Tool: mcp__outlook-bridge__outlook_list_mail
Args: {
  "folder": "Archive",
  "top": 20,
  "select": "Id,Subject,From,ToRecipients,CcRecipients,ReceivedDateTime,ConversationId"
}
```

Filter the results client-side to messages where `From.upn` matches the user's UPN. For body content, follow up per-Id with `mcp__outlook-bridge__outlook_get_mail` (use `body: "text"` for plain-text extraction).

If no new emails found in either source, report "Already up to date" and exit.

### 3. Map Recipients for New Emails
For each new sent email, identify recipients:
```sql
SELECT p.name, p.email, ep.role_in_email
FROM email_people ep
JOIN people p ON ep.person_id = p.id
WHERE ep.email_id = ? AND ep.role_in_email IN ('to', 'cc');
```

### 4. Compute Incremental Metrics
For each recipient with new emails:
- Compute the same metrics as `/style-rebuild` but only on new data
- Compare against existing profile in `shared/style-guide.md`

### 5. Detect Style Drift
Flag when new patterns diverge from existing profile:

| Drift Type | Trigger |
|------------|---------|
| **Length drift** | Avg reply length changed >20% |
| **Tone shift** | Formality level changed for a recipient |
| **Language switch** | Language distribution shifted significantly |
| **New greeting/closing** | Previously unseen pattern appears 3+ times |
| **New recipient** | Recipient not yet profiled in style guide |

### 6. Backup and Update Style Guide
- Create timestamped backup in `~/.claude/drafts/style-guide-backups/`
- Update `shared/style-guide.md` with:
  - Updated per-recipient profiles (merge new data with existing)
  - New recipient profiles (if min threshold met)
  - Updated global patterns
  - Drift annotations where detected

### 7. Update Sync State
Write updated `~/.claude/drafts/style-sync-state.json`:
```json
{
  "last_sync": "ISO-8601 timestamp (now)",
  "emails_processed": N,
  "sync_count": N+1,
  "drift_detected": ["recipient1: length drift", "recipient2: tone shift"]
}
```

### 8. Present Sync Report
```
STYLE SYNC REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Period: [last_sync] to [now]
New emails processed: N

UPDATED PROFILES:
  [Name] — N new emails, [changes]
  [Name] — N new emails, [changes]

NEW PROFILES:
  [Name] — N emails, [language], [tone]

DRIFT ALERTS:
  [Name]: Length drift — avg was X words, now Y words
  [Name]: Tone shift — was formal, trending semi-formal

NO CHANGES:
  [Name], [Name] — no new data
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
</process>

<specifications>
## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--force` | No | `false` | Re-process all emails regardless of last sync |
| `--dry-run` | No | `false` | Show report without updating style guide |
| `--min-emails` | No | `3` | Minimum emails to create a new recipient profile |

## Output
- Sync report with drift alerts
- Updated style-guide.md (unless --dry-run)
- Updated sync state file
</specifications>

<examples>
## Usage Examples

### Sync since last run
```
/style-sync
```

### Force full re-sync
```
/style-sync --force
```

### Preview changes without applying
```
/style-sync --dry-run
```
</examples>
