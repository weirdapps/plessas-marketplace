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

2. **Find its spec**, so fixes can name slide ids: if
   `${CLAUDE_PLUGIN_DATA}/work/<file name without .pptx>/deck.yaml` exists, pass it; otherwise fixes
   name slide numbers.

3. **Review.** Render folder: `${CLAUDE_PLUGIN_DATA}/work/review_<timestamp>/`, the timestamp from
   `TZ='Europe/Athens' date '+%Y%m%d%H%M'`. Dispatch `decks:presentation-qa` with `pptx: <file>`, the
   spec or `none`, and `render: <that folder>`. If the Agent tool is unavailable or denied, Read
   `${CLAUDE_PLUGIN_ROOT}/agents/presentation-qa.md` and run the review yourself, reading any
   `CLAUDE_PLUGIN_ROOT` placeholder in it as this plugin's folder. Tools run as
   `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`; exit 2 means the environment could not be
   prepared: show the printed fix and stop.

4. **Report** what QA returned, in this order:
   - The verdict in one line: PASS, FAIL, or UNVERIFIED (validator clean, slides not visually
     checked, with the reason). A deck is ready to ship only on PASS; say so plainly otherwise.
   - The validator checks that failed, and any check that examined nothing although the deck has
     what it measures.
   - The fixes, grouped by slide, most serious first.

   Then offer `/decks:polish-slides <file>` to apply them. Do not edit the deck, rebuild it, write a
   draft record or touch `style-preferences.md`. The `document-skills:pptx` skill is not used here;
   if it loads anyway, the NBG Standards override its typography and margin advice.

</process>
