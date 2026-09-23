---
description: "Create an NBG-branded infographic or data visual from supplied data: a native slide when a chart, KPI tiles, cards, process steps or a table can carry it, otherwise an SVG diagram placed on a slide"
argument-hint: "<data or description> [folder to save in]"
allowed-tools: Agent, Read, Write, Edit, Bash, Glob, Grep, Skill(manage-nano-banana:manage-nano-banana)
---

<objective>
Turn the user's data into one on-brand visual, delivered as a single NBG slide (`.pptx`) and a PNG
of it, built by the plugin's builder so it is editable and checked.

User request: $ARGUMENTS
</objective>

<rules>
- Tools run as `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`; exit 2 means the environment
  could not be prepared: show the printed fix and stop.
- Every number and label comes from the user. Data needs a source and an as-of date: ask for them
  when the request lacks them, never invent one.
- If the Agent tool is unavailable or denied, Read `${CLAUDE_PLUGIN_ROOT}/agents/<agent>.md` and do
  its job yourself, reading any `CLAUDE_PLUGIN_ROOT` placeholder in it as this plugin's folder.
- Only the builder writes the slide: no python-pptx, PptxGenJS or OOXML, and not the
  `document-skills:pptx` skill; if it loads anyway, the NBG Standards override its advice.
</rules>

<process>

1. **Set up.** Deck id `<timestamp>_<slug>` (timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'`),
   WORK = `${CLAUDE_PLUGIN_DATA}/work/<deck id>/` (`mkdir -p "<WORK>/images"`), output folder the
   one the user named or `$HOME/Downloads`, as an absolute path.

2. **Choose the route.** Read `${CLAUDE_PLUGIN_ROOT}/tools/nbg-presentation/deck.schema.json` first.
   - **Native slide** (the default): the visual is a chart (`bar`, `bar_horizontal`, `bar_stacked`,
     `area_line` for a trend, `doughnut` for part of a whole), a `waterfall`, `kpi` tiles, `cards`,
     `process` steps or a `table`. Write `<WORK>/deck.yaml` with that one slide, an action title
     that states the insight, and its `content.source`, followed by a `back_cover` slide.
   - **Diagram**: a funnel, timeline, matrix, hierarchy or cycle that no slide type expresses.
     Dispatch `decks:infographic-specialist` with the brief, `output: <WORK>/images/<slug>.svg` and
     `size_in: [12.0, 4.8]`. Then write `<WORK>/deck.yaml` with one `image` slide pointing at
     `images/<slug>.svg`, the alt text the agent returned, an action title, and a `back_cover`.
   - **Generated illustration**, only when the user explicitly asks for an AI-generated image and
     `Skill(manage-nano-banana:manage-nano-banana)` is available: decorative imagery only, never a
     number or a data label, on a white background with the teal palette from
     `${CLAUDE_PLUGIN_ROOT}/shared/brand-system/tokens.yaml`. Deliver the image itself and say that
     it bypassed the builder and the validator.

3. **Check, build, render.**

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" check "<WORK>/deck.yaml"
   bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" build "<WORK>/deck.yaml" "<WORK>/deck.pptx"
   bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" render "<WORK>/deck.pptx" "<WORK>/render"
   ```

   Fix the spec and repeat on a check or build exit 1. Read the first slide's PNG in
   `<WORK>/render` and confirm the numbers match the data, every label reads, and nothing is clipped.
   Render exit 4 means fonts were substituted, so text fit is unconfirmed; exit 3 means LibreOffice
   is missing: deliver without the PNG and say the slide was not visually checked.

4. **Deliver** to the output folder: `<deck id>.pptx` (the slide to paste into a deck), the first
   slide's PNG as `<deck id>.png`, and on the diagram route the SVG as `<deck id>.svg`.

</process>
