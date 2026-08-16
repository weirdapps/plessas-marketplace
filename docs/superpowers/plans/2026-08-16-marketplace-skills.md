# Natural-Language Triggering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each of the six plugins a router skill so colleagues reach the right workflow by describing what they want, in Greek or English, without knowing any command name.

**Architecture:** One `SKILL.md` per plugin. The description states a bounded intent space plus a negative boundary and relies on the model to generalise. The body maps intent to the plugin's existing commands and ends with a no-match rule that asks rather than guesses. No workflow logic is duplicated. A portability regression in `chat-reply`, and the guardrail gap that let it ship, are closed first because the skills layer routes into that command.

**Tech Stack:** Markdown with YAML frontmatter, GitHub Actions shell steps, bash (`installers/pii-gauntlet.sh`). No new dependencies, no new test framework.

**Spec:** `docs/superpowers/specs/2026-08-16-marketplace-skills-design.md`

## Global Constraints

- Branch is `feat/natural-language-skills`, already created off `master`.
- Skills are auto-discovered from `plugins/<plugin>/skills/<skill>/SKILL.md`. Do NOT add a `skills` key to any `plugin.json`.
- Every skill description: 400 characters minimum, contains Greek-script text, contains a `Do NOT use` clause naming sibling skills.
- Exemplars in descriptions are samples, never a list. Each description must contain the literal instruction that they are not exhaustive and the model should judge by meaning.
- Exemplars must be oblique where possible: at least two per skill must not name the domain noun.
- Route on the object of the request, not the verb.
- No em-dash in any file authored or edited by this plan. Comma, colon or period; hyphen for ranges.
- The repository is PUBLIC. No absolute paths under `~/SourceCode`, no personal names, no references to a personal `CLAUDE.md`.
- `installers/pii-gauntlet.sh` must pass at every commit.
- CI runs `ubuntu-latest` (GNU grep). Local validation runs on macOS (BSD grep). Use `grep -E` only; `grep -P` is unavailable on BSD.

---

### Task 1: Close the portability regression

**Files:**

- Modify: `installers/pii-gauntlet.sh:98-114` (`check()`), `installers/pii-gauntlet.sh:190`
- Modify: `plugins/chat/commands/chat-reply.md:25,27,31`
- Modify: `plugins/mail/commands/send-mail.md:95`
- Modify: `plugins/chat/README.md`
- Modify: `CHANGELOG.md`

**Interfaces:**

- Consumes: nothing.
- Produces: `apply_exclusion "$hits" "$exclude"` in `pii-gauntlet.sh`, and a `check()` accepting an optional third argument, an exclusion regex matched against the path prefix of each hit in either mode (`path:line:content` in CI, `./path:content` in doctor). Later tasks rely on `bash installers/pii-gauntlet.sh --mode=ci` exiting 0.

- [ ] **Step 1: Broaden the path check so it fails on the current tree**

In `installers/pii-gauntlet.sh`, replace line 190:

```bash
check "User-specific paths" "/Users/plessas|/SourceCode/claude-config|claude-config/shared-memory"
```

with:

```bash
# Personal source paths. Broadened 2026-08-16: the old pattern named one repo
# (/SourceCode/claude-config) and so let ~/SourceCode/teams-access/... ship
# green in plugins/chat/commands/chat-reply.md.
#
# Design records under docs/superpowers/ are excluded BY PATH. They quote the
# offending paths in order to document them, which is the opposite of leaking
# them. Live configuration never lives there: it lives in plugins/, installers/
# and scripts/, none of which is excluded. The script already excludes itself
# at line 54, so the pattern below does not match its own definition.
check "User-specific paths" \
  "/Users/[a-z]|~/SourceCode|\\\$HOME/SourceCode|claude-config/shared-memory" \
  "^(\./)?(docs/superpowers/|CHANGELOG\.md)"
```

The `(\./)?` is load-bearing. CI mode emits hits as `path:line:content`, doctor
mode emits them as `./path:content`. One regex has to tolerate both.

The exclusion covers all of `docs/superpowers/`, not just `plans/`. The spec at
`docs/superpowers/specs/2026-08-16-marketplace-skills-design.md` quotes the same
paths five times while documenting this very defect; excluding only `plans/`
leaves Step 6 permanently red.

- [ ] **Step 2: Teach `check()` the exclusion argument, in BOTH modes**

Doctor mode sets `FAIL=1` on tracked hits exactly as CI mode does, so an
exclusion applied only to the CI branch would leave the local run red on the
historical records. Both branches get it.

In `installers/pii-gauntlet.sh`, insert this helper immediately above `check()`
at line 98:

```bash
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
```

Then make three edits inside `check()`:

Add the third parameter, after `local pattern="$2"`:

```bash
  local exclude="${3:-}"
```

In the CI branch, after `hits=$(scan_ci "$pattern")`:

```bash
    hits=$(apply_exclusion "$hits" "$exclude")
```

In the doctor branch, after `hits=$(scan_doctor "$pattern")` (line 117):

```bash
  hits=$(apply_exclusion "$hits" "$exclude")
```

Change nothing else. Every existing `check` call passes two arguments, so
`exclude` is empty for all of them and their behaviour is unchanged.

