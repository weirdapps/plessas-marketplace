---
description: "First-run auth for the teams-bridge MCP: sign in to Microsoft Teams in one command"
argument-hint: "[--force-reauth]"
allowed-tools: Bash, mcp__plugin_chat_teams-bridge__*
---

# /chat:auth-setup

One-command bootstrap for the `chat` plugin. Probes the bridge and drives Microsoft 365 OAuth via the bundled `teams-cli` if needed.

Replaces the legacy `installers/auth-wizard.sh` step. No global `npm link` required; it uses the CLI bundled inside the MCP server's `node_modules`.

## Implementation

Parse `$ARGUMENTS` for `--force-reauth`.

### Step 0: ensure the bundled MCP server is built

The `teams-bridge` server does not install itself on first use, because doing so inside the MCP
startup handshake overruns Claude Code's timeout. Check and, if needed, build it once:

```bash
SERVER="${CLAUDE_PLUGIN_ROOT}/mcp-server"
if [ ! -d "$SERVER/node_modules" ] || [ ! -f "$SERVER/dist/server.js" ]; then
  (cd "$SERVER" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci && npm run build)
fi
```

This takes 30-60 seconds the first time and is instant afterwards. **Tell the user to restart
Claude Code once it finishes**, because the MCP server is only started at session start; it will
not pick up the new build in the current session.

Re-run this step after any plugin update. An update installs into a new versioned directory,
which starts empty.

### Step 1: Probe the bridge

Call `mcp__plugin_chat_teams-bridge__teams_doctor` with no arguments. Step 0 has already ensured the server is installed and built, so this boots it and reports its state. If the call fails because the server is not running, the Step 0 build has not been picked up yet: restart Claude Code and run this command again.

Inspect the response:

- `lastStartup.status === 'fail'` → STOP. The MCP itself is broken. Print the error and tell the user to read `mcp-server/.last-startup.json` or run `bash <plugin>/mcp-server/run.sh` manually. Do not proceed.
- `cli.mode === 'path'` → WARN. The bridge is falling back to a global `teams-cli` on PATH. Suggest the user run `(cd "${CLAUDE_PLUGIN_ROOT}/mcp-server" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci && npm run build)` to switch to bundled mode, then re-run this command. Still proceed if user wants to keep going.
- `auth.status === 'ok'` AND no `--force-reauth` flag → SKIP. Print `teams-cli already authenticated as <auth.account.upn> (<auth.hoursRemaining>h remaining)` and render the final report.
- Otherwise → continue to Step 2.

### Step 2: Drive OAuth

Find the bundled CLI and drive `login`:

```bash
CLI="${CLAUDE_PLUGIN_ROOT}/mcp-server/node_modules/teams-cli/dist/cli.js"
[ -f "$CLI" ] || { echo "Bundled CLI missing — run /chat:auth-setup again after the bridge finishes building."; exit 1; }

node "$CLI" login
```

This opens a Playwright-driven browser window. The user signs in to Outlook web (Teams reuses the Outlook session token); the captured Bearer is persisted in the teams-cli profile dir. Block until the command returns.

Re-call `mcp__plugin_chat_teams-bridge__teams_doctor`. If `auth.status` is still not `ok`, report the failure and stop.

### Step 3: Final report

```
chat plugin: auth setup complete

  MCP bridge   : <ok | warn>
  CLI install  : <bundled | path>  v<cliVersion>
  Auth         : ok, <upn>  (<hoursRemaining>h remaining)

  Next: try /chat:chat-inbox
```

## Notes

- **No SharePoint host needed**: `teams-cli` captures the Bearer from the Outlook web session, not from a tenant-specific endpoint. The user only needs an M365 account.
- **Idempotent**: re-running is safe. Default behavior skips when already authenticated. Pass `--force-reauth` to invalidate cached tokens and sign in fresh.
- **No global install needed**: drives OAuth through the bundled CLI at `mcp-server/node_modules/teams-cli/dist/cli.js`. The note in `chat-doctor.md` about `chat-watch` (the long-running monitor) still applies; `chat-watch` is a separate process that uses the global `teams-cli` install. This command does not affect it.
- **Interactive OAuth**: `teams-cli login` opens a real Chrome/Edge window via Playwright. M365 auth requires an interactive sign-in. The user must complete sign-in in the browser; the slash command will block until they do.
- **Headless / SSH sessions** are not supported; see `/mail:auth-setup` for the workaround.
- This command replaces the `auth-wizard.sh` step from `installers/install.sh`. Together with `/mail:auth-setup`, it removes the last out-of-band install step from the onboarding flow.
