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

# Default to CI mode on a runner. Three repositories invoke this script with no
# --mode flag at all, so they got doctor mode, which fails hard when the private
# denylist is absent -- and on a runner it is always absent. Keying off the
# environment rather than the caller means a workflow cannot get this wrong by
# omission. GitHub, GitLab and most others set CI=true.
if [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ]; then
  MODE="ci"
else
  MODE="doctor"
fi
_MODE_FROM_ENV="$MODE"
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

# This script's path relative to the repo root. Derived, not hardcoded: the
# same file lives in installers/ in some repos and scripts/ in others, and
# hand-maintained copies are what let them drift apart in the first place.
# Both modes need it now, so it is computed before either branch.
SELF_REL=$(git ls-files --full-name -- "$0" 2>/dev/null | head -1)
[ -z "$SELF_REL" ] && SELF_REL="installers/pii-gauntlet.sh"

# Build the file list once. CI mode = tracked only. Doctor mode = working tree.
if [ "$MODE" = "ci" ]; then
  # Exclude self + auto-generated lockfiles at any depth (lockfiles contain SHAs / hashes that
  # collide with the 9-digit-ID regex but carry no PII risk).
  # User-cleared public showcase assets (maintainer confirmed 2026-06-08): the
  # decks screenshot library is public-safe. Narrowed to the .png files: the
  # subtree holds 117 PNGs and 5 INDEX.md, and excluding the whole prefix meant
  # the five TEXT files were exempt from every check. The PNGs are the only part
  # that needs skipping and grep would drop them anyway under
  # --binary-files=without-match; the exclusion just saves opening them. The
  # stated reason for the exemption was that the INDEX.md captions name employer
  # products, which is the employer-name check, and that check is separately
  # opted out here by .pii-gauntlet-allow-employer-name. So the captions cost
  # nothing to scan, while the mail-domain, tenant, Azure-id and denylist checks
  # now cover them.
  TRACKED=$(git ls-files \
    | grep -v "^$SELF_REL$" \
    | grep -vE '(^|/)LICENSE(\.md|\.txt)?$' \
    | grep -vE '(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Pipfile\.lock)$' \
    | grep -vE '^plugins/decks/assets/screenshots/.*\.png$' \
    || true)
  TRACKED_TMP=$(mktemp)
  printf '%s\n' "$TRACKED" > "$TRACKED_TMP"
fi

# Helper: get the tracked-vs-untracked status of a file.
file_is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

# ---------------------------------------------------------------------------
# The tracked TREE, as distinct from file CONTENTS
# ---------------------------------------------------------------------------
#
# TWO PATH POPULATIONS, DELIBERATELY DIFFERENT, kept adjacent so the difference
# reads as designed rather than as one of them having a bug.
#
#   TRACKED (built above, CI mode) is what the CONTENT checks grep. It drops
#   the screenshot PNGs, because grepping a PNG's bytes is meaningless:
#   --binary-files=without-match discards them anyway and opening 117 of them
#   only costs time.
#
#   TREE_PATHS is what the FILENAME check reads, and it deliberately INCLUDES
#   those same PNGs. A filename is text no matter what the file contains, and
#   for a binary it is the ONLY readable surface there is.
#
# Do NOT "fix" this by making the tree check reuse TRACKED. Two tracked PNGs
# disclosed an internal project name in their own filenames while every content
# check passed and the gate printed GAUNTLET PASS. Exempting binaries from the
# tree check would reproduce exactly that blindness.
TREE_PATHS=$(git ls-files | grep -v "^$SELF_REL$" || true)
UNTRACKED_PATHS=$(git ls-files --others --exclude-standard 2>/dev/null || true)

# Pair every path with its separator-normalised form as "orig<TAB>normalised",
# so a hit already carries its own path. No index to map back, one pass per
# check, and the "do the two lists stay aligned" invariant stops existing
# rather than having to be verified. Cost is O(paths), not O(paths x hits).
#
# The normalisation matters more than case does. Filenames join words with _ .
# or -, so a pattern written "two words" matches prose and misses Two_words.png.
# Measured over 799 tracked paths and every check: as-written 0 hits, -i alone
# 0, separators alone 1, -i plus separators 2, both real, no false positives.
# Without normalisation this check finds nothing at all, which would make it a
# check that exists only to look reassuring: the failure mode being removed
# here, not one to add back.
#
# Matching runs against the whole pasted line, so a hit on EITHER the raw or
# the normalised form counts, which is the union wanted. One consequence: a
# `$`-anchored pattern would anchor to the normalised half. No pattern in use
# is `$`-anchored.
#
# Hits are emitted as "path:(filename)" so they share the "path:" shape the
# doctor-mode tracked/untracked splitter already parses, which is what gives
# the CI-tracked-only and doctor-also-untracked split for free.
scan_paths() {
  local pattern="$1"
  local list="$2"
  [ -n "$list" ] || return 0
  paste <(printf '%s\n' "$list") <(printf '%s\n' "$list" | tr '_.-' '   ') \
    | grep -iE "$pattern" 2>/dev/null \
    | cut -f1 \
    | sed 's/$/:(filename)/' \
    || true
}

