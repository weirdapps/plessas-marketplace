#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { printf "${GREEN}[OK]${NC}   %s\n" "$1"; }
warn() { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
fail() { printf "${RED}[FAIL]${NC} %s\n" "$1"; }

echo "========================================"
echo "  plessas-marketplace auth wizard"
echo "========================================"
echo
echo "This will authenticate outlook-cli and teams-cli."
echo "Each step opens a browser window for M365 sign-in."
echo

# --- Step 1: Outlook ---
echo "--- Step 1/3: Outlook (outlook-cli login) ---"
if command -v outlook-cli >/dev/null 2>&1; then
  if outlook-cli auth-check >/dev/null 2>&1; then
    ok "outlook-cli already authenticated"
  else
    echo "Opening browser for Outlook sign-in..."
    outlook-cli login --sharepoint-host groupnbg.sharepoint.com || warn "outlook-cli login failed or was cancelled"
    if outlook-cli auth-check >/dev/null 2>&1; then
      ok "outlook-cli authenticated"
    else
      fail "outlook-cli auth check failed after login"
    fi
  fi
else
  warn "outlook-cli not installed — skipping. Install it first, then re-run."
fi

echo

# --- Step 2: Teams ---
echo "--- Step 2/3: Teams (teams-cli login) ---"
if command -v teams-cli >/dev/null 2>&1; then
  if teams-cli auth-check >/dev/null 2>&1; then
    ok "teams-cli already authenticated"
  else
    echo "Opening browser for Teams sign-in..."
    teams-cli login || warn "teams-cli login failed or was cancelled"
    if teams-cli auth-check >/dev/null 2>&1; then
      ok "teams-cli authenticated"
    else
      fail "teams-cli auth check failed after login"
    fi
  fi
else
  warn "teams-cli not installed — skipping. Install it first, then re-run."
fi

echo

# --- Step 3: Signature ---
echo "--- Step 3/3: Email signature capture ---"
if command -v outlook-cli >/dev/null 2>&1 && outlook-cli auth-check >/dev/null 2>&1; then
  if [ -f "$HOME/.outlook-cli/signature.html" ]; then
    ok "Signature already exists at ~/.outlook-cli/signature.html"
  else
    echo "Capturing signature from your latest sent email..."
    outlook-cli capture-signature 2>/dev/null && ok "Signature captured" || warn "Signature capture failed — you can set it up manually later"
  fi
else
  warn "Skipping signature capture — outlook-cli not authenticated"
fi

echo
echo "========================================"
printf "${GREEN}  Auth wizard complete!${NC}\n"
echo "========================================"
echo
echo "Check overall status: $(dirname "$0")/status.sh"
