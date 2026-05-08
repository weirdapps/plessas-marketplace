---
description: "Restore a previous version of the style guide from backups"
argument-hint: "[date|list]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep
---

<objective>
List available style guide backups and restore a selected version, replacing the current style guide.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 1. List Available Backups
Scan `~/.claude/drafts/style-guide-backups/` for backup files.
Files follow the naming convention: `YYYYMMDDHHMM_style-guide.md`

Present available versions:
```
STYLE GUIDE BACKUPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 202603210830 — 15.2 KB — [first line / description]
  2. 202603180600 — 14.8 KB — [first line / description]
  3. 202603150430 — 12.1 KB — [first line / description]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If user passed `list` as argument, stop here after showing the list.

### 2. Select Version
If a date argument was provided (YYYYMMDD or YYYYMMDDHHMM), find the matching backup.
If no date was provided and not `list`, ask the user which version to restore.

### 3. Backup Current Version
Before overwriting, save the current style guide:
```bash
TZ='Europe/Athens' date '+%Y%m%d%H%M'
cp plugins/email-handler/shared/style-guide.md \
   ~/.claude/drafts/style-guide-backups/YYYYMMDDHHMM_style-guide.md
```

### 4. Restore Selected Version
Copy the selected backup to `plugins/email-handler/shared/style-guide.md`.

### 5. Show Diff Summary
Briefly summarize what changed between the restored version and the one it replaced:
- Recipient profiles added/removed
- Tone changes
- Length changes
- Any other notable differences

### 6. Confirm
```
STYLE GUIDE RESTORED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Restored from: [backup filename]
Current saved as: [new backup filename]
Changes: [brief summary]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
</process>

<specifications>
## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `date` | No | — | Date to restore (YYYYMMDD or YYYYMMDDHHMM format) |
| `list` | No | — | Just list available backups without restoring |

## Output
- List of available backups (always shown)
- Restored style guide (if date selected)
- Diff summary between restored and replaced versions
</specifications>

<examples>
## Usage Examples

### List available backups
```
/style-rollback list
```

### Restore a specific date
```
/style-rollback 20260318
```

### Restore with exact timestamp
```
/style-rollback 202603180600
```

### Interactive — will prompt for selection
```
/style-rollback
```
</examples>
