# Changelog

All notable changes to `plessas-marketplace` are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] — 2026-09-09

A full audit of the marketplace: correctness, security, CI and documentation. The headline
items are three defects that were invisible because the things meant to catch them reported
success.

### Fixed — correctness

- **Every MCP tool name in the repo was wrong.** A plugin-bundled server namespaces its tools
  `mcp__plugin_<plugin>_<server>__<tool>`, so the real name is
  `mcp__plugin_mail_outlook-bridge__outlook_list_mail`, not `mcp__outlook-bridge__outlook_list_mail`.
  All 140 references used the bare form, which matches nothing: `allowed-tools` pre-approved
  nothing, so every MCP call inside a mail, chat or meetings command fell back to the permission
  flow, prompting interactively and **auto-denying in headless and scheduled runs**. Both
  `meetings` commands additionally gated their fail-fast check on the bare prefix, so they
  reported `mail` as missing even when it was installed. `validate_consistency.py` now enforces
  the scoped form.
- **Every chart in every shipped deck example rendered empty.** `nbg_build.py` read chart data
  from `slide.content.*` while all three examples wrote it to `slide.chart.data.*`, and the
  `chart` key was never read. Measured on a build of `quarterly-report.yaml`: both chart parts
  carried zero `<c:ser>`, zero categories and zero values, and `nbg_validate.py` reported the
  deck as passing.
- **Three of seventeen validator checks examined nothing.** `check_font_sizes`,
  `check_title_overflow` and `check_color_contrast` iterated `a:rPr`, while every deck the
  builder produces carries `a:defRPr` (measured: 0 versus 37). All three passed vacuously on
  every run; the tell was `Sizes used:` printing an empty list. Every check now reports how many
  candidates it examined, and a zero-candidate pass is no longer reported as clean.
- `From.upn` does not exist on a message; the field is `From.EmailAddress.Address`. Seven call
  sites meant the sent-mail corpus was always empty, so the style-learning loop silently learned
  nothing.
- `email-handler.md` referenced `outlook_reply_mail` and `outlook_forward_mail`, neither of which
  has ever existed.
- The label-colour picker chose between white and `#202020` without checking the winner cleared
  anything. At fill luminance 0.2101 the best available ratio is 4.036:1, under WCAG AA; two
  palette colours (`#5D8D2F`, `#F60037`) failed. Pure black as the dark candidate moves the
  crossover to 4.583:1 and clears all 52.
- `install.ps1` passed `-Encoding` to `Copy-Item`, which has no such parameter. With
  `$ErrorActionPreference = 'Stop'` this killed every fresh Windows install at the CLAUDE.md step.
- `install.ps1` reported `[OK]` after failed `npm install`, `npm run build` and `pip install`,
  because `$ErrorActionPreference` does not govern native exit codes. Every native call now
  checks `$LASTEXITCODE`.
- `install.sh` aborted two thirds of the way through on a machine without `python3`, leaving a
  half-installed state.
- Neither installer installed `nbg-keynote`'s dependencies, so `/create-keynote` died with
  `ModuleNotFoundError` on a fresh install.
- `inject_table_data.py` renamed every namespace prefix it had not pre-registered, corrupting
  exactly the real PowerPoint files it exists to edit.
- `nbg_keynote.py --validate` passed four classes of spec that then crashed the build.
- `nbg_build.py` never inspected the validator's return code, so a crashed validator was
  indistinguishable from a clean deck. It also had no argument parsing: `-o out.pptx` wrote a
  file named `-o`.
- Device-mockup content boxes were wrong for both 16 Pro frames, clipping the screenshot and
  leaving transparent strips. Frame geometry is now measured from each PNG and asserted in CI.
- 128 INDEX filename references pointed at files that do not exist; 6 resolved before, 128 now.

### Fixed — security

- **Windows command injection in both bundled MCP servers.** `spawn` was called with
  `shell: true` on Windows, routing mail subjects, bodies, folder names and Teams message HTML
  through `cmd.exe`. A shell is now used only for the legacy PATH-fallback case, where Node
  refuses to spawn a `.cmd` shim without one.
- **A timed-out send was retried up to four times.** Exit 5 covers a lost response as well as a
  failed call, and was blanket-retryable, so a `sendMail` that Graph had already accepted could be
  delivered four times. Retryability is now a property of the call: non-idempotent writes surface
  the ambiguity instead of repeating it.
- `outlook_move_mail` now refuses Deleted Items, Junk, Trash and Recoverable Items by name, and
  the documented 20-id batch cap is enforced rather than merely declared.
