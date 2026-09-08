# plessas-marketplace

Production Claude Code plugin marketplace for workplace productivity at NBG. Six plugins, each
self-contained under `plugins/<name>/`. GitHub: `weirdapps/plessas-marketplace`. Replaces the
archived `communications-marketplace` (2026-05-30).

## Plugin Inventory

| Plugin | Commands | Purpose |
|--------|----------|---------|
| `decks` | `/create-presentation`, `/create-keynote`, `/redesign-deck`, `/polish-slides`, `/presentation-review` | Multi-agent PPTX pipeline: storyline-architect → storyboard-designer → graphics-renderer → presentation-qa. NBG-branded; brand assets in `shared/brand-system/`. `/create-keynote` is the one dark full-bleed exception (Standard #21) — a separate Pillow compositor in `tools/nbg-keynote/`, for stage talks only. |
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
```

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

Three workflows run tests and checks, and all of them can go red.

- **`tests.yml`** is the authoritative gate. `pytest plugins -q` on Python 3.12, and
  `npm ci` + `npm run typecheck` + `npm test` for both bundled MCP servers on Node 20.
  Unconditional: no repo-visibility gate, no token gate, no `continue-on-error`. It also
  asserts each server's `tests/` directory is non-empty, so a suite cannot pass by being
  deleted.
- **`lint.yml`** runs the whole `.pre-commit-config.yaml` hook set (ruff, ruff-format,
  mypy, gitleaks, yamllint, markdownlint, hygiene) plus `claude plugin validate --strict`
  on all six plugins and the marketplace root. `plugin validate` needs no credentials and
  no network.
- **`validate-plugins.yml`** runs `scripts/validate_consistency.py`, which is where the
  repo-specific invariants live.

`sonarcloud.yml` still runs pytest, but only to produce `coverage.xml`. It is not the gate.

Run locally before pushing:

```bash
uv run --no-project --with pyyaml python scripts/validate_consistency.py --verbose
bash installers/pii-gauntlet.sh --mode=doctor
pytest plugins -q
(cd plugins/mail/mcp-server && npm run typecheck && npm test)
(cd plugins/chat/mcp-server && npm run typecheck && npm test)
```

`validate_consistency.py` needs `pyyaml`, which a stock `python3` does not have; the
`uv run` form above is the reliable invocation. `scripts/skill-trigger-probe.sh` measures
natural-language routing across the six router skills, spawns real `claude` calls, and is
**not** wired into CI. Its case 2 is nondeterministic (four runs on identical input gave
three fails and one pass), so treat 16/17 as the score and do not read a single run as a
regression or an improvement.

## Facts about Claude Code this repo has been burned by

Each of these was verified against the live runtime in Claude Code 2.1.265, not inferred
from documentation. They are the failure modes most likely to recur.

- **A plugin-bundled MCP server's tools are namespaced `mcp__plugin_<plugin>_<server>__<tool>`.**
  So the tool is `mcp__plugin_mail_outlook-bridge__outlook_list_mail`, never
  `mcp__outlook-bridge__outlook_list_mail`. The bare form does not exist and matches nothing:
  in `allowed-tools` it pre-approves nothing, and in a hook matcher or permission rule it
  never fires. A server the USER configures stays bare, which is why `mcp__second-brain__*`
  is correct as written. `validate_consistency.py` now enforces this.
- **`allowed-tools` pre-approves; it does not restrict.** Every tool stays callable whatever
  the field says. The consequence is not cosmetic: an unlisted tool prompts interactively and
  is **auto-denied in headless, `-p` and scheduled runs**. `disallowed-tools` is the field
  that actually removes a tool.
- **The `agents` key in `plugin.json` loads nothing.** A valid file list passes
  `claude plugin validate --strict` and registers zero agents; an invalid value silently
  voids the manifest's other component paths and falls back to full auto-discovery.
  `agents/*.md` at the plugin root is the only mechanism that works, so an agent that must
  load lives there and nowhere else. `commands`, by contrast, accepts an array of
  directories and works, but REPLACES the default scan, so `./commands` must be listed
  explicitly alongside any addition.
- **`plugin.json` `version` is the update cache key.** Claude Code executes from
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. A version that never changes
  means installed users never receive a fix, however many commits land. Bump it in both
  `plugin.json` and the `marketplace.json` entry on every release; the two disagreeing is a
  trap, because `plugin.json` silently wins.
- **`claude plugin validate` passing is not evidence a plugin works.** It checks manifest
  shape. It does not check that tool names resolve, that referenced agents exist, or that an
  MCP server starts.
- **`marketplace.json` accepts a top-level `version`, but NOT top-level `license`,
  `homepage` or `repository`.** Those are per-plugin-entry fields; at the root they are
  unknown fields, which `--strict` treats as errors.

## The defect this repo keeps producing

A declared constraint is documentation until something reads it. Five instances were found
in one audit: `allowed-tools` naming tools that did not exist under that namespace; a
"Safety contract (enforced by code)" where four of five clauses were prose; a `since`
parameter advertised in an MCP inputSchema and discarded by the handler; a `maxItems: 20`
batch cap no validator consulted; and three validator checks that iterated `a:rPr` when
every deck the builder produces carries `a:defRPr`, so they passed having examined nothing.

The general rule, and the one worth applying to any new check: **a check must distinguish
"found nothing" from "did not look".** A validator that reports success without measuring is
worse than no validator, because a human stops looking. `nbg_validate.py` now tracks how
many candidates each check examined, and `presentation-qa.md` instructs the agent to treat a
zero-candidate pass as unverified.

## Key Dependencies

- `mail` and `chat` bundle their own MCP servers (Node.js 20+, TypeScript). `mcp-server/dist/` is
  gitignored, NOT committed: `installers/install.sh` builds it, and `run.sh` rebuilds on first MCP
  call if `dist/server.js` is missing. Never commit `dist/`.
- `meetings` requires `mail`, declared machine-readably as `"dependencies": ["mail"]` in its
  `plugin.json`, so Claude Code installs `mail` with it. Note there are no OPTIONAL plugin
  dependencies: a declared dependency that is missing or disabled disables the dependent plugin,
  so only genuinely hard dependencies belong in that field. Soft integrations (`second-brain`,
  `document-skills`) are probed at runtime in the skill body instead.
- Optional enrichment: `second-brain` MCP (richer attendee dossiers), `document-skills` plugin
  (better xlsx/docx output).
- Python tooling: ruff + mypy via `pyproject.toml` (no package install — tooling-only config).
- Python 3.12+ is required by the `decks` Python tools. `numpy>=2.5.2`, the floor in both
  `tools/nbg-keynote/requirements.txt` and `bundled/creative/tools/device-mockup/requirements.txt`,
  declares `requires-python >=3.12`, so `pip install -r` fails to resolve on 3.11. `ruff`
  `target-version` and `mypy` `python_version` are pinned to `py312`/`3.12` to match.

## Brand Notes

`decks` ships NBG branding. To adapt for another brand: swap `plugins/decks/shared/brand-system/`
assets and do a project-wide rename of "NBG". No .pptx template is bundled. The multi-agent
pipeline itself is brand-agnostic.
