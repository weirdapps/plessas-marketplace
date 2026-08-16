#!/usr/bin/env bash
# skill-trigger-probe.sh
#
# Measures natural-language routing across the six marketplace skills.
# Runs each test case in its own `claude` invocation so no case can see
# another's answer.
#
# What it measures: whether the model routes oblique phrasings to the right
# skill, resolves verb collisions by object, withholds chat-reply when
# preconditions are not met, fires chat-reply when both preconditions are met,
# and refuses out-of-domain requests.
#
# Limitation: this harness isolates the six descriptions from competing
# marketplace skills and from conversation context, making it a clean
# measurement of the descriptions and an optimistic one for a busy session.
# Run a real-session spot check of three or four cases after any description
# change.
#
# Requires: claude CLI on PATH with ambient auth (Claude Code session or
# ANTHROPIC_API_KEY). No personal config files are sourced.
#
# Usage: bash scripts/skill-trigger-probe.sh [--verbose]

set -u

VERBOSE=0
[[ "${1:-}" == "--verbose" ]] && VERBOSE=1

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
CASE_NUM=0

# ── Skill file lookup ──────────────────────────────────────────────────────
skill_file() {
  case "$1" in
    outlook-mail)      echo "$REPO/plugins/mail/skills/outlook-mail/SKILL.md" ;;
    teams-chat)        echo "$REPO/plugins/chat/skills/teams-chat/SKILL.md" ;;
    presentations)     echo "$REPO/plugins/decks/skills/presentations/SKILL.md" ;;
    spreadsheets)      echo "$REPO/plugins/excel/skills/spreadsheets/SKILL.md" ;;
    word-documents)    echo "$REPO/plugins/docs/skills/word-documents/SKILL.md" ;;
    meeting-workflows) echo "$REPO/plugins/meetings/skills/meeting-workflows/SKILL.md" ;;
  esac
}

extract_desc() {
  grep -m1 '^description: ' "$1" | sed 's/^description: //'
}

# Build the Shape A system prompt once, extracting descriptions live
build_shape_a_system() {
  local mail_desc chat_desc decks_desc excel_desc docs_desc mtg_desc
  mail_desc=$(extract_desc "$(skill_file outlook-mail)")
  chat_desc=$(extract_desc "$(skill_file teams-chat)")
  decks_desc=$(extract_desc "$(skill_file presentations)")
  excel_desc=$(extract_desc "$(skill_file spreadsheets)")
  docs_desc=$(extract_desc "$(skill_file word-documents)")
  mtg_desc=$(extract_desc "$(skill_file meeting-workflows)")

  printf 'You are a skill router. Six skills are available, each described below.\nGiven a user phrasing, output ONLY the skill name that should handle it, or NONE if no skill matches.\nOutput a single word - no explanation, no punctuation.\n\nAvailable skills:\n- outlook-mail: %s\n- teams-chat: %s\n- presentations: %s\n- spreadsheets: %s\n- word-documents: %s\n- meeting-workflows: %s' \
    "$mail_desc" "$chat_desc" "$decks_desc" "$excel_desc" "$docs_desc" "$mtg_desc"
}

SHAPE_A_SYSTEM=$(build_shape_a_system)

# Strip ANSI/VT100 escape sequences, return first non-empty word.
# Also normalises qualified command names: /plugin:cmd-name -> cmd-name
parse_output() {
  local raw="$1"
  local word
  word=$(printf '%s' "$raw" \
    | sed 's/\x1b\[[0-9;]*[A-Za-z]//g' \
    | sed 's/\x1b\[[0-9]*[JKH]//g' \
    | sed 's/\r//g' \
    | grep -E '\S' \
    | head -1 \
    | awk '{print $1}')
  # Strip leading /plugin: prefix so both /chat:chat-reply and chat-reply match
  printf '%s' "$word" | sed 's|^/[^:]*:||'
}

# ── Shape A probe ──────────────────────────────────────────────────────────
run_shape_a() {
  local num="$1" phrasing="$2" expected="$3" context="${4:-}"
  CASE_NUM=$((CASE_NUM + 1))

  local user_msg
  if [[ -n "$context" ]]; then
    user_msg="Context: $context
User says: $phrasing
Which skill handles this? Reply with only the skill name or NONE."
  else
    user_msg="User says: $phrasing
Which skill handles this? Reply with only the skill name or NONE."
  fi

  local full_prompt
  full_prompt=$(printf '%s\n\n%s' "$SHAPE_A_SYSTEM" "$user_msg")

  local raw actual
  if ! raw=$(printf '%s' "$full_prompt" | claude --print --model sonnet 2>&1); then
    printf "ERROR: 'claude' CLI failed on case %d. Is it on PATH and authenticated? Aborting.\n" "$num" >&2
    exit 3
  fi
  actual=$(parse_output "$raw")

  local verdict="FAIL"
  [[ "$actual" == "$expected" ]] && verdict="PASS"

  if [[ "$verdict" == "PASS" ]]; then
    PASS=$((PASS + 1))
    printf "PASS  %2d  expected=%-18s  actual=%-18s  %s\n" \
      "$num" "$expected" "$actual" "${phrasing:0:45}"
  else
    FAIL=$((FAIL + 1))
    printf "FAIL  %2d  expected=%-18s  actual=%-18s  %s\n" \
      "$num" "$expected" "$actual" "${phrasing:0:45}"
  fi
  [[ "$VERBOSE" == "1" ]] && printf "      raw_head: %s\n" "$(echo "$raw" | head -1)"
}