- [ ] **Step 3: Run the gauntlet in both modes and confirm it now FAILS (red)**

Run: `bash installers/pii-gauntlet.sh --mode=ci`
Expected: `FAIL [User-specific paths]:` listing `plugins/chat/commands/chat-reply.md:25`. Exit code 1.

Run: `bash installers/pii-gauntlet.sh --mode=doctor`
Expected: the same file listed under the tracked heading, and NOT
`docs/superpowers/plans/2026-05-11-share-readiness.md`. If the historical plan
appears, `(\./)?` is missing from the exclusion regex or `apply_exclusion` was
not wired into the doctor branch.

In both modes, `chat-reply.md:25` must be the ONLY hit. If either the spec or a
plan under `docs/superpowers/` also appears, the exclusion is scoped to `plans/`
instead of the whole `docs/superpowers/` tree.

If either mode passes with no hits at all, the pattern is not matching. Check
that `~/SourceCode` is not being shell-expanded inside the double quotes.

Note on the starting state: the gauntlet is ALREADY red on this branch before
you begin, because the plan and spec commits quote the old check line and the
offending path while documenting them. That is the defect this step fixes, not
something you introduced. Green is expected only from Step 6 onward.

- [ ] **Step 4: Fix `chat-reply.md`**

In `plugins/chat/commands/chat-reply.md`, replace step 5 (line 25):

```markdown
5. **Show the draft** inline for transparency, then send it via `mcp__teams-bridge__teams_send_message`. Every message MUST start with the `[Claude]` prefix so recipients know they are reading the agent and not the account owner typing personally.
```

Replace step 6 (line 27):

```markdown
6. **Before sending**: verify the target chat resolves to the intended, known recipient. If the target chat is ambiguous or unfamiliar, fall back to draft-and-confirm.
```

Replace the first bullet under `## Important` (line 31):

```markdown
- Auto-send is the default for this plugin. Draft-and-confirm only when the target chat is ambiguous or unfamiliar. If you would rather approve every message, say so at the start of the session and this command will draft instead.
```

The frontmatter already declares `mcp__teams-bridge__teams_send_message` in `allowed-tools`. Do not change the frontmatter.

- [ ] **Step 5: Make the send-mail example tenant-neutral**

In `plugins/mail/commands/send-mail.md:95`, replace:

```json
  "cc": ["your.email@nbg.gr"],
```

with:

```json
  "cc": ["your.email@example.com"],
```

- [ ] **Step 6: Run the gauntlet in both modes and confirm it PASSES (green)**

Run: `bash installers/pii-gauntlet.sh --mode=ci`
Expected: `OK   [User-specific paths]` and exit code 0, with every other check still OK.

Run: `bash installers/pii-gauntlet.sh --mode=doctor`
Expected: no `FAIL` line for any check. `INFO` lines about gitignored files are
acceptable; they are local-only by definition.

- [ ] **Step 7: Prove the exclusion is path-scoped, not content-scoped**

```bash
grep -c '~/SourceCode' docs/superpowers/plans/2026-05-11-share-readiness.md
grep -c '~/SourceCode' docs/superpowers/specs/2026-08-16-marketplace-skills-design.md
git ls-files -z | xargs -0 grep -lE "/Users/[a-z]|~/SourceCode" 2>/dev/null
```

Expected: both counts non-zero, and the file list containing only paths under
`docs/superpowers/` plus `installers/pii-gauntlet.sh` itself. This confirms the
strings are still present and are being skipped by path, not removed and not
hidden by a weakened pattern. If `plugins/` appears in that list, Step 4 is
incomplete.

- [ ] **Step 8: Record the decision so it does not get reverted**

Append to `plugins/chat/README.md` under `## How it works`:

```markdown
### Send behaviour

`/chat-reply` auto-sends by default. This is deliberate as of 2026-08-16 and
supersedes the earlier draft-and-approve default. Every message carries a
`[Claude]` prefix so recipients know they are reading an agent, and the command
falls back to draft-and-confirm when the target chat is ambiguous or unfamiliar.
To approve every message instead, say so at the start of the session.
```

Add a new section at the top of `CHANGELOG.md`, directly below the intro paragraph and above `## [2.1.0]`:

```markdown
## [Unreleased]

### Added

- Natural-language triggering: one router skill per plugin, so requests reach the right workflow without a command name. Greek and English.
- `docs/skill-triggers.md`: each skill's domain, boundaries, and the tie-break policy
- `validate-plugins.yml`: skill frontmatter validation (description floor, Greek text, negative boundary clause)

### Changed

- `chat/commands/chat-reply.md` sends through the bundled `teams-bridge` MCP instead of an absolute path to a local checkout, which never resolved on any machine but the maintainer's
- `chat-reply` auto-send is now the documented public default. This supersedes the draft-and-approve default recorded in `docs/superpowers/plans/2026-05-11-share-readiness.md`, which should be read as historical from this date.
- `installers/pii-gauntlet.sh` user-path check broadened from one named repo to any `~/SourceCode` or `/Users/<name>` path, with historical records excluded by path
- `mail/commands/send-mail.md` CC example uses a neutral domain
```

