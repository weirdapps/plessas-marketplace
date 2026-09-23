---
description: "Learn the user's presentation preferences from their own edits: compare a deck they finalised with the draft this plugin built, and record repeated patterns in their personal style preferences"
argument-hint: "[path to the finalised .pptx]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__plugin_mail_outlook-bridge__outlook_list_mail, mcp__plugin_mail_outlook-bridge__outlook_get_mail, mcp__plugin_mail_outlook-bridge__outlook_download_attachments
---

<objective>
Learn how this user edits the decks the plugin builds, so the next deck needs fewer edits. This
command only learns from edits to a deck the plugin built. To check a deck before it ships, use
`/decks:review-deck`.

User request: $ARGUMENTS
</objective>

<rules>
- Everything this command writes lives in `${CLAUDE_PLUGIN_DATA}`: the comparison records and
  `${CLAUDE_PLUGIN_DATA}/style-preferences.md`. Never write into the plugin folder; the shipped
  Standards change only through a deliberate commit.
- Tools run as `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`; exit 2 means the tool could
  not run (most often its environment could not be prepared): show the message and fix it printed
  and stop.
- Extract decks with `decks-py extract`, not the `document-skills:pptx` skill; if that skill loads
  anyway, the NBG Standards override its advice.
</rules>

<process>

### 1. Find the draft record

Draft records are written by `decks-py record` when a deck ships: one YAML file per deck in
`${CLAUDE_PLUGIN_DATA}/presentations/pending/`, with `id`, `created`, `status`, `topic`,
`file_path`, `file_hash` (`sha256:<hex>`), `spec_path`, `slides` (`index`, `id`, `type`, `title`)
and `spec`, a full snapshot of the deck spec it was built from. If there are none, say that there
is no draft to compare against, and stop.

- A path was given: match it to the record whose `file_path` has the same file name, else list
  the pending records (`created`, `topic`, file) and ask which one it finalises.
- No path given: look for the finalised version of each pending record, newest first:
  1. The file at `file_path` still exists and its hash (`shasum -a 256`) differs from
     `file_hash`: that is the edited deck.
  2. The mail plugin, when its tools are available: `mcp__plugin_mail_outlook-bridge__outlook_list_mail`
     on Sent Items, then on any folder the user names, with `since` set to the record's `created`
     and `top: 25`; `mcp__plugin_mail_outlook-bridge__outlook_get_mail` on messages whose `.pptx`
     attachment name shares the record's slug; keep only messages that deliver the deck (not review
     requests); `mcp__plugin_mail_outlook-bridge__outlook_download_attachments` with
     `out: ${CLAUDE_PLUGIN_DATA}/work/review_<record id>/` (create it with `mkdir -p` first).
  3. Otherwise ask for the path.

  Show what you found and ask the user to confirm before comparing.

### 2. Compare

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" extract "<final.pptx>"
```

The extract gives one `## Slide N: <title>` section per slide, with bullets, tables, charts as
tables, `[image: ...]` markers and `Notes:`. Compare it with the record's `spec` and `slides`, slide
by slide: title rewrites, reordering, points added,
removed or reworded, slide type or chart type swaps, slides added or deleted, cover subtitle and
speaker notes. Classify each slide:

| Class | Meaning |
|---|---|
| `USED_AS_IS` | no change beyond formatting |
| `MODIFIED` | title reworded, points edited or type changed |
| `HEAVILY_REWRITTEN` | different content, structure or visual |
| `NOT_USED` | deleted from the final |
| `NEW` | added by the user |

### 3. Save the comparison

Write `${CLAUDE_PLUGIN_DATA}/presentations/reviewed/<record id>.review.yaml` with the record id,
both file paths, the finalised deck's hash as `final_hash` (never `file_hash`, which marks a draft
record and makes `/decks:polish-slides` treat the file as shipped unedited), the date, the
per-slide classes with before and after titles, and the patterns you saw. Then set the draft record's `status` to `reviewed` and move it from `pending/`
to `reviewed/`.

### 4. Update the preferences

Read every `*.review.yaml` in `${CLAUDE_PLUGIN_DATA}/presentations/reviewed/` and count, for each
pattern, the reviews it appears in. Every pattern goes into the Learned table: seen in one review it
is a hint the agents lean toward; seen in two or more it is a rule for this user. Write
`${CLAUDE_PLUGIN_DATA}/style-preferences.md` in this shape, keeping the Defaults section the user
writes by hand:

```markdown
# Presentation style preferences

Learned by /decks:presentation-review from edits to decks the plugin built. An overlay on the
shipped Standards: a numbered Standard wins any conflict.

## Defaults
- Cover subtitle: <what this user puts on covers, e.g. their unit names, pipe-separated>

## Learned
| Preference | Reviews | Last seen | Confidence |
|---|---|---|---|
| <e.g. titles lead with the number> | 3 | <date> | medium |
| <e.g. one chart per slide, no bullets beside it> | 1 | <date> | hint |
```

Confidence is `hint` at 1 review, `medium` at 2 or 3, and `high` at 4 or more. A pattern that
contradicts a numbered Standard is listed under a `## Not applied` heading with the Standard's
number, never in the Learned table. The storyline and storyboard agents read this file on every
build.

### 5. Report

The slide counts per class, the patterns in this deck, and which rows were added or strengthened,
naming each hint that one more review would turn into a rule.

</process>
