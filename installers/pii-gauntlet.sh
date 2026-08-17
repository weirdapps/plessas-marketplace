#!/usr/bin/env bash
# pii-gauntlet.sh — verify no PII leaked into plessas-marketplace.
#
# TWO MODES:
#   --mode=ci      Scan only git-tracked files. Used by GitHub Actions to gate
#                  pushes. Any hit = FAIL = exit 1.
#   --mode=doctor  (default) Scan the entire working tree. Distinguishes tracked
#                  hits (FAIL — these would ship publicly) from gitignored hits
#                  (INFO — local-only, never pushed). Exit 1 only on tracked hits.
#
# Why two modes:
#   The CI mode is the actual safety gate.
#   The doctor mode helps the maintainer notice PII drift in their LOCAL files
#   before they accidentally `git add` something. It must NOT scare a teammate
#   running the script casually — "FAIL" on a gitignored file would teach them
#   to ignore the script entirely, defeating the point.
#
# Self-exclusion: this script contains the very patterns it searches for, so
# `--exclude=pii-gauntlet.sh` is essential to avoid self-match false positives.

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODE="doctor"
for arg in "$@"; do
  case "$arg" in
    --mode=ci)     MODE="ci" ;;
    --mode=doctor) MODE="doctor" ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

echo "=== PII Gauntlet (mode: $MODE) ==="
echo "Repo: $REPO_ROOT"
echo

FAIL=0
INFO=0

# Build the file list once. CI mode = tracked only. Doctor mode = working tree.
if [ "$MODE" = "ci" ]; then
  # Exclude self + auto-generated lockfiles at any depth (lockfiles contain SHAs / hashes that
  # collide with the 9-digit-ID regex but carry no PII risk).
  # User-cleared public showcase assets (maintainer confirmed 2026-06-08): the
  # decks screenshot library is public-safe, and its INDEX.md captions legitimately
  # name NBG products (dual card, Skroutz, …). Exclude that subtree from scanning.
  TRACKED=$(git ls-files \
    | grep -v '^installers/pii-gauntlet.sh$' \
    | grep -vE '(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Pipfile\.lock)$' \
    | grep -vE '^plugins/decks/assets/screenshots/' \
    || true)
  TRACKED_TMP=$(mktemp)
  printf '%s\n' "$TRACKED" > "$TRACKED_TMP"
fi

# Helper: get the tracked-vs-untracked status of a file.
file_is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

scan_doctor() {
  local pattern="$1"
  grep -riE \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=dist \
    --exclude-dir=__pycache__ \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    --exclude-dir=.remember \
    --exclude-dir=installers/deps \
    --exclude=pii-gauntlet.sh \
    --exclude=PII-GAUNTLET.md \
    --exclude=package-lock.json \
    --binary-files=without-match \
    "$pattern" . 2>/dev/null \
    | grep -vE 'plugins/decks/assets/screenshots/' \
    || true
}

scan_ci() {
  local pattern="$1"
  # Search only git-tracked files. NUL-delimit the list and use `xargs -0`
  # (portable on BSD/macOS and GNU). The old `xargs -a FILE -d '\n'` form is
  # GNU-only: on macOS it errors "invalid option -- a", gets swallowed by
  # 2>/dev/null, and the gate silently PASSES while scanning nothing.
  if [ -s "$TRACKED_TMP" ]; then
    tr '\n' '\0' < "$TRACKED_TMP" | xargs -0 grep -nE --binary-files=without-match "$pattern" 2>/dev/null || true
  fi
}

# Drop hits whose PATH is a historical record rather than live configuration.
# Path-scoped only. Never extend this to filter on matched content: that would
# hide live hits and turn a working guardrail into a false green.
apply_exclusion() {
  local hits="$1"
  local exclude="$2"
  if [ -z "$exclude" ] || [ -z "$hits" ]; then
    printf '%s' "$hits"
    return
  fi
  printf '%s\n' "$hits" | grep -vE "$exclude" || true
}

