# NBG Presentation Examples

Sample YAML storylines for different presentation types. Use these as templates for your own presentations.

## Available Examples

| Example | Description | Best For |
|---------|-------------|----------|
| `executive-summary.yaml` | Concise board-level summary | Board meetings, executive briefings |
| `quarterly-report.yaml` | Detailed performance metrics | Quarterly reviews, financial reporting |
| `strategy-deck.yaml` | Strategic initiative proposal | Strategy presentations, investment cases |

## Usage

### Option 1: Use with nbg_build.py

```bash
# Navigate to the tools directory
cd plugins/decks/tools/nbg-presentation

# Build a presentation from an example
python nbg_build.py ../../examples/executive-summary.yaml output.pptx
python nbg_build.py ../../examples/executive-summary.yaml -o output.pptx   # same thing
```

The build exits non-zero if the deck fails `nbg_validate.py`, so a zero exit means the file was
written and it passed. Dependencies: see `../tools/nbg-presentation/README.md`.

### Option 2: Use as Template

1. Copy an example to your working directory
2. Modify the content to match your needs
3. Run through the nbg_build.py tool or use the `/create-presentation` command

## YAML Structure

All examples follow the McKinsey-quality storyline structure.

There is no `template:` key. `nbg_build.py` draws every slide from scratch with python-pptx and
never opens a .pptx, so a template value could not have changed the output; the key was metadata
pointing at a file, and both are gone. See `brand-system/generation-methods.md`.

```yaml

presentation:
  title: "Presentation Title"
  audience: "Target audience"
  purpose: "Why this presentation exists"
  main_recommendation: "The key takeaway (Pyramid Principle)"

slides:
  - type: cover
    content:
      title: "..."
      subtitle: "..."
      date: "..."

  - type: divider
    content:
      number: "01"
      title: "Section Title"

  - type: content
    content:
      title: "Action Title (full sentence)"  # McKinsey style
      bumper: "SECTION TAG"  # Optional
      points:
        - "Bullet point 1"
        - "Bullet point 2"

  - type: chart
    recommended_visual: bar_chart  # Helps select best layout
    content:
      title: "Chart Action Title"
      description: "Optional caption, rendered under the title"
      source:                      # REQUIRED on chart and table slides
        name: "NBG MIS"
        as_of: "31 December 2025"
        basis: "constant currency" # optional definitional caveat
    chart:
      type: bar          # bar | bar_stacked | bar_horizontal | line | doughnut | pie
      data:
        categories: ["Q1", "Q2", "Q3"]
        series:
          - name: "2025"
            values: [12, 15, 18]
          - name: "2026"
            values: [14, 19, 23]

  - type: table
    content:
      title: "Table Action Title"
      source:
        name: "NBG management accounts"
        as_of: "31 December 2025"
    table:
      headers: ["Metric", "2025", "2026"]
      rows:
        - ["Revenue", "EUR 42M", "EUR 48M"]
      highlight_column: 2   # optional, emphasises that column in NBG Teal

  - type: back_cover
```

`chart.data` is the contract. The builder reads `chart.type`, `chart.data.categories` and
`chart.data.series`; a chart slide with no series prints a warning and leaves the plot area blank.

`content.source` is the other contract, and unlike the one above it **blocks**: a chart or table
slide without it fails `nbg_validate.py`'s Exhibit Sources check and the build exits non-zero. It
needs `name` (where the number came from) and `as_of` (when it was true); `basis` is optional and
carries the definitional caveat. Declaring a source and omitting `as_of` fails at build time, before
the validator runs, because the builder can see the mapping and a half-source is a spec error. It
renders as an 11pt footnote below the exhibit. The sources in the three examples are synthetic,
written to show the shape.

## Slide Types

| Type | Usage | Required Fields |
|------|-------|-----------------|
| `cover` | Opening slide | title, subtitle, date |
| `divider` | Section break | number, title |
| `content` | Text with bullets | title, points |
| `chart` | Data visualization | title, chart data, source |
| `table` | Tabular data | title, table data, source |
| `infographic` | Visual process/list | title, items (renders as bullets: there is no infographic layout yet) |
| `back_cover` | Closing slide | (none) |

## Visual Recommendations

Use `recommended_visual` to hint at the best chart/layout:

| Visual | Best For |
|--------|----------|
| `bar_chart` | Comparisons, rankings |
| `line_chart` | Trends over time |
| `pie_chart` | Proportions (actually renders as doughnut) |
| `numbered_infographic` | Process steps, numbered lists |
| `kpi_dashboard` | Key metrics display |
| `table` | Detailed data |

## Quality Standards

All examples follow McKinsey quality standards:

- **Pyramid Principle**: Lead with the answer, then support
- **Action Titles**: Full sentences that tell the story (not labels)
- **One Message Per Slide**: No exceptions
- **So What Test**: Every slide must matter
- **5-7 Second Rule**: Scannable at a glance
