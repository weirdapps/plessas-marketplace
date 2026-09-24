# NBG Chart Specifications

> Machine source: [`tokens.yaml`](tokens.yaml), section `charts` (plus `type.chart_*`). This is the
> one home for chart styling in prose: `ooxml-charts.md` and the agents point here. The builder
> renders every chart from these values; a value changes in tokens.yaml first.

## Critical Rules

### NEVER Use Pie Charts

**Pie charts are PROHIBITED.** Always use **doughnut charts** instead:

- More modern and professional appearance
- Center hole provides space for key metrics
- Better visual hierarchy

### Always Specify Explicit Colors

**CRITICAL:** Every chart part carries an explicit NBG colour: series fills and lines, data
labels, axis labels, axis lines and legend text. A part left to inherit takes the Office theme
(`#4F81BD` blue, `#C0504D` red, Calibri), which is how line charts shipped in Office colours.
`nbg_build.py` writes both the explicit colours and an NBG theme, so a chart a colleague adds in
PowerPoint afterwards also starts on-brand.

## Chart Style (tokens.yaml `charts`)

| Part | Spec |
|------|------|
| Font | Aptos throughout |
| Series colours | The sequence below, in order; at most 6 series (8 absolute, Standard #22) |
| Gridlines | None |
| Data labels | 12pt Bold `#003841`; inside a filled bar, the builder picks black or white by contrast against the fill |
| Category axis | Labels 12pt `#202020`; axis line 0.5pt `#BEC1BE` |
| Value axis | Hidden on bar and column charts, and pinned at zero whenever every bar is zero or more (waterfalls too); on line and area charts visible, labels 11pt `#939793`, no axis line |
| Legend | Bottom, 12pt `#202020`, and by default only on a bar chart with several series: a doughnut names its slices in the ring and a multi-series line names each line at its last point |
| Bar and column | Gap width 35%; stacked bars overlap 100%, their value axis runs from zero to the tallest stack, and a segment too thin for its label goes without one (`decks-py check` warns) |
| Line | 3.5pt, straight segments (no smoothing), hollow circle markers size 6 (white fill, a 2pt ring in the series colour) |
| Area-line | The line above, plus a 15% fill in the series colour under the first series only |
| Doughnut | Hole size 55%; slices in the ring order `#00ADBF`, `#003841`, `#007B85`, `#BEC1BE`, `#00DFF8`, `#939793` (`charts.doughnut.slice_palette`), so NBG Teal never sits beside Medium Gray; every slice named with its share inside the ring |
| Waterfall | Gap width 100%; totals `#003841`, increases `#00ADBF`, decreases `#AA0028` |
| Highlight | One category in `#00ADBF`, the rest in `#BEC1BE` (`chart.highlight_category` in the deck spec) |
| Time series | Area-line by default, never a bare line (Standard #2.8) |

The muted `#939793` value-axis labels are the one sanctioned sub-AA text use in charts (2.96:1,
Standard #22): they are secondary to the direct data labels, never the only way to read a value.

## Chart Type Hierarchy

| Priority | Chart Type | Use For |
|----------|------------|---------|
| 1 | **Doughnut** | Proportions, percentages (ALWAYS instead of pie) |
| 2 | **Column Clustered** | Comparisons, rankings, categories (vertical) |
| 3 | **Bar Clustered** | Horizontal comparisons (same color as column, `#00ADBF`) |
| 4 | **Stacked Column** | Composition over time (3-4 series max) |
| 5 | **Area-Line** | Trends and time series (the default for any time series) |
| 6 | **Waterfall** | Financial flows, bridges |
| 7 | **Line with markers** | A trend across categories that are not a time series; still the Standard #5 stroke and markers |

In a deck spec these are `chart.type`: `doughnut`, `bar`, `bar_horizontal`, `bar_stacked`,
`area_line`, `line`, and the `waterfall` slide type.

## Color Sequence

Use these colors in order for data series (`tokens.yaml` `charts.palette`, no # prefix):

| Order | Hex | Name | RGB |
|-------|-----|------|-----|
| 1 | `00ADBF` | Cyan | 0, 173, 191 |
| 2 | `003841` | Dark Teal | 0, 56, 65 |
| 3 | `007B85` | NBG Teal | 0, 123, 133 |
| 4 | `939793` | Medium Gray | 147, 151, 147 |
| 5 | `BEC1BE` | Light Gray | 190, 193, 190 |
| 6 | `00DFF8` | Bright Cyan | 0, 223, 248 |

Series 3 and 4 are only 1.70:1 apart: never let those two alone carry a distinction. Label every
series directly rather than relying on a colour-only legend (Standard #22).

## Bar and Column Charts

- One series: `#00ADBF` for column AND horizontal bar charts.
- Data labels above (or at the end of) each bar, 12pt Bold `#003841`, with a number format that
  matches the data's precision.
- Value axis hidden; category axis labels 12pt `#202020` with a 0.5pt `#BEC1BE` axis line.
- Stacked: labels sit inside the segments, so each series' label colour comes from the contrast
  picker (dark on `#00ADBF`, `#BEC1BE`, `#00DFF8`; white on `#003841`, `#007B85`). The value axis
  runs from zero to the tallest stack. A segment too short or too narrow for its label goes
  without one, and `decks-py check` names each: group the small series into "Other", or give the
  chart more room.
- A legend (bottom, 12pt `#202020`) appears by default only when a bar chart has several series.

## Doughnut Charts

**ALWAYS use doughnut instead of pie charts.** Hole 55%. The slices take the ring order
(`charts.doughnut.slice_palette`: `#00ADBF`, `#003841`, `#007B85`, `#BEC1BE`, `#00DFF8`,
`#939793`), the chart sequence reordered so NBG Teal never sits beside Medium Gray (1.70:1),
including where the last slice meets the first. 1pt white lines separate the slices.

Every slice carries its name and its share inside the ring, 12pt Bold in the contrast-picked
colour, the name wrapping between words to fit. When a slice has no room for its name, the chart
names the slices in a bottom legend (12pt `#202020`) instead and `decks-py check` warns.

## Line and Area-Line Charts

### Area-Line (the default for a time series)

A line with a low-opacity fill below it: 3.5pt line, straight segments, hollow circle markers, and
a 15% fill in the series colour under the first series only (under several lines the fills
blended into a grey-brown wash, so the others stay plain lines). No gridlines, no axis lines,
muted value-axis labels (11pt `#939793`), category labels 12pt `#202020`. Data labels are off:
the value a reader needs sits in the KPI callout.

Pair it with a **KPI callout** beside the chart: the slide keeps its 24pt Regular action title
(Standard #16), and the callout is the Inline KPI Callout in `layouts.md` (value 18pt Bold
`#007B85`, label 12pt `#202020`) with an optional signed delta: positive `#007B85`, negative
`#AA0028`, neutral `#202020` (`components.kpi.delta`; the corporate green `#73AF3C` is 2.65:1 on
white and never carries text).

### Line with markers

For a trend across categories that are not a time series. Same stroke and markers as above, no
fill, and no value labels (line and area-line charts carry none). With several series the builder
names each one at its last point, right of the line, and draws no legend; put the one value that
matters in a KPI callout.

## Hollow "Donut" Markers (Standard #5)

The single line and marker spec for this brand system. Every line, area-line and multi-series
line chart uses it; no other block in this file repeats these numbers.

- Line width 3.5pt (44450 EMU), straight segments, never smoothed
- Marker: circle, size 6
- Marker fill: white (the hollow centre)
- Marker outline: the series colour, 2pt (25400 EMU, `charts.line.marker_line_pt`). It is thinner
  than the line on purpose: a 3.5pt ring fills a 6pt marker, which then reads as a solid dot

In python-pptx (how `nbg_build.py` writes it):

```python
series.format.line.color.rgb = series_color
series.format.line.width = Pt(3.5)
series.smooth = False
series.marker.style = XL_MARKER_STYLE.CIRCLE
series.marker.size = 6
series.marker.format.fill.solid()
series.marker.format.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)  # white centre
series.marker.format.line.color.rgb = series_color                       # coloured ring
series.marker.format.line.width = Pt(2)                                 # thinner than the line
```

## Stacked Area Chart: existing decks only, not built by the plugin

The builder has no stacked-area chart: it is not a deck-spec `chart.type`. For a new deck, show
composition over time with `bar_stacked`, or overlapping trends with a multi-series `area_line`
or `line`. This spec is for reading or repairing a stacked-area chart in an existing deck.

Both series take semi-transparent fills (40% opacity) in the chart sequence (for example
`#00ADBF` under `#BEC1BE`) and matching outlines at **2.5pt**. The 2.5pt is deliberate: this
stroke outlines a filled region rather than carrying a value, so the 3.5pt data-line width in
Standard #5 does not apply to it.

## Status Colors for Charts

The corporate palette, scoped in [colors.md](colors.md#statussemantic-colors). Status pill
colors are a different palette and never appear in a chart.

| Status | Hex | Use For |
|--------|-----|---------|
| Success/Positive | `73AF3C` | Growth, improvements |
| Alert/Negative | `AA0028` | Declines, issues, CMTs |
| Neutral | `939793` | Baseline, previous period |

## Chart Design Best Practices

### Clean, Minimal Charts

1. **Remove clutter**: no gridlines
2. **Single focus**: Each chart = ONE key message
3. **Data labels**: Only show if they add value
4. **Legend**: at the bottom, never obscuring data; prefer direct labels
5. **Colors**: 3-4 per chart is the design target. The hard categorical ceiling, and the
   OOXML trap that silently degrades a palette past six series, are in Standard #22

### Supporting Key Messages

- Add callout boxes for insights (e.g., "+47%", "-800K")
- Use tight rounded rectangles (Standard #12) for highlight callouts
- Keep subtitle explaining the data context
- Every chart carries a dated source line (`content.source` in the deck spec)

### Layout Tips

- **Two-column**: Chart on right, text/bullets on left (40/60 split, `dimensions.md`)
- **Full-width**: Single important chart with annotations

## Tables

The full table spec (fills, borders, row heights, in-cell emphasis, alignment) lives in
[layouts.md](layouts.md#table-styling-nbg-executive-signature). In short: header `#003841` with
12pt Bold white, zebra `#FFFFFF` / `#F5F8F6`, 12pt `#202020` body, numbers right-aligned, 1pt
white borders.

## Waterfall: Data Labels

Every waterfall label is the bar's signed contribution, written into the label as text in the
chart's `number_format` (`+1,624`, `-2,439`, `+2.5%` for `0.0%`, `+12 m` for `#,##0" m"`, and
Greek separators in a Greek deck, `+1.624`; a total carries a sign only when it is negative), so
it reads the same in every viewer.
All labels are 12pt Bold (`type.chart_data_label`). Where a label sits depends on the bar:

| Bar | Label | Colour |
|-----|-------|--------|
| A step, increase or decrease, entirely above zero | Just above the bar | `#003841` |
| A total, or a step reaching below zero | Centred in the bar | The contrast picker: white on `#003841` totals and `#AA0028` decreases, black on `#00ADBF` increases |

A centred label inside a thin step would run over both edges of the bar, which is why the steps
above zero carry theirs on top. The value axis is hidden and there is no legend: the labels and
the category axis carry the chart.

In a deck spec a waterfall is the `waterfall` slide type with `chart.data.items` (label, value,
and `total: true` for the bars drawn from zero; the first and last items are totals by default).
