# meetings — Quickstart

A 5-minute path from zero to "I walk into every meeting prepared and walk out with decisions captured."

## What it does

Reads today's calendar via Microsoft Graph, builds a per-attendee dossier from your knowledge store (last contact, open action items, recent decisions, sentiment) when the optional `second-brain` MCP is available, and cross-references your inbox for emails related to the meeting topics. The output is a structured per-meeting briefing with suggested talking points. After the meeting, captures decisions, action items, and follow-ups into a structured debrief — and optionally distributes a summary to attendees.

## Prerequisites

- Claude Code installed
- The **`mail` plugin** must be installed first — `meetings` uses its bundled `outlook-bridge` MCP server for calendar access. There is no separate calendar MCP.
- A Microsoft 365 / Outlook account at NBG (or any tenant)
- Optional: the `second-brain` MCP server (via the `mail-pro` plugin in the [`plessas-lab`](https://github.com/weirdapps/plessas-lab) marketplace) for richer attendee dossiers built from your email corpus. Without it, briefings still work — they fall back to calendar metadata + live inbox cross-reference.

## Install

Inside Claude Code, install both — `mail` first, then `meetings`:

```
/plugin install mail@plessas-marketplace
/plugin install meetings@plessas-marketplace
```

## Authenticate

No additional auth. The plugin re-uses the `outlook-cli` session set up by the `mail` plugin. If you've already run the `mail` auth wizard, you're done. If not, see `mail`'s [QUICKSTART.md](../mail/QUICKSTART.md#authenticate).

To verify at any time: `outlook-cli auth-check`.

## Your first command

```
/meeting-prep
```

Output (typical):

```
═══════════════════════════════════════════════
MEETING PREP — 2026-05-11 (today, 3 meetings)
═══════════════════════════════════════════════

09:30–10:00  1:1 with Cards Sector Director
───────────────────────────────────────────────
ATTENDEES:
  • Cards Sector Director
DOSSIER:
  - Last email: yesterday, Q1 Cards revenue update (+12% vs plan)
  - Open actions: 2 (CEO brief decision; fee-restructure memo to ExCo)
  - Recent decision: Fee-restructure rollout approved at last ExCo
TALKING POINTS:
  • Confirm Wed slot to brief CEO on Q1 numbers
  • Status of ExCo approval for new pricing
  • Fee mix shift toward credit — sustainability?

11:00–12:00  ExCo monthly review
───────────────────────────────────────────────
ATTENDEES:
  • CEO
  • Deputy CEO
  • + 6 others
RELATED INBOX:
  - CFO Office: Board pack draft for May (deadline 2026-05-13)
TALKING POINTS:
  • Cards Q1 beat (+12%) — flag for May Board pack
  • Digital channel CSAT issue — second escalation this month

15:00–15:30  ATM hardware partner sync
───────────────────────────────────────────────
ATTENDEES:
  • Vendor account lead
RELATED INBOX:
  - Vendor: ATM platform Q2 roadmap (3 days ago, no reply yet)
TALKING POINTS:
  • Hardware refresh timeline confirmation
  • Digital euro readiness — pilot scope

DAY SUMMARY
───────────────────────────────────────────────
- 1 decision needed today (CEO brief slot)
- 1 stale thread to address before 15:00 (vendor)
═══════════════════════════════════════════════
```

## Top 3 commands

| Command | What it does | When to use |
|---|---|---|
| `/meeting-prep` | Briefing for today's meetings | Morning routine, over coffee |
| `/meeting-prep --date 2026-05-13` | Briefing for a specific date | Day before a Board day or a heavy partner day |
| `/meeting-debrief` | Capture decisions, actions, follow-ups | Right after a meeting ends |

## Common patterns

**Morning routine** (5 min, with coffee):

```
/meeting-prep
# … scan dossiers, decide which talking points to lead with …
```

**Pre-Board prep** (the day before):

```
/meeting-prep --date 2026-05-13
# … review attendee dossiers and related inbox threads in advance …
```

**Post-1:1 capture** (right after the meeting, send summary to attendee):

```
/meeting-debrief --distribute
# … type decisions and actions in free text; Claude structures them and drafts the email …
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Plugin says `outlook-bridge` MCP not available | Install the `mail` plugin: `/plugin install mail@plessas-marketplace` |
| Calendar shows wrong meetings or is empty | Outlook desktop must be syncing M365 (not local-only calendars). Check Outlook → Account settings. Then `outlook-cli auth-check` |
| Attendee dossiers are empty | Optional `second-brain` MCP isn't installed. Briefings still work; install `mail-pro` from the [`plessas-lab`](https://github.com/weirdapps/plessas-lab) marketplace to add dossiers from your email corpus (requires private second-brain repo access) |
| AppleScript fallback not engaging | macOS-only. Pass `--outlook` to force the AppleScript path (emergency last-resort, bypasses MCPs) |

## Where things live

- **Debriefs**: `~/.claude/meetings/debriefs/` (structured JSON, one per meeting)
- **Calendar / auth**: re-uses `outlook-cli`'s `~/.outlook-cli/` setup from the `mail` plugin

## Want more?

- Architecture and calendar-access matrix: see [README.md](README.md)
- Auth setup and `outlook-cli` details: see the `mail` plugin's [QUICKSTART.md](../mail/QUICKSTART.md)
- All commands: type `/` in Claude Code, scroll to the `meetings:` group
