---
description: "Pre-meeting briefing with attendee dossiers from calendar and knowledge store context (via MCP)"
argument-hint: "[--date YYYY-MM-DD] [--outlook] [--no-inbox]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Read today's calendar, cross-reference with the knowledge store (via MCP) and inbox, and produce a per-meeting briefing with attendee dossiers and suggested talking points.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

### 0. Verify Outlook MCP Available (FAIL-FAST)

This plugin reads the calendar via `mcp__outlook-bridge__*` tools, which are bundled in the **mail** plugin. Before doing anything else, check the bridge is reachable:

```
Tool: mcp__outlook-bridge__outlook_auth_check
```

If the tool is **not available** (no `mcp__outlook-bridge__*` tools listed in your environment), stop and tell the user:

> The `meetings` plugin requires the `mail` plugin to be installed (it bundles the `outlook-bridge` MCP server). Install it with:
> `/plugin install mail@plessas-marketplace`
> Then run `/mail:auth-setup` and try `/meeting-prep` again.

Do not attempt the AppleScript fallback unless the user explicitly passes `--outlook`. If the tool exists but returns `auth_required`, surface the `outlook-cli login --sharepoint-host <your-tenant>.sharepoint.com` flow.

### 1. Parse Arguments

- `--date YYYY-MM-DD`: Prep for a specific date (default: today)
- `--outlook`: Use Outlook AppleScript instead of the MCP path (emergency fallback only)
- `--no-inbox`: Skip inbox cross-referencing (faster)

### 2. Read Calendar

Read events using outlook-bridge MCP as the primary source (Microsoft Graph via `outlook-cli`):

```
Tool: mcp__outlook-bridge__outlook_list_calendar
Args: { "from": "now", "to": "end of day" }   # or explicit ISO range when --date is set
```

For full attendee/body detail on a specific event:

```
Tool: mcp__outlook-bridge__outlook_get_event
Args: { "id": "<event Id>" }
```

Fall back to Outlook AppleScript only if the outlook-bridge MCP is unavailable or `--outlook` is passed.
Extract: summary, start/end time, location, attendees, notes.
See `shared/calendar-access.md` for the full access-pattern matrix.

### 3. Build Attendee Dossiers

For each unique attendee, query the knowledge store via MCP:

```
Use `mcp__second-brain__person_context` with `name_or_email="<attendee_name>"`
```

### 4. Cross-Reference Inbox and Archive

Search Inbox and Archive for emails related to meeting topics or from meeting attendees via the outlook-bridge MCP:

```
Tool: mcp__outlook-bridge__outlook_list_mail
Args: { "folder": "Inbox", "top": 50, "select": "Id,Subject,From,ToRecipients,CcRecipients,ReceivedDateTime,ConversationId" }

Tool: mcp__outlook-bridge__outlook_list_mail
Args: { "folder": "Archive", "top": 50, "select": "Id,Subject,From,ToRecipients,CcRecipients,ReceivedDateTime,ConversationId" }
```

Filter client-side by attendee email and topic keywords. Archive is the canonical source for the user's own sent mail (user CCs himself on everything, Sent Items is regularly emptied). For body content on relevant matches, follow up with `mcp__outlook-bridge__outlook_get_mail`.

### 5. Generate Briefing

Produce a structured briefing per meeting:

- Attendee dossiers (last contact, open items, recent decisions, sentiment)
- Related inbox emails
- Suggested talking points based on open items and context
- Summary with conflict warnings and cross-meeting patterns

### 6. Present

Display the full briefing in the conversation.
</process>

<specifications>
## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--date` | No | today | Date to prep for (YYYY-MM-DD) |
| `--outlook` | No | false | Force Outlook AppleScript path (macOS only; emergency fallback — bypasses the outlook-bridge MCP) |
| `--no-inbox` | No | false | Skip inbox cross-referencing |

## Output

- Per-meeting briefing with attendee dossiers
- Related inbox emails
- Suggested talking points
- Day summary with conflict warnings
</specifications>

<examples>
## Usage Examples

### Today's meetings (default)

```
/meeting-prep
```

### Prep for tomorrow

```
/meeting-prep --date 2026-03-22
```

### Use Outlook calendar

```
/meeting-prep --outlook
```

### Quick prep without inbox scan

```
/meeting-prep --no-inbox
```

</examples>

<related_commands>

## Related Commands

| Command | When to Use |
|---------|-------------|
| `/meeting-debrief` | After a meeting to capture decisions and action items |
| `/mail-review` | For full inbox briefing beyond meeting-related emails |
| `/send-mail` | To send follow-up emails after meetings |
</related_commands>
