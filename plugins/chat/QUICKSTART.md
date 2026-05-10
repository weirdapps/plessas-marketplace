# chat — Quickstart

A 5-minute path from zero to "my Teams chats are summarised and my replies are drafted."

## What it does

Bridges Microsoft Teams to Claude Code. Reads your chats and channels via Microsoft Graph and the chatsvc API, drafts replies that match the tone of the existing thread (Greek or English, auto-detected), summarises long threads to the decisions and action items that matter, and produces executive digests of busy project channels. Send paths are draft-first by design — every message that lands in someone's Teams is your finger on Send.

## Prerequisites

- Claude Code installed
- A Microsoft 365 / Teams account at NBG (or any tenant)
- The marketplace setup script has been run (`installers/install.sh`) — this puts `teams-cli` on your PATH

## Install

Inside Claude Code:

```
/plugin install chat@plessas-marketplace
```

That's it. No further configuration files to edit.

## Authenticate

One time, run the auth wizard from your terminal:

```bash
~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh
```

A Playwright-controlled browser window opens for Microsoft 365 sign-in. Approve the requested permissions. The wizard captures your Teams session token and stores it locally.

To verify auth at any time: `teams-cli auth-check`.

## Your first command

```
/chat-inbox
```

Output (typical):

```
═══════════════════════════════════════════════
TEAMS INBOX — 2026-05-10, 09:14
═══════════════════════════════════════════════

NEEDS RESPONSE (3)
───────────────────────────────────────────────
1. Cards Sector Director (1:1) — 2 unread
   "Need your sign-off on Q1 cards revenue slide before
    the 11:00 ExCo prep — see attached deck"
   ACTION: Reply with sign-off or redlines (deadline: 11:00)

2. Cards Leadership (group, 6 people) — 4 unread
   Discussion on the new fee-restructure rollout; Fraud
   Director raised a vector concern that needs a call.
   ACTION: Decide if call needed or async resolution OK

3. Digital Director (1:1) — 1 unread
   CSAT drop on new release — escalation path question
   ACTION: Delegate to Customer Insights or take ownership

FYI (4)
───────────────────────────────────────────────
4. Direct Reports (group) — 2 unread (loyalty programme kudos thread)
5. Subsidiary leadership (group) — 1 unread (board pack reminder)
6. Embedded Banking project (channel) — 7 unread across 2 threads
7. Peer AGM (1:1) — 1 unread (Business Banking sync request)

LOW PRIORITY (3)
───────────────────────────────────────────────
8. Teams notifications, Yammer cross-posts, Viva Insights
═══════════════════════════════════════════════
```

To draft a reply, run `/chat-reply <chat_id>` with the chat_id from the briefing.

## Top 3 commands

| Command | What it does | When to use |
|---|---|---|
| `/chat-inbox` | Recent chats summary, grouped by urgency, with action recommendations | Morning Teams triage; quick check between meetings |
| `/chat-reply <chat_id>` | Draft a reply to a specific chat in matching language and tone | Responding to a 1:1 or group message |
| `/chat-summarize <chat_id>` | Condense a long thread to decisions, action items, and key points | Catching up on a thread you missed |

Bonus commands: `/chat-channel-digest <channel>` (executive summary of a project channel), `/chat-doctor` (diagnose teams-bridge if something breaks).

## Common patterns

**Morning Teams triage** (5 min):

```
/chat-inbox
# … scan the urgency groups, pick what needs a reply now …
/chat-reply <chat_id_of_urgent_one>
# … review draft, send …
```

**Catch up on a project channel** (e.g. Embedded Banking after a few days away):

```
/chat-channel-digest <channel>
# Returns: executive summary across recent threads —
# decisions made, open questions, who's blocked
```

**Reply with auto-language detection**:

```
/chat-reply <chat_id>
# Greek thread → Greek reply (matches recipient register)
# English thread → English reply
# Mixed thread → defaults to dominant language of last 5 messages
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `auth_required` error | Re-run the auth wizard, or `teams-cli login` |
| Cold-start delay (30-60s) on first command after install | Normal — the MCP server runs `npm install` + `npm run build` the first time. Subsequent calls are instant |
| "Channel sends not supported" | Microsoft Graph send scope is missing for channels in the underlying API. Send works for chats (1:1, group); channel **reads** work fine |
| `teams-cli` not on PATH | Some corporate-locked laptops disallow `npm link` to global. The MCP `run.sh` falls back to invoking the locally cloned binary at `installers/deps/teams-access/dist/cli.js`. No action needed |

If anything else looks off, run `/chat-doctor` — it surfaces the exact problem (missing CLI, expired session, network issue) and tells you the one command to fix it.

## Where things live

- **Auth / session token**: `~/.teams-cli/` (not inside the marketplace dir)
- **MCP server**: bundled at `plugins/chat/mcp-server/`, built on first run
- **`teams-cli` binary**: linked via `npm link` after marketplace setup; fallback path `installers/deps/teams-access/dist/cli.js`

## Want more?

- Architecture and how the bridge works: see [README.md](README.md)
- All commands: type `/` in Claude Code, scroll to the `chat:` group