- [ ] **Step 9: Commit**

```bash
git add installers/pii-gauntlet.sh plugins/chat/commands/chat-reply.md \
        plugins/mail/commands/send-mail.md plugins/chat/README.md CHANGELOG.md
git commit -m "fix(chat): send via teams-bridge MCP, not an absolute local path

Commit c75ca37, whose stated purpose was README badges, replaced the
public draft-and-approve default with the maintainer's personal setup:
an absolute ~/SourceCode path, the maintainer's name, and a reference to
a personal CLAUDE.md. The path never resolved on anyone else's machine.

Auto-send is kept and is now documented as the deliberate public default,
superseding the May decision, so this does not silently revert again.

The pii-gauntlet path check named one repo and so let the path through.
Broadened to any ~/SourceCode or /Users/<name> path, with historical
records excluded by path rather than by weakening the pattern."
```

---

### Task 2: Skill validation in CI, proven by the first skill

**Files:**

- Modify: `.github/workflows/validate-plugins.yml` (after the `Validate command frontmatter` step, before `Consistency checks`)
- Create: `plugins/mail/skills/outlook-mail/SKILL.md`

**Interfaces:**

- Consumes: `bash installers/pii-gauntlet.sh` passing, from Task 1.
- Produces: a CI step named `Validate skill frontmatter` that every later task runs to verify its skill. Establishes the SKILL.md shape that Tasks 3 to 7 follow.

- [ ] **Step 1: Add the validation step**

In `.github/workflows/validate-plugins.yml`, insert after the `Validate command frontmatter` step and before `Consistency checks`:

```yaml
      - name: Validate skill frontmatter
        run: |
          errors=0
          for skill_file in plugins/*/skills/*/SKILL.md; do
            [ -f "$skill_file" ] || continue
            if ! head -1 "$skill_file" | grep -q "^---$"; then
              echo "$skill_file: missing frontmatter"
              errors=$((errors + 1))
              continue
            fi
            desc=$(awk '/^---$/{n++; next} n==1 && /^description:/{sub(/^description:[ ]*/,""); print; exit}' "$skill_file")
            if [ -z "$desc" ]; then
              echo "$skill_file: missing description"
              errors=$((errors + 1))
              continue
            fi
            # Three weak structural floors. They exist to stop a future edit
            # regressing to a short description that never fires. Do NOT grow
            # them into rules about which phrases a description contains:
            # enumerating phrases is the failure mode this design rejects.
            if [ "${#desc}" -lt 400 ]; then
              echo "$skill_file: description is ${#desc} chars, minimum 400"
              errors=$((errors + 1))
            fi
            if ! printf '%s' "$desc" | grep -qE '[α-ωΑ-Ω]'; then
              echo "$skill_file: description has no Greek-script text"
              errors=$((errors + 1))
            fi
            if ! printf '%s' "$desc" | grep -q 'Do NOT use'; then
              echo "$skill_file: description has no negative boundary"
              errors=$((errors + 1))
            fi
          done
          [ $errors -eq 0 ] && echo "All skill files validated" || exit 1
```

- [ ] **Step 2: Create a deliberately bad skill and confirm the step fails (red)**

```bash
mkdir -p plugins/mail/skills/outlook-mail
cat > plugins/mail/skills/outlook-mail/SKILL.md <<'EOF'
---
name: outlook-mail
description: Email stuff.
---
EOF
```

Extract and run just the step body locally:

```bash
bash -c 'errors=0
for skill_file in plugins/*/skills/*/SKILL.md; do
  [ -f "$skill_file" ] || continue
  desc=$(awk "/^---\$/{n++; next} n==1 && /^description:/{sub(/^description:[ ]*/,\"\"); print; exit}" "$skill_file")
  [ "${#desc}" -lt 400 ] && { echo "$skill_file: ${#desc} chars"; errors=1; }
  printf "%s" "$desc" | grep -qE "[α-ωΑ-Ω]" || { echo "$skill_file: no Greek"; errors=1; }
  printf "%s" "$desc" | grep -q "Do NOT use" || { echo "$skill_file: no boundary"; errors=1; }
done
exit $errors'
```

Expected: three failures reported for `plugins/mail/skills/outlook-mail/SKILL.md`, exit code 1.

- [ ] **Step 3: Write the real skill**

Overwrite `plugins/mail/skills/outlook-mail/SKILL.md`:

