# mail — Quickstart

A 5-minute path from zero to "my Outlook inbox is briefed and my replies are drafted."

## What it does

Reads your Outlook inbox via Microsoft Graph, classifies every email (reply / delegate / forward / monitor / urgent / skip / follow-up), drafts replies that match your personal communication style per recipient, and learns from what you actually send so it gets sharper over time. Sending and reading both go through `outlook-cli`, so there is no AppleScript dependency — works on Mac, Windows, and Linux equally.

It is intentionally NOT an autopilot — every send is your finger on the keyboard.

## Prerequisites

- Claude Code installed
- A Microsoft 365 / Outlook account at NBG (or any tenant — see [Authenticate](#authenticate) for non-NBG tenants)
- Outlook desktop installed (used for activating drafts you choose to send through the GUI)
- The marketplace setup script has been run (`installers/install.sh`) — this puts `outlook-cli` on your PATH

## Install

Inside Claude Code:

```
/plugin install mail@plessas-marketplace
```

That's it. No further configuration files to edit.

## Authenticate

One time, run the auth wizard from your terminal:

```bash
~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh
```

A browser window opens for Microsoft 365 sign-in. Approve the requested permissions (Read / Send mail, calendar, contacts). The wizard captures your Outlook signature too.

> **Tenant host:** the auth wizard will prompt you for your M365 tenant SharePoint host on first run (e.g. `contoso.sharepoint.com`). Find it in any SharePoint URL you own: `https://<this-part>.sharepoint.com/...`. The answer is persisted to `~/.outlook-cli/config.json` and reused on subsequent runs. Override with the `PLESSAS_SHAREPOINT_HOST` env var if needed.

If you need to sign in manually (e.g., to switch tenants), use:

```bash
outlook-cli login --sharepoint-host <your-tenant>.sharepoint.com
outlook-cli capture-signature   # optional, for /send-mail
```

To verify auth at any time: `outlook-cli auth-check`.

## Your first command

```
/inbox-briefing
```

Output (typical):

```
═══════════════════════════════════════════════
INBOX BRIEFING — 2026-05-10, 09:14
═══════════════════════════════════════════════

NEW SINCE LAST RUN (4 emails)
───────────────────────────────────────────────
1. Cards Sector Director — Q1 Cards revenue update
   GIST: Cards Q1 revenue beat plan +12%; flags fee mix shifting toward credit
   ACTION: ↩️ REPLY — needs ack + decision on whether to brief CEO this week

2. Digital Director — Digital channel CSAT
   GIST: New release dropped CSAT 4 points; A/B test results inconclusive
   ACTION: 👉 DELEGATE — Customer Insights team should own this

3. CFO Office — Board pack draft for May
   GIST: Draft board pack ready for review; deadline 2026-05-13
   ACTION: ⚡ URGENT — high stakes, needs your read by Wed

4. LinkedIn — 3 new connection requests
   GIST: Routine notification
   ACTION: ⏭️ SKIP

INSIGHTS
───────────────────────────────────────────────
- 1 email needs your decision today (Cards Sector Director — CEO brief)
- Digital channel CSAT issue is the second escalation this month — pattern
- Board pack deadline is 3 days out — reserve time Wed AM
═══════════════════════════════════════════════
```

If you want briefing + drafts in one go, run `/mail-review` instead.

## Top 3 commands

| Command | What it does | When to use |
|---|---|---|
| `/inbox-briefing` | Read-only inbox scan with action recommendations | Morning triage; quick check between meetings |
| `/mail-review` | Briefing + draft replies for actionable emails | When you have 15 minutes to clear the queue |
| `/send-mail` | Compose + send a new email with HTML formatting and attachments | Outbound communications, follow-ups, distribution emails |

Other commands: `/reply`, `/forward`, `/archive-thread`, `/triage-inbox`, `/mail-doctor`, `/style-stats`, `/style-rollback`, `/decisions`, `/draft-review`, `/style-sync`, `/folder-tree`.

## Common patterns

**Morning triage** (5 min):

```
/inbox-briefing
# … scan the actions, decide what's worth your time …
/mail-review --count 10
# … pick 2-3 drafts to send, dismiss the rest …
```

**Bulk-archive a noisy thread**:

```
/archive-thread "<subject keyword>"
```

**Send a quick reply that matches your style for that recipient**:

```
/reply <message_id>
```

Pulls the thread, drafts the reply, opens Outlook with the draft pre-loaded for your final review and send.

**Send a new email** (e.g. follow-up to direct report after a meeting):

```
/send-mail
# Claude asks: To, Subject, Body. Draft is opened in Outlook desktop.
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `auth_required` error | Run `outlook-cli login --sharepoint-host <your-tenant>.sharepoint.com` |
| Briefing shows 0 emails | Check `outlook-cli auth-check`. If `expired`, re-run `outlook-cli login` |
| Draft doesn't open in Outlook | Ensure Outlook desktop is installed and running |
| `mcp__outlook-bridge__*` tools not available | Run `~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.sh` to (re)build the bundled MCP server |
| `Throttled (429)` errors during big sweeps | The MCP caps concurrency at 2. If you still hit this, wait 60s and retry |
| Draft style feels off for a specific recipient | Run `/mail-review` 3-4 times — the self-learning loop calibrates per recipient automatically. For a manual rebuild, install `mail-pro` from the [`plessas-lab`](https://github.com/weirdapps/plessas-lab) marketplace and run `/style-rebuild` (requires private second-brain repo) |

## Where things live

- **Drafts pending review**: `~/.claude/drafts/pending/` (JSON files)
- **Reviewed drafts** (after the learning loop classifies them): `~/.claude/drafts/reviewed/`
- **Inbox state** (which emails were seen last run): `~/.claude/drafts/inbox-state.json`
- **Style guide** (your personal communication patterns): `plugins/mail/shared/style-guide.md` — gitignored, lives only on your laptop. Generic template at `style-guide-example.md`
- **Outlook auth + signature**: `~/.outlook-cli/` (not inside the marketplace dir)

## Want more?

- Architecture and self-learning loop details: see [README.md](README.md)
- Style guide structure: open `shared/style-guide-example.md`
- Optional `mail-pro` add-on (corpus analytics, requires `second-brain`): available in the [`plessas-lab`](https://github.com/weirdapps/plessas-lab) marketplace
- All commands: type `/` in Claude Code, scroll to the `mail:` group
