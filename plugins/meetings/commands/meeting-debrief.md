---
description: "Post-meeting debrief — capture decisions, action items, and distribute summary"
argument-hint: "[meeting name or number] [--distribute]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Capture post-meeting outcomes: decisions made, action items assigned, follow-ups needed. Save structured debrief and optionally distribute summary to attendees.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 0. Verify Outlook MCP Available (FAIL-FAST)

This plugin reads the calendar via `mcp__outlook-bridge__*` tools bundled in the **mail** plugin. Check the bridge is reachable:

```
Tool: mcp__outlook-bridge__outlook_auth_check
```

If the tool is **not available**, stop and tell the user:

> The `meetings` plugin requires the `mail` plugin to be installed.
> Install it with: `/plugin install mail@plessas-marketplace`
> Then re-run `/meeting-debrief`.

### 1. Identify Meeting

- If user specifies a meeting name, match it against today's calendar
- If no meeting specified, show today's calendar events and ask which one
- If only one meeting today (or one recently ended), use it automatically

### 2. Read Calendar for Meeting Details

Use the outlook-bridge MCP as the primary calendar source — structured M365-synced data via Microsoft Graph:

```
Tool: mcp__outlook-bridge__outlook_list_calendar
Args: { "from": "start of today", "to": "end of today" }

Tool: mcp__outlook-bridge__outlook_get_event
Args: { "id": "<event Id>" }
```

Fall back to Outlook AppleScript only if the outlook-bridge MCP is unavailable.
See `shared/calendar-access.md` for access patterns.

### 3. Capture Debrief

Ask the user to provide (free text is fine):

- **Decisions made** — what was decided, by whom
- **Action items** — what, who owns it, deadline
- **Follow-ups** — things to track or revisit
- **Key takeaways** — notable observations

Parse and structure the user's input.

### 4. Save Debrief

Ensure `~/.claude/meetings/debriefs/` exists.
Save as `YYYY-MM-DD-meeting-name.json` with structured data:

- Meeting metadata (name, date, time, attendees)
- Decisions with attribution
- Action items with owners and deadlines
- Follow-ups with timing
- Free-form notes

### 5. Distribute Summary (if `--distribute` or user confirms)

Compose a concise HTML meeting summary with:

- Decisions listed
- Action items table (action, owner, deadline)
- Next steps

Use `/send-mail` to create the email via Outlook, addressed to all attendees.

### 6. Log to Decision Tracker

If `plugins/_shared/decision-tracker/` exists, append decisions and action items.
</process>

<specifications>
## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `meeting` | No | auto-detect | Meeting name or number from today's list |
| `--distribute` | No | false | Send summary to attendees after capture |

## Output

- Structured debrief saved to `~/.claude/meetings/debriefs/`
- Optional email summary sent to attendees
- Decisions and actions logged to tracker (if available)
</specifications>

<examples>
## Usage Examples

### Debrief the most recent meeting

```
/meeting-debrief
```

### Debrief a specific meeting

```
/meeting-debrief project review
```

### Debrief and send summary to attendees

```
/meeting-debrief --distribute
```

### Provide debrief inline

```
/meeting-debrief project review
Decisions: Go with vendor A, budget approved at 50K
Actions: Maria to send PO by Friday, John to schedule kickoff
Follow-up: Check delivery timeline in 2 weeks
```

</examples>

<related_commands>

## Related Commands

| Command | When to Use |
|---------|-------------|
| `/meeting-prep` | Before a meeting to get attendee dossiers and context |
| `/send-mail` | To send follow-up emails independently |
| `/mail-review` | To review inbox for meeting-related threads |
</related_commands>
