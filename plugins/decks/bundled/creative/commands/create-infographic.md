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
- Tools run as `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" <command>`; exit 2 means the tool could
  not run (most often its environment could not be prepared): show the message and fix it printed
  and stop.
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
   Every deck the validator accepts opens with a `cover` and closes with a `back_cover`, so
   `<WORK>/deck.yaml` holds three slides: a cover titled after the visual, the visual's slide, and
   the back cover.
   - **Native slide** (the default): the visual is a chart (`bar`, `bar_horizontal`, `bar_stacked`,
     `area_line` for a trend, `doughnut` for part of a whole), a `waterfall`, `kpi` tiles, `cards`,
     `process` steps or a `table`. Give it an action title that states the insight and its
     `content.source`.
   - **Diagram**: a funnel, timeline, matrix, hierarchy or cycle that no slide type expresses. The
     visual's slide is an `image` slide with an action title, `path: images/<slug>.svg` and an alt
     text from the brief. Write a placeholder at that path
     (`<svg xmlns="http://www.w3.org/2000/svg" id="decks-placeholder" viewBox="0 0 864 346"/>`), run
     `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" check "<WORK>/deck.yaml" --format json`, and read its
     `image_slots` entry for that slide (it appears once the slide lays out cleanly). Dispatch
     `decks:infographic-specialist` with the brief, `output: <WORK>/images/<slug>.svg` and `size_in`
     set to that entry's `[w, h]`, rounded down to 2 decimals. It replaces the placeholder; replace
     the alt text with the one it returns.
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

   Fix the spec and repeat on a check or build exit 1 (each error names the field and a fix). An
   error or warning that the diagram's labels print under 10 or 12 pt names the `size_in` to
   redraw at: dispatch `decks:infographic-specialist` again with it. Read
   `<WORK>/render/slide-02.png`, the visual's slide, and confirm the numbers match the data, every
   label reads, and nothing is clipped. Render exit 4 means Aptos was substituted, so text fit is
   unconfirmed: say so; exit 3 means LibreOffice is not installed: deliver without the PNG and say
   the slide was not visually checked.

4. **Deliver** to the output folder: `<deck id>.pptx` (its second slide is the one to paste into a
   deck), `slide-02.png` as `<deck id>.png`, and on the diagram route the SVG as `<deck id>.svg`.

</process>
