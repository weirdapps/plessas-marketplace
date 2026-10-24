---
description: "Build an NBG-branded HTML deck that the reader edits in the browser (text, layout, pictures, slides) and saves as PDF; the same brand and storyline discipline as the PowerPoint decks. With --keynote, an HTML keynote: the dark stage format, still editable"
argument-hint: "[--keynote] <brief, file path or deck.yaml> [folder to save in]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Build an NBG deck as one self-contained, editable HTML file plus its PDF, both checked, or say
plainly why they did not pass.

User request: $ARGUMENTS
</objective>

<rules>
- Use this command when the user asks for an **HTML** presentation (in Greek, «HTML παρουσίαση»),
  and with `--keynote` when they ask for an **HTML keynote** («HTML keynote»): the dark stage
  format of Standard #21 as an editable HTML deck. A plain "presentation" is PowerPoint
  (`/decks:create-presentation`); a plain keynote is `/decks:create-keynote`. Do not switch
  formats on your own.
- **Keynote mode** (`--keynote`, or the request says keynote): also read
  `${CLAUDE_PLUGIN_ROOT}/shared/brand-system/keynote.md` (archetypes, type scale, hard rules) and
  the keynote section of the component guide. The deck is `<main class="deck keynote">`; every
  slide but the back cover carries a speaker note; at most two chart slides of at most seven bars;
  the words live in the notes, the slides are the backdrop. A keynote asked for by name is built
  even if a Standard #21 entry criterion fails: say so in one line and go on.
- Read `${CLAUDE_PLUGIN_ROOT}/shared/brand-system/html-decks.md` before writing any HTML: it is
  the component guide, and its classes are the only layout vocabulary. The numbered Standards in
  `${CLAUDE_PLUGIN_ROOT}/shared/presentation-style-guide.md` apply unchanged (action titles, one
  message per slide, a source on every exhibit, no em dashes, Greek logo).
- Every tool runs as `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`. Exit 2 means it could
  not run: show its message and the fix it printed, and stop. Exit 3 from `html-check` or
  `html-pdf` means no Chrome, Edge or Chromium: deliver the HTML only and say the layout was not
  checked in a browser.
- Write colours and sizes through the design-system variables (`var(--c-teal)`, `var(--fs-body)`),
  never as raw numbers. No `<script>`, no external URL, no shadows.
- Never invent a figure, source, date or name. What the material does not say is a question for
  the user.
- If the Agent tool is unavailable or denied, do the stage yourself: Read
  `${CLAUDE_PLUGIN_ROOT}/agents/<agent>.md` and follow it.
</rules>

<process>

### 1. Set up

- Deck id `<timestamp>_<slug>` (timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'`, slug two
  to five lowercase words joined by underscores, no version suffix).
- WORK = `${CLAUDE_PLUGIN_DATA}/work/<deck id>/`, with `images/` (`mkdir -p`).
- Output folder: the one the user named, else `$HOME/Downloads`, as an absolute path. The deck
  ships as `<folder>/<deck id>.html` and `<folder>/<deck id>.pdf`.
- Preferences: `${CLAUDE_PLUGIN_DATA}/style-preferences.md` if it exists, else none.

### 2. Material

As in `/decks:create-presentation` step 2: text in the request is the brief; a `.pptx` or `.pdf`
goes through `decks-py extract "<file>" > "<WORK>/source.md"`; a `deck.yaml` is copied to
`<WORK>/deck.yaml` and becomes the storyline as it is (skip step 3 unless `decks-py check` fails
on more than missing sources). An existing HTML deck the user wants changed is edited in place
and rebuilt (step 5 onwards).

### 3. Storyline

Dispatch `decks:storyline-architect` with `work: <WORK>`, `deck: <WORK>/deck.yaml`, `mode: new`,
audience, purpose, language and the material. Its `deck.yaml` is the content contract for the
HTML: one message per slide, action titles, the exhibits and their sources. Its slide `type`s and
layout choices are hints only; the HTML uses the components of the guide.

