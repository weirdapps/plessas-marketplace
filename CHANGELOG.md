# Changelog

All notable changes to `plessas-marketplace` are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
