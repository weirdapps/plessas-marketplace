# Contributing

`plessas-marketplace` is maintained primarily for an internal team at NBG (National Bank of Greece). Bug reports and pull requests from anyone are welcome — we'll prioritise issues that affect the NBG team but won't ignore others.

## Reporting a bug

Open an issue at <https://github.com/weirdapps/plessas-marketplace/issues>. Use the **Bug report** template. Include:

- Which plugin and command (e.g. `mail` / `/inbox-briefing`)
- The OS and Node.js version (`node --version`)
- The exact command you ran and the error you saw
- Output of `installers/status.sh` (or `status.ps1`) — it captures install state

## Asking a usage question

Use the **Question** issue template. Tag with the plugin name. Please check the [day-one guide](docs/day-one.md) and [workflow docs](docs/workflows/) first.

## Suggesting a change

For small fixes (typos, broken links, command-name corrections):

1. Fork
2. Open a PR with a short description

For substantive changes (new commands, new plugins, refactoring):

1. Open an issue first to discuss the approach
2. Wait for maintainer feedback before writing code — we may have already considered it or have constraints from the NBG context

## Pull request requirements

All PRs must pass the CI guards:

- **PII Check**: scans for personal data leakage. See `installers/pii-gauntlet.sh`. Run locally with `bash installers/pii-gauntlet.sh --mode=doctor` to check before pushing.
- **rename-guard**: catches stale command names, missing `allowed-tools` declarations, deprecated tool names.

Run both locally before opening a PR:

```bash
bash installers/pii-gauntlet.sh --mode=ci
# rename-guard checks happen via grep — see .github/workflows/rename-guard.yml for the exact patterns
```

## Code style

- **Bash**: targeted at `bash 4+` (macOS ships with bash 3 — install `bash` from Homebrew if you contribute on macOS). Use `set -euo pipefail`.
- **Python**: 3.11+, type hints encouraged.
- **TypeScript** (MCP servers): strict mode, no `any`. Match the existing tsconfig.
- **Markdown**: prefer line breaks every ~100 chars but don't enforce. Use GitHub-flavored markdown.

## What's out of scope for this repo

- **Branding for non-NBG companies**: this marketplace is shaped for NBG (Aptos font, NBG colours, Greek-language defaults in mail). Forking is welcome; PRs to make it brand-agnostic are not on the v1 roadmap.
- **Adding more bundled MCP servers**: each bundled MCP increases install complexity. New plugins should prefer the `Skill(...)` pattern over bundling new servers unless absolutely necessary.

## License

By contributing you agree that your contributions are licensed under the same MIT license as the rest of the repository.
