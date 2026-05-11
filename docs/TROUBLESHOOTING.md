# Troubleshooting cookbook

Look up your error message or symptom, copy-paste the fix. For broader "how do I…" questions, see [FAQ.md](FAQ.md).

---

## Quick triage

If something's broken, run the right doctor first — each surfaces the exact problem with a one-line fix:

| Plugin | Doctor command |
|---|---|
| `mail` | `/mail-doctor` |
| `chat` | `/chat-doctor` |
| Whole marketplace | `~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh` |

---

## Install and setup

### `command not found: claude`

Claude Code itself isn't on your PATH.

```bash
which claude          # should print a path
echo $PATH            # check Claude is in here
```

Reinstall from <https://claude.ai/claude-code>.

### `command not found: outlook-cli` (or `teams-cli`)

The marketplace setup script clones and `npm link`s these CLIs. If they didn't land on PATH:

```bash
# Re-run the setup script (idempotent)
bash ~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.sh
```

If `npm link` fails (some corporate-locked laptops disallow writing to the global npm prefix):

```bash
# Find where npm wants to put global binaries
npm prefix -g

# Add that bin/ subdir to your shell's PATH (zsh example)
echo 'export PATH="$(npm prefix -g)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

If your IT policy actually blocks global npm linking, the bundled MCPs fall back to invoking the locally cloned binaries at `~/.claude/plugins/marketplaces/plessas-marketplace/installers/deps/{outlook-access,teams-access}/dist/cli.js`. No user action required for the plugins to work — but you won't have `outlook-cli` available as a standalone command in your shell.

### `Node.js: v18.x.x found, need v20+`

Update Node to v20 or newer:

- macOS / Linux: `brew install node@20` (or use nvm: `nvm install 20 && nvm use 20`)
- Windows: download from <https://nodejs.org/>

### `python3: command not found` (decks plugin)

Install Python 3.11+ from <https://www.python.org/downloads/>. The `decks` plugin builds a virtual env on first install for its PowerPoint validation tools.

### `git: command not found`

Install git from <https://git-scm.com/downloads>.

### `Permission denied` when running `installers/install.sh`

```bash
chmod +x ~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.sh
~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.sh
```

### `/plugin install <name>` says "plugin not found"

Two possibilities:

1. The marketplace isn't added to Claude Code yet:

   ```
   /plugin marketplace add weirdapps/plessas-marketplace
   ```

2. The plugin name is misspelled. Valid names: `mail`, `meetings`, `chat`, `decks`, `excel`, `docs`, `mail-pro`.

---

## Authentication

### Outlook: `auth_required` returned by an MCP tool

Your M365 token has expired or was never set. Run:

```bash
outlook-cli login --sharepoint-host <your-tenant>.sharepoint.com
```

A browser window opens; sign in with your M365 credentials. Token persists for ~30 days; you'll be re-prompted automatically when it expires. The auth wizard prompts for your tenant on first install; you can also find it in any SharePoint URL you own: `https://<this-part>.sharepoint.com/...`.

### Outlook: `Throttled (429)` errors during big inbox sweeps

Microsoft Graph rate-limits at the application level. The `outlook-bridge` MCP caps concurrency at 2 to avoid this — but very large sweeps (1000+ messages) can still trip it.

Wait 60 seconds and retry. For very large operations, scope the sweep:

```
/mail-review --count 50
```

### Outlook: `wrong tenant` or signed in to wrong account

Reset auth completely:

```bash
rm -rf ~/.outlook-cli
outlook-cli login --sharepoint-host <correct-host>.sharepoint.com
```

### Teams: `auth_required` or `expired`

```bash
teams-cli auth-check        # confirms current state
~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh
```

The auth wizard re-runs the Playwright browser sign-in for Teams. Browser window opens — sign in with your M365 account, approve the requested permissions, browser closes automatically.

### Teams: silent renew fails / browser doesn't open

Try the manual renewal:

```bash
teams-cli auth-renew     # silent renewal using persisted browser profile
```

If that fails, do a fresh login:

```bash
teams-cli login --chrome-channel chrome
```

If your IT blocks Playwright (uncommon but possible on locked laptops), file an issue with the error output.

### `outlook-cli`: signature wasn't captured

```bash
outlook-cli capture-signature
```

You need a recent message in your Sent Items folder for this to work — the tool extracts the signature from the most recent send. Send yourself a test email if your Sent Items is empty.

---

## Cold-start delay

### First `/chat-*` or `/mail-*` command after install hangs for 30-60 seconds

Normal. The bundled MCP servers are doing `npm install` + `npm run build` for the first time. Subsequent calls are instant. Watch the Claude Code terminal output — you'll see "Building outlook-bridge MCP..." or similar.

If it hangs more than 2 minutes, kill it and run the install script manually so you can see what's failing:

```bash
bash ~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.sh
```

---

## Plugin-specific

### mail: briefing returns 0 emails but you have unread messages

```bash
outlook-cli auth-check       # is your token valid?
outlook-cli list-mail        # does the CLI itself see your inbox?
```

If both pass but the briefing is still empty, restart Claude Code (`Ctrl+C` and re-launch). The MCP server may be in a stale state.

