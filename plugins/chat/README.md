# chat v1.0

Microsoft Teams interactive commands. Inbox briefings, draft replies, thread summaries, channel digests. Bundles the `teams-bridge` MCP server (a thin wrapper around `teams-cli`).

## Commands

| Command | Description |
|---------|-------------|
| `/chat-inbox` | Summarise unread Teams chats — recent activity, urgency assessment, action items |
| `/chat-reply` | Draft a reply to a Teams chat. Shows draft for approval before sending |
| `/chat-summarize` | Summarise a single Teams chat or thread — decisions, action items, key points |
| `/chat-channel-digest` | Executive summary of a Teams channel — recent activity across threads |
| `/chat-doctor` | Diagnose `teams-bridge` MCP — Node binary, CLI install mode, auth status, last startup, suggested next step |
| `/auth-setup` | One-time Teams auth bootstrap (`--force-reauth` to redo it) |

## How it works

The plugin ships with a Node-based MCP server (`mcp-server/` — built on first start via `run.sh`) that wraps `teams-cli` (a separate npm package, installed automatically by the marketplace setup script). All Teams operations go through that bridge:

- **Read paths** (`teams_list_chats`, `teams_list_messages`, `teams_resolve_mri`) read from Microsoft Graph + the chatsvc API
- **Write paths** (`teams_send_message`) post via Graph (chats only — channel sends are not yet supported by the underlying API scope)

Send paths are draft-first by design — `/chat-reply` shows the proposed message for your approval before invoking `teams_send_message`.

### Send behaviour

`/chat-reply` auto-sends by default. This is deliberate as of 2026-08-16 and
supersedes the earlier draft-and-approve default. Every message carries a
`[Claude]` prefix so recipients know they are reading an agent, and the command
falls back to draft-and-confirm when the target chat is ambiguous or unfamiliar.
To approve every message instead, say so at the start of the session.

## Setup

The marketplace setup script (`installers/install.sh`) handles all dependencies:

1. Clones and `npm link`s the `teams-cli` package (from `weirdapps/teams-access`)
2. Builds the bundled `teams-bridge` MCP server

> **Warning — npm name collision:** A *different* `teams-cli@1.1.0` exists on the npm registry. The bridge's `package.json` uses a `git+https://` URL pointing at `weirdapps/teams-access` — never switch it to a bare semver range or you'll pull a stranger's package.

To authenticate Teams (one-time), inside Claude Code:

```text
/chat:auth-setup
```

This opens a Playwright-controlled browser window, signs you in via your Microsoft 365 account, and persists the session token. Run `teams-cli auth-check` to verify.

`installers/auth-wizard.sh` does the same thing from a terminal, but it is the deprecated path. Prefer the slash command.

## Cold-start delay

The first time you run a `/chat-*` command after install (or after a long idle period), the MCP server's `run.sh` will silently `npm install` and `npm run build` if needed. This adds 30-60 seconds the very first time. Subsequent calls are instant.

## Troubleshooting

If a command returns an auth error, run `/chat-doctor` first — it surfaces the exact problem (missing CLI, expired session, network issue) and tells you the one command to fix it.

If `teams-cli` is not on PATH after install (some corporate-locked laptops disallow `npm link` to the global prefix), the plugin still works. `teams-cli` is also a pinned `git+https` dependency of the bridge itself, so the server resolves `teams-cli/dist/cli.js` out of `plugins/chat/mcp-server/node_modules/` and only falls back to a bare `teams-cli` PATH lookup if that resolution fails. No user action required. What you lose is `teams-cli` as a standalone command in your own shell.

## License

MIT
