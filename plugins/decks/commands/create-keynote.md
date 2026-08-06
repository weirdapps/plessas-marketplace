---
description: "Create a dark full-bleed NBG keynote for a stage talk (Standard #21)"
argument-hint: "[talk topic, audience, and venue]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep, Skill(manage-nano-banana)
---

<objective>
Build an NBG **keynote**: a dark, cinematic, full-bleed deck for a talk delivered live from a stage.

User request: $ARGUMENTS
</objective>

<critical>
This is NOT the command for normal decks. Keynote mode is **Standard #21**, the single sanctioned
exception to the light-mode NBG format, and it is fenced. Check the entry criteria FIRST. If the
deck does not qualify, stop and use `/create-presentation` instead.
</critical>

<process>

### Step 1 — Gate on the entry criteria (do this before anything else)

Read `${CLAUDE_PLUGIN_ROOT}/shared/brand-system/keynote.md`.

All four must hold:

1. Audience is **external or bank-wide** — conference, town hall, industry panel. NOT a committee,
   board or ExCo working session.
2. **Delivered live from a stage by a speaker.** Not read alone, not circulated as a document.
3. **Projected large, in a darkened room.**
4. The slides are the **backdrop, not the record** — the argument lives in the speaker notes.

If any of these is unclear from `$ARGUMENTS`, ask. If any fails, say so plainly and switch to
`/create-presentation`. Never for ExCo, board, credit committee, or a deck someone else will edit:
keynote slides are flattened images and can only be regenerated from their YAML.

### Step 2 — Storyline

Dispatch `decks:storyline-architect` with the brief, telling it this is a **spoken keynote**:

- Roughly 12-18 slides. One idea per slide, nothing more.
- The arc: cover → the consensus → the challenger or the evidence → the complication → the reality
  → the turn (divider) → two or three moves → the moat or the payoff → closing line → back cover.
- Every slide needs a **spoken note**, and the note carries the argument. The slide carries at most
  one sentence or one number.
- Action titles throughout. No bullets except on a single `points` slide.
- No em-dashes. No invented NBG names or figures — every number needs a source.

### Step 3 — Choose an archetype per slide

Map each message to one of the nine archetypes in `keynote.md`:

| The slide needs to say | Archetype |
|---|---|
| who is speaking, about what | `cover` |
| one sentence and nothing else | `statement` |
| one number carries the slide | `hero-stat` |
| two numbers in tension | `duo-stat` |
| a comparison across categories | `bars` (max 2 in the deck, max 7 bars) |
| three things a regulator or market did | `points` |
| the talk turns here | `divider` |
| the line to repeat afterwards | `closing` |
| the end | `back` |

### Step 4 — Imagery

Keynote photography is cinematic, dark, and blue-teal graded: night cityscapes, architecture,
close detail, interiors with practical lights. Never stock-smiling people, never bright daylight.

Source it, in this order:
1. Ask the user for photographs they already have.
2. Generate with `Skill(manage-nano-banana)` — prompt for a dark, blue-teal-graded, cinematic frame
   at 16:9 with negative space on the side the text will occupy.

Save images to a working directory under `~/Downloads`, never in the repo.

### Step 5 — Write the YAML

Start from `${CLAUDE_PLUGIN_ROOT}/tools/nbg-keynote/example.yaml`. Set `meta.language: el` for a
Greek talk so the kickers drop the tonos in all-caps. Set `meta.output` to
`~/Downloads/YYYYMMDDHHMM_<talk_name>` — get the timestamp with
`TZ='Europe/Athens' date '+%Y%m%d%H%M'`, never guess it, and never add a version suffix.

Quote any string containing a comma or a colon. Inline flow maps split on commas.

### Step 6 — Validate, then build

```bash
cd ${CLAUDE_PLUGIN_ROOT}/tools/nbg-keynote
python3 nbg_keynote.py <spec>.yaml --validate    # fails on missing notes, >2 charts, bad images
python3 nbg_keynote.py <spec>.yaml
```

The compositor writes both a `.pptx` and a `.pdf`. **Take contrast warnings seriously** — they mean
a photograph is too bright under a text block; swap the image or move the text with `align`.

### Step 7 — Review

Read the generated PDF back and check every slide:

- Text sits clear of the imagery and reads at a glance.
- Kickers, titles and footers align to the 155px gutter.
- The Greek wordmark is on every slide.
- No slide carries more than one idea.
- Every slide has a speaker note.

Report both output paths. Offer to re-render individual slides with `--slides N`.

</process>

<constraints>
- Read `${CLAUDE_PLUGIN_ROOT}/shared/brand-system/keynote.md` before writing any YAML.
- Never edit the generated PPTX by hand — change the YAML and re-render.
- Never commit photographs or generated decks to the repo. Everything goes to `~/Downloads`.
- Greek wordmark always, even on an English talk. There is no English NBG logo.
- No em-dashes, no invented NBG names, no version suffixes in filenames.
</constraints>