check() {
  local label="$1"
  local pattern="$2"
  local exclude="${3:-}"
  local hits

  if [ "$MODE" = "ci" ]; then
    hits=$(scan_ci "$pattern")
    hits=$(apply_exclusion "$hits" "$exclude")
    if [ -n "$hits" ]; then
      echo "FAIL [$label]:"
      echo "$hits" | head -20
      echo
      FAIL=1
    else
      echo "OK   [$label]"
    fi
    return
  fi

  # Doctor mode — separate tracked from gitignored.
  hits=$(scan_doctor "$pattern")
  hits=$(apply_exclusion "$hits" "$exclude")
  if [ -z "$hits" ]; then
    echo "OK   [$label]"
    return
  fi

  local tracked_hits=""
  local untracked_hits=""
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    # line format: ./path/to/file:matched-text
    local path="${line%%:*}"
    path="${path#./}"
    if file_is_tracked "$path"; then
      tracked_hits+="$line"$'\n'
    else
      untracked_hits+="$line"$'\n'
    fi
  done <<< "$hits"

  if [ -n "$tracked_hits" ]; then
    echo "FAIL [$label]:                 (tracked — would ship publicly)"
    printf '%s' "$tracked_hits" | head -20
    echo
    FAIL=1
  fi
  if [ -n "$untracked_hits" ]; then
    echo "INFO [$label]:                 (gitignored / untracked — local-only)"
    printf '%s' "$untracked_hits" | head -10
    echo
    INFO=1
  fi
  if [ -z "$tracked_hits" ] && [ -z "$untracked_hits" ]; then
    echo "OK   [$label]"
  fi
}

# ---------------------------------------------------------------------------
# Patterns (shared between modes)
# ---------------------------------------------------------------------------

# Personal name (full forms — single-word "plessas" is the brand name, OK)
check "Full personal name (EN)" "Dimitris[[:space:]]+Plessas|Dimitrios[[:space:]]+Plessas"
check "Full personal name (GR)" "Δημήτριος[[:space:]]+Πλέσσας|ΠΛΕΣΣΑΣ[[:space:]]+ΔΗΜΗΤΡΙΟΣ"

# Personal emails
check "Personal email" "dimitrios\.plessas@|plessasdimitrios@|plessas@nbg\.gr|plessas@gmail|plessas@yahoo"

# Personal phone / address
check "Personal phone" "694[[:space:]]?9200878|6949200878"
check "Personal address" "174[[:space:]]+Syggrou|Συγγρού[[:space:]]+174"

# Greek tax IDs (9-digit standalone, with non-hex word boundaries).
# Excludes 9-digit substrings inside git SHAs (40-char hex) by requiring
# the surrounding chars are not hex digits.
check "9-digit ID pattern" "[^0-9a-fA-F][0-9]{9}[^0-9a-fA-F]"

# Peer names (NBG colleagues / direct reports / managers)
check "Peer/colleague names" "Volioti|Bitrou|Sioutis|Theofilidi|Θεοφιλίδη|Χριστίνα|Lygeros|Oikonomou|Maraveas|Xona|Petropoulou|Laspas|Koutra|Giemelou"

# Family names
check "Family names" "Kitrilaki|Κιτριλάκη"

# NBG-internal project names (case-insensitive but anchored)
check "Internal projects" "Διπλή κάρτα|\bdual[- ]card\b|IRIS[[:space:]]+pilot|ECB[[:space:]]+Digital[[:space:]]+Euro[[:space:]]+CfEI"

# External partners discussed in NBG-internal context
check "Partner names" "\bWorldline\b|\bHelvia\b|\bWealthyhood\b|\bFeedzai\b|\bMellon\b|\b11FS\b|\bNCR\b"

# Tax authority refs
check "Tax authority" "ΑΑΔΕ|ΑΦΜ|ΑΔΤ|ΑΜΚΑ"

# Source-tree paths: references to the maintainer's local SourceCode tree or
# the claude-config store. Design records under docs/superpowers/ are
# excluded BY PATH -- they quote these patterns to document them, not to leak
# them. Live configuration lives in plugins/, installers/, and scripts/, none
# of which is excluded. CHANGELOG.md is NOT excluded here.
#
# /SourceCode/claude-config is carried over from the pre-2026-08-16 single
# check. Keep it: without it a bare "/SourceCode/claude-config/private/..."
# (no leading ~, no $HOME, no /Users/<name>, not the shared-memory subpath)
# matches none of the other alternatives, and claude-config/private is the
# most sensitive tier there is.
check "Source tree paths" \
  "~/SourceCode|\\\$HOME/SourceCode|/SourceCode/claude-config|claude-config/shared-memory" \
  "^(\./)?(docs/superpowers/)"

# Absolute user home paths. No path exclusions -- historical records must not
# embed a specific maintainer username either.
check "Absolute user paths" \
  "/Users/[a-z]"

# Cleanup
[ "$MODE" = "ci" ] && rm -f "$TRACKED_TMP"

echo
if [ $FAIL -eq 0 ]; then
  if [ "$MODE" = "doctor" ] && [ $INFO -ne 0 ]; then
    echo "=== GAUNTLET PASS (with INFO on gitignored files — local-only, not in git) ==="
  else
    echo "=== GAUNTLET PASS ==="
  fi
  exit 0
else
  echo "=== GAUNTLET FAIL ==="
  if [ "$MODE" = "doctor" ]; then
    echo "Tracked PII detected. These files would ship publicly. Fix before committing."
  else
    echo "Fix the PII leaks above before any public push."
  fi
  exit 1
fi
