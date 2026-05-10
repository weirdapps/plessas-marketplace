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

## Install (≈ 10 minutes)

Four steps. Do them in order.

### 1. Add the marketplace to Claude Code

Inside Claude Code:

```
/plugin marketplace add weirdapps/plessas-marketplace
```

This clones the marketplace into `~/.claude/plugins/marketplaces/plessas-marketplace`.

### 2. Run the one-time setup script

Open your terminal:

**macOS / Linux:**

```bash
bash ~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.sh
```

**Windows (PowerShell, no admin needed):**

```powershell
& ~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.ps1
```

This installs `outlook-cli` and `teams-cli`, builds the bundled MCP servers (Outlook + Teams bridges), and creates Python virtual environments for the `decks` plugin. Idempotent — safe to re-run.

### 3. Install the plugins you want

Inside Claude Code:

```
/plugin install mail@plessas-marketplace
/plugin install meetings@plessas-marketplace
/plugin install chat@plessas-marketplace
/plugin install decks@plessas-marketplace
/plugin install excel@plessas-marketplace
/plugin install docs@plessas-marketplace
```

Skip any you don't need. `mail-pro` is optional — only install if you have access to the private `weirdapps/second-brain` repo.

### 4. Authenticate Outlook + Teams

```bash
~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh
```

(Windows: `auth-wizard.ps1`)

The wizard opens your browser twice — once for Microsoft 365 / Outlook sign-in, once for Teams. It also captures your Outlook signature for use in `/send-mail`.

**You're done.** Try `/inbox-briefing` to verify everything works.

## Prerequisites

- [Claude Code](https://claude.com/claude-code) installed
- Node.js 20+
- Git
- Python 3.11+ (for `decks` plugin's PowerPoint tooling)

The installer in step 2 checks these and provides download links if any are missing.

## Updating

Inside Claude Code:

```
/plugin update plessas-marketplace
```

Re-run `installers/install.sh` after major updates so the bundled MCPs and CLIs refresh too.

## Advanced — One-line installer (CI / unattended deploys)

For scripted installs (CI, IT-managed laptops), the setup script can be triggered directly without going through Claude Code's marketplace UI:

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.sh | bash
```

**Windows (PowerShell):**

```powershell
iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.ps1 | iex
```

You'll still need to run `/plugin install <name>` inside Claude Code afterwards.

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
