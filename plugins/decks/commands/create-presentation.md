---
description: "Build a new NBG-branded deck from a brief, notes, a document, an email thread or a deck spec, then deliver a .pptx that passed the QA gate"
argument-hint: "<brief, file path or deck.yaml> [--from-email <subject>] [folder to save in]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep, mcp__plugin_mail_outlook-bridge__outlook_list_mail, mcp__plugin_mail_outlook-bridge__outlook_get_mail
---

<objective>
Build a board-ready NBG deck from the user's material and deliver a `.pptx` that passed the QA
gate, or say plainly why it did not.

User request: $ARGUMENTS
</objective>

<rules>
- You orchestrate from this conversation. Dispatch each stage's agent with the Agent tool; agents
  never dispatch agents. If the Agent tool is unavailable or denied, do the stage yourself: Read
  `${CLAUDE_PLUGIN_ROOT}/agents/<agent>.md` and follow it, reading any `CLAUDE_PLUGIN_ROOT` or
  `CLAUDE_PLUGIN_DATA` placeholder in it as the same plugin and data folders this command uses.
- Every tool runs as `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`. The first call of a
  tool prepares its environment and can take a minute. Exit 2 from any command means it could not
  run, most often because its environment could not be prepared: tell the user the message and the
  fix it printed. The storyline and the outline checkpoint (steps 3 and 4) still run, since they
  need no build; stop before step 5 until the fix is applied.
- `deck.yaml` (format: `${CLAUDE_PLUGIN_ROOT}/tools/nbg-presentation/deck.schema.json`) is the only
  hand-off between stages. Pass paths, never payloads.
- The builder renders the deck. Nobody writes PptxGenJS, python-pptx or OOXML, and the
  `document-skills:pptx` skill is not used here; if it loads anyway, the NBG Standards override its
  typography and margin advice.
- Never invent a figure, source, date or name, and never compute one the material does not state
  (a remainder, total or share), nor a unit or currency it does not name. Never give a stage leave
  to add one in a dispatch prompt. What the material does not say is a question for
  the user.
</rules>

<process>

### 1. Set up

- Deck id: `<timestamp>_<slug>`, the timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'`, the slug
  two to five lowercase words from the topic joined by underscores (no version suffix).
- Work folder, called WORK below: the path
  `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" workdir "${CLAUDE_PLUGIN_DATA}" "<deck id>"` prints. It creates
  `<WORK>/images` and falls back to a temp folder (saying so) when the data folder cannot be written;
  exit 2 means no folder could be written: tell the user its message and stop.
- Output: the folder the user named, else their Downloads folder, always as an absolute path
  (`$HOME/Downloads`; a quoted `~` does not expand). The deck ships as `<folder>/<deck id>.pptx`.
- Preferences: `${CLAUDE_PLUGIN_DATA}/style-preferences.md` if it exists, else `none`. It is the
  user's overlay on the shipped Standards (`${CLAUDE_PLUGIN_ROOT}/shared/presentation-style-guide.md`),
  and a numbered Standard wins any conflict.

Every dispatch prompt carries these lines, filled in, plus the stage's task:

```text
work: <WORK>
deck: <WORK>/deck.yaml
preferences: <path or none>
mode: new | redesign | preserve
audience / purpose / language: <as known>
material: <brief text, or a path>
```

Quote the material in a dispatch prompt as it is written: never abbreviate, paraphrase or
summarise a figure, a source, a period or an agreed point there.

### 2. Gather the material

- Text in the request: the brief.
- A `.pptx` or `.pdf` path:
  `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" extract "<file>" > "<WORK>/source.md"`, and the material
  is that file. Pictures in a deck show there as `[image: ...]`; they are not carried over, so ask
  for the image files of any the new deck must keep. A `.docx` cannot be extracted: ask the user to
  save it as PDF, or to paste the text.
- A `.yaml` deck spec (from `/excel:excel-to-deck` or the user): copy it to `<WORK>/deck.yaml`, and
  bring its files with it. A relative image path (`image.path`, card and step `icon`, image columns,
  custom image elements) resolves against the spec's own folder first, so for each one that exists
  next to the original spec, copy that file into WORK at the same relative path
  (`mkdir -p` its folder first). A relative path that does not exist there is a plugin library
  path, which the builder finds by itself. Then run `check` on it. Skip step 3 unless check fails
  on anything other than missing sources; then dispatch the storyline architect with
  `mode: preserve` and the spec as the material.
- `--from-email <subject>`: `mcp__plugin_mail_outlook-bridge__outlook_list_mail` on the Inbox with
  `top: 50` and `since` 30 days back, match the subject, then
  `mcp__plugin_mail_outlook-bridge__outlook_get_mail` on the match; save the thread text to
  `<WORK>/source.md`. If those tools are missing, the mail plugin is not installed: say so and ask
  for the content.
- A mode line from `/decks:redesign-deck` or `/decks:polish-slides` (`mode: redesign`, or
  `mode: preserve` with a fix list) passes straight to the storyline architect.
