# plessas-marketplace

Production Claude Code plugin marketplace for workplace productivity at NBG. Six plugins, each
self-contained under `plugins/<name>/`. GitHub: `weirdapps/plessas-marketplace`. Replaces the
archived `communications-marketplace` (2026-05-30).

## Plugin Inventory

| Plugin | Commands | Purpose |
|--------|----------|---------|
| `decks` | `/create-presentation`, `/redesign-deck`, `/polish-slides`, `/presentation-review` | Multi-agent PPTX pipeline: storyline-architect → storyboard-designer → graphics-renderer → presentation-qa. NBG-branded; brand assets in `shared/brand-system/`. |
| `mail` | `/inbox-briefing`, `/mail-review`, `/send-mail`, `/triage-inbox`, `/reply`, `/draft-review`, `/archive-thread`, `/decisions`, `/forward`, `/folder-tree`, `/mail-doctor`, `/style-rollback`, `/style-stats`, `/style-sync`, `/auth-setup` | Outlook command center. Bundles `outlook-bridge` MCP (Node.js server in `mcp-server/`). Two agents: `email-handler` and `triage-engine`. |
| `meetings` | `/meeting-prep`, `/meeting-debrief` | Calendar-aware briefings with attendee dossiers; post-meeting decision and action capture. Depends on `mail` plugin's bundled MCP for calendar access. Agent: `meeting-intelligence`. |
| `chat` | `/chat-inbox`, `/chat-reply`, `/chat-summarize`, `/chat-channel-digest`, `/chat-doctor`, `/auth-setup` | Microsoft Teams reader and reply. Bundles `teams-bridge` MCP (Node.js server in `mcp-server/`). |
| `excel` | `/excel-summary`, `/excel-pivot`, `/excel-variance`, `/excel-to-deck` | Excel analysis with narrative summaries; hands off to `decks` for deck output. Uses `document-skills:xlsx` when installed, falls back to openpyxl/pandas. |
| `docs` | `/docs-create`, `/docs-letter`, `/docs-memo` | Word document creation. Uses `document-skills:docx` when installed, falls back to python-docx. Shared style templates in `shared/`. |

## Repo Structure

```text
plugins/<name>/
  .claude-plugin/plugin.json   # Manifest: name, description, version, commands path
  commands/*.md                # Each command: YAML frontmatter + prompt body
  agents/*.md                  # Agent definitions (decks, mail, meetings)
  shared/                      # Brand assets, style guides loaded by commands
  mcp-server/                  # Bundled Node.js MCP server (mail, chat only)
installers/                    # install.sh / install.ps1 + pii-gauntlet.sh
scripts/                       # sync_brand_system.sh, validate_consistency.py
shared/                        # Cross-plugin shared assets (brand-system, email-style-template)
.claude-plugin/marketplace.json  # Top-level manifest listing all plugins

```text

## Adding a New Plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with required fields: `name`, `description`,
   `version`, `commands` (`"./commands"`).
2. Add command files under `plugins/<name>/commands/<cmd>.md`. Each file needs YAML frontmatter
   (`---`) with at minimum `description` and `allowed-tools`.
3. Add a `plugins/<name>/README.md`.
4. Register in `.claude-plugin/marketplace.json` under `"plugins"`.
5. Avoid bundling a new MCP server unless unavoidable — prefer the `Skill(...)` pattern (see
   CONTRIBUTING.md: "Adding more bundled MCP servers" is explicitly out of scope).

## Testing

No automated Python test suite in this repo. Validation is CI-only:

- `scripts/validate_consistency.py --verbose` — consistency checks across manifests and commands.
- CI runs `ruff` and `mypy` for any Python code (config in `pyproject.toml`).
- PII scan: `bash installers/pii-gauntlet.sh --mode=ci` before any PR.

Run locally before pushing:

```bash
bash installers/pii-gauntlet.sh --mode=doctor
python3 scripts/validate_consistency.py --verbose

```

## CI

Five GitHub Actions workflows (`.github/workflows/`):

| Workflow | Trigger | What it checks |
|----------|---------|----------------|
| `validate-plugins.yml` | push/PR to master | `marketplace.json` JSON validity, all `plugin.json` files have required fields, all READMEs present, all command files have frontmatter, consistency script |
| `pii-check.yml` | push/PR | Personal data leakage scan |
| `rename-guard.yml` | push/PR | Stale command names, missing `allowed-tools`, deprecated tool names |
| `sonarcloud.yml` | push/PR | Static analysis / quality gate |
| `codeql.yml` | push/PR | Security scanning |

## Key Dependencies

- `mail` and `chat` bundle their own MCP servers (Node.js 20+, TypeScript); built artifacts are
  committed under `mcp-server/dist/`.
- `meetings` requires `mail` to be installed (shares its `outlook-bridge` MCP for calendar).
- Optional enrichment: `second-brain` MCP (richer attendee dossiers), `document-skills` plugin
  (better xlsx/docx output), `WorkIQ` MCP (NL calendar queries).
- Python tooling: ruff + mypy via `pyproject.toml` (no package install — tooling-only config).

## Brand Notes

`decks` ships NBG branding. To adapt for another brand: swap `plugins/decks/shared/brand-system/`
assets, replace `NBG-Template-GR.pptx`, and do a project-wide rename of "NBG". The multi-agent
pipeline itself is brand-agnostic.
