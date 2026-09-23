---
description: "Create a dark full-bleed NBG keynote for a talk delivered live from a stage (Standard #21); not for board, committee or working decks"
argument-hint: "[talk topic, audience and venue]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep, Skill(manage-nano-banana:manage-nano-banana)
---

<objective>
Build an NBG keynote: a dark, cinematic, full-bleed deck for a talk delivered live from a stage.

User request: $ARGUMENTS
</objective>

<critical>
This is NOT the command for normal decks. Keynote mode is Standard #21, the single sanctioned
exception to the light NBG format, and it is fenced. Check the entry criteria first. If the deck
does not qualify, stop and use `/decks:create-presentation`.
</critical>

<process>

### 1. Gate on the entry criteria

Read `${CLAUDE_PLUGIN_ROOT}/shared/brand-system/keynote.md`. All four must hold:

1. The audience is external or bank-wide: conference, town hall, industry panel. Not a committee,
   board or ExCo working session.
2. It is delivered live from a stage by a speaker, not read alone or circulated as a document.
3. It is projected large, in a darkened room.
4. The slides are the backdrop, not the record: the argument lives in the speaker notes.

If any is unclear from the request, ask. If any fails, say so plainly and switch to
`/decks:create-presentation`. Never for ExCo, board, credit committee or a deck someone else will
edit: keynote slides are flattened images and can only be regenerated from their YAML.

### 2. Set up

- Deck id `<timestamp>_<slug>` (timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'`; no version
  suffix), work folder WORK = `${CLAUDE_PLUGIN_DATA}/work/<deck id>/` with an `images/` folder
  (`mkdir -p`).
- Output stem: `<folder>/<deck id>`, where folder is the one the user named, else `$HOME/Downloads`,
  always as an absolute path. The
  compositor writes `<stem>.pptx` and `<stem>.pdf`.
- Tools run as `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`; exit 2 means the tool could
  not run (most often its environment could not be prepared): show the message and fix it printed
  and stop.

### 3. Storyline

Dispatch `decks:storyline-architect` with `mode: keynote`, `work: <WORK>`, the brief, and the talk's
language. It writes and validates `<WORK>/keynote.yaml` and returns a photograph suggestion per
slide and any notes it could not write from the brief. If the Agent tool is unavailable or denied,
Read `${CLAUDE_PLUGIN_ROOT}/agents/storyline-architect.md` and do its keynote mode yourself, reading
any `CLAUDE_PLUGIN_ROOT` placeholder in it as this plugin's folder.

### 4. Imagery

Keynote photography is cinematic, dark and blue-teal graded: night cityscapes, architecture, close
detail, interiors with practical lights. Never stock-smiling people, never bright daylight. For each
slide choose one:

1. A photograph the user already has.
2. No photograph: leave `image` out and the compositor paints the house gradient.
3. A generated frame through `Skill(manage-nano-banana:manage-nano-banana)`, when that skill is
   available: dark, blue-teal graded, cinematic, 16:9, with negative space on the side the text
   occupies.

Copy every image into `<WORK>/images/`, set `meta.assets: <WORK>/images` and give each slide
`image: <file name>` and a `scrim` on the side the text sits. While some photographs are still to
come, validate and preview the layout with `--placeholder-images` (a flat dark stand-in under the
same scrim); never build the final deck with it.

### 5. Finish the YAML

Set `meta.output` to the output stem and `meta.language: el` for a Greek talk (kickers then drop
the tonos in capitals). Quote any string containing a comma or a colon: inline flow maps split on
commas.

### 6. Validate, then build

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" keynote "<WORK>/keynote.yaml" --validate
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" keynote "<WORK>/keynote.yaml"
```

`--validate` lays out every slide with the real fonts and fails on missing notes, more than two
charts, missing or unreadable images, text past the right gutter or into the footer row, a cover
title over two lines, overlapping text blocks and negative bar values; fix the YAML until it
passes. It prints the font file behind each weight: if it fell back to Calibri or DejaVu, tell the
user that Aptos is missing before you build. Take contrast warnings seriously on every text
element: a photograph is too bright under it, so swap the image or move the text with `align`.

### 7. Review

Read `<stem>.pdf` and check every slide:

- Text sits clear of the imagery and reads at a glance.
- Kickers, titles and footers align to the 155 px gutter.
- The Greek wordmark is on every slide.
- No slide carries more than one idea, and every slide has a speaker note.

Report both output paths. To change a slide, edit the YAML and re-render; `--slides N,M`
re-renders those slides plus any slide whose spec, photograph or the compositor changed, and reuses
every unchanged frame.

</process>

<constraints>
- Never edit the generated PPTX by hand; change the YAML and re-render. The
  `document-skills:pptx` skill is not used here.
- Never save photographs or generated decks inside a repository; they live in WORK and the output
  folder.
- Greek wordmark always, even on an English talk. There is no English NBG logo.
- No em dashes, no invented NBG names or figures (every number needs a source), no version
  suffixes in file names.
</constraints>