Keynote mode: dispatch it with `mode: keynote` instead; it writes `<WORK>/keynote.yaml` (archetype,
words and speaker note per slide, a photograph suggestion each), which is the contract instead.

### 4. Outline checkpoint (Standard #14)

Show the read-through (id, action title per slide) and every open question in one message and
wait for agreement, unless the user already agreed or asked you not to stop. Apply the answers.
Never fill a source the user did not give.

### 5. Write the deck

Write `<WORK>/deck.src.html` yourself from `deck.yaml`, slide by slide, with the guide's
components: cover, contents for ten slides or more, dividers for sections, content slides, back
cover. Pick each slide's components by its message (numbers that matter: KPI tiles; a comparison:
cards or a table; a trend: bars; a sequence: process). Fill 60-85% of the body (Standard #2.7):
a sparse slide gets `lead` text or a larger exhibit, not empty space.

Pictures: icons from `${CLAUDE_PLUGIN_ROOT}/assets/icons/` (index in its `INDEX.md`), library
illustrations from `${CLAUDE_PLUGIN_ROOT}/assets/illustrations/`. For idea slides (vision,
operating model, before and after) dispatch `decks:illustrator` as `/decks:create-presentation`
step 6 describes, writing into `<WORK>/images/`; on `unavailable`, use the library picture.
Reference every picture by its path; the build inlines it.

Keynote mode: one archetype per slide from `keynote.yaml` (`k-cover`, statement, hero, duo,
`kbars`, points, `k-divider`, `k-closing`, `k-back`), each slide's note in
`<aside class="notes">`. Photographs are required, not optional: the cover, every divider and the
closing stand on one, and so should about a third of the slides. Use the user's own pictures, or,
when `decks-py illustrate --probe` says `ready`, draw them: the cover first as the anchor
(`decks-py illustrate --photo left --brief "<scene>" --out <WORK>/images/cover.jpg`), then every
other one with `--ref <WORK>/images/cover.jpg`, sending them together. Pick each scene for what
the slide says; `--photo` names the side left empty for the text. Without a key and without the
user's pictures, ask for them: do not ship a keynote on the gradient alone. Place each as
`<div class="bg scrim-left"><img src="images/...">` with the scrim on the side the text sits.
Text over a photograph is not measured by the check: judge its contrast on the rendered PNG in
step 7, and change the scrim or the photograph when it does not read from the back of a room.

### 6. Build and check

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" html-build "<WORK>/deck.src.html" "<WORK>/deck.html"
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" html-check "<WORK>/deck.html"
```

Fix every error in `deck.src.html` and build again, at most three rounds. Content past the body
area means too much on the slide: split it or cut words, never shrink type under the floors.

### 7. Look at every slide

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" html-pdf "<WORK>/deck.html" -o "<WORK>/deck.pdf" --png "<WORK>/qa"
```

Read every `<WORK>/qa/slide-NN.png`. Judge each against the Standards: the title states the
message, nothing collides or crowds, the exhibit reads at a glance, colours carry meaning, the
slide is balanced. Fix in `deck.src.html`, rebuild, re-run steps 6 and 7. At most two cycles.
Exit 4 means Aptos was not embedded (another font stood in): the slides were judged with a
substitute font, so say so when you deliver.

### 8. Deliver

Copy `<WORK>/deck.html` and `<WORK>/deck.pdf` to `<folder>/<deck id>.html` and `.pdf`. Report both
paths, the slide count and the result in one line, then tell the user, in their language:

- open the `.html` in Chrome or Edge; double-click text to edit, click a shape to move or resize
  it, right-click for slides, pictures and text boxes;
- **Save** writes the edited deck (keep it: it is the editable master); **PDF** prints it, one
  page per slide (choose Save as PDF);
- to have Claude export or rework an edited copy, give its path: rebuild it with `html-build`
  (keeps their edits, refreshes the editor), check it, export it.

If a check could not run (no browser) or did not pass after two cycles, say so plainly and list
what is left.

</process>
