# Frequently Asked Questions

For specific error messages, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## What is plessas-marketplace?

A collection of Claude Code plugins that automate routine NBG executive workflows: triaging Outlook, summarising Teams chats, building branded presentations, analysing Excel files, and producing Word documents (memos, letters). Think of it as a productivity layer that lives inside Claude Code — you type `/inbox-briefing` and Claude reads your inbox, classifies every email, and drafts your replies.

## Who is it for?

NBG executives and senior team members who already use Outlook, Teams, Excel, and PowerPoint daily. You don't need to be technical — the plugins are designed for "type a slash command, read the output" usage, not "edit YAML files at midnight."

## What platforms does it run on?

- **macOS** — fully supported, primary platform
- **Windows** — fully supported (use `install.ps1` instead of `install.sh`; commands work identically inside Claude Code)
- **Linux / WSL2** — fully supported

There is no AppleScript dependency anywhere. Outlook + Teams operations go through Microsoft Graph via the bundled CLIs.

## Do I have to install all 7 plugins?

No. Pick the ones you want. The dependency rules:

- `mail` is standalone
- `meetings` REQUIRES `mail` (uses its bundled `outlook-bridge` MCP for calendar access)
- `chat` is standalone
- `decks` is standalone
- `excel` is standalone
- `docs` is standalone
- `mail-pro` is an OPTIONAL companion to `mail`, available separately via the [`plessas-lab`](https://github.com/weirdapps/plessas-lab) marketplace — only install if you have access to the `weirdapps/plessas-second-brain` knowledge store

The most common starter set: `mail`, `meetings`, `chat`, `decks`. Add `excel` and `docs` when you find yourself wanting them.

## How long does the install take?

About 10 minutes if everything goes smoothly:

- 2 min — `/plugin marketplace add` + `installers/install.sh` clones repos and builds MCPs
- 3 min of browser sign-ins: `/mail:auth-setup` (M365), then `/chat:auth-setup` (Teams)
- 1 min — `/plugin install <name>` for each plugin
- 4 min — running your first command and reading the briefing

## Can I update without reinstalling?

Yes. Inside Claude Code:

```
/plugin update plessas-marketplace
```

This pulls the latest from GitHub. After major updates (new MCP versions, new CLI deps), re-run the setup script:

```bash
bash ~/.claude/plugins/marketplaces/plessas-marketplace/installers/install.sh
```

It's idempotent — safe to run any time. Skips work already done.

## How often should I update?

Plessas pushes updates as needed (typically once or twice a month). When the team chat says "new release," run `/plugin update`. Reading the [CHANGELOG](../CHANGELOG.md) will tell you what changed.

## How do I uninstall?

Inside Claude Code:

```
/plugin uninstall <name>@plessas-marketplace
/plugin marketplace remove plessas-marketplace
```

To also remove the cloned files and CLIs:

```bash
rm -rf ~/.claude/plugins/marketplaces/plessas-marketplace
npm uninstall -g outlook-cli teams-cli   # if you want to remove them entirely
rm -rf ~/.outlook-cli ~/.teams-cli       # remove auth state
```

Your `~/.claude/CLAUDE.md` is left intact — edit or remove as you wish.

## Can other people see my data?

**No.** The plugins read your Outlook / Teams data via Microsoft Graph using YOUR M365 token. The token lives only on your laptop (`~/.outlook-cli/`, `~/.teams-cli/`). Nothing is sent to GitHub, no central server, no shared database. Your drafts, briefings, and analysis stay on your machine.

The marketplace itself is a PUBLIC GitHub repo — but it contains only code, not user data. Any code you read in `weirdapps/plessas-marketplace` does not have access to your inbox.

## What about Plessas's personal email-style data — is that in the public repo?

**No.** Plessas's personal style guide (`plugins/mail/shared/style-guide.md`) is gitignored — it stays on his laptop and never enters the public repo. The shipping artefact is `style-guide-example.md` (a sanitised template). When you install the `mail` plugin, your own style guide will start blank and the `/mail-review` self-learning loop will populate it from your sent folder over time.

A custom CI gate (`pii-gauntlet.sh` + GitHub Actions workflow) runs on every push to scan for PII patterns (Plessas's name, peer names, NBG-internal project names, personal phone, etc.). The gate must pass before any commit lands on master.

## Is there a "training mode" or "dry run"?

For risky operations, yes:

- `/send-mail` and `/reply` are draft-first by default — they create a draft in Outlook desktop and activate the window for your final review and click-Send
- `/chat-reply` shows the draft in the conversation for your approval before invoking the `teams_send_message` MCP tool
- `/triage-inbox` (advanced) supports `--dry-run` to preview moves without executing

For pure read-only operations (briefings, summaries), there's no risk — they don't modify anything.

## What if I want to use a different SharePoint tenant?

The auth wizard prompts for your M365 tenant SharePoint host on first run (e.g. `contoso.sharepoint.com`). Find it in any SharePoint URL you own: `https://<this-part>.sharepoint.com/...`. Your answer is persisted to `~/.outlook-cli/config.json` and reused on subsequent runs.

To switch tenants later, re-run:

```bash
outlook-cli login --sharepoint-host <your-tenant>.sharepoint.com
outlook-cli capture-signature   # optional, for /send-mail
```

Or set the `PLESSAS_SHAREPOINT_HOST` env var to override the persisted value.

## What if a Claude Code update breaks a plugin?

File an issue at [github.com/weirdapps/plessas-marketplace/issues](https://github.com/weirdapps/plessas-marketplace/issues) with the error message. The plugins are tested against the Claude Code version Plessas uses; major Claude Code releases occasionally need a marketplace update.

In the meantime, the worst case is a single plugin's commands not working — the others continue to work. You can `/plugin disable <name>` to temporarily silence a broken plugin.

## What's the difference between `mail` and `mail-pro`?

`mail-pro` is an optional companion plugin available in the separate [`plessas-lab`](https://github.com/weirdapps/plessas-lab) marketplace (not this one). It adds `/comm-report` (relationship analytics) and `/style-rebuild` (full corpus rebuild) on top of the `mail` plugin. Both require the private `weirdapps/plessas-second-brain` knowledge store.

For most users, `mail` is everything you need. Install `mail-pro` from `plessas-lab` only if you have `second-brain` access and want deep analytics.

## Why are some commands prefixed (e.g., `mail:inbox-briefing`) and others bare (e.g., `/inbox-briefing`)?

Inside Claude Code, slash commands are namespaced by plugin. When you type `/inbox-briefing`, Claude Code finds the unique match (the `mail` plugin's command). If two plugins ship a command with the same name, you'd type the prefixed form `/mail:inbox-briefing` to disambiguate.

In current `plessas-marketplace`, no command name collides across plugins — bare names work everywhere. The prefixed form always works as a fallback.

## How do I know if it's working?

Three quick checks:

1. **Inside Claude Code**: type `/` — you should see commands grouped by plugin (`mail:`, `meetings:`, `chat:`, etc.)
2. **In your terminal**: `~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh` — green checkmarks across the board
3. **End-to-end test**: run `/inbox-briefing` (mail), `/meeting-prep` (meetings), `/chat-inbox` (chat). Each should produce real output within ~5 seconds

For deeper diagnosis: `/mail-doctor`, `/chat-doctor` — each plugin's doctor surfaces the exact problem and the one-line fix.

## Where do generated files go?

`~/Downloads/` always. Filename convention: `YYYYMMDDHHMM_<descriptive_name>.<ext>` (Athens timezone). For example:

- `~/Downloads/202605101430_q1_cards_review.pptx`
- `~/Downloads/202605101430_branch_pivot.xlsx`
- `~/Downloads/202605101430_memo_to_leadership.docx`

This is intentional: ad-hoc artefacts never pollute the marketplace repo or your project directories. Iterations get a NEW timestamp, not a `_v2` suffix.

## I have feedback / a bug / a feature request

File an issue: [github.com/weirdapps/plessas-marketplace/issues](https://github.com/weirdapps/plessas-marketplace/issues)

Or reach out to the marketplace maintainer directly. Bug reports with a copy-pasted error message + the command you ran are the fastest to fix.