```markdown
---
name: outlook-mail
description: Anything to do with the user's Outlook mailbox: reading it, deciding what in it matters, and composing what goes out of it. Covers inbox briefings and triage, finding and summarising messages or threads, drafting replies and forwards, sending new mail, and learning the user's writing style. Use this whenever a request concerns email, however it is phrased, for example "what needs my attention today", "anything urgent from the auditors", "answer Maria", "put together a note to the team", or in Greek «τι τρέχει στο μέιλ μου», «ποιος περιμένει απάντηση», «γράψε στον Κώστα», «βγάλε μου μια σύνοψη από τα χθεσινά». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for Microsoft Teams messages or chats (use teams-chat), for preparing or debriefing meetings (use meeting-workflows), or for reading spreadsheets or Word documents.
---

# Outlook mail

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| see what is in the mailbox and what matters | `/mail:inbox-briefing` |
| the same, plus drafted replies ready to review | `/mail:mail-review` |
| sort, file or clean up the mailbox | `/mail:triage-inbox` |
| answer a message | `/mail:reply` |
| pass a message on to someone else | `/mail:forward` |
| write a new message | `/mail:send-mail` |
| file a finished thread away | `/mail:archive-thread` |
| know what was decided across recent mail | `/mail:decisions` |
| check a draft before it goes out | `/mail:draft-review` |
| see the folder structure | `/mail:folder-tree` |
| teach the plugin their writing style | `/mail:style-sync` |
| inspect or undo style learning | `/mail:style-stats`, `/mail:style-rollback` |
| fix mail access or authentication | `/mail:mail-doctor`, `/mail:auth-setup` |

## When nothing fits

If the request is clearly about email but no row above serves it, say what this
plugin can do and ask which the user wants. Do not pick the nearest row.
```

- [ ] **Step 4: Run the validation and confirm it passes (green)**

Run the same `bash -c` block from Step 2.
Expected: no output, exit code 0.

Then run: `bash installers/pii-gauntlet.sh --mode=ci`
Expected: exit code 0.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/validate-plugins.yml plugins/mail/skills/outlook-mail/SKILL.md
git commit -m "feat(mail): natural-language routing skill, plus CI validation

Description states a bounded intent space with labelled samples and an
explicit instruction to judge by meaning, so unanticipated phrasings
still route. Body maps intent to existing commands; no workflow logic is
duplicated.

CI gains three weak structural floors (length, Greek text, negative
boundary) to stop a future edit regressing to a description that never
fires. They are deliberately not rules about which phrases appear."
```

---

### Task 3: `teams-chat` skill

**Files:**

- Create: `plugins/chat/skills/teams-chat/SKILL.md`

**Interfaces:**

- Consumes: the `Validate skill frontmatter` CI step from Task 2.
- Produces: nothing later tasks depend on.

This skill carries the strictest no-match rule in the plan, because `/chat-reply` auto-sends (Task 1, Step 4). Ambiguity must land on a read-only command.

- [ ] **Step 1: Write the skill**

Create `plugins/chat/skills/teams-chat/SKILL.md`:

```markdown
---
name: teams-chat
description: Anything to do with the user's Microsoft Teams conversations: seeing what came in, catching up on a thread or a channel, working out who is waiting on a response, and replying. Use this whenever a request concerns Teams, chats, channels or direct messages, however it is phrased, for example "what did I miss", "is anyone waiting on me", "catch me up on the project channel", "tell them I am running late", or in Greek «τι έγινε όσο έλειπα», «με έχει ψάξει κανείς», «τι λέει το κανάλι», «πες τους ότι θα αργήσω». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for email (use outlook-mail), for preparing or debriefing a meeting (use meeting-workflows), or for building presentations or documents.
---

# Microsoft Teams chat

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| see what came in and what is unread | `/chat:chat-inbox` |
| catch up on one conversation | `/chat:chat-summarize` |
| catch up on a channel over a period | `/chat:chat-channel-digest` |
| answer someone | `/chat:chat-reply` |
| fix Teams access or authentication | `/chat:chat-doctor`, `/chat:auth-setup` |

## When nothing fits

`/chat:chat-reply` sends the message. Never route to it on inference.

Reach it only when the request unambiguously asks to answer someone and the
target conversation is unambiguous. If either is unclear, run
`/chat:chat-inbox` or `/chat:chat-summarize` so the user can see the context
and say what they want, then ask. Showing the user their messages is always a
safe wrong answer; sending on a guess is not.
```

- [ ] **Step 2: Validate**

Run the `bash -c` validation block from Task 2 Step 2, then `bash installers/pii-gauntlet.sh --mode=ci`.
Expected: both exit 0.

- [ ] **Step 3: Commit**

```bash
git add plugins/chat/skills/teams-chat/SKILL.md
git commit -m "feat(chat): natural-language routing skill

No-match rule is stricter here than elsewhere: chat-reply sends, so
ambiguity routes to chat-inbox or chat-summarize and asks, never to
chat-reply on inference."
```

---

### Task 4: `presentations` skill

**Files:**

- Create: `plugins/decks/skills/presentations/SKILL.md`

**Interfaces:**

- Consumes: the `Validate skill frontmatter` CI step from Task 2.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the skill**

Create `plugins/decks/skills/presentations/SKILL.md`:

```markdown
---
name: presentations
description: Anything to do with building, improving or reviewing slide decks: producing a deck from a brief or from raw content, redesigning an existing one, tightening slides that already work, preparing a full-bleed keynote for a stage talk, and reviewing a deck before it ships. Use this whenever the deliverable is slides, however the request is phrased, for example "I need something for the board on Thursday", "make this presentable", "this deck is a mess", "I am speaking at the conference", or in Greek «θέλω κάτι για το ΔΣ», «φτιάξε μου διαφάνειες», «κάν' το πιο παρουσιάσιμο», «ετοιμάζω μια ομιλία». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for Word documents, letters or memos (use word-documents), for email (use outlook-mail), or for analysing a spreadsheet, including turning one into slides (use spreadsheets).
---

