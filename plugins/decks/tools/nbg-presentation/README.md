# NBG Presentation Tools

Tools for creating National Bank of Greece (NBG) formatted presentations.

## Installation

Ensure you have the required Python packages:

```bash
pip install pyyaml
```

## Tools

### 1. nbg_build.py - Presentation Builder

Creates complete NBG-formatted presentations from YAML outlines.

```bash
python nbg_build.py outline.yaml output.pptx
```

**Example outline.yaml:**

```yaml
template: GR  # or EN

slides:
  - type: covers/simple_white
    content:
      title: "National Bank of Greece"
      subtitle: "Competitive Analysis"
      location: "Athens, Greece"
      date: "February 2026"

  - type: content/text_with_bullets
    content:
      title: "Market Overview"
      paragraphs:
        - text: "Four systemic banks dominate the market"
          bullet: true
        - text: "Total assets exceed EUR 280 billion"
          bullet: true

  - type: charts/pie_single
    content:
      title: "Market Share"
    chart:
      type: doughnut
      labels: ["NBG", "Eurobank", "Piraeus", "Alpha", "Others"]
      values: [27, 23, 21, 19, 10]

  - type: tables/half_page
    content:
      title: "Key Metrics"
    table:
      headers: ["Metric", "NBG", "Eurobank", "Piraeus", "Alpha"]
      rows:
        - ["Assets (B)", "78.5", "82.1", "75.3", "71.2"]
        - ["CET1 %", "17.2%", "15.8%", "14.9%", "15.2%"]
      highlight_column: 1

  - type: back_covers/plain_logo
```

### 2. inject_chart_data.py - Chart Data Injection

Injects real data into chart placeholders.

```bash
python inject_chart_data.py input.pptx chart_config.json output.pptx
```

**Example chart_config.json:**

```json
{
  "charts": [
    {
      "slide": 2,
      "chart_index": 0,
      "type": "doughnut",
      "title": "Market Share",
      "data": {
        "labels": ["NBG", "Eurobank", "Piraeus", "Alpha"],
        "values": [27, 23, 21, 19]
      }
    }
  ]
}
```

### 3. inject_table_data.py - Table Data Injection

Injects real data into table placeholders.

```bash
python inject_table_data.py input.pptx table_config.json output.pptx
```

**Example table_config.json:**

```json
{
  "tables": [
    {
      "slide": 1,
      "table_index": 0,
      "data": {
        "headers": ["Metric", "NBG", "Eurobank"],
        "rows": [
          ["Assets", "78.5B", "82.1B"],
          ["CET1", "17.2%", "15.8%"]
        ]
      },
      "highlight_column": 1
    }
  ]
}
```

### 4. nbg_validate.py - Brand Validation

Validates presentations against NBG brand guidelines.

```bash
python nbg_validate.py presentation.pptx
```

**Output:**

```
NBG Brand Validation Report
==================================================
File: presentation.pptx
==================================================

✓ Slides: 7 slide(s) in presentation
✓ Dimensions: 13.33" x 7.5" (LAYOUT_WIDE) (NBG standard)
✓ Colors: All 15 colors within NBG palette
✓ Fonts: Fonts used: Aptos, Aptos SemiBold
✓ Logo: 5 media file(s) found
✓ Back Cover: Last slide appears to be a plain back cover

==================================================
Summary: 6 passed, 0 failed
All checks passed! Presentation follows NBG guidelines.
==================================================
```

## Slide Catalog

Available slide types (see `assets/slide-catalog.yaml`):

### Covers

- `covers/simple_white` - White background title slide
- `covers/simple_dark` - Dark teal background
- `covers/with_image_right` - Image on right
- `covers/with_image_left` - Image on left

### Content

- `content/text_only` - Full text layout
- `content/text_with_bullets` - Title + bullets
- `content/two_column_text` - Two columns
- `content/text_image_right` - Text + image

### Charts

- `charts/pie_single` - Pie/doughnut chart
- `charts/pie_with_text` - Pie + text boxes
- `charts/bar_single` - Single bar chart
- `charts/bar_dual` - Two bar charts
- `charts/line_single` - Line chart

### Infographics

- `infographics/numbered_4` - 4 items (01-04)
- `infographics/numbered_6` - 6 items (01-06)
- `infographics/numbered_9` - 9 items (3x3)
- `infographics/funnel` - Funnel diagram

### Tables

- `tables/half_page` - Table with description
- `tables/full_page` - Full page table

### Back Covers

- `back_covers/plain_logo` - Plain with NBG logo (ALWAYS use this)

## NBG Brand Guidelines

### Dimensions

- Width: 13.33 inches (LAYOUT_WIDE)
- Height: 7.5 inches
- Matches LAYOUT_WIDE standard

### Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Dark Teal | #003841 | Titles, headings |
| NBG Teal | #007B85 | Primary brand |
| Bright Cyan | #00DFF8 | Accents, bullets |
| Dark Text | #202020 | Body text |
| White | #FFFFFF | Background |

### Chart Colors (in order)

1. #00ADBF - Cyan
2. #003841 - Dark Teal
3. #007B85 - NBG Teal
4. #939793 - Medium Gray
5. #BEC1BE - Light Gray
6. #00DFF8 - Bright Cyan

### Fonts

- Primary: Aptos
- Bullets: Arial
- Fallback: Calibri, Tahoma

### Rules

- Always use white or off-white backgrounds
- **Never include "Thank You" slides**
- Always end with plain back cover with logo
- Section numbers: "01", "02" format in NBG Teal
- Bullets use Bright Cyan
- All text boxes: margin = 0
