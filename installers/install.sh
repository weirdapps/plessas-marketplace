#!/usr/bin/env bash
set -euo pipefail

# plessas-marketplace installer (macOS / Linux)
# Usage: curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.sh | bash

REPO_URL="https://github.com/weirdapps/plessas-marketplace.git"
INSTALL_DIR="$HOME/.claude/plugins/marketplaces/plessas-marketplace"
CLAUDE_MD="$HOME/.claude/CLAUDE.md"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { printf "${GREEN}[OK]${NC}   %s\n" "$1"; }
warn() { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
fail() { printf "${RED}[FAIL]${NC} %s\n" "$1"; exit 1; }

echo "========================================"
echo "  plessas-marketplace installer"
echo "========================================"
echo

# --- Prerequisites ---
echo "Checking prerequisites..."

command -v git >/dev/null 2>&1 || fail "git not found. Install: https://git-scm.com/downloads"
ok "git $(git --version | cut -d' ' -f3)"

command -v node >/dev/null 2>&1 || fail "Node.js not found. Install: https://nodejs.org/ (v20+)"
NODE_VER=$(node --version | sed 's/v//' | cut -d. -f1)
[ "$NODE_VER" -ge 20 ] || fail "Node.js $NODE_VER found, need 20+. Update: https://nodejs.org/"
ok "Node.js $(node --version)"

# npm is not optional: every MCP build and every CLI link below shells out to
# it. It does not always ship alongside node (corporate images and some distro
# packages split them), and without this check the first `npm install` dies
# with a bare "command not found" rather than something a user can act on.
command -v npm >/dev/null 2>&1 || fail "npm not found (node is present but npm is not). Install Node.js from https://nodejs.org/, which bundles npm."
ok "npm $(npm --version)"

# Python is optional -- this installer must finish without it -- but when it IS
# present the VERSION matters. numpy >= 2.5.2, the floor in both
# plugins/decks/tools/nbg-keynote/requirements.txt and
# plugins/decks/bundled/creative/tools/device-mockup/requirements.txt, itself
# declares requires-python >= 3.12. On 3.11 or older `pip install -r` cannot
# resolve, and under `set -euo pipefail` that aborted the whole installer two
# thirds of the way through -- before the CLIs and the CLAUDE.md template -- on
# the strength of a dependency this same script calls optional. Check
# major.minor the way the Node check above does, and record the verdict.
PYTHON_OK=0
if command -v python3 >/dev/null 2>&1; then
  PY_VER=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)
  case "$PY_VER" in ''|*[!0-9.]*) PY_VER="0.0" ;; esac
  PY_MAJOR=${PY_VER%%.*}
  PY_MINOR=${PY_VER##*.}
  if [ "$PY_MAJOR" -gt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 12 ]; }; then
    PYTHON_OK=1
    ok "Python $PY_VER (for decks plugin)"
  else
    warn "Python $PY_VER found, the decks Python tools need 3.12+. /create-presentation, /create-keynote and device-mockup will be skipped; the rest installs normally. Update: https://www.python.org/downloads/"
  fi
else
  warn "Python3 not found. The decks Python tools need 3.12+. Install: https://www.python.org/downloads/"
fi

command -v claude >/dev/null 2>&1 || fail "Claude Code not found. Install: https://claude.ai/claude-code"
ok "Claude Code found"

echo

# --- Clone or update ---
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Marketplace already installed. Updating..."
  cd "$INSTALL_DIR"
  git pull --ff-only 2>&1 | tail -3
  ok "Updated to latest"
else
  echo "Cloning plessas-marketplace..."
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone "$REPO_URL" "$INSTALL_DIR" 2>&1 | tail -3
  ok "Cloned to $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# --- Build MCP servers ---
echo
echo "Building MCP servers..."

if [ -d "plugins/mail/mcp-server" ]; then
  echo "  Building outlook-bridge MCP..."
  (cd plugins/mail/mcp-server && npm install --silent && npm run build --silent) 2>&1 | tail -2
  ok "outlook-bridge MCP built"
fi

if [ -d "plugins/chat/mcp-server" ]; then
  echo "  Building teams-bridge MCP..."
  (cd plugins/chat/mcp-server && npm install --silent && npm run build --silent) 2>&1 | tail -2
  ok "teams-bridge MCP built"
fi

