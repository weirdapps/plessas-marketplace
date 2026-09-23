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
- Tools run as `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`; exit 2 means the environment
  could not be prepared: show the printed fix and stop.
- Extract decks with `decks-py extract`, not the `document-skills:pptx` skill; if that skill loads
  anyway, the NBG Standards override its advice.
</rules>

<process>

### 1. Find the draft record

Draft records are written by `decks-py record` when a deck ships, into
`${CLAUDE_PLUGIN_DATA}/presentations/pending/`. Each names the delivered file, its hash, when it
was built, and the deck spec it was built from. If there are none, say that there is no draft to
compare against, and stop.

- A path was given: match it to a record by file name (the deck id is the name without `.pptx`),
  else list the pending records (date, title, file) and ask which one it finalises.
- No path given: look for the finalised version of each pending record, newest first:
  1. The delivered file still exists and its hash differs from the record's: that is the edit.
  2. The mail plugin, when its tools are available: `mcp__plugin_mail_outlook-bridge__outlook_list_mail`
     on Sent Items, then on any folder the user names, with `since` set to the record's build date
     and `top: 25`; `mcp__plugin_mail_outlook-bridge__outlook_get_mail` on messages whose `.pptx`
     attachment name matches the record's slug; keep only messages that deliver the deck (not review
     requests); `mcp__plugin_mail_outlook-bridge__outlook_download_attachments` with
     `out: ${CLAUDE_PLUGIN_DATA}/work/review_<deck id>/`.
  3. Otherwise ask for the path.

  Show what you found and ask the user to confirm before comparing.

### 2. Compare

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" extract "<final.pptx>"
```

Compare that with the record's spec, slide by slide: title rewrites, reordering, points added,
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

Write `${CLAUDE_PLUGIN_DATA}/presentations/reviewed/<deck id>.review.json` with the record id, both
file paths and hashes, the date, the per-slide classes with before and after titles, and the
patterns you saw. Then move the draft record from `pending/` to `reviewed/`.

### 4. Update the preferences

Read every `*.review.json` in `${CLAUDE_PLUGIN_DATA}/presentations/reviewed/`. A pattern becomes a
preference only when it appears in 2 or more reviews. Write `${CLAUDE_PLUGIN_DATA}/style-preferences.md`
in this shape, keeping the Defaults section the user writes by hand:

```markdown
# Presentation style preferences

Learned by /decks:presentation-review from edits to decks the plugin built. An overlay on the
shipped Standards: a numbered Standard wins any conflict.

## Defaults
- Cover subtitle: <what this user puts on covers, e.g. their unit names, pipe-separated>

## Learned
| Preference | Reviews | Last seen | Confidence |
|---|---|---|---|
| <e.g. titles lead with the number> | 3 | <date> | high |
```

Confidence is `medium` at 2 reviews and `high` at 4 or more. A pattern that contradicts a numbered
Standard is listed under a `## Not applied` heading with the Standard's number, never as a
preference. The storyline and storyboard agents read this file on every build.

### 5. Report

The slide counts per class, the patterns in this deck, and which preferences were added or
strengthened. If nothing reached two reviews yet, say how many more reviews would confirm each
pattern.

</process>
