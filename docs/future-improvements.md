# Future improvements — auth-setup slash command rollout

Deferred work captured during the 2026-05-22 introduction of `/mail:auth-setup` and `/chat:auth-setup`. Each item below is bounded and could be picked up independently in a future PR.

## 1. Delete the legacy auth scripts

**Why deferred:** `installers/auth-wizard.{sh,ps1}` and `installers/lib/tenant-prompt.{sh,ps1}` are referenced from 8 doc files plus `SECURITY.md` plus `install.sh`. Deleting cleanly requires sweeping all references in the same PR. The slash commands cover 100% of the functionality, so the legacy scripts are now redundant — just not yet safe to remove.

**Files to delete:**

- `installers/auth-wizard.sh`
- `installers/auth-wizard.ps1`
- `installers/lib/tenant-prompt.sh`
- `installers/lib/tenant-prompt.ps1`
- `installers/lib/` directory if empty after removal

**References to sweep in the same PR:**

- `README.md` — drop the "Legacy path (deprecated, still works)" note
- `installers/install.sh` — drop the "Legacy alternative" block (Next steps)
- `installers/install.ps1` — same
- `plugins/chat/QUICKSTART.md:30`
- `plugins/chat/README.md:34`
- `plugins/mail/QUICKSTART.md:33`
- `plugins/meetings/commands/meeting-prep.md:28`
- `docs/migration-from-communications-marketplace.md:49,82,101`
- `docs/TROUBLESHOOTING.md:151`
- `docs/FAQ.md:42`
- `docs/day-one.md:76-77`
- `SECURITY.md:18` — update scope list
- `CHANGELOG.md` — add `### Removed` entry

`docs/superpowers/plans/2026-05-11-share-readiness.md` references should NOT be touched — that's a historical plan document.

## 2. Trim the install.sh / install.ps1 CLI install block

**Why deferred:** removing `install_cli_from_repo` simplifies the installer by ~70 lines but risks breaking existing users who already have the global `outlook-cli` / `teams-cli` symlinks pointing at `installers/deps/`. The MCP bridges already work without the global install (bundled via `git+https` npm dep), so the global install only matters for users who run `outlook-cli` / `teams-cli` directly from their terminal.

**Migration path for affected users:**

```bash
# Before removing install_cli_from_repo:
which outlook-cli  # if path is in installers/deps/, unlink first
(cd ~/.claude/plugins/marketplaces/plessas-marketplace/installers/deps/outlook-access && npm unlink -g)
(cd ~/.claude/plugins/marketplaces/plessas-marketplace/installers/deps/teams-access  && npm unlink -g)
# Then re-install globally if still desired:
npm install -g outlook-tool teams-cli  # or however we choose to publish them
```

A migration message in `CHANGELOG.md ### Removed` should call this out.

## 3. Approach B — native MCP login tools

**Why deferred:** the current slash commands shell out to the bundled CLI via `node <path>/dist/cli.js login`. This works but couples the slash command to the marketplace install path and to a child-process spawn. The architecturally cleaner alternative is to expose `outlook_login`, `teams_login`, and `outlook_auth_check` / `teams_auth_check` as native MCP tools.

**What changes:**

- Add `src/tools/login.ts` to both bridges. Wraps the existing `runOutlookCli(['login', '--sharepoint-host', host])` flow.
- Slash commands become single MCP-call orchestrations — no Bash, no path-hardcoding.
- Bundled CLI path discovery problem goes away entirely.
- Other agents (e.g., `meeting-prep` doing a "ensure I can read your calendar" pre-flight) can call the login tool too — currently they have to fail with `auth_required` and tell the user to run a slash command.

**Trade:** requires updating both bridges (TypeScript code), bumping versions, rebuilding, re-testing. ~half-day of work per bridge.

## 4. Windows-side parity

**Why deferred:** Claude Code slash commands ARE cross-platform — the `.md` files in `commands/` work identically on macOS/Linux/Windows. The Bash heredocs inside the command body are the only macOS/Linux-specific piece. For Windows users, the slash commands will need PowerShell equivalents inside the Implementation section.

**Likely solution:** add an OSTYPE-guarded fork in the Implementation section that picks Bash vs PowerShell. Alternative: rewrite the heredoc/Python persist step using only Claude Code tools (Read, Write, Edit) so the command is genuinely OS-agnostic — that's the right answer, but adds complexity.

## 5. Smoke test on a fresh environment

**Why deferred:** the new commands are written but only exercised against Plessas's already-set-up machine. The doctor-as-bootstrap-probe trick depends on:

1. `run.sh` running `npm install` on first MCP launch ✓ confirmed via code reading
2. `npm install` actually fetching `outlook-tool` / `teams-cli` from `git+https://...` URLs ✓ confirmed by inspecting node_modules
3. The `mcp__outlook-bridge__outlook_doctor` call from inside the slash command actually triggering MCP startup if it's not already running — **not confirmed**. Possible that the MCP server starts only on the first user-facing command, not on doctor calls.

**Test plan:**

```bash
# On a VM or fresh user account:
rm -rf ~/.claude/plugins/marketplaces/plessas-marketplace
# /plugin marketplace add weirdapps/plessas-marketplace
# /plugin install mail@plessas-marketplace
# /mail:auth-setup  <-- does this work end-to-end?
```

## 6. Phase 2 — GitHub Releases distribution

Long-horizon improvement, decoupled from the auth-setup work. Switch from `git+https` npm deps to GitHub Releases tarballs:

```bash
# In run.sh, instead of npm install:
CLI_DIR="$HOME/.cache/weirdapps/outlook-cli"
[ -x "$CLI_DIR/dist/cli.js" ] || {
  curl -fsSL https://github.com/weirdapps/outlook-access/releases/latest/download/outlook-cli.tgz \
    | tar xz -C "$CLI_DIR"
}
```

**Wins:** no npm/git tangle, no `git+https://x@github.com/...#commit` workaround for npm/cli#2610, deterministic version pinning per release, faster first-run (tarball download vs git clone + npm install).

**Cost:** requires CI in `outlook-access` and `teams-access` to publish prebuilt tarballs on each tag.