scan_doctor() {
  local pattern="$1"
  # The trailing screenshots filter below is anchored to the `./path:` prefix,
  # not matched loose against the whole line. Unanchored, the literal string
  # "plugins/decks/assets/screenshots/" appearing in a line's CONTENT suppressed
  # that line from every check: a one-substring suppression token, the same
  # defect as the "copyright" filter that used to sit in apply_exclusion.
  grep -riE \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=dist \
    --exclude-dir=__pycache__ \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    --exclude-dir=.remember \
    --exclude-dir=data \
    --exclude-dir=attachments \
    --exclude-dir=backups \
    --exclude-dir=archive \
    --exclude-dir=.next \
    --exclude-dir=dist \
    --exclude-dir=coverage \
    --exclude-dir=installers/deps \
    --exclude=pii-gauntlet.sh \
    --exclude=LICENSE \
    --exclude=LICENSE.md \
    --exclude=LICENSE.txt \
    --exclude=PII-GAUNTLET.md \
    --exclude=package-lock.json \
    --binary-files=without-match \
    "$pattern" . 2>/dev/null \
    | grep -vE '^\./plugins/decks/assets/screenshots/.*\.png:' \
    || true
}

scan_ci() {
  local pattern="$1"
  # Search only git-tracked files. NUL-delimit the list and use `xargs -0`
  # (portable on BSD/macOS and GNU). The old `xargs -a FILE -d '\n'` form is
  # GNU-only: on macOS it errors "invalid option -- a", gets swallowed by
  # 2>/dev/null, and the gate silently PASSES while scanning nothing.
  # -i, matching scan_doctor above. Without it the GATE was case-sensitive
  # while the local doctor was not, so the check that blocks a push was the
  # weaker of the two, which is backwards. Measured over the tracked tree, that
  # single missing flag hid one real disclosure from CI that the doctor caught.
  if [ -s "$TRACKED_TMP" ]; then
    tr '\n' '\0' < "$TRACKED_TMP" | xargs -0 grep -inE --binary-files=without-match "$pattern" 2>/dev/null || true
  fi
}

# Drop hits that are documentation rather than live configuration.
#
# Two kinds of exclusion, and they are NOT interchangeable:
#   $2 content: matched anywhere on the grep line. Keep it narrow, because a
#      broad content exclusion is indistinguishable from switching the check off.
#   $3 path: matched against the `path:` prefix only. A path-shaped pattern let
#      loose on the whole line also matches CONTENT, which is how `<[^>]+>`
#      silently excluded every line carrying an HTML tag. A line like
#      `<td>firstname.surname@<employer-domain></td>` passed the mail-domain
#      check because of the `<td>`, not because of anything about the address.
apply_exclusion() {
  local hits="$1"
  local exclude="$2"
  local exclude_path="${3:-}"
  # No early return, and no filter that only some callers get. The old version
  # short-circuited when both exclude args were empty, so a denylist entry with
  # a blank third field took a different code path from a generic check with an
  # empty exclude. Every caller now runs the same two filters, each a no-op when
  # its argument is empty.
  #
  # There used to be a third, unconditional filter here dropping any line that
  # contained "(c) YYYY" or the word "copyright", case-insensitively, in the
  # name of licence attribution. LICENSE, LICENSE.md and LICENSE.txt are already
  # removed from the file list in both modes, so it protected nothing and
  # instead handed anyone a one-word suppression token: an audit confirmed that
  # "Copyright 2026 - reach me at <real address>" was dropped silently while the
  # same address without the word was caught. It is gone.
  if [ -n "$hits" ] && [ -n "$exclude_path" ]; then
    hits=$(printf '%s\n' "$hits" | grep -vE "^[^:]*($exclude_path)" || true)
  fi
  if [ -n "$hits" ] && [ -n "$exclude" ]; then
    hits=$(printf '%s\n' "$hits" | grep -vE "$exclude" || true)
  fi
  printf '%s' "$hits"
}

