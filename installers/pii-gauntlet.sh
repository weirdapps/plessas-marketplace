#!/usr/bin/env bash
# pii-gauntlet.sh — verify no PII leaked into plessas-marketplace before any public push
# Run from anywhere; will cd to the repo root.
# Exit 0 = clean. Non-zero = PII detected, see output for details.
#
# Self-exclusion: this script contains the very patterns it searches for, so
# `--exclude=pii-gauntlet.sh` is essential to avoid self-match false positives.

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== PII Gauntlet ==="
echo "Repo: $REPO_ROOT"
echo

FAIL=0

check() {
  local label="$1"
  local pattern="$2"
  local hits
  hits=$(grep -riE \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=dist \
    --exclude-dir=__pycache__ \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    --exclude=pii-gauntlet.sh \
    --exclude=PII-GAUNTLET.md \
    --binary-files=without-match \
    "$pattern" . 2>/dev/null || true)
  if [ -n "$hits" ]; then
    echo "FAIL [$label]:"
    echo "$hits" | head -20
    echo
    FAIL=1
  else
    echo "OK   [$label]"
  fi
}

# Personal name (full forms — single-word "plessas" is the brand name, OK)
check "Full personal name (EN)" "Dimitris[[:space:]]+Plessas|Dimitrios[[:space:]]+Plessas"
check "Full personal name (GR)" "Δημήτριος[[:space:]]+Πλέσσας|ΠΛΕΣΣΑΣ[[:space:]]+ΔΗΜΗΤΡΙΟΣ"

# Personal emails
check "Personal email" "dimitrios\.plessas@|plessasdimitrios@|plessas@nbg\.gr|plessas@gmail|plessas@yahoo"

# Personal phone / address
check "Personal phone" "694[[:space:]]?9200878|6949200878"
check "Personal address" "174[[:space:]]+Syggrou|Συγγρού[[:space:]]+174"

# Greek tax IDs (9-digit standalone, with word boundaries)
check "9-digit ID pattern" "[^0-9][0-9]{9}[^0-9]"

# Peer names (NBG colleagues / direct reports / managers)
check "Peer/colleague names" "Volioti|Bitrou|Sioutis|Theofilidi|Lygeros|Oikonomou|Maraveas|Xona|Petropoulou|Laspas|Koutra|Giemelou"

# Family names
check "Family names" "Kitrilaki|Κιτριλάκη"

# NBG-internal project names (case-insensitive but anchored)
check "Internal projects" "Διπλή κάρτα|\bdual[- ]card\b|IRIS[[:space:]]+pilot|ECB[[:space:]]+Digital[[:space:]]+Euro[[:space:]]+CfEI"

# External partners discussed in NBG-internal context (McKinsey excluded — Pyramid Principle / SCQA are public methodology references)
check "Partner names" "\bWorldline\b|\bHelvia\b|\bWealthyhood\b|\bFeedzai\b|\bMellon\b|\b11FS\b|\bNCR\b"

# Tax authority refs
check "Tax authority" "ΑΑΔΕ|ΑΦΜ|ΑΔΤ|ΑΜΚΑ"

# Personal source paths (specific to user's machine)
check "User-specific paths" "/Users/plessas|/SourceCode/claude-config|claude-config/shared-memory"

echo
if [ $FAIL -eq 0 ]; then
  echo "=== GAUNTLET PASS ==="
  exit 0
else
  echo "=== GAUNTLET FAIL ==="
  echo "Fix the PII leaks above before any public push."
  exit 1
fi