### mail: drafts open in the wrong Outlook account

`outlook-cli` uses your default M365 identity. To check which account is configured:

```bash
outlook-cli auth-check
```

To switch identity, log out and back in with the right account:

```bash
rm -rf ~/.outlook-cli
outlook-cli login --sharepoint-host <correct-host>.sharepoint.com
```

### mail: draft style feels off for a specific recipient

The self-learning loop calibrates per recipient automatically. Run `/mail-review` 3-4 times — each time it ingests recent sent items and updates the recipient profile. After ~10 sends to that recipient, the style should match.

For an immediate manual rebuild, install `mail-pro` (requires private `second-brain` repo) and run:

```
/style-rebuild
```

### meetings: "outlook-bridge MCP not available"

The `meetings` plugin uses `mail`'s bundled MCP for calendar access. Install `mail` first:

```
/plugin install mail@plessas-marketplace
```

### meetings: calendar shows wrong events / events missing

Outlook desktop must be syncing M365 calendars (not local-only). Open Outlook → Account Settings → Data Files; confirm M365 is the default. The MCP reads via Microsoft Graph independently, but local Outlook has to be configured for the same tenant.

### meetings: attendee dossiers are empty

Optional `second-brain` MCP isn't installed. Briefings still work (calendar + inbox cross-ref) — just without the historical dossiers. Install `mail-pro` to add dossiers from your email corpus (requires private `second-brain` repo access).

### chat: channel sends don't work

By design — Microsoft Graph's send scope is missing for channels. Send works for chats only. Channel reads (`/chat-channel-digest`) work fine.

### chat: replies in wrong language

`/chat-reply` auto-detects the thread's language. If the recent messages are in Greek, the draft is in Greek; English, English. If you want to force a language, mention it in the prompt: "draft in Greek" or "reply in English."

### decks: PPTX validation fails with "bumper position invalid"

Known quirk of `nbg_validate.py`. Use bumper y=0.30, h=0.19, 10pt and title y=0.55. The plugin's `graphics-renderer` agent applies these automatically; if you're hand-editing slides, match the spec.

### decks: infographics look text-only / no AI image generation

The `manage-nano-banana` skill is OPTIONAL — it lives in the separate `weirdapps/plessas-lab` marketplace. If you want AI-generated rasterised images, install that marketplace too:

```
/plugin marketplace add weirdapps/plessas-lab
/plugin install manage-nano-banana@plessas-lab
```

Without it, decks use SVG-based icons + infographics, which are sharper and brand-compliant anyway. Most decks don't need raster images.

### excel: Greek headers show as boxes / squares

Open the file once in Excel and re-save as `.xlsx`. Legacy `.xls` or CSV-as-`.xlsx` may have UTF-8 encoding issues. The plugin reads the workbook's own column names verbatim — fixing the encoding fixes the display.

### excel: pivot output looks wrong

The plugin shows its assumptions before computing. Read them back: "I'll group by Region, sum Revenue, compare Q4 vs Q3." If wrong, restate explicitly: "group by Branch (column F), not by Region (column C)."

### docs: Greek text uses wrong font

Aptos handles Greek correctly. If you see boxes or squares in Word, your Word install may be missing Aptos. Install Microsoft 365 Insider build, or use the Aptos Display package from the Office font installer.

### docs: letterhead missing

Default uses NBG branding from `shared/brand-system/`. Pass `--no-letterhead` to suppress for personal letters. To customise, edit `shared/brand-system/` files (advanced — talk to the maintainer).

---

## Updates

### `/plugin update` says "no updates available" but you know there are

```bash
cd ~/.claude/plugins/marketplaces/plessas-marketplace
git pull --ff-only
```

Then restart Claude Code. The native `/plugin update` mechanism is occasionally cache-stale.

### After update, MCP server fails to start

Re-build the MCP servers:

```bash
bash ~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.sh
```

This re-runs `npm install` + `npm run build` for both bundled MCPs.

---

## Catastrophic recovery

### "I broke it. How do I start over?"

```bash
# Inside Claude Code
/plugin uninstall mail@plessas-marketplace
/plugin uninstall meetings@plessas-marketplace
/plugin uninstall chat@plessas-marketplace
/plugin uninstall decks@plessas-marketplace
/plugin uninstall excel@plessas-marketplace
/plugin uninstall docs@plessas-marketplace
/plugin marketplace remove plessas-marketplace
```

```bash
# In your terminal
rm -rf ~/.claude/plugins/marketplaces/plessas-marketplace
rm -rf ~/.outlook-cli ~/.teams-cli
npm uninstall -g outlook-cli teams-cli
```

Then follow the [README install steps](../README.md#install--10-minutes) from scratch. The whole reinstall takes ~10 minutes.

---

## Still stuck?

File an issue: [github.com/weirdapps/plessas-marketplace/issues](https://github.com/weirdapps/plessas-marketplace/issues)

Include:

1. The exact command you ran
2. The exact error message (copy-paste, don't paraphrase)
3. The output of `~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh`
4. Your OS (macOS 14, Windows 11, etc.) and Claude Code version (`claude --version`)
