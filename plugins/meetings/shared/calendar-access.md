# Calendar Access Patterns

> **Cross-platform note:** AppleScript fallback paths in this file (`tell application "Microsoft Outlook"`, `tell application "Mail"`, etc.) only run on macOS. On Windows or Linux, the agent should rely on `mcp__outlook-bridge__*` tools and skip the AppleScript blocks entirely. Each AppleScript block is prefixed with an explicit OSTYPE guard.

Calendar access for meeting intelligence. The outlook-bridge MCP wrapper around `outlook-cli` is the primary method (Microsoft Graph, structured JSON). Outlook AppleScript is a last-resort emergency fallback.

> **IMPORTANT**: macOS Calendar is NOT reliable — it is out of sync with M365. NEVER use macOS Calendar AppleScript.

## PRIMARY: outlook-cli via outlook-bridge MCP

Use `mcp__outlook-bridge__outlook_list_calendar` for structured queries (today, date range, attendees-per-event). The wrapper authenticates via `outlook-cli`'s cached session — call `mcp__outlook-bridge__outlook_auth_check` first if you suspect the token has expired.

### Today's events

```
Tool: mcp__outlook-bridge__outlook_list_calendar
Args: { "from": "now", "to": "end of day" }
```

### Date range

```
Tool: mcp__outlook-bridge__outlook_list_calendar
Args: { "from": "2026-04-22T00:00:00Z", "to": "2026-04-29T00:00:00Z" }
```

`from`/`to` accept ISO-8601 timestamps or relative expressions like `"now"`, `"now + 7d"`, `"end of day"`.

### Single event details (with full attendees + body)

```
Tool: mcp__outlook-bridge__outlook_get_event
Args: { "id": "AAMkAGI..." }
```

**Advantages of outlook-bridge MCP:**

- M365 source of truth via Microsoft Graph (no local sync drift)
- Structured JSON responses (subject, start/end, attendees with response status, body, location)
- No AppleScript fragility on long-running events or recurring series
- Works regardless of whether Outlook.app is running

If a call returns `{error: "auth_required"}`, run `outlook-cli login` via Bash with user approval and retry.

## EMERGENCY FALLBACK: Microsoft Outlook AppleScript (macOS only)

Use Outlook AppleScript ONLY if the outlook-bridge MCP is unavailable.

### Reading Today's Calendar Events

**macOS only — skip on Windows/Linux:**

```bash
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo "Skipping AppleScript fallback — not on macOS." >&2
  exit 0
fi
osascript <<'APPLESCRIPT'
tell application "Microsoft Outlook"
    set today to current date
    set time of today to 0
    set tomorrow to today + (1 * days)
    set output to ""

    set todayEvents to (every calendar event whose start time >= today and start time < tomorrow)
    repeat with e in todayEvents
        set output to output & "===" & linefeed
        set output to output & "SUMMARY: " & subject of e & linefeed
        set output to output & "START: " & (start time of e as string) & linefeed
        set output to output & "END: " & (end time of e as string) & linefeed
        try
            set output to output & "LOCATION: " & location of e & linefeed
        on error
            set output to output & "LOCATION: (none)" & linefeed
        end try
        try
            set output to output & "NOTES: " & plain text content of e & linefeed
        on error
            set output to output & "NOTES: (none)" & linefeed
        end try
        try
            set attendeeList to ""
            repeat with a in attendees of e
                set attendeeList to attendeeList & name of a & " <" & address of a & ">, "
            end repeat
            set output to output & "ATTENDEES: " & attendeeList & linefeed
        on error
            set output to output & "ATTENDEES: (none)" & linefeed
        end try
    end repeat
    return output
end tell
APPLESCRIPT
```

### Outlook Property Reference

| Property | Outlook |
|----------|---------|
| Event title | `subject of e` |
| Start time | `start time of e` |
| End time | `end time of e` |
| Body text | `plain text content of e` |
| Attendee name | `name of a` |
| Attendee email | `address of a` |

### Outlook Recurring Events

Outlook handles recurring events differently. The `every calendar event` query may return the series master rather than individual occurrences. To get occurrences for a date range, the `whose start time >= X and start time < Y` filter should work for most cases, but complex recurrence patterns may require checking `is recurring of e`.

## Choosing the Right Method

| Scenario | Method |
|----------|--------|
| Default — structured "what's on my calendar" / range / event detail | outlook-bridge MCP (`outlook_list_calendar`, `outlook_get_event`) |
| outlook-bridge unavailable | Outlook AppleScript |
| User passes `--outlook` flag | Outlook AppleScript |

**Default strategy**: Use outlook-bridge MCP as the primary calendar source. It's M365-backed via Microsoft Graph and returns structured JSON. Fall back to Outlook AppleScript only if the MCP is unavailable.