check() {
  local label="$1"
  local pattern="$2"
  local exclude="${3:-}"
  local exclude_path="${4:-}"
  local hits

  if [ "$MODE" = "ci" ]; then
    # Contents AND filenames, in one verdict per check. Folding them together
    # rather than bolting on a separate section is deliberate: it means a check
    # added later cannot silently skip the tree, which is the shape of every
    # hole found in this file.
    hits=$(printf '%s\n%s' "$(scan_ci "$pattern")" "$(scan_paths "$pattern" "$TREE_PATHS")" | grep -v '^$' || true)
    hits=$(apply_exclusion "$hits" "$exclude" "$exclude_path")
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
  #
  # Untracked FILENAMES are included here and not in CI, matching how doctor
  # already treats untracked CONTENT: an untracked path never ships, so it is
  # INFO rather than FAIL, but doctor exists to surface local drift before
  # someone stages it, and a check silently exempt from that would be the same
  # surprise this file keeps producing.
  hits=$(printf '%s\n%s\n%s' \
    "$(scan_doctor "$pattern")" \
    "$(scan_paths "$pattern" "$TREE_PATHS")" \
    "$(scan_paths "$pattern" "$UNTRACKED_PATHS")" | grep -v '^$' || true)
  hits=$(apply_exclusion "$hits" "$exclude" "$exclude_path")
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
# ---------------------------------------------------------------------------
# Generic organisation tells (safe to keep in a public repo)
# ---------------------------------------------------------------------------
#
# These are patterns, not names, so publishing them discloses nothing. They are
# also the checks that were missing entirely: the four exposures found in the
# 2026-08-24 audit all passed the gauntlet green, because nothing here looked
# for the employer's name, its mail domain, or a tenant hostname.

# Placeholders are the whole point of a good example, so they must not trip the
# check that exists to catch the real thing. Without these excludes the gauntlet
# flags `contoso.sharepoint.com` (the correct placeholder) and its own CHANGELOG
# entries describing the removal of the real host. A check that fires on
# deliberate, already-disclosed content teaches you to ignore it, which is how
# the four real exposures sat unnoticed next to a green gauntlet.
# Doc placeholders. Extend this when a new invented example host trips the check:
# being asked once "is this a real tenant?" is the check doing its job, and is a
# far better failure mode than the silence it replaces.
#
# Every exclusion below names a placeholder VALUE. None of them exempts a FILE.
#
# There used to be a PLACEHOLDER_PATH='example|sample|template', passed as the
# path argument to the employer-name, mail-domain and tenant checks. Unanchored
# and matched as a substring against the path of every hit, it exempted
# thirteen tracked files outright, among them
# shared/claude-md-template/team-claude-md.md,
# shared/email-style-template/style-guide-template.md,
# plugins/mail/shared/style-guide-example.md, everything under
# plugins/decks/examples/, plugins/decks/assets/templates/NBG-Template-GR.pptx
# and all three .github/*TEMPLATE* files. Two of them already carry real-shaped
# addresses, so a genuine address, tenant or employer name planted in any of the
# thirteen was invisible. An audit reproduced it: an address under
# shared/email-style-template/ was dropped while the identical line under docs/
# was caught.
#
# It is gone, and nothing replaced it, because it was never load-bearing.
# Removing it exposes exactly four lines across two files, three of which the
# value-based excludes below already cover; the fourth is the bare local part
# "name" in the signature-block example, handled by PLACEHOLDER_MAIL. The path
# argument to `check` still exists for a file that genuinely cannot be scanned,
# but it must then be an anchored, named path with a comment saying why, never a
# substring.
PLACEHOLDER='contoso|firstname\.lastname|your\.email|recipient\.name'

# shared/email-style-template/style-guide-template.md shows the shape of a
# signature line, "M: +30 ..., E: name@nbg.gr". The local part is the literal
# word "name", a placeholder value rather than a person. Anchored on the left so
# a real address that merely ENDS in "name" (real.name@..., admin.name@...) is
# still caught.
PLACEHOLDER_MAIL="$PLACEHOLDER|(^|[^A-Za-z0-9._%+-])name@"

# Invented tenant hosts, and only the ones this repo actually uses: contoso
# (already in PLACEHOLDER), test, overridden and envvar. The list previously
# also carried dummy, placeholder, foo, bar and the bare single letters a, b, x,
# y and z, none of which appear anywhere in the repo.
#
# The single letters were a live hole, not just clutter. `a` followed by
# `(-my)?\.sharepoint` matches the LAST CHARACTER of any real tenant label, so
# alpha.sharepoint.com, zorba.sharepoint.com and omega-my.sharepoint.com were
# all excluded and the tenant check could not fire on them. That is the same
# defect commit 6367bff claimed to have fixed when it replaced a bare `[a-z]`
# with "explicitly named fixture hosts"; five of the names it chose were single
# characters. The alternation is now anchored on the left by a character that
# cannot appear inside a host label, so a fixture name has to be the whole
# label.
PLACEHOLDER_TENANT="$PLACEHOLDER|your[-_.]?tenant|(^|[^a-z0-9.-])(test|overridden|envvar)(-my)?\.sharepoint"

# Some repos name the employer on purpose: a marketplace written for colleagues
# says so in its README by design. Those opt out with a repo-root marker rather
# than carrying a permanent red light.
if [ ! -f ".pii-gauntlet-allow-employer-name" ]; then
  check "Employer name" '(^|[^A-Za-z0-9])(NBG|ΕΤΕ)([^A-Za-z0-9]|$)|Εθνική Τράπεζα|National Bank of Greece' "$PLACEHOLDER"
else
  echo "OK   [Employer name] (opted out via .pii-gauntlet-allow-employer-name)"
fi

check "Employer mail domain" '[A-Za-z0-9._%+-]+@nbg\.gr' "$PLACEHOLDER_MAIL"
check "SharePoint tenant"    '[a-z0-9-]+\.sharepoint\.com' "$PLACEHOLDER_TENANT"
# A bare UUID is not a finding: fixtures, generated filenames and message ids
# are full of them, and flagging all of them is how a check earns the right to
# be ignored. What matters is a GUID sitting where a TENANT id sits, so key on
# the surrounding context rather than on the shape alone.
check "Azure AD tenant id" \
  '(tenant[_-]?id|tenantId|\"tid\"|authority|login\.microsoftonline\.com/|realm)[^0-9a-f]{0,24}[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' \
  '00000000-0000-0000-0000-000000000000|11111111-2222-3333-4444-555555555555|00000000-|11111111-|22222222-|33333333-|44444444-|55555555-|66666666-|77777777-|88888888-|99999999-|aaaaaaaa-|bbbbbbbb-|cccccccc-|dddddddd-|eeeeeeee-|ffffffff-|/common|/organizations|/consumers'

# ---------------------------------------------------------------------------
# Name-based checks, loaded from a private denylist
# ---------------------------------------------------------------------------
#
# The literal terms used to live in this file. That made the guard the
# disclosure: this script is anonymously readable, and it enumerated colleague
# names, a family name, a personal mobile and address, personal emails,
# unreleased internal project names, the partner list and every private repo
# path, complete with comment headers explaining which was which.
#
# They now live outside every public repo. Nothing here reveals what is checked.

PII_DENYLIST="${PII_DENYLIST:-$HOME/.claude/private/pii-denylist.conf}"

if [ -r "$PII_DENYLIST" ]; then
  # Tab-delimited: the patterns are full of regex alternation pipes, so "|"
  # cannot be the field separator.
  loaded=0
  while IFS=$'\t' read -r label pattern exclude; do
    case "$label" in ''|\#*) continue ;; esac
    [ -z "$pattern" ] && continue
    check "$label" "$pattern" "$exclude"
    loaded=$((loaded + 1))
  done < "$PII_DENYLIST"
  echo "     ($loaded name-based checks loaded from the private denylist)"
else
  # Absence is handled differently by mode, on purpose.
  #
  # In CI on a public repo the denylist legitimately does not exist and never
  # will, so failing here would just paint six repos red forever. Say plainly
  # that the name checks did not run, and let the generic ones stand.
  #
  # Locally the file should always be there. Its absence is a real
  # misconfiguration, and a guard that cannot evaluate its condition must
  # refuse rather than pass. That distinction is the whole point: the previous
  # version of this script reported OK on every check while, on macOS, scanning
  # exactly zero files.
  if [ "$MODE" = "ci" ]; then
    echo "SKIP [name-based checks]: no denylist at $PII_DENYLIST"
    echo "     Generic org-tell checks above still ran. Name, family, partner and"
    echo "     private-path checks did NOT. This is expected in public CI."
  else
    echo "FAIL [name-based checks]: no denylist at $PII_DENYLIST"
    echo "     Locally this file must exist. Without it the name, family, partner"
    echo "     and private-path checks are silently absent, which is exactly the"
    echo "     false green this rewrite removes."
    echo "     Fix: ensure ~/.claude/private -> claude-config/private is linked,"
    echo "     or set PII_DENYLIST to the file."
    FAIL=1
  fi
fi

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
