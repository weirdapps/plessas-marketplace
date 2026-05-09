#!/usr/bin/env bash
# Auto-build and run the teams-bridge MCP server.
# Installs npm deps and compiles TypeScript on first run.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$DIR/node_modules" ]; then
  echo "teams-bridge: installing npm dependencies..." >&2
  (cd "$DIR" && npm install --silent) >&2
fi

if [ ! -f "$DIR/dist/server.js" ]; then
  echo "teams-bridge: building MCP server..." >&2
  (cd "$DIR" && npm run build --silent) >&2
fi

exec node "$DIR/dist/server.js"