# Presentations

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| a new deck from a brief or from content | `/decks:create-presentation` |
| a dark full-bleed deck for a stage talk | `/decks:create-keynote` |
| an existing deck rebuilt to standard | `/decks:redesign-deck` |
| existing slides tightened, not rebuilt | `/decks:polish-slides` |
| a deck checked before it ships | `/decks:presentation-review` |

The line between redesign and polish is scope: redesign changes structure and
layout, polish leaves both alone. If the user's intent sits between the two,
ask which they mean rather than choosing.

## When nothing fits

If the request is clearly about slides but no row above serves it, say what
this plugin can do and ask. Do not pick the nearest row.

A request that starts from a spreadsheet belongs to the spreadsheets skill,
which owns `/excel:excel-to-deck`, even though the output is a deck.
```

- [ ] **Step 2: Validate**

Run the `bash -c` validation block from Task 2 Step 2, then `bash installers/pii-gauntlet.sh --mode=ci`.
Expected: both exit 0.

- [ ] **Step 3: Commit**

```bash
git add plugins/decks/skills/presentations/SKILL.md
git commit -m "feat(decks): natural-language routing skill

Cedes spreadsheet-sourced decks to the spreadsheets skill, which owns
excel-to-deck, so 'turn this file into slides' is not torn in two."
```

---

### Task 5: `spreadsheets` skill

**Files:**

- Create: `plugins/excel/skills/spreadsheets/SKILL.md`

**Interfaces:**

- Consumes: the `Validate skill frontmatter` CI step from Task 2.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the skill**

Create `plugins/excel/skills/spreadsheets/SKILL.md`:

```markdown
---
name: spreadsheets
description: Anything to do with reading, analysing or explaining spreadsheet data: summarising what a workbook contains, pivoting and regrouping it, explaining why a number moved against plan or against last period, and handing the analysis to a deck. Use this whenever the subject is a spreadsheet or the numbers inside one, however the request is phrased, for example "what is going on in this file", "why is Q3 short", "break it down by region", "I need this in slides for tomorrow", or in Greek «τι λέει αυτό το αρχείο», «γιατί πέφτει το τρίμηνο», «σπάσ' το ανά μονάδα», «κάν' το παρουσίαση». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for Word documents (use word-documents), for email (use outlook-mail), or for building a deck that does not start from spreadsheet data (use presentations).
---

# Spreadsheets

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| understand what a workbook holds | `/excel:excel-summary` |
| regroup or cross-tabulate the data | `/excel:excel-pivot` |
| explain a gap against plan, budget or a prior period | `/excel:excel-variance` |
| carry the analysis into slides | `/excel:excel-to-deck` |

`/excel:excel-to-deck` stays here rather than in presentations, because the
work starts from the data. Route "turn this file into slides" here.

## When nothing fits

If the request is clearly about a spreadsheet but no row above serves it, say
what this plugin can do and ask. Do not pick the nearest row.
```

- [ ] **Step 2: Validate**

Run the `bash -c` validation block from Task 2 Step 2, then `bash installers/pii-gauntlet.sh --mode=ci`.
Expected: both exit 0.

- [ ] **Step 3: Commit**

```bash
git add plugins/excel/skills/spreadsheets/SKILL.md
git commit -m "feat(excel): natural-language routing skill"
```

---

### Task 6: `word-documents` skill

**Files:**

- Create: `plugins/docs/skills/word-documents/SKILL.md`

**Interfaces:**

- Consumes: the `Validate skill frontmatter` CI step from Task 2.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the skill**

Create `plugins/docs/skills/word-documents/SKILL.md`:

```markdown
---
name: word-documents
description: Anything to do with producing a formal written document in Word: a structured document from a brief, a business letter to an external party, or an internal memo. Use this whenever the deliverable is a written document rather than slides or an email, however the request is phrased, for example "I need this in writing", "something official for the regulator", "write it up properly", "put it on letterhead", or in Greek «γράψ' το επίσημα», «θέλω μια επιστολή», «κάν' το σημείωμα», «βγάλ' το σε Word». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for slide decks (use presentations), for email, including formal email (use outlook-mail), or for reading spreadsheets (use spreadsheets).
---

# Word documents

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| a structured document from a brief or content | `/docs:docs-create` |
| a formal letter to someone outside the organisation | `/docs:docs-letter` |
| an internal memo | `/docs:docs-memo` |

Letter versus memo is audience, not tone: a letter goes outside, a memo stays
inside. If the audience is unclear, ask.

## When nothing fits

If the request is clearly about a written document but no row above serves it,
say what this plugin can do and ask. Do not pick the nearest row.

"Formal" alone does not mean a document. A formal message sent by email is
still email and belongs to outlook-mail.
```

- [ ] **Step 2: Validate**

Run the `bash -c` validation block from Task 2 Step 2, then `bash installers/pii-gauntlet.sh --mode=ci`.
Expected: both exit 0.

- [ ] **Step 3: Commit**

```bash
git add plugins/docs/skills/word-documents/SKILL.md
git commit -m "feat(docs): natural-language routing skill

