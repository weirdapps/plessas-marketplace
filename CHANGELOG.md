# Changelog

All notable changes to `plessas-marketplace` are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed (team-rollout readiness pass — 2026-05-10)
- **`installers/pii-gauntlet.sh`**: 9-digit-ID regex was matching SHA fragments inside nested `package-lock.json` files (e.g. `plugins/mail/mcp-server/package-lock.json`), turning the GitHub Actions PII Check workflow red on `master`. Tightened the file exclusion to match common lockfiles (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`) at any depth. `./installers/pii-gauntlet.sh --mode=ci` now passes.
- **All `raw.githubusercontent.com/.../main/...` URLs → `master/...`**: the curl one-liner installer was 404'ing because the default branch is `master`, not `main`. Updated 6 locations: `README.md` (×2), `installers/install.sh`, `installers/install.ps1`, `docs/migration-from-communications-marketplace.md` (×2).
- **`plugins/decks/commands/create-presentation.md`**: gated the `manage-nano-banana` skill (which lives in the separate `plessas-lab` marketplace, not bundled here). The command now silently degrades to SVG-based `Infographic Specialist` + `Icon Designer` if `Skill(manage-nano-banana)` is unavailable, instead of failing.
- **`plugins/mail/commands/mail-review.md`**: gated section 6b ("Gather Context from Second-Brain") behind `mcp__second_brain__*` availability. Users without the optional `mail-pro` plugin (and its private `second-brain` dependency) no longer hit "skill not found" errors mid-flow.
- **`plugins/meetings/`**: added a fail-fast Step 0 to both `/meeting-prep` and `/meeting-debrief` that checks for `mcp__outlook-bridge__outlook_auth_check` availability. If the `mail` plugin (which bundles `outlook-bridge`) isn't installed, users now get a clear error and install instruction instead of a silent failure. `plugin.json` description updated to surface the dependency.
- **`plugins/meetings/README.md`**: removed stale "Meeting intelligence for the communications marketplace" tagline; clarified `mail`-plugin dependency.

### Added (team-rollout readiness pass — 2026-05-10)
- **`plugins/chat/README.md`**, **`plugins/excel/README.md`**, **`plugins/docs/README.md`**: per-plugin READMEs for the three plugins that previously shipped without one. Use the `mail-pro/README.md` skeleton (overview, command table, how-it-works, setup, tips, license).
- **`README.md` install section rewritten**: now leads with the Claude Code marketplace flow (`/plugin marketplace add weirdapps/plessas-marketplace` → `installers/install.sh` → `/plugin install <name>` → `auth-wizard.sh`). The curl one-liner is preserved as an "Advanced — One-line installer" path for CI / unattended deploys.

### Added
- New `mail-pro` plugin (companion to `mail`) hosting the second-brain-dependent `/comm-report` and `/style-rebuild` commands plus `style-sync.py`. Lets the base `mail` plugin work for everyone, and isolates the private-repo dependency. See [`docs/workflows/mail-pro.md`](docs/workflows/mail-pro.md).
- `install.sh` and `install.ps1` now auto-clone, build, and `npm link` `outlook-cli` and `teams-cli` into `installers/deps/`. No more manual side-quest. Existing installs of those CLIs are detected and respected.
- `installers/pii-gauntlet.sh --mode=doctor`: separates tracked hits (FAIL — would ship publicly) from gitignored hits (INFO — local-only). The CI mode (`--mode=ci`) scans only `git ls-files` and is the actual safety gate.
- `rename-guard` CI workflow extended with two new guards: no stale `nbg-brand-system` paths, no deprecated `Task` tool name in `allowed-tools` (current name is `Agent`).
- Governance: `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`.

### Changed
- `decks` plugin: vendored brand directory renamed `shared/nbg-brand-system/` → `shared/brand-system/`. All 10 internal references updated.
- `decks` plugin: documentation updated to flat-agent layout (`agents/<name>.md` not `agents/<name>/AGENT.md`).
- `decks` plugin: 4 command frontmatters standardised on `Agent` (was deprecated alias `Task`).
- `mail` plugin: `style-sync.py` script moved to `mail-pro/scripts/` (along with the second-brain-dependent commands). Path resolution now uses `__file__` so it works for any install location.
- `bundled/creative/agents/device-mockup.md`: stripped dead references to NBG-internal screenshot library.
- `docs/day-one.md`, `docs/migration-from-communications-marketplace.md`: command-name corrections (`/mail-reply` → `/reply`).

### Removed
- The pre-`/reply` rename of `/mail-reply` from documentation. The command itself has been `/reply` since the previous round of renames.

## [1.0.0] — 2026-05-09

Initial public release.

### Added
- Six plugins: `decks`, `mail`, `meetings`, `chat`, `excel`, `docs`
- Bundled MCP servers: `outlook-bridge` (in `mail`), `teams-bridge` (in `chat`)
- Cross-platform installers (macOS / Linux: `install.sh`; Windows: `install.ps1`)
- Auth wizard (`auth-wizard.sh` / `.ps1`) for one-step Outlook + Teams sign-in
- Status check (`status.sh` / `.ps1`)
- `pii-gauntlet.sh` to prevent personal data leaks pre-push
- `rename-guard` CI workflow to catch stale command names and missing `allowed-tools`
- Brand system at `shared/brand-system/` (NBG colours, fonts, layouts)
- Team CLAUDE.md template at `shared/claude-md-template/`
- Migration guide from `communications-marketplace` (which is now deprecated and will be archived 2026-06-08)
