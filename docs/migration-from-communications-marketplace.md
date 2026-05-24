# Migrating from communications-marketplace

If you previously installed `communications-marketplace`, here's how to switch to `plessas-marketplace`.

## Who should read this

You only need this guide if you previously installed [`weirdapps/communications-marketplace`](https://github.com/weirdapps/communications-marketplace) on your laptop. **Most NBG team members onboarding to plessas-marketplace are new users** — they should follow the [top-level README install steps](../README.md#install--10-minutes) instead.

`communications-marketplace` is being **archived on 2026-05-30** (compressed from original 2026-06-08). After that date the GitHub repo will be read-only — existing installs keep working but receive no further updates.

## What changed

| Old plugin | New plugin | What's different |
|---|---|---|
| presentation-maker | **decks** | creative-toolkit bundled inside (no separate install) |
| email-handler | **mail** | outlook-bridge MCP bundled inside |
| meeting-prep | **meetings** | Name change only |
| outlook-bridge | (bundled in **mail**) | No longer a standalone plugin |
| creative-toolkit | (bundled in **decks**) | No longer a standalone plugin |
| teams-monitor | Moved to plessas-lab as **chat-watch** | Not part of plessas-marketplace |
| — | **chat** (NEW) | Interactive Teams commands |
| — | **excel** (NEW) | Excel analysis |
| — | **docs** (NEW) | Word document creation |
| — | **mail-pro** (NEW) | Optional companion to `mail` for users with the private `second-brain` knowledge store. Hosts `/comm-report` and `/style-rebuild`. |

## Migration steps

### Option A — Claude Code marketplace flow (recommended)

This mirrors the path new users follow.

Inside Claude Code:

```
# 1. Remove old marketplace
/plugin marketplace remove communications-marketplace

# 2. Add the new marketplace
/plugin marketplace add weirdapps/plessas-marketplace
```

Then in your terminal:

```bash
# 3. Run the setup script (idempotent; respects existing outlook-cli / teams-cli installs)
bash ~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.sh

# 4. Re-run the auth wizard (re-uses existing auth if still valid)
~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh

# 5. Verify everything works
~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh
```

Back inside Claude Code:

```
# 6. Install the plugins you want
/plugin install mail@plessas-marketplace
/plugin install meetings@plessas-marketplace
/plugin install chat@plessas-marketplace
/plugin install decks@plessas-marketplace
/plugin install excel@plessas-marketplace
/plugin install docs@plessas-marketplace

# Optional — only if you have private weirdapps/second-brain access
/plugin install mail-pro@plessas-marketplace
```

### Option B — One-line installer (for unattended migration)

**macOS / Linux:**

```bash
# 1. Remove old marketplace (inside Claude Code)
/plugin marketplace remove communications-marketplace

# 2. Run the one-liner
curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.sh | bash

# 3. Auth wizard
~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh

# 4. Status check
~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh

# 5. Inside Claude Code, install the plugins you want
# (same as Option A step 6)
```

**Windows (PowerShell):**

```powershell
# 1. Remove old marketplace (inside Claude Code)
/plugin marketplace remove communications-marketplace

# 2. Run the one-liner
iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.ps1 | iex

# 3. Auth wizard
~\.claude\plugins\marketplaces\plessas-marketplace\installers\auth-wizard.ps1

# 4. Status check
~\.claude\plugins\marketplaces\plessas-marketplace\installers\status.ps1
```

## What carries over automatically

- **Auth state**: `~/.outlook-cli/` and `~/.teams-cli/` are untouched — no need to re-authenticate if your tokens are still valid
- **Signature**: `~/.outlook-cli/signature.html` carries over
- **CLAUDE.md**: your existing `~/.claude/CLAUDE.md` is preserved (we don't overwrite)

## What you may need to redo

- **Personal email style guide**: if you customised `email-handler/shared/style-guide.md`, that's specific to the old plugin. After installing the new marketplace, run `/style-rebuild` to regenerate from your sent mail corpus.
- **Recipient profiles**: the `recipient-profiles.db` was user-generated. It rebuilds organically from your `/reply` usage. No action needed unless you want to accelerate it.
- **Triage rules**: if you customised triage rules in the old email-handler, copy them to `plugins/mail/shared/triage-rules-starter.yaml` in the new marketplace.

## Command mapping

| Old command | New command |
|---|---|
| `/create-presentation` | `/create-presentation` (unchanged) |
| `/redesign-deck` | `/redesign-deck` (unchanged) |
| `/polish-slides` | `/polish-slides` (unchanged) |
| `/inbox-briefing` | `/inbox-briefing` (unchanged) |
| `/mail-review` | `/mail-review` (unchanged) |
| `/send-mail` | `/send-mail` (unchanged) |
| `/meeting-prep` | `/meeting-prep` (unchanged) |
| `/meeting-debrief` | `/meeting-debrief` (unchanged) |
| — | `/chat-inbox` (NEW) |
| — | `/chat-reply` (NEW) |
| — | `/chat-summarize` (NEW) |
| — | `/chat-channel-digest` (NEW) |
| — | `/excel-summary` (NEW) |
| — | `/excel-pivot` (NEW) |
| — | `/excel-variance` (NEW) |
| — | `/excel-to-deck` (NEW) |
| — | `/docs-create` (NEW) |
| — | `/docs-letter` (NEW) |
| — | `/docs-memo` (NEW) |
| `/comm-report` | `/comm-report` (moved to **mail-pro** plugin — requires private second-brain repo access) |
| `/style-rebuild` | `/style-rebuild` (moved to **mail-pro** plugin — same reason) |

All existing commands keep the same names. The two corpus-driven commands moved to a new `mail-pro` plugin so users without the private `second-brain` knowledge store still get a fully functional `mail` plugin.

## teams-monitor — note carefully

`communications-marketplace` shipped a Python `teams-monitor` plugin (a launchd background daemon that watched Teams chats and posted briefings to email). That plugin is **gone** from `plessas-marketplace`.

Two replacements, both with different shapes:

| Old (background daemon) | New (interactive) | Where |
|---|---|---|
| `teams-monitor` (launchd Python) — passive watcher posting briefings to email | `chat` plugin — interactive commands you invoke from Claude Code (`/chat-inbox`, `/chat-reply`, etc.) | This marketplace (`plessas-marketplace`) |
| `teams-monitor` (launchd Python) — passive watcher | `chat-watch` skill in `plessas-lab` (still launchd-driven if you want continuous monitoring) | Separate marketplace ([`weirdapps/plessas-lab`](https://github.com/weirdapps/plessas-lab)) — install that marketplace too if you want the daemon back |

If you had the old `teams-monitor` launchd job running, the marketplace removal does NOT auto-disable it. Find it manually:

```bash
launchctl list | grep -i teams
launchctl unload ~/Library/LaunchAgents/com.weirdapps.teams-monitor.plist
rm ~/Library/LaunchAgents/com.weirdapps.teams-monitor.plist
```

(Substitute the actual plist filename if different.)

## Verification — did the migration work?

1. Inside Claude Code, type `/` and confirm you see commands prefixed with `mail:`, `meetings:`, `chat:`, `decks:`, `excel:`, `docs:` (and `mail-pro:` if you installed it)
2. Run `~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh` — green checkmarks across the board
3. Try `/inbox-briefing` — should produce a briefing within ~5 seconds of M365 latency
4. Try `/meeting-prep` — if you've installed both `mail` and `meetings`, this should walk today's calendar
5. (If applicable) Try `/chat-inbox` — should return your last 10-20 Teams chats

If any of the above fails, run the relevant doctor command first (`/mail-doctor`, `/chat-doctor`) — each surfaces the exact problem and the one-line fix.

## Background scripts

The daily style-guide sync (invoked from `~/SourceCode/second-brain/scripts/launchd/wrappers/sb-daily-sync.sh` after the second-brain ingest) was ported from `communications-marketplace/scripts/style-sync.py` to `plessas-marketplace/plugins/mail-pro/scripts/style-sync.py` (moved out of `mail` into `mail-pro` on 2026-05-09 along with the other second-brain-dependent commands). The script writes to `plugins/mail/shared/style-guide.md` (gitignored — the user's real personal style guide). The launchd wrapper has been updated; no user action needed unless you wired up your own automation against the old path.

## Need help?

File an issue at [github.com/weirdapps/plessas-marketplace/issues](https://github.com/weirdapps/plessas-marketplace/issues) or message the marketplace maintainer directly.
