# Email Handler

Email command center — inbox briefings, action recommendations, style-matched draft replies, Outlook sending, and self-learning.

## What It Does

1. **Learns** from previous drafts vs your actual responses (automatic, every run)
2. **Briefs** you on your inbox — gists, insights, new vs previously seen
3. **Recommends** actions — reply, delegate, forward, monitor, skip, urgent, follow-up
4. **Drafts** replies matching your communication style per recipient
5. **Sends** via the `outlook-bridge` MCP server (Microsoft Graph v2.0, draft-first by default)
6. **Tracks** inbox state across runs to highlight what's changed

## Commands

| Command | Description |
|---------|-------------|
| `/inbox-briefing` | Quick inbox scan — summaries, action flags, insights (read-only, no drafting) |
| `/mail-review` | Full inbox briefing + action flags + draft replies |
| `/triage-inbox` | Triage unread mail: rule-match, LLM-classify, batch-move with a safety contract and undo |
| `/draft-review` | Deep learning pass — compare drafts to actual responses |
| `/reply` | Reply (or reply-all) to an email with auto-quote + signature, draft-first |
| `/forward` | Forward an email to new recipient(s), draft-first by default |
| `/send-mail` | Send an email via Outlook (HTML, attachments, auto-CC self) |
| `/archive-thread` | Move a conversation thread to `Inbox/Archive-<current-year>`, creating the folder if needed |
| `/folder-tree` | Display the Outlook folder hierarchy with message counts as a Unicode tree |
| `/decisions` | Surface recent decisions, track delegations, and check decision consistency |
| `/style-rollback` | Restore a previous version of the style guide from backups |
| `/style-stats` | Accuracy trends, top corrections, and recipient profile accuracy |
| `/style-sync` | Periodic deep sync — update style guide from new sent emails since last sync |
| `/mail-doctor` | Diagnose `outlook-bridge` MCP: Node binary, CLI install mode, auth status, last startup |
| `/auth-setup` | One-time M365 OAuth bootstrap + signature capture |

`/comm-report` and `/style-rebuild` are **not** in this plugin. They moved to the optional
`mail-pro` plugin in the separate [`plessas-lab`](https://github.com/weirdapps/plessas-lab)
marketplace, because they require the private `weirdapps/plessas-second-brain` knowledge store.

## How It Works

### Inbox Briefing

Every run separates emails into **NEW** (since last run) and **PREVIOUSLY SEEN**, with:

- 1-2 sentence gist of each email
- Recommended action (reply, delegate, forward, monitor, skip, urgent, follow-up)
- Insights: who's waiting, cross-thread patterns, urgency flags, delegation opportunities

### Self-Learning Loop

```
/mail-review → drafts saved to ~/.claude/drafts/pending/
    ↓
You edit and send → CC'd copies land in your inbox
    ↓
Next /mail-review → auto-compares drafts vs actual responses
    ↓
Style guide updated → next drafts are more accurate
```

No manual `/draft-review` needed — learning runs automatically at the start of every `/mail-review`. Use `/draft-review` only for deep analysis or focused recipient review.

### Persistent State

| File | Purpose |
|------|---------|
| `~/.claude/drafts/pending/` | Saved drafts awaiting comparison |
| `~/.claude/drafts/reviewed/` | Processed drafts with actual vs draft diffs |
| `~/.claude/drafts/inbox-state.json` | Last-seen emails for new vs seen tracking |
| `~/.claude/drafts/learnings.md` | Historical log of accuracy improvements |
| `shared/style-guide.md` | Communication style guide (updated by learning) |

## Setup

Requires:

- The bundled `outlook-bridge` MCP server built (`installers/install.sh` does this; otherwise `run.sh` builds it on the first MCP call)
- `outlook-cli` authenticated: run `/auth-setup`, or `outlook-cli login` directly; see https://github.com/weirdapps/outlook-access
- Optional: `second-brain` MCP server, which enriches drafts and briefings with historical sender context. Without it every command here still works, just with less context

Works on macOS, Linux, WSL2, and Windows wherever `outlook-cli` runs. There is no AppleScript dependency.

## Backend

All read AND send paths go through the `outlook-bridge` MCP plugin, which wraps `outlook-cli` (Microsoft Graph v2.0 + a Playwright-captured Outlook web session). There is no fallback toggle: if the bridge or `outlook-cli` is down, fix it (`outlook-cli auth-check`, `outlook-cli login`) rather than route around it.

The legacy AppleScript send path is preserved in git history but no longer wired into any command.

## Style Guide

Built by analyzing thousands of actual emails from your sent folder. The style guide lives at `shared/style-guide.md` (gitignored — yours stays local). A sanitized template is at `shared/style-guide-example.md` to show the structure.

The shipped reference style guide (NBG context) is characterized by:

- **Ultra-brief**: 60%+ of replies are 1-10 words
- **No greetings/closings**: Straight to the point (BRIEF format)
- **Lowercase**: Almost always starts lowercase in Greek
- **Recipient-aware**: Different tone for boss vs direct reports vs PA
- **Greek internal**: Greek for NBG colleagues, English for internationals
- **Self-improving**: Automatically updated based on draft-vs-actual comparisons

**To generate your own style guide**, in order of least to most setup:

1. Just use `/mail-review`. The first run creates `shared/style-guide.md` from the template, and the self-learning loop refines it per recipient on every subsequent run. No extra dependency.
2. `/style-sync` for a batch update from sent mail. With no prior sync state it processes your whole history. It prefers the `second-brain` knowledge store and falls back to your Archive mailbox via `outlook-bridge` (Sent Items is deliberately never read).
3. `/style-rebuild`, a full statistical rebuild, is **not in this plugin**. It lives in the optional `mail-pro` plugin in the [`plessas-lab`](https://github.com/weirdapps/plessas-lab) marketplace and requires the private `second-brain` knowledge store.
