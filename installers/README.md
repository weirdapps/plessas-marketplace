# Installers

This directory contains installation scripts for the plessas-marketplace plugins.

## Updating bundled CLIs

`outlook-cli` and `teams-cli` are pinned to specific commits in the MCP `package.json` files. To pull a newer version:

1. Get the new SHA from the upstream repo:

   ```bash
   git ls-remote https://github.com/weirdapps/outlook-access.git refs/heads/master | awk '{print $1}'
   ```

2. Update the pin in `plugins/mail/mcp-server/package.json`:

   ```json
   "outlook-tool": "github:weirdapps/outlook-access#<NEW_SHA>"
   ```

3. Rebuild + relock:

   ```bash
   cd plugins/mail/mcp-server
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

4. Commit the package.json + package-lock.json changes.

Same flow for `teams-cli` in `plugins/chat/mcp-server/package.json` against the `weirdapps/teams-access` repo.
