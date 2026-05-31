#!/usr/bin/env bash
#
# sync_brand_system.sh — keep the two NBG brand-system trees identical.
#
# CANONICAL (edit here):  plugins/decks/shared/brand-system/
# MIRROR   (auto-synced): shared/brand-system/      <-- do NOT hand-edit
#
# Usage:
#   scripts/sync_brand_system.sh            # --apply (default): copy canonical .md -> mirror
#   scripts/sync_brand_system.sh --check    # exit 1 if the trees differ (CI / pre-commit guard)
#
set -euo pipefail
shopt -s nullglob
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CANON="$ROOT/plugins/decks/shared/brand-system"
MIRROR="$ROOT/shared/brand-system"
MODE="${1:---apply}"

[ -d "$CANON" ] || { echo "canonical tree missing: $CANON" >&2; exit 2; }
mkdir -p "$MIRROR"

if [ "$MODE" = "--check" ]; then
  drift=0
  for f in "$CANON"/*.md; do
    n="$(basename "$f")"
    cmp -s "$f" "$MIRROR/$n" || { echo "DRIFT: $n differs or missing in mirror"; drift=1; }
  done
  for f in "$MIRROR"/*.md; do
    n="$(basename "$f")"
    [ -f "$CANON/$n" ] || { echo "DRIFT: $n present in mirror but not canonical"; drift=1; }
  done
  if [ "$drift" = 0 ]; then
    echo "✓ brand-system trees in sync"
  else
    echo "✗ brand-system drift — run: scripts/sync_brand_system.sh --apply" >&2
    exit 1
  fi
else
  count=0
  for f in "$CANON"/*.md; do cp "$f" "$MIRROR/$(basename "$f")"; count=$((count+1)); done
  for f in "$MIRROR"/*.md; do
    n="$(basename "$f")"
    [ -f "$CANON/$n" ] || rm -f "$f"
  done
  echo "✓ mirrored $count files: canonical (decks) -> mirror (shared/)"
fi