Guards the common confusion that 'formal' implies a document: a formal
message sent by email is still email."
```

---

### Task 7: `meeting-workflows` skill

**Files:**

- Create: `plugins/meetings/skills/meeting-workflows/SKILL.md`

**Interfaces:**

- Consumes: the `Validate skill frontmatter` CI step from Task 2.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the skill**

Create `plugins/meetings/skills/meeting-workflows/SKILL.md`:

```markdown
---
name: meeting-workflows
description: Anything to do with meetings either side of the meeting itself: working out what is coming up and what the user needs to know before walking in, who the attendees are and what the history with them is, and afterwards capturing what was decided and what everyone owes. Use this whenever the subject is a meeting, a call or the user's schedule, however the request is phrased, for example "who am I seeing tomorrow", "what do I need before this call", "what did we actually agree", "who owns what now", or in Greek «τι έχω αύριο», «τι πρέπει να ξέρω πριν τη σύσκεψη», «τι αποφασίσαμε τελικά», «κράτα τα action items». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for sending the follow-up email itself (use outlook-mail), for Teams chats and channels (use teams-chat), or for building the deck shown in the meeting (use presentations).
---

# Meeting workflows

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| to be ready for something coming up | `/meetings:meeting-prep` |
| to capture what came out of something that happened | `/meetings:meeting-debrief` |

Tense decides: before the meeting is prep, after it is debrief. If the user
refers to a meeting without making the tense clear, ask which they mean rather
than inferring from the calendar.

## When nothing fits

If the request is clearly about a meeting but neither row serves it, say what
this plugin can do and ask. Do not pick the nearer row.

Writing and sending the follow-up mail is mail work: hand it to outlook-mail
once the debrief has captured the content.
```

- [ ] **Step 2: Validate**

Run the `bash -c` validation block from Task 2 Step 2, then `bash installers/pii-gauntlet.sh --mode=ci`.
Expected: both exit 0.

- [ ] **Step 3: Commit**

```bash
git add plugins/meetings/skills/meeting-workflows/SKILL.md
git commit -m "feat(meetings): natural-language routing skill"
```

---

### Task 8: Document the trigger surface

**Files:**

- Create: `docs/skill-triggers.md`
- Modify: `README.md` (new subsection under `## Architecture`, before `### Bundled MCP servers` at line 155)

**Interfaces:**

- Consumes: all six skills, Tasks 2 to 7.
- Produces: `docs/skill-triggers.md`, which Task 9 appends its results to.

- [ ] **Step 1: Write `docs/skill-triggers.md`**

```markdown
# Skill triggers

Each plugin ships one skill, so you can describe what you want instead of
remembering a command. Both Greek and English work.

This page deliberately does NOT list accepted phrasings. There is no phrase to
learn. Say what you want the way you would say it to a colleague, and the
request should reach the right plugin. If it does not, that is a defect in the
skill, not in how you asked. Report it.

## What each skill owns

| Skill | Plugin | Owns | Does not own |
|---|---|---|---|
| `outlook-mail` | `mail` | The Outlook mailbox: reading it, deciding what matters, composing what goes out | Teams messages, meeting prep and debrief, spreadsheets, Word documents |
| `teams-chat` | `chat` | Teams conversations: what came in, catching up, replying | Email, meeting prep and debrief, presentations, documents |
| `presentations` | `decks` | Slide decks: creating, redesigning, polishing, reviewing | Word documents, email, decks that start from a spreadsheet |
| `spreadsheets` | `excel` | Spreadsheet data: summarising, pivoting, variance, and carrying it into slides | Word documents, email, decks not sourced from data |
| `word-documents` | `docs` | Formal written documents: structured documents, letters, memos | Slides, email including formal email, spreadsheets |
| `meeting-workflows` | `meetings` | Either side of a meeting: preparation and debrief | Sending the follow-up email, Teams chats, the deck shown in the meeting |

## How overlaps are resolved

Route on the object of the request, not the verb. Verbs are shared across the
whole marketplace; the object is what identifies the domain.

| Verb, in either language | The object decides |
|---|---|
| summarise, σύνοψη, περίληψη | a file or spreadsheet goes to `spreadsheets`; a chat or Teams thread to `teams-chat`; a mailbox or mail thread to `outlook-mail`; a meeting that already happened to `meeting-workflows` |
| send, reply, στείλε, απάντησε | mail, Outlook or a person's address goes to `outlook-mail`; Teams, chat or μήνυμα to `teams-chat` |
| make, build, φτιάξε | presentation, slides or deck goes to `presentations`; document, letter, memo or Word to `word-documents` |
| prepare, brief, ετοίμασε | an upcoming meeting goes to `meeting-workflows`; anything else follows its own object |

Two standing exceptions, where the object rule would split work that belongs
together:

- `excel-to-deck` stays with `spreadsheets`, because the work starts from data.
- `meeting-workflows` yields to `outlook-mail` when the object is an email that
  merely concerns a meeting, because the work is mail work.

## When a skill is unsure

Every skill ends with a no-match rule: if a request sits inside its domain but
no command clearly serves it, the skill says what it can do and asks. It does
not pick the nearest command.

This matters most in `chat`, where `/chat-reply` sends the message. That
command is reached only when the request unambiguously asks to answer someone
and the target conversation is unambiguous. Otherwise the skill shows you your
messages and asks.
```

