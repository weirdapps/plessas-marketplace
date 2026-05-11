# Installers

This directory contains installation scripts for the plessas-marketplace plugins.

## Updating bundled CLIs

`outlook-cli` and `teams-cli` are pinned to specific commits in the MCP `package.json` files via `git+https://x@github.com/.../<repo>.git#<SHA>` (the `x@` is a workaround for [npm/cli#2610](https://github.com/npm/cli/issues/2610) — without the fake username, npm rewrites the lockfile URL to `git+ssh://`, which fails for teammates without GitHub SSH keys).

To pull a newer version:

1. Get the new SHA from the upstream repo:

   ```bash
   git ls-remote https://github.com/weirdapps/outlook-access.git refs/heads/master | awk '{print $1}'
   ```

2. Update the pin in `plugins/mail/mcp-server/package.json`:

   ```json
   "outlook-tool": "git+https://x@github.com/weirdapps/outlook-access.git#<NEW_SHA>"
   ```

3. Rebuild + relock:

   ```bash
   cd plugins/mail/mcp-server
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

4. Verify the lockfile recorded `git+https://x@github.com/...` (NOT `git+ssh://`):

   ```bash
   cat package-lock.json | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['packages']['node_modules/outlook-tool']['resolved'])"
   ```

5. Commit the package.json + package-lock.json changes.

Same flow for `teams-cli` in `plugins/chat/mcp-server/package.json` against the `weirdapps/teams-access` repo.

### Why the `x@` username?

npm's arborist normalizes hosted-git URLs (GitHub, GitLab, BitBucket) to `git+ssh://` in the `resolved` lockfile field — even when `package.json` explicitly says `https`. This is a known npm bug. Including any username in the URL (`x@`, `anything@`, etc.) bypasses this normalization. The username is meaningless for public repos but tells npm to preserve the URL as-is. See [npm/cli#2610](https://github.com/npm/cli/issues/2610) for context.
