---
description: "Diagnose the teams-bridge MCP — node, CLI install mode, auth, last startup, and what to fix"
argument-hint: ""
allowed-tools: mcp__teams-bridge__teams_doctor
---

# /chat-doctor

Run a self-diagnostic on the teams-bridge MCP server. Use this whenever the chat commands seem broken or you want to confirm everything is healthy.

## Implementation

1. Call `mcp__teams-bridge__teams_doctor` with no arguments.
2. Render the result as a compact one-screen report:

```
teams-bridge MCP — Doctor

  MCP server   : <name> v<version>
  Node binary  : <path>  (<version>)
  CLI install  : <bundled | path>  v<cliVersion>
                 <path>
  Auth         : <ok | expired | missing | error>  (<hoursRemaining>h remaining if ok)
                 <account.upn if available>
  Last startup : <ok | fail | unknown>  at <ts>
                 <error if fail>

  → <suggestion>
```

3. If `suggestion` ends with a runnable command, surface it as a copyable line on its own.
4. If anything is red (auth error, last startup fail, CLI in `path` mode without a global teams-cli on PATH), print a short follow-up explanation.

## Notes

- Read-only diagnostic — no side effects.
- This is the FIRST command to try when chat commands fail. It tells you exactly what's wrong without needing to dig through MCP logs.
- "CLI mode = bundled" means the plugin's `mcp-server/node_modules/teams-cli/` is being used (preferred — survives PATH stripping). "CLI mode = path" means the MCP server is calling `teams-cli` via shell PATH (legacy fallback).
- Does NOT affect `chat-watch` (the long-running monitor). chat-watch uses the global `teams-cli` install at `~/.local/share/fnm/aliases/default/bin/teams-cli` — independent of this MCP server.