- [ ] **Step 2: Add the README subsection**

In `README.md`, insert immediately before `### Bundled MCP servers` (line 155):

```markdown
### Natural-language triggering

Every plugin ships one skill, so you do not have to know a command name. Ask
for what you want, in Greek or English, and the request routes to the right
workflow: "what needs my attention today", «τι έγινε στα Teams όσο έλειπα»,
"I need something for the board on Thursday".

Commands still work and are still the precise way to invoke a specific
workflow. The skills are an additional entry point, not a replacement.

Domains, boundaries, and how overlaps resolve: [`docs/skill-triggers.md`](docs/skill-triggers.md).
```

- [ ] **Step 3: Verify links and validation**

Run: `bash installers/pii-gauntlet.sh --mode=ci`
Expected: exit 0.

Run: `python3 scripts/validate_consistency.py --verbose`
Expected: exit 0. This script iterates plugin directories and inspects `commands/`; a new `skills/` directory is ignored by it and must not cause a failure. If it does fail, the failure is a real incompatibility and must be fixed here rather than worked around.

Run: `test -f docs/skill-triggers.md && grep -q 'skill-triggers.md' README.md && echo "link OK"`
Expected: `link OK`.

- [ ] **Step 4: Commit**

```bash
git add docs/skill-triggers.md README.md
git commit -m "docs: describe the natural-language trigger surface

Deliberately documents domains and boundaries rather than accepted
phrasings. Listing phrasings would teach colleagues to speak in commands
again, which is the problem this work exists to remove."
```

---

### Task 9: Held-out smoke test

**Files:**

- Modify: `docs/skill-triggers.md` (append a results section)

**Interfaces:**

- Consumes: all six skills and the documentation, Tasks 2 to 8.
- Produces: a recorded pass or fail for each of sixteen cases.

**What "held out" means here.** A domain noun may appear in a case; that is
what the model keys on and avoiding it would make the test meaningless. What
must NOT appear is a phrasing lifted from a description. The bar is mechanical:
no case may share a contiguous run of three or more words with any description.

- [ ] **Step 0: Prove the cases are held out before running any of them**

```bash
python3 - <<'PY'
import re, glob, unicodedata

CASES = [
 "ο Παπαδόπουλος μου είχε στείλει κάτι την Τρίτη και δεν το βρίσκω πουθενά",
 "the migration thread exploded overnight, where did it land",
 "the steering committee gave me a forty minute slot and I have nothing to put on screen",
 "τα νούμερα του Ιουνίου δεν βγαίνουν με τον προϋπολογισμό, δες τα",
 "the committee needs this circulated internally as a formal record",
 "σε μισή ώρα μπαίνω με τη Nova και δεν θυμάμαι πού είχαμε μείνει",
]

def words(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.findall(r"\w+", s, re.UNICODE)

descs = []
for f in glob.glob("plugins/*/skills/*/SKILL.md"):
    t = open(f, encoding="utf-8").read()
    m = re.search(r"^description: (.+)$", t, re.M)
    if m:
        descs.append((f, words(m.group(1))))

def runs(w, n):
    return {tuple(w[i:i+n]) for i in range(len(w)-n+1)}

bad = 0
for i, case in enumerate(CASES, 1):
    cw = words(case)
    worst = 0; where = ""
    for f, dw in descs:
        for n in range(min(len(cw), 8), 2, -1):
            if runs(cw, n) & runs(dw, n):
                if n > worst: worst, where = n, f
                break
    if worst >= 3:
        print(f"FAIL case {i}: shares a {worst}-word run with {where}")
        bad = 1
    else:
        print(f"ok   case {i}: longest shared run < 3 words")
raise SystemExit(bad)
PY
```

Expected: six `ok` lines, exit 0. On any `FAIL`, rewrite that case with a fresh
phrasing and re-run. Do NOT weaken the threshold, and do NOT edit the
description to make the case pass: the description is the thing under test.

## Method: a scripted probe, not a live session

Revised 2026-08-16, before Task 9 ran. The original method said "in a clean
Claude Code session with all six plugins installed". That is not executable:

- The installed marketplace is a separate clone under
  `~/.claude/plugins/marketplaces/`, not this worktree, and it contains no
  skills. The new skills are live nowhere.
- Making them live would mean repointing the maintainer's live plugin
  configuration at an unmerged branch, so their own working sessions would
  start triggering skills that are still under review. That is a side effect
  outside this worktree and is not ours to take.
- Testing after merge is circular: this test is what gates the merge.

Instead, drive the local `claude` CLI headlessly, once per case. This measures
the real artifact, because skill selection IS a model reading descriptions and
choosing. Verified working: source `~/.config/nbg-vertex/env`, export
`ANTHROPIC_MODEL` and `CLOUD_ML_REGION` from it, then
`claude --print --model sonnet`. Strip the leading terminal escape sequence
from the output before parsing.

