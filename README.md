# plessas-marketplace

Six Claude Code plugins for productivity at a financial-services workplace: presentations, mail, meetings, chat, spreadsheets, and documents.

[![Validate Plugins](https://github.com/weirdapps/plessas-marketplace/actions/workflows/validate-plugins.yml/badge.svg)](https://github.com/weirdapps/plessas-marketplace/actions/workflows/validate-plugins.yml)
[![PII Check](https://github.com/weirdapps/plessas-marketplace/actions/workflows/pii-check.yml/badge.svg)](https://github.com/weirdapps/plessas-marketplace/actions/workflows/pii-check.yml)
[![CodeQL](https://github.com/weirdapps/plessas-marketplace/actions/workflows/codeql.yml/badge.svg)](https://github.com/weirdapps/plessas-marketplace/actions/workflows/codeql.yml)
[![SonarCloud Analysis](https://github.com/weirdapps/plessas-marketplace/actions/workflows/sonarcloud.yml/badge.svg)](https://github.com/weirdapps/plessas-marketplace/actions/workflows/sonarcloud.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=weirdapps_plessas-marketplace&metric=alert_status)](https://sonarcloud.io/project/overview?id=weirdapps_plessas-marketplace)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What this is

A Claude Code plugin marketplace built around the desk work of an executive at National Bank of Greece (NBG): drafting mail, walking into meetings prepared, keeping up with Teams chats, shipping board-ready presentations, and reading spreadsheets and Word documents. Each plugin is self-contained, ships with the commands and agents it needs, and bundles its own MCP server when it needs to reach an external system.

Everything except the `decks` brand assets is domain-neutral. If you work at a different firm, install the plugins you need, point them at your M365 tenant, and (for `decks`) swap the template and colour palette.

Owner: [weirdapps](https://weirdapps.github.io/resume/). License: MIT.

> **v2.2.0**. Replaces [`communications-marketplace`](https://github.com/weirdapps/communications-marketplace), archived 2026-05-30. Migration notes: [`docs/migration-from-communications-marketplace.md`](docs/migration-from-communications-marketplace.md).

## The six plugins

| Plugin | What it does | Key commands |
|--------|--------------|--------------|
| [`decks`](plugins/decks/) | Multi-agent presentation pipeline (storyline, storyboard, graphics, QA) that ships board-ready PPTX. Bundles a creative toolkit for icons, infographics, and device mockups. NBG-branded by default; brand assets are all in one directory. | `/create-presentation`, `/create-keynote`, `/redesign-deck`, `/polish-slides`, `/presentation-review`, plus `/create-icon`, `/create-infographic`, `/create-mockup` from the bundled creative toolkit |
| [`mail`](plugins/mail/) | Outlook command centre. Bundles the `outlook-bridge` MCP server, which shells out to the [`outlook-tool`](https://github.com/weirdapps/outlook-access) CLI (pinned via `git+https`) for M365 read and send. | `/inbox-briefing`, `/mail-review`, `/triage-inbox`, `/reply`, `/forward`, `/send-mail`, `/archive-thread`, `/decisions`, `/draft-review`, `/folder-tree`, `/mail-doctor`, `/style-sync`, `/style-stats`, `/style-rollback`, `/auth-setup` |
| [`meetings`](plugins/meetings/) | Pre-meeting briefings with attendee dossiers built from email history; post-meeting decision and action-item capture. Reads the calendar through `mail`'s bundled MCP, so `mail` must be installed first. | `/meeting-prep`, `/meeting-debrief` |
| [`chat`](plugins/chat/) | Microsoft Teams reader and reply. Bundles the `teams-bridge` MCP server, which shells out to the [`teams-cli`](https://github.com/weirdapps/teams-access) CLI (pinned via `git+https`). | `/chat-inbox`, `/chat-reply`, `/chat-summarize`, `/chat-channel-digest`, `/chat-doctor`, `/auth-setup` |
| [`excel`](plugins/excel/) | Spreadsheet analysis with narrative summaries, pivot views, variance commentary, and a one-shot handoff to `decks`. Uses `document-skills:xlsx` when installed, otherwise falls back to `openpyxl` / `pandas`. | `/excel-summary`, `/excel-pivot`, `/excel-variance`, `/excel-to-deck` |
| [`docs`](plugins/docs/) | Word document creation for reports, formal letters, and internal memos. Uses `document-skills:docx` when installed, otherwise falls back to `python-docx`. | `/docs-create`, `/docs-letter`, `/docs-memo` |

Manifest of record: [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json).

## Install

### Prerequisites

- **Claude Code** ([claude.ai/claude-code](https://claude.ai/claude-code))
- **Node.js 20+** ([nodejs.org](https://nodejs.org/))
- **Python 3.12+** ([python.org](https://www.python.org/downloads/)). Required by `decks`: its `numpy >= 2.5.2` floor is itself `requires-python >=3.12`, so `pip install -r` cannot resolve on 3.11.
- **Git 2.30+**
- **Chrome or Edge** for first-time browser session capture used by `outlook-tool` and `teams-cli`

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.sh | bash
```

### Windows (PowerShell)

```powershell
iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.ps1 | iex
```

The installer clones the marketplace into `~/.claude/plugins/marketplaces/plessas-marketplace/`. It does not install any Claude Code plugin on its own; that step happens next, inside Claude Code.

### Wire the marketplace into Claude Code

Run this once, inside Claude Code:

```text
/plugin marketplace add weirdapps/plessas-marketplace
```

Then install the plugins you want:

```text
/plugin install decks@plessas-marketplace
/plugin install mail@plessas-marketplace
/plugin install meetings@plessas-marketplace
/plugin install chat@plessas-marketplace
/plugin install excel@plessas-marketplace
/plugin install docs@plessas-marketplace
```

### Updating

```text
/plugin update plessas-marketplace
```

Updates are delivered by the plugin `version`, which is the cache key Claude Code uses. Auto-update is
off by default for third-party marketplaces, so `/plugin update` is the step that actually fetches a
release.

After an update, re-run `installers/install.sh` (or `install.ps1`) so the bundled MCP servers and their
CLIs rebuild against the pinned commits. A version bump creates a fresh plugin cache directory, so the
first MCP call after a release rebuilds `node_modules` unless you do.

## Configuration

Only `mail` and `chat` need authentication; the other four plugins work out of the box.

### `/mail:auth-setup`

Bootstraps the `outlook-bridge` MCP: probes it, drives Microsoft 365 OAuth via the bundled `outlook-tool` CLI, and captures your email signature for outgoing drafts.

- First run asks for your SharePoint host (e.g. `contoso.sharepoint.com`). The answer is persisted to `~/.outlook-cli/config.json` (chmod 600). Override with the `PLESSAS_SHAREPOINT_HOST` env var.
- Idempotent. Re-run any time; the doctor skips completed steps.
- Flags: `--force-reauth`, `--skip-signature`.

### `/chat:auth-setup`

Bootstraps the `teams-bridge` MCP the same way. Drives `teams-cli login`, which opens a Playwright browser window. Teams reuses the Outlook web session, so no SharePoint host is required.

- Flag: `--force-reauth`.

### Legacy path (deprecated)

`installers/auth-wizard.sh` / `auth-wizard.ps1` cover the same auth flow outside Claude Code. They still work but the slash commands are the recommended path.

## Architecture

```text
.claude-plugin/marketplace.json      # top-level manifest: name, version, plugins[]
plugins/
  decks/
    commands/                        # 5 deck commands + 3 creative commands (both paths are
                                     # declared in plugin.json, because `commands` REPLACES the default scan)
    agents/                          # 8 agents. `agents/` is the ONLY directory Claude Code
                                     # auto-discovers, so every agent lives here: storyline-architect,
                                     # storyboard-designer, graphics-renderer, presentation-qa,
                                     # nbg-presenter (orchestrator), icon-designer,
                                     # infographic-specialist, device-mockup
    skills/presentations/            # natural-language router
    bundled/creative/                # commands, tools and assets for the creative toolkit
    tools/nbg-presentation/          # nbg_build.py, nbg_validate.py, chart/table injectors
    shared/brand-system/             # colours, fonts, layouts, style guide
    assets/                          # NBG template, logos, illustrations, icons, mockups
  mail/
    commands/                        # 15 slash commands (see table)
    agents/                          # email-handler, triage-engine
    skills/outlook-mail/             # natural-language router
    mcp-server/                      # outlook-bridge MCP (TypeScript, Node 20+)
      src/tools/                     # 16 MCP tools (see below)
      tests/                         # vitest suite (4 files)
      dist/                          # built JS, gitignored (produced by run.sh / install.sh)
      run.sh                         # entrypoint invoked by Claude Code
  meetings/
    commands/                        # /meeting-prep, /meeting-debrief
    agents/                          # meeting-intelligence
    skills/meeting-workflows/        # natural-language router
                                     # plugin.json declares `"dependencies": ["mail"]`
                                     # no MCP server: reads calendar through mail's bundled outlook-bridge
  chat/
    commands/                        # 6 slash commands (see table)
    skills/teams-chat/               # natural-language router
    mcp-server/                      # teams-bridge MCP (TypeScript, Node 20+)
      src/tools/                     # 11 MCP tools (see below)
      tests/                           # vitest suite
      dist/                          # built JS, gitignored (produced by run.sh / install.sh)
      run.sh
  excel/  commands/ skills/          # 4 commands + 1 router skill; no MCP, no agents
  docs/   commands/ skills/          # 3 commands + 1 router skill; no MCP, no agents
installers/
  install.sh, install.ps1            # clone-and-wire (posix / powershell)
  auth-wizard.sh, auth-wizard.ps1    # legacy auth path (deprecated)
  status.sh, status.ps1              # install-state report
  pii-gauntlet.sh                    # PII scan (CI + local doctor modes)
  lib/tenant-prompt.{sh,ps1}         # SharePoint host prompt used by auth-wizard
scripts/
  validate_consistency.py            # manifest / command consistency checks
  sync_brand_system.sh               # keeps decks brand assets in sync
shared/                              # cross-plugin templates (email-style, brand-system)
.github/workflows/                   # tests, lint, validate-plugins, pii-check, rename-guard,
                                     # sonarcloud, codeql, dependabot-auto-merge
```

### Natural-language triggering

Every plugin ships one skill, so you do not have to know a command name. Ask
for what you want, in Greek or English, and the request routes to the right
workflow: "what needs my attention today", «τι έγινε στα Teams όσο έλειπα»,
"I need something for the board on Thursday".

Commands still work and are still the precise way to invoke a specific
workflow. The skills are an additional entry point, not a replacement.

Domains, boundaries, and how overlaps resolve: [`docs/skill-triggers.md`](docs/skill-triggers.md).

### Bundled MCP servers

Two of the plugins ship their own MCP server as a TypeScript project under `plugins/<name>/mcp-server/`. Both wrap external CLIs that are pulled in as npm dependencies (`git+https`, pinned to specific commit SHAs so the lockfile stays reproducible).

**`outlook-bridge`** (from `plugins/mail/mcp-server/`) exposes 16 tools:

`outlook_auth_check`, `outlook_capture_signature`, `outlook_create_folder`, `outlook_doctor`, `outlook_download_attachments`, `outlook_find_folder`, `outlook_forward`, `outlook_get_event`, `outlook_get_mail`, `outlook_list_calendar`, `outlook_list_folders`, `outlook_list_mail`, `outlook_move_mail`, `outlook_reply`, `outlook_reply_all`, `outlook_send_mail`.

Backed by [`outlook-tool`](https://github.com/weirdapps/outlook-access), pinned to commit `c278600ccc54253c83fa8e353b5009081e05e1a0`.

**`teams-bridge`** (from `plugins/chat/mcp-server/`) exposes 11 tools:

`teams_auth_check`, `teams_auth_renew`, `teams_doctor`, `teams_health_check`, `teams_list_channels`, `teams_list_chats`, `teams_list_messages`, `teams_list_teams`, `teams_login`, `teams_resolve_mri`, `teams_send_message`.

Backed by [`teams-cli`](https://github.com/weirdapps/teams-access), pinned to commit `eb2beadea83000a16b01b09a6574e972c1d57405`.

Neither server commits its `dist/` output (`dist/` is gitignored). `installers/install.sh` builds both up front; if you skip the installer, `run.sh` runs `npm ci` and `npm run build` on the first MCP call, which adds 30-60 seconds once.

### Optional enhancements

All six plugins work standalone. These optional pieces add richer context when present:

| Component | Enhances | What it adds | Without it |
|-----------|----------|--------------|------------|
| `second-brain` MCP | `mail`, `meetings` | Historical sender context, attendee dossiers with prior decisions and open actions | Briefings still work via `outlook-bridge`; dossiers say "no historical context" |
| `document-skills` plugin | `excel`, `docs` | Higher-fidelity xlsx / docx generation | Falls back to `openpyxl` / `pandas` and `python-docx` (auto-installed on first use) |
| `/mail:style-sync` | `mail` | Personalised drafts that match your voice per recipient | Drafts use professional defaults (brief for internal, full for external) |

## Brand notes

- **`decks`** ships NBG branding out of the box: `plugins/decks/assets/` (logos, templates, colour palette), `plugins/decks/shared/brand-system/`, and agent prompts referencing NBG colour hex codes and font stacks. The pipeline itself (storyline, storyboard, renderer, QA) is brand-agnostic. No PowerPoint template is bundled: the builder draws every slide from scratch, so there is nothing to swap. To retarget, update `plugins/decks/shared/brand-system/` and do a project-wide rename of `NBG` to your brand.
- **`mail`**, **`meetings`**, **`chat`**, **`excel`**, and **`docs`** are fully brand-agnostic. They ship with sensible defaults you can override in your global `CLAUDE.md`.

## Development and testing

### Local validation

```bash
# Consistency across manifests, commands, agents and MCP tool names.
# Needs pyyaml, which a stock python3 does not have:
uv run --no-project --with pyyaml python scripts/validate_consistency.py --verbose

# Scan for personal data (file contents AND tracked filenames):
bash installers/pii-gauntlet.sh --mode=doctor

# Manifests, exactly as CI checks them:
claude plugin validate . --strict
for p in plugins/*/; do claude plugin validate "$p" --strict; done

# Python tools:
pytest plugins -q

# Bundled MCP servers:
(cd plugins/mail/mcp-server && npm ci && npm run typecheck && npm test)
(cd plugins/chat/mcp-server && npm ci && npm run typecheck && npm test)
```

Every one of those runs in CI. `tests.yml` is the authoritative gate for the test
suites; `sonarcloud.yml` also runs pytest, but only to produce `coverage.xml` for the scan.

### CI (`.github/workflows/`)

| Workflow | Trigger | Enforces |
|----------|---------|----------|
| `tests.yml` | push / PR to master | `pytest plugins` on Python 3.12, and `npm ci` + `npm run typecheck` + `npm test` for both bundled MCP servers on Node 20. Unconditional: no visibility gate, no token gate, no `continue-on-error`. Also asserts each server's `tests/` directory is non-empty, so a suite can never pass by being absent |
| `lint.yml` | push / PR to master | The full `.pre-commit-config.yaml` hook set (ruff, ruff-format, mypy, gitleaks, yamllint, markdownlint, hygiene), plus `claude plugin validate --strict` on all six plugins and the marketplace root |
| `validate-plugins.yml` | push / PR to master | `marketplace.json` is valid JSON, every plugin has `plugin.json` and a README, every command file at any depth has YAML frontmatter, `scripts/validate_consistency.py` passes |
| `pii-check.yml` | push / PR | No personal data in git-tracked file contents or filenames (runs `installers/pii-gauntlet.sh --mode=ci`) |
| `rename-guard.yml` | push / PR | No stale slash-command names, every command at any depth declares `allowed-tools`, no deprecated tool aliases, no references to the pre-rename shared brand-system path |
| `sonarcloud.yml` | push / PR | Static analysis and quality gate, and the coverage run that feeds it (public projects only) |
| `codeql.yml` | push / PR / weekly Mon 06:00 UTC | Security scanning for Python and TypeScript / JavaScript |
| `dependabot-auto-merge.yml` | Dependabot PRs | Auto-merges patch and minor updates (grouped or ungrouped); majors always require manual review. A thin caller: the logic lives in the shared reusable workflow `weirdapps/shared-workflows/.github/workflows/dependabot-auto-merge.yml@main` |

### Releasing

Plugin versions are the cache key Claude Code uses to decide whether an installed copy is
stale. A plugin pinned to a version that never changes is **never updated**, however many
commits land behind it. So every release bumps `version` in both
`plugins/<name>/.claude-plugin/plugin.json` and that plugin's entry in
`.claude-plugin/marketplace.json`; `validate_consistency.py` fails the build when the two
disagree, and `claude plugin tag` creates the matching `<name>--v<version>` git tag.

Auto-update is off by default for third-party marketplaces, so users pick up a release with
`/plugin update` rather than automatically.

### Adding a new plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with `name`, `description`, `version`, and `commands: "./commands"`.
2. Add command files under `plugins/<name>/commands/<cmd>.md`. Each file needs YAML frontmatter with at minimum `description` and `allowed-tools`.
3. Add `plugins/<name>/README.md`.
4. Register the plugin in `.claude-plugin/marketplace.json` under `plugins[]`.
5. Avoid bundling a new MCP server unless unavoidable: prefer skills or Claude Code tools. Bundled MCP servers are an escape hatch, not the default (see `CONTRIBUTING.md`).

## Documentation

- [Day-one walkthrough](docs/day-one.md)
- [Per-plugin workflow guides](docs/workflows/)
- [FAQ](docs/FAQ.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Migration from `communications-marketplace`](docs/migration-from-communications-marketplace.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

MIT. See [LICENSE](LICENSE).

## Support

Bug reports and questions: [github.com/weirdapps/plessas-marketplace/issues](https://github.com/weirdapps/plessas-marketplace/issues).

Security issues: report privately via the [Security tab](https://github.com/weirdapps/plessas-marketplace/security/advisories); see [SECURITY.md](SECURITY.md).
