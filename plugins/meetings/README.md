# Meeting Prep Plugin

Meeting intelligence for `plessas-marketplace`. Reads your calendar, builds per-attendee dossiers from knowledge store context (via MCP), and captures post-meeting decisions.

> **Requires the `mail` plugin.** This plugin uses the `outlook-bridge` MCP server bundled inside `mail` to read your calendar. Install `mail` first (or alongside): `/plugin install mail@plessas-marketplace`.

## Commands

| Command | Description |
|---------|-------------|
| `/meeting-prep` | Pre-meeting briefing with attendee dossiers for today's meetings |
| `/meeting-debrief` | Post-meeting capture of decisions, action items, and follow-ups |

## How It Works

### Meeting Prep (`/meeting-prep`)

1. Reads today's calendar events via outlook-bridge MCP (primary, M365-synced via `outlook-cli`), with WorkIQ MCP as fallback for natural-language queries
2. Extracts attendees from each meeting
3. Queries the knowledge store via MCP tools for each attendee:
   - Recent email exchanges and sentiment
   - Open action items owned by/assigned to them
   - Recent decisions involving them
4. Cross-references with inbox for emails related to meeting topics
5. Produces a per-meeting briefing with attendee dossiers and suggested talking points

### Meeting Debrief (`/meeting-debrief`)

1. Identifies which meeting to debrief (from calendar or user input)
2. Captures decisions made, action items assigned, and follow-ups needed
3. Saves structured debrief to `~/.claude/meetings/debriefs/`
4. Optionally distributes summary to attendees via `/send-mail`

## Integration

- **knowledge store MCP server**: Attendee dossiers, historical context, decision/action tracking
- **mail plugin**: Cross-references inbox emails related to meeting topics; distributes debrief summaries via `/send-mail`

## Data Storage

```
~/.claude/meetings/
  debriefs/           # Post-meeting debriefs (JSON)
```

## Calendar Support

- **outlook-bridge MCP** (`mcp__outlook-bridge__outlook_list_calendar` / `outlook_get_event`) — primary. Cross-platform via `outlook-cli`, structured JSON.
- **WorkIQ MCP** (`mcp__workiq__ask_work_iq`) — fallback for natural-language queries that don't map cleanly to structured arguments. Optional.
- **Outlook AppleScript** — emergency last-resort fallback on macOS only. Documented in `shared/calendar-access.md` but not invoked by default.
- macOS Calendar is NEVER used (out of sync with M365)
- See `shared/calendar-access.md` for the full access pattern
