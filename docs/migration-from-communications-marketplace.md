# Migrating from communications-marketplace

If you previously installed `communications-marketplace`, here's how to switch to `plessas-marketplace`.

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

### macOS / Linux

```bash
# 1. Remove old marketplace
claude plugin marketplace remove communications-marketplace

# 2. Install new marketplace
curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/main/installers/install.sh | bash

# 3. Run auth wizard (re-uses existing auth if still valid)
~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh

# 4. Check everything works
~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh
```

### Windows (PowerShell)

```powershell
# 1. Remove old marketplace
claude plugin marketplace remove communications-marketplace

# 2. Install new marketplace
iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/main/installers/install.ps1 | iex

# 3. Run auth wizard
~\.claude\plugins\marketplaces\plessas-marketplace\installers\auth-wizard.ps1

# 4. Check everything works
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

## Background scripts

The daily style-guide sync (invoked from `~/SourceCode/second-brain/scripts/launchd/wrappers/sb-daily-sync.sh` after the second-brain ingest) was ported from `communications-marketplace/scripts/style-sync.py` to `plessas-marketplace/plugins/mail-pro/scripts/style-sync.py` (moved out of `mail` into `mail-pro` on 2026-05-09 along with the other second-brain-dependent commands). The script writes to `plugins/mail/shared/style-guide.md` (gitignored — the user's real personal style guide). The launchd wrapper has been updated; no user action needed unless you wired up your own automation against the old path.
