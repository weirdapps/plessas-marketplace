# NBG Chart Specifications

## Critical Rules

### NEVER Use Pie Charts

**Pie charts are PROHIBITED.** Always use **doughnut charts** instead:

- More modern and professional appearance
- Center hole provides space for key metrics
- Better visual hierarchy

### Always Specify Explicit Colors

**CRITICAL:** Always specify explicit NBG colors for all chart elements to avoid PptxGenJS defaults (like #333333):

- `catAxisLabelColor`
- `valAxisLabelColor`
- `catAxisLineColor`
- `legendColor`
- `dataLabelColor`

## Chart Type Hierarchy

| Priority | Chart Type | Use For |
|----------|------------|---------|
| 1 | **Doughnut** | Proportions, percentages (ALWAYS instead of pie) |
| 2 | **Column Clustered** | Comparisons, rankings, categories (vertical) |
| 3 | **Bar Clustered** | Horizontal comparisons (same color as column — `#00ADBF`) |
| 4 | **Stacked Column** | Composition over time (3-4 series max) |
| 5 | **Line with markers** | Trends, time series (hollow "donut" markers) |
| 6 | **Stacked Area** | Two overlapping trends (semi-transparent fills) |
| 7 | **Waterfall** | Financial flows, bridges (faked via stacked column with invisible base) |
| 8 | **Area-Line** | Single trend with subtle fill (PREFERRED over plain line for single series) |

## Color Sequence

Use these colors in order for data series (no # prefix):

| Order | Hex | Name | RGB |
|-------|-----|------|-----|
| 1 | `00ADBF` | Cyan | 0, 173, 191 |
| 2 | `003841` | Dark Teal | 0, 56, 65 |
| 3 | `007B85` | NBG Teal | 0, 123, 133 |
| 4 | `939793` | Medium Gray | 147, 151, 147 |
| 5 | `BEC1BE` | Light Gray | 190, 193, 190 |
| 6 | `00DFF8` | Bright Cyan | 0, 223, 248 |

```javascript
const NBG_CHART_COLORS = ['00ADBF', '003841', '007B85', '939793', 'BEC1BE', '00DFF8'];
```

## Bar Chart Configuration

```javascript
slide.addChart(pptx.ChartType.bar, chartData, {
  x: 0.37, y: 1.3, w: 8.0, h: 4.8,
  chartColors: ['00ADBF'],

  // Data labels
  showValue: true,
  valueFontFace: 'Aptos',
  valueFontSize: 11,
  valueFontBold: true,
  valueFontColor: '202020',  // Explicit NBG color

  // Bar spacing
  barGapWidthPct: 35,

  // Category axis
  catAxisLabelFontFace: 'Aptos',
  catAxisLabelFontSize: 12,
  catAxisLabelColor: '202020',      // EXPLICIT - avoid defaults
  catAxisLineColor: 'BEC1BE',       // EXPLICIT - avoid defaults
  catAxisLineSize: 0.5,

  // Value axis
  valAxisHidden: true,
  valAxisLabelColor: '202020',      // EXPLICIT - even if hidden

  // Grid lines
  catGridLine: { style: 'none' },
  valGridLine: { style: 'none' },

  // Legend
  showLegend: false,

  // Plot area
  plotArea: { border: { color: 'BEC1BE', pt: 0 } },
});
```

## Doughnut Chart Configuration

**ALWAYS use doughnut instead of pie charts.**

```javascript
slide.addChart(pptx.ChartType.doughnut, chartData, {
  x: 0.37, y: 1.4, w: 5.5, h: 4.5,
  chartColors: ['00ADBF', '003841'],

  // Doughnut settings
  holeSize: 55,
  showLabel: false,
  showPercent: true,

  // Data labels
  dataLabelFontFace: 'Aptos',
  dataLabelFontSize: 12,
  dataLabelColor: '202020',         // EXPLICIT - avoid defaults

  // Legend
  showLegend: true,
  legendPos: 'b',
  legendFontFace: 'Aptos',
  legendFontSize: 12,
  legendColor: '202020',            // EXPLICIT - avoid defaults
});
```

## Line Chart Configuration

### Preferred Style: Area-Line (Line with Subtle Fill)

**This is the preferred format for all time-series / trend charts.** Uses an area chart
with low-opacity fill below the line, smooth curves, and visible dot markers. The result
is a clean, modern look — no grid lines, no axis lines, muted axis labels.

Pair with a **KPI callout** in the slide header: title on the left, large metric value
on the right with a change delta (green/red) and optional YtD.

```javascript
// PREFERRED: Area-Line Chart
slide.addChart(pptx.ChartType.area, chartData, {
  x: 0.37, y: 1.4, w: 7.0, h: 3.8,
  chartColors: ['007B85'],          // NBG Teal (single series)
  chartColorsOpacity: 15,           // Subtle fill below the line

  // Line styling
  lineSize: 3,                      // Thick line
  lineSmooth: false,                // Straight segments between points (smooth only if requested)
  lineDash: 'solid',

  // Markers — filled dots at each data point
  showMarker: true,
  markerSize: 8,

  // Data labels — HIDE for clean look (value shown in KPI callout instead)
  showValue: false,

  // Category axis — visible labels, no axis line
  catAxisLabelFontFace: 'Aptos',
  catAxisLabelFontSize: 11,
  catAxisLabelColor: '939793',      // Muted gray labels
  catAxisLineShow: false,           // No axis line

  // Value axis — visible labels (e.g. 0%, 2%, 4%), no axis line
  valAxisHidden: false,
  valAxisLabelFontFace: 'Aptos',
  valAxisLabelFontSize: 11,
  valAxisLabelColor: '939793',      // Muted gray labels
  valAxisLineShow: false,           // No axis line

  // Grid lines — NONE for clean background
  catGridLine: { style: 'none' },
  valGridLine: { style: 'none' },

  // Legend
  showLegend: false,

  // Plot area — clean white, no border
  plotArea: {
    fill: { color: 'FFFFFF' },
    border: { pt: 0 }
  },
});
```

#### KPI Callout Pattern (pair with area-line chart)

Add text shapes above the chart for the headline metric:

```javascript
// Title (left-aligned)
slide.addText('Αμοιβαία Κεφάλαια', {
  x: 0.37, y: 0.9, w: 5.0, h: 0.5,
  fontFace: 'Aptos', fontSize: 18, bold: true, color: '003841',
});

// Current value (right-aligned, large)
slide.addText('3.8%', {
  x: 6.5, y: 0.8, w: 2.5, h: 0.5,
  fontFace: 'Aptos', fontSize: 28, bold: true, color: '003841',
  align: 'right',
});

// Change delta (right-aligned, colored)
slide.addText('-0.5', {
  x: 7.5, y: 0.85, w: 1.5, h: 0.3,
  fontFace: 'Aptos', fontSize: 14, color: 'AA0028',  // Red for negative
  align: 'right',
});

// YtD label (right-aligned, muted)
slide.addText('YtD: 4.3%', {
  x: 7.5, y: 1.1, w: 1.5, h: 0.25,
  fontFace: 'Aptos', fontSize: 11, color: '939793',
  align: 'right',
});
```

### Alternative: Plain Line Chart (no fill)

Use when area fill would be misleading (e.g. multiple overlapping series) or when
data labels on each point are needed.

```javascript
slide.addChart(pptx.ChartType.line, chartData, {
  x: 0.37, y: 1.4, w: 7.0, h: 3.8,
  chartColors: ['007B85'],

  // Line styling
  lineSize: 3,
  lineSmooth: false,                // Straight segments (smooth only if requested)
  lineDash: 'solid',

  // Markers
  showMarker: true,
  markerSize: 10,

  // Data labels (when needed)
  showValue: true,
  valueFontFace: 'Aptos',
  valueFontSize: 11,
  valueFontBold: true,
  valueFontColor: '202020',
  dataLabelPosition: 't',
  dataLabelFontFace: 'Aptos',
  dataLabelColor: '202020',

  // Category axis
  catAxisLabelFontFace: 'Aptos',
  catAxisLabelFontSize: 11,
  catAxisLabelColor: '939793',
  catAxisLineShow: false,

  // Value axis
  valAxisHidden: false,
  valAxisLabelFontFace: 'Aptos',
  valAxisLabelFontSize: 11,
  valAxisLabelColor: '939793',
  valAxisLineShow: false,

  // Grid lines — none
  catGridLine: { style: 'none' },
  valGridLine: { style: 'none' },

  // Legend
  showLegend: false,

  // Plot area
  plotArea: {
    fill: { color: 'FFFFFF' },
    border: { pt: 0 }
  },
});
```

## Status Colors for Charts

| Status | Hex | Use For |
|--------|-----|---------|
| Success/Positive | `73AF3C` | Growth, improvements |
| Alert/Negative | `AA0028` | Declines, issues, CMTs |
| Neutral | `939793` | Baseline, previous period |

## Chart Design Best Practices

### Clean, Minimal Charts

1. **Remove clutter**: Hide gridlines where possible
2. **Single focus**: Each chart = ONE key message
3. **Data labels**: Only show if they add value
4. **Legend**: Position at bottom or right, never obscuring data
5. **Colors**: Max 3-4 colors per chart

### Supporting Key Messages

- Add callout boxes for insights (e.g., "+47%", "-800K")
- Use roundRect shapes for highlight callouts
- Keep subtitle explaining the data context

### Layout Tips

- **Two-column**: Chart on right, text/bullets on left (40/60 split)
- **Full-width**: Single important chart with annotations
- **Bar charts**: Use `barGapWidthPct: 35` for clean spacing

## Complete Chart Colors Reference

```javascript
const NBG = {
  colors: {
    // Chart series (in order)
    cyan: '00ADBF',
    darkTeal: '003841',
    teal: '007B85',
    mediumGray: '939793',
    lightGray: 'BEC1BE',
    brightCyan: '00DFF8',

    // Text/labels
    darkText: '202020',

    // Status
    success: '73AF3C',
    alert: 'AA0028',

    // Backgrounds
    white: 'FFFFFF',
    offWhite: 'F5F8F6',
  },

  chartColors: ['00ADBF', '003841', '007B85', '939793', 'BEC1BE', '00DFF8'],
};
```

## Avoiding Default Colors

PptxGenJS may inject default colors (like #333333) if you don't specify them explicitly. Always include these properties:

```javascript
// ALWAYS INCLUDE THESE to avoid #333333 defaults:
catAxisLabelColor: '202020',
valAxisLabelColor: '202020',
catAxisLineColor: 'BEC1BE',
legendColor: '202020',
dataLabelColor: '202020',
valueFontColor: '202020',
```

## Table Configuration

```javascript
// Header row
const headerStyle = {
  fontFace: 'Aptos',
  fontSize: 11,
  bold: true,
  color: 'FFFFFF',
  fill: { color: '003841' },
};

// Data rows
const cellStyle = {
  fontFace: 'Aptos',
  fontSize: 10,
  color: '202020',
  fill: { color: 'E6F0F1' },  // Light teal tint
};

// Alternating rows
const altCellStyle = {
  ...cellStyle,
  fill: { color: 'F0F5F3' },
};

// Table options
{
  border: { pt: 1, color: 'FFFFFF' },
  align: 'left',
  valign: 'middle',
}
```

## Line Chart — Hollow "Donut" Markers (NBG executive preference)

Line charts should use **thicker lines** with **hollow circle markers** (white fill, colored ring matching line width):

```javascript
// Line styling — NBG executive preference
lineSize: 3.5,         // thicker than default 2.5
lineSmooth: false,     // straight segments

// Hollow "donut" markers — colored ring, white center
showMarker: true,
markerStyle: 'circle',
markerSize: 10,        // larger for visibility
// Marker fill: WHITE (creates the hollow center)
// Marker line: SAME COLOR as the series line, SAME WIDTH as the line (3.5pt)
```

In python-pptx:

```python
series.format.line.width = Pt(3.5)
series.marker.style = 8  # circle
series.marker.size = 10
series.marker.format.fill.solid()
series.marker.format.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)  # white center
series.marker.format.line.color.rgb = series_color  # colored ring
series.marker.format.line.width = Pt(3.5)  # match line width
```

## Stacked Area Chart (2+ series, semi-transparent)

Use for showing composition trends over time. Both series should have **semi-transparent fills** (40% opacity) and matching line borders:

```javascript
// Series colors (in layer order, bottom to top)
chartColors: ['00ADBF', 'BEC1BE'],
chartColorsOpacity: 40,  // 40% opacity for softer, more professional look

// Line borders matching each series
lineSize: 2.5,
```

In python-pptx, apply alpha via XML manipulation on each series' solid fill:

```python
alpha_el = etree.SubElement(color_elem, qn("a:alpha"))
alpha_el.set("val", "40000")  # 40% = softer than 25%, more readable than 60%
```

## Table — Number Alignment Rule

**CRITICAL**: numeric columns (amounts, percentages, counts) must be **right-aligned**. Text columns remain left-aligned.

```javascript
// Header: right-align numeric column headers
// Data: right-align numeric cells
// Text columns (Unit, Priority, etc.): LEFT align always
```

In python-pptx:

```python
numeric_cols = {1, 2, 3, 4}  # indices of numeric columns
for p in cell.text_frame.paragraphs:
    if col_idx in numeric_cols:
        p.alignment = PP_ALIGN.RIGHT
```

## Waterfall — Data Label Positioning

Waterfall is faked via stacked column with invisible base. Data labels should appear **inside bars** (CENTER position) with **white text** on colored bars:

```javascript
// Data labels inside bars
dataLabelPosition: 'center',
dataLabelColor: 'FFFFFF',  // white text on colored bars
dataLabelFontSize: 12,
dataLabelFontBold: true,
```

For bars that start from the x-axis (opening/closing totals): labels appear at CENTER inside the tall bar. For floating bars (increases/decreases): labels appear centered within the floating segment.

If a bar is too small for the label to fit, the label should have a white background halo for readability.
