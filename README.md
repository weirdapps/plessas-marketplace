# plessas-marketplace

[![Validate Plugins](https://github.com/weirdapps/plessas-marketplace/actions/workflows/validate-plugins.yml/badge.svg)](https://github.com/weirdapps/plessas-marketplace/actions/workflows/validate-plugins.yml)
[![SonarCloud Analysis](https://github.com/weirdapps/plessas-marketplace/actions/workflows/sonarcloud.yml/badge.svg)](https://github.com/weirdapps/plessas-marketplace/actions/workflows/sonarcloud.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=weirdapps_plessas-marketplace&metric=alert_status)](https://sonarcloud.io/project/overview?id=weirdapps_plessas-marketplace)
[![PII Check](https://github.com/weirdapps/plessas-marketplace/actions/workflows/pii-check.yml/badge.svg)](https://github.com/weirdapps/plessas-marketplace/actions/workflows/pii-check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Six Claude Code plugins for productivity at a financial-services workplace. Each plugin is a self-contained unit with commands, agents, and the MCP wiring it depends on — install only what you need.

> **Status:** v1.0.0 — stable. Replaces [`communications-marketplace`](https://github.com/weirdapps/communications-marketplace) (archived 2026-05-30). Migration guide: [docs/migration-from-communications-marketplace.md](docs/migration-from-communications-marketplace.md).

## Plugins

| Plugin | Key commands | What it does |
|--------|-------------|-------------|
| [`decks`](plugins/decks/) | `/create-presentation`, `/redesign-deck`, `/polish-slides`, `/presentation-review` | Multi-agent presentation pipeline: storyline → storyboard → pixel-perfect graphics → QA. NBG-branded out of the box; swap the template and color palette for any brand. |
| [`mail`](plugins/mail/) | `/inbox-briefing`, `/mail-review`, `/send-mail`, `/triage-inbox`, `/reply` | Outlook command center: triage inbox, draft style-matched replies, send HTML email. Bundles the `outlook-bridge` MCP for M365 access. |
| [`meetings`](plugins/meetings/) | `/meeting-prep`, `/meeting-debrief` | Pre-meeting briefings with attendee dossiers from email history; post-meeting decision and action-item capture. |
| [`chat`](plugins/chat/) | `/chat-inbox`, `/chat-reply`, `/chat-summarize`, `/chat-channel-digest` | Microsoft Teams interactive commands: read and reply across chats and channels. Bundles the `teams-bridge` MCP. |
| [`excel`](plugins/excel/) | `/excel-summary`, `/excel-pivot`, `/excel-variance`, `/excel-to-deck` | Excel analysis with narrative summaries, pivot views, variance commentary, and one-click deck handoff. |
| [`docs`](plugins/docs/) | `/docs-create`, `/docs-letter`, `/docs-memo` | Word document creation: generic documents, formal letters, and internal memos with consistent formatting. |

## Install

### Prerequisites

- **Claude Code** — [claude.ai/claude-code](https://claude.ai/claude-code)
- **Node.js 20+** — [nodejs.org](https://nodejs.org/)
- **Python 3.11+** — [python.org](https://www.python.org/downloads/)
- **Git 2.30+** — `git --version` to confirm
- **Chrome or Edge** — required for `outlook-cli` and `teams-cli` first-time browser session capture

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.sh | bash
```

### Windows (PowerShell)

```powershell
iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.ps1 | iex
```

### First-time setup inside Claude Code

```text
/plugin marketplace add weirdapps/plessas-marketplace
```

Then install and authenticate each plugin you want:

```text
/plugin install mail@plessas-marketplace
/mail:auth-setup

/plugin install chat@plessas-marketplace
/chat:auth-setup
```

`decks`, `meetings`, `excel`, and `docs` need no auth — just `/plugin install <name>@plessas-marketplace`.

> **Auth prompts:** `/mail:auth-setup` asks for your Microsoft 365 SharePoint host (e.g. `contoso.sharepoint.com`). The answer is saved to `~/.outlook-cli/config.json` and reused on subsequent runs. Override with `PLESSAS_SHAREPOINT_HOST=…` if needed. `/chat:auth-setup` captures a Teams session from your Outlook web login — no host input required.
>
> **Legacy path (deprecated):** `installers/auth-wizard.{sh,ps1}` covers the same auth flow outside Claude Code. It still works but will be removed in a future release — prefer the slash commands.

## Updating

```text
/plugin update plessas-marketplace
```

After major updates, re-run `installers/install.sh` (or `.ps1`) so the bundled MCPs and CLIs refresh.

## Optional enhancements

All six plugins work out of the box after install. These optional components add richer context when configured:

| Component | Enhances | What it adds | Without it |
|-----------|----------|--------------|------------|
| `second-brain` MCP | `mail`, `meetings` | Historical sender context, attendee dossiers with decisions and action items, topic intelligence | Briefings and meeting prep still work via `outlook-bridge`; dossiers show "No historical context" |
| `WorkIQ` MCP | `meetings` | Natural-language calendar queries (e.g. "do I have conflicts?") | `outlook-bridge` handles all calendar reads; only free-form NL queries are lost |
| Style guide (`/mail:style-sync`) | `mail` | Personalized drafts that match your email voice per recipient | Drafts use professional defaults (BRIEF internal, FULL external) |

## Notes

- **`decks`** ships with NBG corporate branding (template, color palette, agent prompts). The pipeline itself — storyline → storyboard → renderer → QA — is brand-agnostic. To adapt: swap `NBG-Template-GR.pptx`, update `plugins/decks/shared/brand-system/colors.md`, and do a project-wide rename of "NBG" to your brand.
- **`mail`, `meetings`, `chat`, `excel`, `docs`** are fully brand-agnostic.
- **`excel`** and **`docs`** use the `document-skills` plugin (`document-skills:xlsx` / `document-skills:docx`) when installed. Without it they fall back to `openpyxl`/`pandas` and `python-docx` (auto-installed on first use). For best results: `/plugin install document-skills`.

## Documentation

- [Day-one walkthrough](docs/day-one.md)
- [Per-plugin workflow guides](docs/workflows/)
- [Migration from `communications-marketplace`](docs/migration-from-communications-marketplace.md)

## License

MIT — see [LICENSE](LICENSE).

## Support

[github.com/weirdapps/plessas-marketplace/issues](https://github.com/weirdapps/plessas-marketplace/issues)