# ── Shape B probe ──────────────────────────────────────────────────────────
run_shape_b() {
  local num="$1" phrasing="$2" expected="$3" skill_key="$4"
  CASE_NUM=$((CASE_NUM + 1))

  local sf skill_content
  sf=$(skill_file "$skill_key")
  skill_content=$(cat "$sf")

  local prompt
  prompt=$(printf 'You are reading the skill card below. A user makes a request.\nDecide which command the skill would run, or reply ASK if the skill should explain its options and ask the user rather than running any command.\nOutput only the bare command name or ASK. Nothing else.\n\nSKILL CARD:\n%s\n\nUser request: %s' \
    "$skill_content" "$phrasing")

  local raw actual
  if ! raw=$(printf '%s' "$prompt" | claude --print --model sonnet 2>&1); then
    printf "ERROR: 'claude' CLI failed on case %d. Is it on PATH and authenticated? Aborting.\n" "$num" >&2
    exit 3
  fi
  actual=$(parse_output "$raw")

  local verdict="FAIL"
  [[ "$actual" == "$expected" ]] && verdict="PASS"

  if [[ "$verdict" == "PASS" ]]; then
    PASS=$((PASS + 1))
    printf "PASS  %2d  expected=%-18s  actual=%-18s  %s\n" \
      "$num" "$expected" "$actual" "${phrasing:0:45}"
  else
    FAIL=$((FAIL + 1))
    printf "FAIL  %2d  expected=%-18s  actual=%-18s  %s\n" \
      "$num" "$expected" "$actual" "${phrasing:0:45}"
  fi
  [[ "$VERBOSE" == "1" ]] && printf "      raw_head: %s\n" "$(echo "$raw" | head -1)"
}

# ── Test cases ─────────────────────────────────────────────────────────────
# Shape A: which of the six skills handles this phrasing (or NONE).
# Shape B: given one skill's full SKILL.md, which command runs (or ASK).

printf "skill-trigger-probe  %s\n" "$(date '+%Y-%m-%d %H:%M')"
printf "Repo: %s\n\n" "$REPO"

printf "Shape A: oblique (1-6)\n"
run_shape_a 1  "ο Παπαδόπουλος μου είχε στείλει κάτι την Τρίτη και δεν το βρίσκω πουθενά"  "outlook-mail"
run_shape_a 2  "the migration thread exploded overnight, where did it land"                   "teams-chat"
run_shape_a 3  "the steering committee gave me a forty minute slot and I have nothing to put on screen" "presentations"
run_shape_a 4  "τα νούμερα του Ιουνίου δεν βγαίνουν με τον προϋπολογισμό, δες τα"          "spreadsheets"
run_shape_a 5  "the committee needs this circulated internally as a formal record"            "word-documents"
run_shape_a 6  "σε μισή ώρα μπαίνω με τη Nova και δεν θυμάμαι πού είχαμε μείνει"           "meeting-workflows"

printf "\nShape A: verb-collision (7-10)\n"
run_shape_a 7  "κάνε μου μια σύνοψη από το κανάλι"                                          "teams-chat"
run_shape_a 8  "στείλε του ότι το είδα"                                                      "teams-chat"  "We were discussing a Teams thread"
run_shape_a 9  "φτιάξε μου κάτι επίσημο για τον πελάτη"                                     "word-documents"
run_shape_a 10 "ετοίμασέ με για τη Δευτέρα"                                                  "meeting-workflows"

printf "\nShape B: no-match, must ask, not run nearest command (11-14)\n"
run_shape_b 11 "διάγραψε όλα τα μέιλ από τον Ιούνιο"                                        "ASK"  "outlook-mail"
run_shape_b 12 "στείλε το ίδιο μήνυμα σε δέκα άτομα"                                        "ASK"  "teams-chat"
run_shape_b 13 "convert this deck to PDF"                                                     "ASK"  "presentations"
run_shape_b 14 "κλείσε μου ραντεβού με τον Νίκο"                                             "ASK"  "meeting-workflows"

printf "\nShape A: out-of-domain (15-16)\n"
run_shape_a 15 "what is the weather in Athens"                                                "NONE"
run_shape_a 16 "τι λέει το χαρτοφυλάκιό μου σήμερα;"                                        "NONE"

printf "\nShape B: positive control, chat-reply must fire (17)\n"
run_shape_b 17 "απάντησε στον Νίκο στη συνομιλία μας για το migration ότι το είδα"          "chat-reply" "teams-chat"

# ── Summary ────────────────────────────────────────────────────────────────
printf "\nResult: %d/%d passing\n" "$PASS" "$((PASS + FAIL))"
[[ "$FAIL" -gt 0 ]] && exit 1
exit 0
