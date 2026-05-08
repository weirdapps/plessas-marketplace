---
description: "Surface recent decisions, track delegations, and check decision consistency"
argument-hint: "[today|week|TOPIC] [--pending]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Surface recent decisions from both the local decision log and the knowledge store (via MCP), track delegated actions with aging alerts, and check for decision consistency.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 1. Determine Scope
- `today`: decisions from the current day
- `week`: decisions from the last 7 days (default)
- `[TOPIC]`: filter decisions by topic name
- `--pending`: show only pending/undecided items

### 2. Load Local Decision Log
Read `~/.claude/drafts/decisions.json` for locally tracked decisions.
If the file doesn't exist, create it with an empty array.

### 3. Query Knowledge Store Decisions (via MCP)

Use `mcp__second_brain__query_decisions` with:
- `days=7` (for week scope) or `days=1` (for today scope)
- `topic="[topic]"` if a topic filter was specified
- `person="[person]"` if filtering by decision-maker

### 4. Query Action Items (via MCP)

Use `mcp__second_brain__query_actions` with:
- `status="open"` for pending items
- `owner="[owner]"` if filtering by owner

### 5. Filter by Topic (if specified)

Use `mcp__second_brain__query_decisions` with `topic="[topic]"`

### 6. Cross-Reference Local and DB
Merge local decisions with DB decisions:
- Identify decisions present in both (reconcile)
- Flag decisions only in local log (not yet in DB)
- Flag decisions only in DB (not tracked locally)

### 7. Delegation Tracker with Aging
For action items with assigned owners:
```
DELEGATION TRACKER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVERDUE (action needed):
  [Task] — assigned to [Owner] — due [date] (X days overdue)
  [Task] — assigned to [Owner] — due [date] (X days overdue)

DUE SOON (next 3 days):
  [Task] — assigned to [Owner] — due [date]

IN PROGRESS:
  [Task] — assigned to [Owner] — due [date]

COMPLETED:
  [Task] — assigned to [Owner] — completed [date]
```

### 8. Decision Consistency Checks
Look for potential contradictions:
- Same topic, different decisions on different dates
- Reversals (approved then denied, or vice versa)
- Conflicting delegations (same task assigned to multiple people)

```
CONSISTENCY ALERTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[date]: Approved [X] — but on [earlier date] denied similar request
[date]: Delegated [task] to [A] — but [B] was already assigned
```

### 9. Present Decision Report
```
DECISIONS — [period]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total decisions: N
Total action items: N (X completed, Y pending, Z overdue)

RECENT DECISIONS:
  [date] [topic] — [decision summary] (decided by [name])
  [date] [topic] — [decision summary] (decided by [name])

DELEGATION STATUS:
  [overdue/due soon/in progress/completed counts]

CONSISTENCY: [OK | N alerts found]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
</process>

<specifications>
## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `scope` | No | `week` | Time scope: `today`, `week`, or a topic name |
| `--pending` | No | `false` | Show only pending/undecided items |
| `--owner` | No | all | Filter delegations by owner name |

## Output
- Decision summary for the period
- Delegation tracker with aging alerts
- Consistency check results
</specifications>

<examples>
## Usage Examples

### This week's decisions (default)
```
/decisions
```

### Today's decisions only
```
/decisions today
```

### Filter by topic
```
/decisions cards
```

### Show only pending items
```
/decisions --pending
```

### Filter delegations by owner
```
/decisions week --owner Georgiou
```
</examples>
