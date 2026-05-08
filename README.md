# plessas-marketplace

Cross-platform Claude Code plugins for productivity at a financial-services workplace.

> **Status:** v1.0.0 in active development. Public release imminent.

## What's inside

| Plugin | What it does |
|---|---|
| `decks` | Branded presentations: storyline → storyboard → graphics → QA. Bundles icons, infographics, device mockups. |
| `mail` | Outlook commands: triage, briefings, drafts, style-matching. Bundles outlook-cli MCP wrapper. |
| `meetings` | Pre-meeting briefings with attendee dossiers; post-meeting decision capture. |
| `chat` | Microsoft Teams interactive commands: inbox, reply, summarize, channel digest. Bundles teams-bridge MCP. |
| `excel` | Excel analysis: summary, pivot, variance, deck handoff. Wraps document-skills:xlsx. |
| `docs` | Word document creation: generic, formal letter, internal memo. Wraps document-skills:docx. |

## Install (5 minutes)

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/main/installers/install.sh | bash
```

### Windows (PowerShell, no admin needed)

```powershell
iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/main/installers/install.ps1 | iex
```

After install, run the auth wizard:
- macOS/Linux: `~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh`
- Windows: `~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.ps1`

## Prerequisites

- [Claude Code](https://claude.com/claude-code) installed
- Node.js 20+
- Git
- Python 3.11+ (for `decks` plugin's PowerPoint tooling)

The installer will check these and provide download links if any are missing.

## Documentation

- [Day-one walkthrough](docs/day-one.md)
- [Workflow guides](docs/workflows/) — one per plugin
- [Migration from `communications-marketplace`](docs/migration-from-communications-marketplace.md)

## Brand specifics

This marketplace ships with NBG (National Bank of Greece) brand defaults baked in (Aptos 12pt, color `#404040`, NBG layouts in `decks`). NBG is a public listed bank — these are public brand assets. Future versions may parameterize brand specs for non-NBG users.

## License

MIT — see [LICENSE](LICENSE).

## Support

Issues: [github.com/weirdapps/plessas-marketplace/issues](https://github.com/weirdapps/plessas-marketplace/issues)