# --- Warm the plugin cache, which is the tree Claude Code actually executes ---
#
# The builds above warm THIS clone. Claude Code does not run plugins from here:
# it runs them from ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/.
# The copy it makes at `/plugin install` time contains exactly the git-tracked
# files, and mcp-server/dist and node_modules are BOTH gitignored, so nothing
# built above can ever reach the tree that runs. The first real MCP call then
# pays run.sh's `npm ci` plus build, which is the 30-to-60-second first-call
# stall that can blow Claude Code's MCP startup handshake.
#
# The cache directory does not exist until `/plugin install` has run, so on a
# genuine first install this loop finds nothing and says so. Re-run the
# installer after installing the plugins and it warms them. Worth doing once:
# the cache is keyed by plugin VERSION, not by marketplace commit, so a warmed
# build survives every subsequent `git pull` until the next version bump.
CACHE_DIR="$HOME/.claude/plugins/cache/plessas-marketplace"
echo
echo "Warming the plugin cache (the tree Claude Code actually executes)..."
# FOUND counts plugins present in the cache; WARMED counts those now built.
# They differ when a build fails, and conflating them made a build error print
# the "run /plugin install first" advice on top of it, pointing at the wrong fix.
FOUND=0
WARMED=0
if [ -d "$CACHE_DIR" ]; then
  for mcp_dir in "$CACHE_DIR"/*/*/mcp-server; do
    [ -d "$mcp_dir" ] || continue
    [ -f "$mcp_dir/package.json" ] || continue
    plugin_name=$(basename "$(dirname "$(dirname "$mcp_dir")")")
    FOUND=$((FOUND + 1))
    if [ -f "$mcp_dir/dist/server.js" ] && [ -d "$mcp_dir/node_modules" ]; then
      ok "$plugin_name MCP already warm in the cache"
      WARMED=$((WARMED + 1))
      continue
    fi
    echo "  Building $plugin_name MCP in the cache..."
    if (cd "$mcp_dir" && npm install --silent && npm run build --silent) 2>&1 | tail -2; then
      ok "$plugin_name MCP built in the cache"
      WARMED=$((WARMED + 1))
    else
      warn "$plugin_name MCP failed to build in the cache. Its first call will rebuild and may stall 30-60s."
    fi
  done
fi
if [ "$FOUND" -eq 0 ]; then
  warn "No installed plugins in the cache yet. Expected on a first install: do the /plugin steps printed at the end, then re-run this installer. Skipping it only costs a 30-60s stall on each bundled MCP's first call."
fi

# --- Install Python deps for decks ---
# One virtualenv per tool, because each ships its own requirements.txt with a
# different dependency set. nbg-keynote had no block at all, so /create-keynote
# -- a shipped, advertised command -- died with ModuleNotFoundError on its first
# line after a "successful" install.
#
# Every failure in here warns and continues. The old device-mockup block ran a
# bare `python3 -m venv` with no guard, so under `set -euo pipefail` a missing
# or too-old python3 took the whole installer down before the CLIs and the
# CLAUDE.md template at the bottom of this script, leaving a half-installed
# state, on the strength of a dependency the prerequisite check above calls
# optional. pip is on
# the same footing: a resolver failure or a dead network must cost you the
# decks Python tools, not the install.
install_python_tool() {
  local label="$1"      # e.g. nbg-keynote
  local tool_dir="$2"   # holds requirements.txt, receives .venv
  local disables="$3"   # what the user loses if this one fails
  local req="$tool_dir/requirements.txt"
  local venv_dir="$tool_dir/.venv"

  [ -f "$req" ] || return 0

  if [ ! -d "$venv_dir" ] && ! python3 -m venv "$venv_dir"; then
    warn "python3 -m venv failed for $label - $disables. On Debian/Ubuntu: apt install python3-venv"
    return 0
  fi
  if "$venv_dir/bin/pip" install -q -r "$req" 2>&1 | tail -3; then
    ok "$label Python deps installed"
  else
    warn "pip install failed for $label - $disables. Output above."
  fi
}

if [ "$PYTHON_OK" -eq 1 ]; then
  echo
  echo "Installing Python dependencies for decks..."
  install_python_tool "nbg-presentation" "plugins/decks/tools/nbg-presentation" \
    "/create-presentation and /redesign-deck cannot build a PPTX"
  install_python_tool "nbg-keynote" "plugins/decks/tools/nbg-keynote" \
    "/create-keynote cannot run"
  install_python_tool "device-mockup" "plugins/decks/bundled/creative/tools/device-mockup" \
    "the device-mockup tool cannot render screenshots"
