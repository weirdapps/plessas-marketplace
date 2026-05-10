# Security Policy

## Reporting a vulnerability

If you discover a security issue in this marketplace or any of the bundled plugins, **do not open a public issue**. Instead:

1. Go to the **Security** tab of this repository: <https://github.com/weirdapps/plessas-marketplace/security/advisories>
2. Click **"Report a vulnerability"**

GitHub manages the disclosure flow privately — only the maintainers see the report until a fix is published. We aim to acknowledge new reports within 5 business days.

## Scope

In scope:

- The marketplace plugins themselves (`decks`, `mail`, `mail-pro`, `meetings`, `chat`, `excel`, `docs`)
- The bundled MCP servers (`outlook-bridge`, `teams-bridge`)
- The installer scripts (`installers/install.{sh,ps1}`, `installers/auth-wizard.{sh,ps1}`, `installers/pii-gauntlet.sh`)

Out of scope:

- Vulnerabilities in upstream dependencies (`outlook-cli`, `teams-cli`, `second-brain`) — please report those in their own repositories
- Vulnerabilities in Claude Code itself — report at <https://github.com/anthropics/claude-code/issues>

## Sensitive data the marketplace handles

The plugins access the user's Microsoft 365 account (mail, calendar, Teams) via personal-tenant credentials cached in `~/.outlook-cli/` and `~/.teams-cli/`. They do **not** transmit this data anywhere outside the user's machine and the user's own M365 tenant. Reports about credential storage, token caching, or unintended exfiltration are particularly welcome.
