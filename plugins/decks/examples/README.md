# Deck spec examples

Four deck specs in the canonical schema
([`tools/nbg-presentation/deck.schema.json`](../tools/nbg-presentation/deck.schema.json)).
Together they use every slide type the builder renders; copy the closest one and
change the content. The figures and sources in them are synthetic, written to show
the shape.

| Example | Audience | Slide types it shows |
|---|---|---|
| [`executive-summary.yaml`](executive-summary.yaml) | Board | cover, kpi, chart (bar with a highlighted category), cards (SVG icons, a recommended option, a takeaway), two_column (bullets beside an area_line chart, 40/60), back_cover |
| [`quarterly-report.yaml`](quarterly-report.yaml) | Executive committee | cover, contents, divider, content (level-2 bullet, takeaway), chart (area_line, bar_stacked, doughnut), table, waterfall, back_cover |
| [`strategy-deck.yaml`](strategy-deck.yaml) | Strategy committee | cover, divider, content (caption), process, cards (grid, a highlighted card), chart (bar_horizontal), table, image, custom (positioned elements with a line chart), back_cover |
| [`greek-deck.yaml`](greek-deck.yaml) | Executive committee, in Greek | cover, contents, divider, content (a Greek pill in accent-free capitals), kpi, chart (bar), back_cover |

The card icons are small duotone SVGs in [`icons/`](icons); the image slide uses
`illustrations/Growth.png`, which resolves against the plugin's `assets/` folder.

## Build one

From the repository root (inside Claude Code the launcher is
`"${CLAUDE_PLUGIN_ROOT}/bin/decks-py"`):

```bash
bash plugins/decks/bin/decks-py check plugins/decks/examples/executive-summary.yaml
bash plugins/decks/bin/decks-py build plugins/decks/examples/executive-summary.yaml ~/Downloads/executive-summary.pptx
bash plugins/decks/bin/decks-py render ~/Downloads/executive-summary.pptx ~/Downloads/executive-summary-render
```

`check` writes nothing and names every problem by slide, spec path and fix. `build`
runs the same check first, so it never writes a deck from a broken spec, then
validates the deck it wrote: exit 0 means written and valid. `render` draws every
slide as a PNG through LibreOffice for a visual check. The commands, the spec fields
per slide type and the exit codes are in
[`tools/nbg-presentation/README.md`](../tools/nbg-presentation/README.md).

## What every spec needs

- A `cover` first and a `back_cover` last (Standard #19); no "Thank you" slide.
- An action title on every other slide: one sentence that states the insight, on one
  line.
- `content.source` with `name` and `as_of` on every exhibit (chart, waterfall, table,
  kpi, or a two-column or custom slide holding one). The build refuses an exhibit
  without it.
- No legacy names. `check` accepts them with a warning naming the replacement, but an
  example is what gets copied, so these use only the canonical ones.
- A neutral cover subtitle. The presenting unit's own sub-units belong in the user's
  preferences, not in a shared example.