- The `[Claude]` attribution prefix on Teams sends is enforced in the bridge, not only in prose.
- Three holes in `pii-gauntlet.sh`, each of which switched checks off: an unanchored path
  exemption that exempted 13 tracked files including two already containing real addresses; a
  filter that dropped any line containing the word "copyright"; and single-letter fixture-host
  names that made any tenant ending in a, b, x, y or z invisible. The CI gate was also
  case-sensitive where the local doctor was not, and neither could see tracked *filenames* —
  two shipped PNGs disclosed an internal project name in their own names while the scanner
  reported PASS.
- Every argument is now validated against its declared inputSchema at the MCP dispatch point,
  so required fields, types, enums and bounds are checked rather than documented.

### Added

- `tests.yml`: `pytest plugins` plus both vitest suites and typechecks, unconditional. Previously
  the only Python test run in CI was gated on `sonarcloud.yml` finding a directory named `tests`,
  and the sole match was a TypeScript directory.
- `lint.yml`: the full pre-commit hook set plus `claude plugin validate --strict` on all seven
  manifests.
- `teams-bridge` went from zero tests to a real suite; `--passWithNoTests` is gone. Test counts
  across the repo: 45 to 88 Python, 29 to 138 TypeScript.
- Six new checks in `validate_consistency.py`, including MCP tool-name resolution and
  plugin/marketplace version agreement.
- Standard #22: accessibility, with measured contrast ratios, the WCAG 2.1 AA baseline via
  EN 301 549 V3.2.1 and a WCAG 2.2 gap-test.
- `"dependencies": ["mail"]` on `meetings`, replacing a prose-only requirement.

### Changed

- All six plugins to 1.1.0, marketplace to 2.2.0. **Plugin version is the cache key Claude Code
  uses to decide whether an installed copy is stale, and it had never been bumped**, so no user
  had ever received a post-install fix.
- The three bundled creative commands and four previously unreachable agents now load. `decks`
  registers 9 skills and 8 agents, up from 6 and 4. Agent files moved into `agents/`, which is
  the only directory Claude Code auto-discovers.
- The QA gate is dispatched by `create-presentation`, `redesign-deck` and `polish-slides`; it was
  reachable from none of them.
