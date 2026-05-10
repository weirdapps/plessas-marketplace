## What this PR does

## Why

## Plugins / files touched

e.g. `mail`, `decks/agents/storyline-architect.md`

## Checklist

- [ ] CI guards pass locally (`bash installers/pii-gauntlet.sh --mode=ci` and the `rename-guard` patterns)
- [ ] If a new command was added: `allowed-tools` is declared in the frontmatter
- [ ] If a command was renamed: the old name is added to the rename-guard regex (or a follow-up issue is opened to do so)
- [ ] If user-facing text or docs changed: no personal names, emails, phone numbers, or NBG-internal terms (the PII gauntlet enforces this — run it)
- [ ] If a new MCP server was added: built `dist/` is gitignored, install.sh builds it on install
