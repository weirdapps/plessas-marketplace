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

# Enforce the package.json engines floor. find_node prefers whatever `command -v
# node` returns and otherwise takes the newest fnm/nvm dir by mtime, either of
# which can be a Node 18. Without this check the server fails later with an
# obscure syntax or API error instead of here.
NODE_VERSION="$("$NODE_BIN" -v 2>/dev/null || true)"
NODE_MAJOR="${NODE_VERSION#v}"
NODE_MAJOR="${NODE_MAJOR%%.*}"
case "$NODE_MAJOR" in ''|*[!0-9]*) NODE_MAJOR=0 ;; esac
if [ "$NODE_MAJOR" -lt 20 ]; then
  # write_status interpolates its argument raw into JSON: strip quotes/newlines.
  BAD_NODE="$(printf '%s at %s' "${NODE_VERSION:-unknown}" "$NODE_BIN" | tr -d '\\"\n\r')"
  write_status "fail" "\"node $BAD_NODE is below the required v20. Install Node.js v20+ from https://nodejs.org/\""
  echo "outlook-bridge: FATAL: node $BAD_NODE is below the required v20. Install Node.js v20+ from https://nodejs.org/" >&2
  exit 1
fi

# Prefer the committed single-file bundle. esbuild inlines the only npm package
# either server imports at runtime (@modelcontextprotocol/sdk); everything else
# it touches is a Node builtin, and the CLI is spawned as a subprocess rather
# than imported. So this path needs no node_modules and no build step: measured
# cold, with node_modules renamed away, it serves `initialize` in well under a
# second, against the 15.5s `npm ci` the fallback below has to demand of the
# user first. Rebuild it with `npm run build:bundle`; CI reruns that build and
# compares the bytes (see the bundle-drift job in .github/workflows/lint.yml),
# so an edit to src/ that is not rebuilt fails there rather than shipping.
BUNDLE="$DIR/bundle/server.mjs"
if [ -f "$BUNDLE" ]; then
  write_status "ok" "null"
  exec "$NODE_BIN" "$BUNDLE"
fi

NPM_BIN="$(dirname "$NODE_BIN")/npm"
# Prefer a bare `npm` in the printed command when it is on the user's PATH; fall
# back to the absolute path we resolved, which always works.
if command -v npm >/dev/null 2>&1; then NPM_SHOW="npm"; else NPM_SHOW="$NPM_BIN"; fi
INSTALL_CMD="npm ci"
[ -f "$DIR/package-lock.json" ] || INSTALL_CMD="npm install"
# write_status interpolates its argument raw into JSON: strip quotes/newlines.
SAFE_DIR="$(printf '%s' "$DIR" | tr -d '\\"\n\r')"

# Fail fast rather than installing or building inside the MCP startup handshake.
# `npm ci` here costs ~15s with a warm npm cache and 30-60s cold, which overruns
# Claude Code's 30s MCP startup timeout: the server then appears to hang and
# never start, with nothing saying why. One legible error the user can act on
# beats a silent timeout. The two cases are kept apart because their remedies
# and their costs differ.
if [ ! -d "$DIR/node_modules" ]; then
  write_status "fail" "\"dependencies not installed. Run: cd $SAFE_DIR && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 $INSTALL_CMD && npm run build\""
  {
    echo "outlook-bridge: FATAL: bundle/server.mjs is missing AND dependencies are not installed, so the server cannot start."
    echo "  bundle/server.mjs is committed to the repo, so a checkout normally has it."
    echo "  Run this once (takes 30-60s), then restart Claude Code:"
    echo ""
    echo "    cd \"$DIR\" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 $NPM_SHOW ${INSTALL_CMD#npm } && $NPM_SHOW run build"
    echo ""
  } >&2
  exit 1
fi

if [ ! -f "$DIR/dist/server.js" ]; then
  write_status "fail" "\"server not built. Run: cd $SAFE_DIR && npm run build\""
  {
    echo "outlook-bridge: FATAL: bundle/server.mjs is missing and dist/ is not built, so there is nothing to run."
    echo "  Dependencies are present, so this is quick. Run it, then restart Claude Code:"
    echo ""
    echo "    cd \"$DIR\" && $NPM_SHOW run build"
    echo ""
  } >&2
  exit 1
fi

write_status "ok" "null"
exec "$NODE_BIN" "$DIR/dist/server.js"
