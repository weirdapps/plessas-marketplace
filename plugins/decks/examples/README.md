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
cd plugins/presentation-maker/tools/nbg-presentation

# Build a presentation from an example
python nbg_build.py ../../examples/executive-summary.yaml output.pptx
```

### Option 2: Use as Template

1. Copy an example to your working directory
2. Modify the content to match your needs
3. Run through the nbg_build.py tool or use the `/create-presentation` command

## YAML Structure

All examples follow the McKinsey-quality storyline structure:

```yaml
template: GR  # or EN for English template

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
    chart:
      type: bar
      data: {...}

  - type: back_cover
```

## Slide Types

| Type | Usage | Required Fields |
|------|-------|-----------------|
| `cover` | Opening slide | title, subtitle, date |
| `divider` | Section break | number, title |
| `content` | Text with bullets | title, points |
| `chart` | Data visualization | title, chart data |
| `table` | Tabular data | title, table data |
| `infographic` | Visual process/list | title, items |
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
