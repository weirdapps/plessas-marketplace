#!/usr/bin/env bash
# Auto-build and run the outlook-bridge MCP server.
# Resilient to PATH stripping (launchd, GUI launches, fnm shell rotation): walks
# known node install locations rather than relying on PATH lookup.
# Writes .last-startup.json on every start (consumed by the doctor tool).
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
STATUS_FILE="$DIR/.last-startup.json"

write_status() {
  local status="$1"
  local error="$2"
  printf '{"ts":"%s","status":"%s","error":%s,"node":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "$status" \
    "${error:-null}" \
    "${NODE_BIN:-unknown}" \
    > "$STATUS_FILE" 2>/dev/null || true
}

find_node() {
  if command -v node >/dev/null 2>&1; then command -v node; return 0; fi
  for c in /opt/homebrew/bin/node /usr/local/bin/node /usr/bin/node; do
    [ -x "$c" ] && { echo "$c"; return 0; }
  done
  local fnm_root="$HOME/.local/share/fnm/node-versions"
  if [ -d "$fnm_root" ]; then
    local latest
    latest=$(ls -t "$fnm_root" 2>/dev/null | head -1)
    [ -n "$latest" ] && [ -x "$fnm_root/$latest/installation/bin/node" ] && \
      { echo "$fnm_root/$latest/installation/bin/node"; return 0; }
  fi
  local nvm_root="$HOME/.nvm/versions/node"
  if [ -d "$nvm_root" ]; then
    local latest
    latest=$(ls -t "$nvm_root" 2>/dev/null | head -1)
    [ -n "$latest" ] && [ -x "$nvm_root/$latest/bin/node" ] && \
      { echo "$nvm_root/$latest/bin/node"; return 0; }
  fi
  return 1
}

NODE_BIN="$(find_node)" || {
  write_status "fail" '"node binary not found in PATH, /opt/homebrew, /usr/local, fnm, or nvm. Install Node.js v20+ from https://nodejs.org/"'
  echo "outlook-bridge: FATAL: node binary not found. Install Node.js v20+ from https://nodejs.org/" >&2
  exit 1
}
NPM_BIN="$(dirname "$NODE_BIN")/npm"

if [ ! -d "$DIR/node_modules" ]; then
  export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
  echo "outlook-bridge: installing npm dependencies (first run, ~30-60s)..." >&2
  if [ -f "$DIR/package-lock.json" ]; then
    if ! (cd "$DIR" && "$NPM_BIN" ci --silent) >&2; then
      write_status "fail" '"npm ci failed — check network and ~/.npm logs"'
      exit 1
    fi
  else
    if ! (cd "$DIR" && "$NPM_BIN" install --silent) >&2; then
      write_status "fail" '"npm install failed — check network and ~/.npm logs"'
      exit 1
    fi
  fi
fi

if [ ! -f "$DIR/dist/server.js" ]; then
  echo "outlook-bridge: building MCP server..." >&2
  if ! (cd "$DIR" && "$NPM_BIN" run build --silent) >&2; then
    write_status "fail" '"npm run build failed — see stderr"'
    exit 1
  fi
fi

write_status "ok" "null"
exec "$NODE_BIN" "$DIR/dist/server.js"
