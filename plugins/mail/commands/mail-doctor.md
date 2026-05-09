---
description: "Diagnose the outlook-bridge MCP — node, CLI install mode, auth, last startup, and what to fix"
argument-hint: ""
allowed-tools: mcp__outlook-bridge__outlook_doctor
---

# /mail-doctor

Run a self-diagnostic on the outlook-bridge MCP server. Use this whenever the mail commands seem broken or you want to confirm everything is healthy.

## Implementation

1. Call `mcp__outlook-bridge__outlook_doctor` with no arguments.
2. Render the result as a compact one-screen report:

```
outlook-bridge MCP — Doctor

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
4. If anything is red (auth error, last startup fail, CLI in `path` mode without a global outlook-cli on PATH), print a short follow-up explanation.

## Notes

- Read-only diagnostic — no side effects.
- This is the FIRST command to try when mail commands fail. It tells you exactly what's wrong without needing to dig through MCP logs.
- "CLI mode = bundled" means the plugin's `mcp-server/node_modules/outlook-tool/` is being used (preferred — survives PATH stripping). "CLI mode = path" means the MCP server is calling `outlook-cli` via shell PATH (legacy fallback).
