---
description: "Polish an existing NBG deck without restructuring it: QA review, then targeted fixes through its deck spec and a rebuild, or a slide-for-slide rebuild when it has no spec"
argument-hint: "<path to .pptx> [folder to save in]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep, Skill(decks:create-presentation)
---

<objective>
Bring an existing deck up to the NBG standard while keeping its structure: the same slides, in the
same order, making the same argument.

User request: $ARGUMENTS
</objective>

<rules>
- Dispatch agents with the Agent tool; agents never dispatch agents. If the Agent tool is
  unavailable or denied, Read `${CLAUDE_PLUGIN_ROOT}/agents/<agent>.md` and do the stage yourself,
  reading any `CLAUDE_PLUGIN_ROOT` or `CLAUDE_PLUGIN_DATA` placeholder in it as the folders this
  command uses.
- Tools run as `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`; exit 2 means the tool could
  not run (most often its environment could not be prepared): show the message and fix it printed
  and stop.
- Only the builder writes a deck. Never edit a `.pptx` directly, never write python-pptx, PptxGenJS
  or OOXML, and never modify the user's file: a polish ships as a new file. The
  `document-skills:pptx` skill is not used here; if it loads anyway, the NBG Standards override its
  typography and margin advice.
- Polish scope: wording, type sizes, the element a slide uses, brand fixes. No reordering and no new
  slides, except splitting a slide QA says is overloaded. Anything bigger is
  `/decks:redesign-deck`.
- Never invent a figure, source or name.
</rules>

<process>

1. **Find the deck.** It must be an existing `.pptx`. Pasted content with no deck is a new deck:
   run `/decks:create-presentation` with it instead.

2. **Find its spec.** Every deck the plugin shipped has a draft record in
   `${CLAUDE_PLUGIN_DATA}/presentations/pending/` or `reviewed/`: a `*.yaml` file with `file_path`,
   `file_hash` (`sha256:<hex>`, the deck as shipped) and `spec_path`. The `*.review.yaml` files next
   to them are comparisons written by `/decks:presentation-review`; they are never draft records.
   Hash the file with `shasum -a 256 "<file>"` (`sha256sum` where `shasum` is missing) and Grep the
   draft records for a `file_hash:` line holding that hex.
   - A draft record matches: this is the deck exactly as shipped. Its `spec_path` is the spec, and
     the folder holding it is OLD. Take the spec route (3a).
   - No draft record matches, but the hex appears in a `*.review.yaml` (the hash of a deck the user
     finalised), or a draft record's `file_path` has this file's name: the user edited the deck
     after it shipped. Ask once: rebuild from that record's spec (their manual edits are lost), or
     polish the edited file as a deck without a spec (3b).
   - Neither: 3b.

3. **Review.** Create the polish's work folder, called WORK: a new deck id
   `<timestamp>_<slug>` (timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'`, the slug of the
   original name), then `mkdir -p "${CLAUDE_PLUGIN_DATA}/work/<new deck id>/images"`. On the spec
   route, copy the spec and every file it references in first, keeping their relative paths:
   `cp -R "<OLD>/." "<WORK>/"`, then `rm -rf "<WORK>/qa"` so no old render is reused.
   Dispatch `decks:presentation-qa` with `pptx: <the user's file>`, `deck: <WORK>/deck.yaml` on the
   spec route (else `none`) and `render: <WORK>/qa/0`. A PASS means there is nothing to polish: say
   so and stop.

   **3a. Spec route.** Apply the fixes that fall inside polish scope to `<WORK>/deck.yaml`, list any
   that fall outside it for the user, then dispatch `decks:graphics-renderer` with
   `out: <WORK>/deck.pptx` and `decks:presentation-qa` again with `render: <WORK>/qa/<cycle>`. At
   most 2 fix cycles. Deliver: on PASS or UNVERIFIED copy to `<folder>/<new deck id>.pptx` (folder:
   the one the user named, else `$HOME/Downloads`, as an absolute path) and run
   `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" record "<folder>/<new deck id>.pptx" "<WORK>/deck.yaml" --data "${CLAUDE_PLUGIN_DATA}"`;
   on FAIL, do not copy, and report the remaining fixes and the build's path.

   **3b. No spec.** Show the fix list (by slide number) and ask once which the user wants:
   - **Rebuild on the NBG builder**, slide for slide: same slides, order and wording, with the fixes
     applied. Before they choose, name the slides whose visuals a deck spec cannot carry (diagrams,
     photos, screenshots that extraction does not recover), since those come back simplified.
     On yes: save the fix list to `<WORK>/fixes.md`, then invoke `/decks:create-presentation`
     through the Skill tool with the file's absolute path, the line
     `mode: preserve (keep every slide, its order and its wording; apply the fix list at <WORK>/fixes.md)`,
     and the folder if the user named one.
   - **Keep the list** and apply it by hand in PowerPoint. The list is the deliverable.

</process>
