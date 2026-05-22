---
description: "First-run auth for the outlook-bridge MCP — sign in to M365, capture signature, ready in one command"
argument-hint: "[--force-reauth] [--skip-signature]"
allowed-tools: Bash, Read, mcp__outlook-bridge__outlook_doctor, mcp__outlook-bridge__outlook_capture_signature
---

# /mail:auth-setup

One-command bootstrap for the `mail` plugin. Probes the bridge, drives Microsoft 365 OAuth via the bundled `outlook-cli` if needed, and captures the user's email signature for outgoing drafts.

Replaces the legacy `installers/auth-wizard.sh` step. No global `npm link` required — uses the CLI bundled inside the MCP server's `node_modules`.

## Implementation

Parse `$ARGUMENTS` for `--force-reauth` and `--skip-signature` flags.

### Step 1 — Probe the bridge

Call `mcp__outlook-bridge__outlook_doctor` with no arguments. This also boots the MCP server, which on first run triggers `npm install` + `npm run build` inside `plugins/mail/mcp-server/` — guaranteeing the bundled `outlook-tool` CLI is present.

Inspect the response:

- `lastStartup.status === 'fail'` → STOP. The MCP itself is broken. Print the error and tell the user to read `mcp-server/.last-startup.json` or run `bash <plugin>/mcp-server/run.sh` manually. Do not proceed.
- `cli.mode === 'path'` → WARN. The bridge is falling back to a global `outlook-cli` on PATH. Suggest the user run `(cd ~/.claude/plugins/marketplaces/plessas-marketplace/plugins/mail/mcp-server && npm install)` to switch to bundled mode, then re-run this command. Still proceed if user wants to keep going.
- `auth.status === 'ok'` AND no `--force-reauth` flag → SKIP to Step 3 (signature). Print `outlook-cli already authenticated as <auth.account.upn> (<auth.hoursRemaining>h remaining)`.
- Otherwise → continue to Step 2.

### Step 2 — Drive OAuth

Resolve the SharePoint host. Priority order:

1. `$PLESSAS_SHAREPOINT_HOST` env var
2. `sharepoint_host` field in `~/.outlook-cli/config.json` (use Read to inspect)
3. Prompt the user: "Enter your Microsoft 365 SharePoint host (e.g. `contoso.sharepoint.com`). Find it in any SharePoint URL: `https://<this-part>.sharepoint.com/…`"

If the user supplies a host interactively, persist it to `~/.outlook-cli/config.json` with `chmod 600`:

```bash
mkdir -p ~/.outlook-cli
python3 - "$HOST" <<'PY'
import json, os, sys
host = sys.argv[1]
path = os.path.expanduser('~/.outlook-cli/config.json')
data = {}
if os.path.exists(path):
    try: data = json.load(open(path))
    except Exception: pass
data['sharepoint_host'] = host
json.dump(data, open(path, 'w'), indent=2)
PY
chmod 600 ~/.outlook-cli/config.json
```

(Pass via `sys.argv` to dodge shell-interpolation injection.)

Find the bundled CLI and drive `login`:

```bash
CLI="$HOME/.claude/plugins/marketplaces/plessas-marketplace/plugins/mail/mcp-server/node_modules/outlook-tool/dist/cli.js"
[ -f "$CLI" ] || { echo "Bundled CLI missing — run /mail:auth-setup again after the bridge finishes building."; exit 1; }

node "$CLI" login --sharepoint-host "$HOST"
```

This opens a Playwright-driven browser window. The user signs in interactively; the token is captured to `~/.outlook-cli/`. Block until the command returns.

Re-call `mcp__outlook-bridge__outlook_doctor`. If `auth.status` is still not `ok`, report the failure and stop — do not attempt signature capture against a broken auth.

### Step 3 — Capture signature

Skip if `--skip-signature` was passed.

If `~/.outlook-cli/signature.html` already exists (use Read or `[ -f ]`), report `Signature already present` and stop.

Otherwise call `mcp__outlook-bridge__outlook_capture_signature` with no arguments. Report success or surface the error verbatim — signature capture is best-effort, never block on it.

### Step 4 — Final report

Render a one-screen summary:

```
mail plugin — auth setup complete

  MCP bridge   : <ok | warn>
  CLI install  : <bundled | path>  v<cliVersion>
  Auth         : ok — <upn>  (<hoursRemaining>h remaining)
  Signature    : <captured | already present | skipped | failed>

  Next: try /mail:inbox-briefing
```

## Notes

- **Idempotent**: re-running is safe. Default behavior skips already-completed steps. Pass `--force-reauth` to invalidate cached tokens and sign in fresh.
- **No global install needed**: drives OAuth through the bundled CLI at `mcp-server/node_modules/outlook-tool/dist/cli.js`. If the user also wants a system-wide `outlook-cli` binary for ad-hoc terminal use, they can `npm install -g outlook-tool` separately — but it is not required for any plugin command.
- **Tenant persistence**: the SharePoint host is stored in `~/.outlook-cli/config.json` after first prompt; subsequent runs use it silently. Override at any time with `PLESSAS_SHAREPOINT_HOST=…` in the environment.
- **Interactive OAuth**: `outlook-cli login` opens a real Chrome/Edge window via Playwright. This is intentional and not configurable — M365 auth requires an interactive sign-in. The user must complete sign-in in the browser; the slash command will block until they do.
- **Headless / SSH sessions** are not supported by Playwright's auth capture. Users on headless boxes must run this command on a machine with a GUI, then copy `~/.outlook-cli/` to the target machine.
- This command replaces the `auth-wizard.sh` step from `installers/install.sh`. Once `/chat:auth-setup` ships too, the meta-installer can drop both its `install_cli_from_repo` block (CLIs are bundled) and `auth-wizard.sh` invocation (slash commands handle auth).
