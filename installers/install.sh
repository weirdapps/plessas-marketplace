#!/usr/bin/env bash
set -euo pipefail

# plessas-marketplace installer (macOS / Linux)
# Usage: curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/main/installers/install.sh | bash

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

if command -v python3 >/dev/null 2>&1; then
  ok "Python3 $(python3 --version 2>&1 | cut -d' ' -f2) (for decks plugin)"
else
  warn "Python3 not found. decks plugin requires it. Install: https://www.python.org/downloads/"
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

# --- Install Python deps for decks ---
if command -v python3 >/dev/null 2>&1 && [ -f "plugins/decks/tools/nbg-presentation/requirements.txt" ]; then
  echo
  echo "Installing Python dependencies for decks..."
  VENV_DIR="plugins/decks/tools/nbg-presentation/.venv"
  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
  fi
  "$VENV_DIR/bin/pip" install -q -r "plugins/decks/tools/nbg-presentation/requirements.txt" 2>&1 | tail -3
  ok "decks Python deps installed"
fi

if [ -f "plugins/decks/bundled/creative/tools/device-mockup/requirements.txt" ]; then
  VENV_DIR="plugins/decks/bundled/creative/tools/device-mockup/.venv"
  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
  fi
  "$VENV_DIR/bin/pip" install -q -r "plugins/decks/bundled/creative/tools/device-mockup/requirements.txt" 2>&1 | tail -3
  ok "device-mockup Python deps installed"
fi

# --- Install outlook-cli and teams-cli if not available ---
echo
if ! command -v outlook-cli >/dev/null 2>&1; then
  warn "outlook-cli not found. Mail plugin requires it."
  echo "  Install: git clone https://github.com/weirdapps/outlook-access.git && cd outlook-access && npm install && npm run build && npm link"
else
  ok "outlook-cli found"
fi

if ! command -v teams-cli >/dev/null 2>&1; then
  warn "teams-cli not found. Chat plugin requires it."
  echo "  Install: git clone https://github.com/weirdapps/teams-access.git && cd teams-access && npm install && npm run build && npm link"
else
  ok "teams-cli found"
fi

# --- Drop CLAUDE.md template ---
echo
if [ ! -f "$CLAUDE_MD" ]; then
  echo "No existing ~/.claude/CLAUDE.md found. Installing team template..."
  mkdir -p "$(dirname "$CLAUDE_MD")"
  cp "$INSTALL_DIR/shared/claude-md-template/team-claude-md.md" "$CLAUDE_MD"
  ok "Team CLAUDE.md installed at $CLAUDE_MD"
  echo "  Please edit it and replace the << REPLACE >> sections with your details."
else
  ok "Existing CLAUDE.md found — not overwriting. See $INSTALL_DIR/shared/claude-md-template/team-claude-md.md for the team template."
fi

# --- Done ---
echo
echo "========================================"
printf "${GREEN}  Installation complete!${NC}\n"
echo "========================================"
echo
echo "Next steps:"
echo "  1. Run the auth wizard:  $INSTALL_DIR/installers/auth-wizard.sh"
echo "  2. Check status:         $INSTALL_DIR/installers/status.sh"
echo "  3. Open Claude Code and try: /mail-briefing"
echo
echo "Documentation: $INSTALL_DIR/docs/"
echo "Day-one guide: $INSTALL_DIR/docs/day-one.md"