Two probe shapes:

**Shape A** (cases 1 to 10, 15, 16): build the prompt from the six
descriptions extracted live from the `SKILL.md` files, present the user's
phrasing, and ask which single skill should handle it or `NONE`. Answer must
be a bare skill name or `NONE`.

**Shape B** (cases 11 to 14): these test behaviour inside a skill, not which
skill fires. Supply the full text of the named skill's `SKILL.md`, present the
phrasing, and ask which command it would run or whether it would ask the user
first. Answer must be a bare command name or `ASK`.

Each case runs in its own CLI invocation so no case can see another's answer.

Honest limitation, to be recorded with the results: in a real session other
installed marketplaces' skills also compete for the same request, and the model
sees the whole conversation rather than one phrasing. This harness isolates the
descriptions, which makes it a clean measurement of the descriptions and an
optimistic one for a busy session. Recommend a real-session spot check of three
or four cases after merge.

- [ ] **Step 1: Run the six oblique cases (Shape A)**

None names its domain noun directly.

| # | Phrasing | Must route to |
|---|---|---|
| 1 | «ο Παπαδόπουλος μου είχε στείλει κάτι την Τρίτη και δεν το βρίσκω πουθενά» | `outlook-mail` |
| 2 | "the migration thread exploded overnight, where did it land?" | `teams-chat` |
| 3 | "the steering committee gave me a forty minute slot and I have nothing to put on screen" | `presentations` |
| 4 | «τα νούμερα του Ιουνίου δεν βγαίνουν με τον προϋπολογισμό, δες τα» | `spreadsheets` |
| 5 | "the committee needs this circulated internally as a formal record" | `word-documents` |
| 6 | «σε μισή ώρα μπαίνω με τη Nova και δεν θυμάμαι πού είχαμε μείνει» | `meeting-workflows` |

- [ ] **Step 2: Run the four verb-collision cases (Shape A)**

One per row of the tie-break policy. Each uses a shared verb, so only the object can decide.

| # | Phrasing | Must route to | Because the object is |
|---|---|---|---|
| 7 | «κάνε μου μια σύνοψη από το κανάλι» | `teams-chat` | a channel |
| 8 | «στείλε του ότι το είδα» (after discussing a Teams thread) | `teams-chat` | a Teams conversation |
| 9 | «φτιάξε μου κάτι επίσημο για τον πελάτη» | `word-documents` | a formal written document |
| 10 | «ετοίμασέ με για τη Δευτέρα» | `meeting-workflows` | an upcoming meeting |

- [ ] **Step 3: Run the four no-match cases (Shape B)**

Each is inside a plugin's domain but served by no command. The skill must say what it can do and ask, not run the nearest command.

| # | Phrasing | Skill | Must NOT |
|---|---|---|---|
| 11 | «διάγραψε όλα τα μέιλ από τον Ιούνιο» | `outlook-mail` | run `triage-inbox` or `archive-thread` |
| 12 | «στείλε το ίδιο μήνυμα σε δέκα άτομα» | `teams-chat` | run `chat-reply` |
| 13 | "convert this deck to PDF" | `presentations` | run `polish-slides` |
| 14 | «κλείσε μου ραντεβού με τον Νίκο» | `meeting-workflows` | run `meeting-prep` |

Case 12 is the most important in the plan. `/chat-reply` sends.

- [ ] **Step 4: Run the two out-of-domain cases (Shape A)**

| # | Phrasing | Expected |
|---|---|---|
| 15 | "what is the weather in Athens" | no skill fires |
| 16 | «τι λέει το χαρτοφυλάκιό μου σήμερα;» | no marketplace skill fires (this belongs to a different marketplace) |

- [ ] **Step 5: Record the results**

Append to `docs/skill-triggers.md`:

```markdown
## Trigger test, 2026-08-16

Sixteen held-out cases, none reusing a phrase from any description. Recorded
so a future change can be re-tested against the same bar.

| # | Phrasing | Expected | Actual | Pass |
|---|---|---|---|---|
```

Fill one row per case with the skill that actually fired.

- [ ] **Step 6: Fix any miss correctly**

For each failing case, widen the domain statement or sharpen a boundary clause
in the relevant description.

Do NOT add the missed phrasing as an exemplar. That would make the case pass
while leaving the real gap open, and it reintroduces the enumeration this
design rejects. If three or more cases miss for one skill, the domain statement
is wrong rather than narrow: rewrite it.

After any edit, re-run the full sixteen. A fix for one skill can shift a
boundary and break another.

- [ ] **Step 7: Commit**

```bash
git add docs/skill-triggers.md plugins/*/skills/*/SKILL.md
git commit -m "test: held-out trigger smoke test, sixteen cases

None of the phrasings appears in any description, so the test measures
generalisation rather than recall. Misses are fixed by widening the
domain or sharpening a boundary, never by adding the missed phrase."
```

- [ ] **Step 8: Full verification before handing back**

```bash
bash installers/pii-gauntlet.sh --mode=ci
python3 scripts/validate_consistency.py --verbose
git log --oneline master..HEAD
git status --porcelain
```

Expected: first two exit 0, nine commits listed, working tree clean.