- Around 700 em-dashes removed from prompt files that themselves forbid em-dashes.
- Roughly a dozen numeric self-contradictions reconciled across the brand system, including the
  body-text floor (stated four ways), the page-number position (0.48" apart) and the left gutter.

## [2.1.0] — 2026-05-11

### Added

- `installers/lib/tenant-prompt.{sh,ps1}` — first-run prompt for M365 SharePoint host, persisted to `~/.outlook-cli/config.json`, env-overridable via `PLESSAS_SHAREPOINT_HOST`
- Python venv install on Windows (`install.ps1` parity with `install.sh`)
- Windows install code blocks + Chrome/Edge prereq + NBG-decks disclosure in README
- PowerShell troubleshooting recipes + Windows-specific gotchas section in `docs/TROUBLESHOOTING.md`
- `<TEMP_DIR>` placeholder convention for cross-platform temp paths
- "Per-plugin notes" section in README disclosing NBG branding in decks plugin

### Changed

- `outlook-bridge` MCP: pinned `typescript ~5.9.3`, `@types/node ^22.0.0`, `vitest ^4.1.5`, added `engines.node >=20`
- `teams-bridge` MCP: same dep pins + added `--passWithNoTests` to test script (no test files yet)
- `outlook-cli` and `teams-cli` GitHub deps now pinned to specific commit SHAs via `git+https://x@github.com/...` workaround for npm/cli#2610 (lockfile would otherwise pin to `git+ssh://`, breaking teammates without SSH keys)
- `auth-wizard.{sh,ps1}` no longer hardcode `<your-tenant>.sharepoint.com` — now prompt
- `outlook-bridge` MCP `doctor` tool reads tenant from config instead of hardcoding
- `mail/commands/mail-review.md` + `mail/agents/email-handler.md` clipboard recipes shown as per-OS code blocks
- `meetings/agents/meeting-intelligence.md` + `calendar-access.md` AppleScript fallbacks now OSTYPE-guarded
- `decks/commands/{create-presentation,presentation-review}.md` auto-create `~/.claude/presentations/{pending,reviewed}/` dirs

### Removed

- `mail-pro` plugin moved to `plessas-lab` (was maintainer-only — depended on private second-brain DB and hardcoded sender filter)

### Fixed

- `decks` plugin Python tools no longer fail on Windows (venv now built by installer)
- Hardcoded `<your-tenant>.sharepoint.com` removed from 5 doc files (QUICKSTART.md, team-claude-md.md, TROUBLESHOOTING.md, FAQ.md, doctor.ts)
- Tenant-prompt.sh persist block hardened against shell injection (uses sys.argv instead of string interpolation)
- Tenant-prompt.ps1 persist failure now terminating (`-ErrorAction Stop`)

## [Unreleased]

### Added (auth-setup slash commands — 2026-05-22)

- **`plugins/mail/commands/auth-setup.md`** — new `/mail:auth-setup` slash command. Probes the outlook-bridge MCP, drives Microsoft 365 OAuth via the bundled `outlook-tool` CLI inside `mcp-server/node_modules/`, captures the email signature. Idempotent; skips already-completed steps. Supports `--force-reauth` and `--skip-signature` flags. Tenant host resolved via env → `~/.outlook-cli/config.json` → interactive prompt (mirrors the existing `tenant-prompt.sh` UX).
- **`plugins/chat/commands/auth-setup.md`** — new `/chat:auth-setup` slash command. Same shape as mail; drives `teams-cli login`. No SharePoint host needed (Teams reuses the Outlook web session). Supports `--force-reauth`.

### Changed (auth-setup slash commands — 2026-05-22)

- **`README.md`** — install flow now leads with `/plugin install <name>@plessas-marketplace` + `/mail:auth-setup` / `/chat:auth-setup`. Legacy shell-based `auth-wizard.{sh,ps1}` path retained as deprecated fallback.
- **`installers/install.sh`** — "Next steps" footer rewritten to recommend the slash-command path; legacy auth-wizard.sh + status.sh kept as alternatives.

### Deferred (capture-only)

The full cleanup that the new slash commands enable is **not** in this release. See [`docs/future-improvements.md`](docs/future-improvements.md) for the deferred scope:

- Delete `installers/auth-wizard.{sh,ps1}` and `installers/lib/tenant-prompt.{sh,ps1}` (replaced by slash commands).
- Trim `install_cli_from_repo` block from `installers/install.{sh,ps1}` — CLIs are already bundled via `git+https` npm deps, the global `npm link` step is redundant.
- Sweep 8 doc files for stale `auth-wizard` references: `plugins/{chat,mail}/QUICKSTART.md`, `plugins/{chat}/README.md`, `plugins/meetings/commands/meeting-prep.md`, `docs/{day-one,FAQ,TROUBLESHOOTING,migration-from-communications-marketplace}.md`, `SECURITY.md`.
- Windows-side parity: `auth-setup.ps1` equivalents (Claude Code slash commands are cross-platform; only `install.ps1` and the legacy shell wizards need updates).
- **Approach B (architectural improvement)**: promote `login`/`auth-check` to native MCP tools (`outlook_login`, `teams_login`) so the slash command body becomes a single MCP call instead of a Bash shell-out to the bundled CLI. Cleaner abstraction, reusable from other agents.
- Smoke test on a fresh environment — confirm doctor-as-bootstrap-probe trick triggers `run.sh` correctly on first call.

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

- Natural-language triggering: one router skill per plugin, so requests reach the right workflow without a command name. Greek and English.
- `docs/skill-triggers.md`: each skill's domain, boundaries, and the tie-break policy
- `validate-plugins.yml`: skill frontmatter validation (description floor, Greek text, negative boundary clause)
- New `mail-pro` plugin (companion to `mail`) hosting the second-brain-dependent `/comm-report` and `/style-rebuild` commands plus `style-sync.py`. Lets the base `mail` plugin work for everyone, and isolates the private-repo dependency. See [`docs/workflows/mail-pro.md`](docs/workflows/mail-pro.md).
- `install.sh` and `install.ps1` now auto-clone, build, and `npm link` `outlook-cli` and `teams-cli` into `installers/deps/`. No more manual side-quest. Existing installs of those CLIs are detected and respected.
- `installers/pii-gauntlet.sh --mode=doctor`: separates tracked hits (FAIL — would ship publicly) from gitignored hits (INFO — local-only). The CI mode (`--mode=ci`) scans only `git ls-files` and is the actual safety gate.
- `rename-guard` CI workflow extended with two new guards: no stale `nbg-brand-system` paths, no deprecated `Task` tool name in `allowed-tools` (current name is `Agent`).
- Governance: `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`.

### Changed

- `chat/commands/chat-reply.md` sends through the bundled `teams-bridge` MCP instead of an absolute path to a local checkout, which never resolved on any machine but the maintainer's
- `chat-reply` auto-send is now the documented public default. This supersedes the draft-and-approve default recorded in `docs/superpowers/plans/2026-05-11-share-readiness.md`, which should be read as historical from this date.
- `installers/pii-gauntlet.sh` user-path check split into two: one for local source-tree paths (with design-record path exclusion) and one for absolute maintainer home paths (no exclusions)
- `mail/commands/send-mail.md` CC example uses a neutral domain
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
