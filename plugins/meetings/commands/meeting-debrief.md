---
description: "Post-meeting debrief: capture decisions, action items, and distribute summary"
argument-hint: "[meeting name or number] [--distribute]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep, mcp__plugin_mail_outlook-bridge__*
---

<objective>
Capture post-meeting outcomes: decisions made, action items assigned, follow-ups needed. Save structured debrief and optionally distribute summary to attendees.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 0. Verify Outlook MCP Available (FAIL-FAST)

This plugin reads the calendar via the outlook-bridge MCP tools bundled in the **mail** plugin, whose names all begin with `mcp__plugin_mail_outlook-bridge__`. Check the bridge is reachable:

```
Tool: mcp__plugin_mail_outlook-bridge__outlook_auth_check
```

If that tool is **not available** (no tool whose name begins with `mcp__plugin_mail_outlook-bridge__` appears in your tool list), stop and tell the user:

> The `meetings` plugin requires the `mail` plugin to be installed.
> Install it with: `/plugin install mail@plessas-marketplace`
> Then re-run `/meeting-debrief`.

### 0b. Dispatch the meeting-intelligence agent

Invoke `agents/meeting-intelligence` for the debrief run. That agent owns the capture flow and the debrief JSON schema. The steps below state the contract it must satisfy; execute them directly only if the agent is unavailable.

### 1. Identify Meeting

- If user specifies a meeting name, match it against today's calendar
- If no meeting specified, show today's calendar events and ask which one
- If only one meeting today (or one recently ended), use it automatically

### 2. Read Calendar for Meeting Details

Use the outlook-bridge MCP as the primary calendar source, which returns structured M365-synced data via Microsoft Graph:

```
Tool: mcp__plugin_mail_outlook-bridge__outlook_list_calendar
Args: { "from": "start of today", "to": "end of today" }

Tool: mcp__plugin_mail_outlook-bridge__outlook_get_event
Args: { "id": "<event Id>" }
```

Fall back to Outlook AppleScript only if the outlook-bridge MCP is unavailable.
See `shared/calendar-access.md` for access patterns.

### 3. Capture Debrief

Ask the user to provide (free text is fine):

- **Decisions made**: what was decided, by whom
- **Action items**: what, who owns it, deadline
- **Follow-ups**: things to track or revisit
- **Key takeaways**: notable observations

Parse and structure the user's input.

### 4. Save Debrief

Ensure `~/.claude/meetings/debriefs/` exists.
Save as `YYYY-MM-DD-meeting-name.json` (lowercase, spaces to hyphens) using exactly these field names, so later runs can read the file back:

```json
{
  "meeting": {
    "name": "Meeting name from calendar",
    "date": "2026-03-21",
    "time": "14:00-15:00",
    "attendees": ["Name 1", "Name 2"]
  },
  "decisions": [
    { "decision": "What was decided", "decided_by": "Who made the call", "context": "Brief context" }
  ],
  "action_items": [
    { "action": "What needs to be done", "owner": "Who owns it", "deadline": "When (if specified)", "status": "open" }
  ],
  "follow_ups": [
    { "topic": "What to track", "when": "When to follow up", "with": "Who to follow up with" }
  ],
  "notes": "Free-form notes or key takeaways",
  "debriefed_at": "ISO-8601 timestamp"
}
```

### 5. Distribute Summary (if `--distribute` or user confirms)

Compose a concise HTML meeting summary with:

- Decisions listed
- Action items table (action, owner, deadline)
- Next steps

Use `/send-mail` to create the email via Outlook, addressed to all attendees.

### 6. Log to Decision Tracker

If a decision tracker exists at `~/.claude/meetings/decision-tracker/`, append the decisions and action items to it. The plugin does not create that directory; skip this step when it is absent.
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
