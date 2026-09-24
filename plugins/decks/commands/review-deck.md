---
description: "Check any .pptx against the NBG brand and content standards before it ships: validator, slide renders and a visual QA review with a fix list. Changes nothing and learns nothing"
argument-hint: "<path to .pptx>"
allowed-tools: Agent, Read, Bash, Glob, Grep
---

<objective>
Tell the user whether their deck is ready to ship, and exactly what to fix if it is not. Read-only:
the deck, the plugin and the user's preferences stay untouched.

User request: $ARGUMENTS
</objective>

<process>

1. **Find the deck.** It must be an existing `.pptx`; ask for the path if the request does not give
   one. A keynote built by `/decks:create-keynote` (dark, full-bleed picture slides) is outside this
   review: say so and stop.

2. **Find its spec**, so fixes can name slide ids: hash the file with `shasum -a 256 "<file>"`
   (`sha256sum` where `shasum` is missing) and Grep the draft records in
   `${CLAUDE_PLUGIN_DATA}/presentations/pending/` and `reviewed/` (every `*.yaml` except
   `*.review.yaml`) for a `file_hash:` line holding that hex. A match means the deck is exactly as
   the plugin shipped it, and that record's `spec_path` is the spec. With no match (the deck was
   edited after it shipped, or the plugin never built it), fixes name slide numbers.

3. **Review.** Render folder: `${CLAUDE_PLUGIN_DATA}/work/review_<timestamp>/`, the timestamp from
   `TZ='Europe/Athens' date '+%Y%m%d%H%M'`. Dispatch `decks:presentation-qa` with `pptx: <file>`, the
   spec or `none`, and `render: <that folder>`. If the Agent tool is unavailable or denied, Read
   `${CLAUDE_PLUGIN_ROOT}/agents/presentation-qa.md` and run the review yourself, reading any
   `CLAUDE_PLUGIN_ROOT` placeholder in it as this plugin's folder. Tools run as
   `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`; exit 2 means the tool could not run (most
   often its environment could not be prepared): show the message and fix it printed and stop.

4. **Report** what QA returned, in this order:
   - The verdict in one line: PASS, FAIL, or UNVERIFIED (validator clean, slides not visually
     checked, with the reason). A deck is ready to ship only on PASS; say so plainly otherwise.
   - The validator checks that failed, and every check that examined nothing (status `skipped`),
     marking as unverified those the deck should have exercised. Report what the validator returned,
     whatever the deck's shape.
   - The fixes, grouped by slide, most serious first.

   Then offer `/decks:polish-slides <file>` to apply them. Do not edit the deck, rebuild it, write a
   draft record or touch `style-preferences.md`. The `document-skills:pptx` skill is not used here;
   if it loads anyway, the NBG Standards override its typography and margin advice.

</process>
