#!/usr/bin/env bash
set -uo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

INSTALL_DIR="$HOME/.claude/plugins/marketplaces/plessas-marketplace"
PASS=0
TOTAL=0

check() {
  local label="$1"
  local result="$2"
  TOTAL=$((TOTAL+1))
  if [ "$result" = "ok" ]; then
    printf "${GREEN}[OK]${NC}   %s\n" "$label"
    PASS=$((PASS+1))
  elif [ "$result" = "warn" ]; then
    printf "${YELLOW}[--]${NC}   %s\n" "$label"
  else
    printf "${RED}[!!]${NC}   %s\n" "$label"
  fi
}

echo "========================================"
echo "  plessas-marketplace status"
echo "========================================"
echo

# Marketplace installed?
[ -d "$INSTALL_DIR/.claude-plugin" ] && check "Marketplace installed" "ok" || check "Marketplace NOT installed" "fail"

# Plugins present?
for plugin in decks mail meetings chat excel docs; do
  if [ -f "$INSTALL_DIR/plugins/$plugin/.claude-plugin/plugin.json" ]; then
    check "Plugin: $plugin" "ok"
  else
    check "Plugin: $plugin — MISSING" "fail"
  fi
done

echo

# MCP servers built?
[ -f "$INSTALL_DIR/plugins/mail/mcp-server/dist/server.js" ] && check "outlook-bridge MCP built" "ok" || check "outlook-bridge MCP NOT built" "fail"
[ -f "$INSTALL_DIR/plugins/chat/mcp-server/dist/server.js" ] && check "teams-bridge MCP built" "ok" || check "teams-bridge MCP NOT built" "fail"

echo

# CLIs available?
command -v outlook-cli >/dev/null 2>&1 && check "outlook-cli available" "ok" || check "outlook-cli NOT available" "fail"
command -v teams-cli >/dev/null 2>&1 && check "teams-cli available" "ok" || check "teams-cli NOT available" "fail"

echo

# Auth status
if command -v outlook-cli >/dev/null 2>&1; then
  outlook-cli auth-check >/dev/null 2>&1 && check "Outlook auth valid" "ok" || check "Outlook auth EXPIRED" "fail"
else
  check "Outlook auth — CLI not installed" "warn"
fi

if command -v teams-cli >/dev/null 2>&1; then
  teams-cli auth-check >/dev/null 2>&1 && check "Teams auth valid" "ok" || check "Teams auth EXPIRED" "fail"
else
  check "Teams auth — CLI not installed" "warn"
fi

# Signature
[ -f "$HOME/.outlook-cli/signature.html" ] && check "Email signature exists" "ok" || check "Email signature MISSING" "warn"

# CLAUDE.md
[ -f "$HOME/.claude/CLAUDE.md" ] && check "CLAUDE.md exists" "ok" || check "CLAUDE.md MISSING" "warn"

echo
echo "========================================"
echo "  $PASS / $TOTAL checks passed"
echo "========================================"