else
  echo
  warn "Skipping the decks Python virtualenvs (see the Python line above). /create-presentation, /create-keynote and device-mockup stay unavailable; everything else installs normally."
fi

# --- Install outlook-cli and teams-cli ---
# Both CLIs live in their own repos (weirdapps/outlook-access, weirdapps/teams-access).
# We clone them into installers/deps/ inside the marketplace, build, and `npm link`
# so `outlook-cli` and `teams-cli` are available on PATH.
echo
echo "Installing required CLIs (outlook-cli, teams-cli)..."

DEPS_DIR="$INSTALL_DIR/installers/deps"
mkdir -p "$DEPS_DIR"

install_cli_from_repo() {
  local repo_name="$1"   # e.g. outlook-access
  local cli_name="$2"    # e.g. outlook-cli
  local repo_url="https://github.com/weirdapps/${repo_name}.git"
  local target="$DEPS_DIR/$repo_name"

  # If the CLI is already on PATH AND we don't manage it (no clone in deps/),
  # respect the existing install and skip.
  if command -v "$cli_name" >/dev/null 2>&1 && [ ! -d "$target/.git" ]; then
    ok "$cli_name already on PATH (not managed by this installer), skipping"
    return 0
  fi

  # Otherwise: clone fresh OR update our managed clone, then build + link.
  if [ -d "$target/.git" ]; then
    echo "  Updating $repo_name..."
    (cd "$target" && git pull --ff-only 2>&1 | tail -2)
  else
    echo "  Cloning $repo_name..."
    git clone --depth 1 "$repo_url" "$target" 2>&1 | tail -2
  fi

  echo "  Building $cli_name..."
  (cd "$target" && npm install --silent 2>&1 | tail -3 && npm run build --silent 2>&1 | tail -2)

  echo "  Linking $cli_name globally (npm link)..."
  if (cd "$target" && npm link --silent 2>&1 | tail -2); then
    if command -v "$cli_name" >/dev/null 2>&1; then
      ok "$cli_name installed and linked"
    else
      warn "$cli_name built but not on PATH. Add $(npm prefix -g)/bin to PATH."
    fi
  else
    warn "npm link failed for $cli_name. On systems with global npm in /usr/local, try: cd $target && sudo npm link"
  fi
}

install_cli_from_repo outlook-access outlook-cli
install_cli_from_repo teams-access teams-cli

# --- Drop CLAUDE.md template ---
echo
if [ ! -f "$CLAUDE_MD" ]; then
  echo "No existing ~/.claude/CLAUDE.md found. Installing team template..."
  mkdir -p "$(dirname "$CLAUDE_MD")"
  cp "$INSTALL_DIR/shared/claude-md-template/team-claude-md.md" "$CLAUDE_MD"
  ok "Team CLAUDE.md installed at $CLAUDE_MD"
  echo "  Please edit it and replace the << REPLACE >> sections with your details."
else
  ok "Existing CLAUDE.md found, not overwriting. See $INSTALL_DIR/shared/claude-md-template/team-claude-md.md for the team template."
fi

# --- Done ---
echo
echo "========================================"
printf "${GREEN}  Installation complete!${NC}\n"
echo "========================================"
echo
echo "Next steps (preferred, runs inside Claude Code):"
echo "  1. /plugin marketplace add weirdapps/plessas-marketplace"
echo "  2. /plugin install mail@plessas-marketplace   (and chat, decks, meetings, excel, docs as desired)"
echo "  3. Re-run this installer once. Claude Code executes plugins from"
echo "     ~/.claude/plugins/cache/, not from this clone, and that cache does not"
echo "     exist until step 2. Re-running prebuilds the bundled MCP servers there;"
echo "     skipping it costs a 30-60s stall on each one's first call."
echo "  4. /mail:auth-setup                            (and /chat:auth-setup if chat is installed)"
echo "  5. Try /inbox-briefing"
echo
echo "Legacy alternative (deprecated, still works):"
echo "  $INSTALL_DIR/installers/auth-wizard.sh"
echo "  $INSTALL_DIR/installers/status.sh"
echo
echo "Documentation: $INSTALL_DIR/docs/"
echo "Day-one guide: $INSTALL_DIR/docs/day-one.md"
