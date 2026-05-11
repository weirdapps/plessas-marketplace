# plessas-marketplace

Cross-platform Claude Code plugins for productivity at a financial-services workplace.

> **Status:** v1.0.0 in active development. Public release imminent.

## What's inside

| Plugin | What it does |
|---|---|
| `decks` | Branded presentations: storyline → storyboard → graphics → QA. Bundles icons, infographics, device mockups. |
| `mail` | Outlook commands: triage, briefings, drafts, style-matching. Bundles outlook-cli MCP wrapper. |
| `mail-pro` | Optional companion to `mail`. Adds `/comm-report` and `/style-rebuild`. Requires private `second-brain` repo access. |
| `meetings` | Pre-meeting briefings with attendee dossiers; post-meeting decision capture. |
| `chat` | Microsoft Teams interactive commands: inbox, reply, summarize, channel digest. Bundles teams-bridge MCP. |
| `excel` | Excel analysis: summary, pivot, variance, deck handoff. Wraps document-skills:xlsx. |
| `docs` | Word document creation: generic, formal letter, internal memo. Wraps document-skills:docx. |

## Install

### Prerequisites (both OSes)

- **Claude Code** — install from <https://claude.ai/claude-code>
- **Node.js 20+** — install from <https://nodejs.org/>
- **Python 3.11+** — install from <https://www.python.org/downloads/>
- **Git** — `git --version` should report v2.30+
- **Chrome or Edge browser** — required for `outlook-cli` and `teams-cli` first-time auth (Playwright drives the browser session capture)

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.sh | bash
~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh
~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh
```

### Windows (PowerShell)

```powershell
iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.ps1 | iex
& "$env:USERPROFILE\.claude\plugins\marketplaces\plessas-marketplace\installers\auth-wizard.ps1"
& "$env:USERPROFILE\.claude\plugins\marketplaces\plessas-marketplace\installers\status.ps1"
```

> **First-run prompt:** the auth wizard will ask for your Microsoft 365 SharePoint host (e.g. `contoso.sharepoint.com`). The answer is saved to `~/.outlook-cli/config.json` and reused. Override with `PLESSAS_SHAREPOINT_HOST=...` env var if needed.

## Updating

Inside Claude Code:

```
/plugin update plessas-marketplace
```

Re-run `installers/install.sh` (or `.ps1` on Windows) after major updates so the bundled MCPs and CLIs refresh too.

## Documentation

- [Day-one walkthrough](docs/day-one.md)
- [Workflow guides](docs/workflows/) — one per plugin
- [Migration from `communications-marketplace`](docs/migration-from-communications-marketplace.md)

## Per-plugin notes

- **`decks`** is NBG-branded. The brand-system docs (`plugins/decks/shared/brand-system/{colors,layouts,typography,charts}.md`), the storyline-architect agent persona, and the `NBG-Template-GR.pptx` template all assume NBG corporate identity. If you're not at NBG, the framework is still useful (storyline → storyboard → renderer → QA), but you'll want to swap the template, replace the color palette in `colors.md`, and edit the agent prompts to reference your brand. Most of the customization is a single search-and-replace of "NBG" with your brand name.
- **`mail`, `meetings`, `chat`, `excel`, `docs`** are brand-agnostic.

## License

MIT — see [LICENSE](LICENSE).

## Support

Issues: [github.com/weirdapps/plessas-marketplace/issues](https://github.com/weirdapps/plessas-marketplace/issues)
