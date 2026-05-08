---
description: "Accuracy trends, top corrections, and recipient profile accuracy for the style learning system"
argument-hint: "[--recipient NAME] [--days N]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Analyze the style learning system's performance: accuracy trends over time, most common corrections, per-recipient accuracy, and style guide evolution.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 1. Load Learning History
Read `~/.claude/drafts/learnings.md` for the full historical record of draft reviews.
Read all files from `~/.claude/drafts/reviewed/` for detailed draft-vs-actual comparisons.

### 2. Compute Accuracy Trend
For each review session (by date), calculate:
- Total drafts reviewed
- SENT_AS_IS count (perfect matches)
- MODIFIED count (partial matches)
- REWRITTEN count (misses)
- NOT_SENT count (triage errors)
- Accuracy score: (SENT_AS_IS + 0.5 * MODIFIED) / total

Plot trend as text sparkline or ASCII chart:
```
ACCURACY TREND (last 10 sessions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mar 01  ████████░░  80%  (4/5 perfect)
Mar 05  ██████████  100% (3/3 perfect)
Mar 08  ██████░░░░  60%  (3/5 perfect)
Mar 12  █████████░  90%  (9/10 perfect)
...
Overall: X% accuracy across N drafts
```

### 3. Top Corrections
Aggregate learnings to find recurring correction patterns:
- Group similar corrections (e.g., "too formal", "too long", "wrong greeting")
- Rank by frequency
- Show top 5 with examples

```
TOP 5 CORRECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Too formal (N times) — "Used 'Dear X' when user prefers 'Hi X'"
2. Too long (N times) — "Draft avg 150 words, user sent avg 80 words"
3. Wrong language (N times) — "Drafted in English, user replied in Greek"
4. Missing action item (N times) — "User added explicit deadline/task"
5. Unnecessary pleasantries (N times) — "User removed opening small talk"
```

### 4. Per-Recipient Accuracy
For each recipient with reviewed drafts:
```
RECIPIENT ACCURACY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Name]     N drafts  X% accuracy  Top issue: [issue]
[Name]     N drafts  X% accuracy  Top issue: [issue]
[Name]     N drafts  X% accuracy  (no issues — perfect match)
```

### 5. Style Guide Evolution Timeline
Track how the style guide has changed over time using backups in `~/.claude/drafts/style-guide-backups/`:
- List backup dates
- Summarize key changes between versions (diff analysis)
- Show when recipient profiles were added/modified

```
STYLE GUIDE EVOLUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[date] — Initial creation
[date] — Added profile for [Name], updated greeting for [Name]
[date] — Tone adjustment for [Name] (formal -> semi-formal)
[date] — Full rebuild from corpus (N emails analyzed)
```

### 6. Present Full Report
Combine all sections into a comprehensive stats report.
</process>

<specifications>
## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--recipient` | No | all | Focus stats on a specific recipient |
| `--days` | No | `30` | How many days of history to analyze |

## Output
- Accuracy trend over time
- Top 5 most common corrections
- Per-recipient accuracy breakdown
- Style guide evolution timeline
</specifications>

<examples>
## Usage Examples

### Full stats overview
```
/style-stats
```

### Stats for a specific recipient
```
/style-stats --recipient Papadopoulos
```

### Last 7 days only
```
/style-stats --days 7
```
</examples>