- If all four keynote criteria of Standard #21 hold (external or bank-wide audience, delivered live
  from a stage, projected large in a dark room, slides as backdrop), stop and suggest
  `/decks:create-keynote`.

### 3. Storyline

Dispatch `decks:storyline-architect`: write `<WORK>/deck.yaml` from the material and check it. It
returns the read-through, open questions and the check result.

### 4. Outline checkpoint (Standard #14)

Show the user the read-through and every open question in one message, and wait for agreement.
The read-through is the detailed outline Standard #14 asks for: per slide its id, type, action
title, and the figures, points or asks it carries, so the user can agree to what will be on the
slides and not to titles alone.

Skip the wait only if the user already said the outline is agreed or asked you not to stop. Then
stop only for a question that blocks the build: an exhibit without a source, which the builder
refuses. Go on with every other open question unanswered, leave the slide saying only what the
material says, and list those questions with the delivered deck. Apply the answers to `deck.yaml` (fill `content.source`, with an `as_of`
that carries its year, in the full form where you can, such as `Q2 2026` or `FY 2025`; remove the
answered `x-open-questions`), then:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" check "<WORK>/deck.yaml"
```

Go on only at exit 0. Never fill a source the user did not give.

### 5. Storyboard

Dispatch `decks:storyboard-designer`: choose slide types, layouts and visuals in `deck.yaml`, plan
any files it needs, and check it.

### 6. Assets (only when `deck.yaml` has `x-assets`)

Illustrations first, when there are any (kind `illustration`): dispatch `decks:illustrator` for the
request marked `anchor: true` with `candidates: 2`, and wait for it. Every other request then goes
out together in one message, one agent per request: `decks:illustrator` (kind `illustration`, with
`ref: <WORK>/<anchor output>`), `decks:icon-designer` (kind `icon`),
`decks:infographic-specialist` (kind `infographic`), `decks:device-mockup` (kind `mockup`). Give
each its request's fields and `<WORK>/<output>` as the file to write.

An illustrator that returns `unavailable` or `failed` is not retried: put the request's `fallback`
library path in place of its output path in `deck.yaml`, then run `check`. When the anchor itself
is unavailable, every illustration request takes its fallback without being dispatched. Pass the
alt text each illustrator returns to the build.

### 7. Build

Dispatch `decks:graphics-renderer` with the deck, `out: <WORK>/deck.pptx` and the asset results. It
returns the build exit and any violations left. For a missing asset file, dispatch its asset agent
again; for a diagram check says must be redrawn, dispatch `decks:infographic-specialist` again
with the `size_in` the issue names; for a missing source or figure, ask the user; then build again.

### 8. QA gate

Dispatch `decks:presentation-qa` with `pptx: <WORK>/deck.pptx`, the deck and
`render: <WORK>/qa/<cycle>` (cycle 0, 1, 2). Its verdict is PASS, FAIL (with fixes written as
`deck.yaml` edits by slide id) or UNVERIFIED (validator clean, slides not rendered).

On FAIL: apply the fixes to `deck.yaml`; for a fix that asks for an illustration drawn again,
dispatch `decks:illustrator` for that request once more (with the anchor as `ref`, and QA's reason
added to the brief). Then repeat steps 7 and 8. At most 2 fix cycles.

### 9. Deliver

- PASS: `cp "<WORK>/deck.pptx" "<folder>/<deck id>.pptx"`, then record the draft the learning loop
  compares against:

  ```bash
  bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" record "<folder>/<deck id>.pptx" "<WORK>/deck.yaml" --data "${CLAUDE_PLUGIN_DATA}"
  ```

  Report the path, the slide count and the verdict in one line. Then read the delivered file back
  with `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" extract "<folder>/<deck id>.pptx"` and, from that
  output rather than from memory, list the deck as built, one line per slide: its id, its action
  title word for word, the figures it shows, the text of its points, cards or takeaway word for
  word (quoted from that output, not described), and its source line, so the user can check it against
  what they agreed without opening the file. The open questions you add are only what the
  material leaves open: do not question what the user stated (a source they named for every
  figure, wording they agreed), and the reply follows the figure rule too (no sums, remainders
  or shares the material does not state). If `record` exits 2 (the data
  folder cannot be written), the deck still ships: add one line saying the draft record was not
  saved, so `/decks:presentation-review` cannot compare against this deck.
- UNVERIFIED: copy, record and report the same way, and say plainly: "The validator passed; the slides were
  not visually checked because <reason QA gave>."
- FAIL after 2 cycles: do not copy. Say plainly that the deck did not pass, list the remaining
  fixes, and give the path of `<WORK>/deck.pptx`. Copy and record it only if the user then asks to
  ship it as it is.

When a deck shipped, close with: "After you edit the deck, run
`/decks:presentation-review <final.pptx>` and the plugin learns from your changes." If the mail
plugin is installed, offer `/mail:send-mail` with the deck attached.

</process>
