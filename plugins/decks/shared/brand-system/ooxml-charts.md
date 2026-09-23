# OOXML Chart Reference for NBG Presentations

> The chart style itself lives in [charts.md](charts.md), quoting [`tokens.yaml`](tokens.yaml)
> `charts`. The XML below writes those values; where the two ever disagree, charts.md wins.

This document shows how the NBG chart style looks in Office Open XML (OOXML). New decks never need
it: `nbg_build.py` writes their charts. Use it to read, check or repair chart XML in an existing
presentation.

Every colour here is an explicit `a:srgbClr`. Never use `a:schemeClr` (`bg1`, `tx1`) for chart
text: it resolves against whatever theme the deck carries, and the validator's contrast check
cannot measure it.

## Chart File Structure

Charts in PPTX files are stored in:

```
ppt/
├── charts/
│   ├── chart1.xml           # Chart definition
│   ├── _rels/
│   │   └── chart1.xml.rels  # Links to embedded data
├── embeddings/
│   └── Microsoft_Excel_Worksheet1.xlsx  # Embedded data
```

## NBG Chart Style Defaults

### Common Settings

```xml
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
              xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
              xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <c:date1904 val="0"/>
  <c:roundedCorners val="0"/>  <!-- square corners on every chart; an absent element means rounded -->
  <c:chart>
    <c:autoTitleDeleted val="1"/>  <!-- No chart title - use slide text instead -->
```

### NBG Color Palette (for charts)

| Order | Hex Code | Name | Usage |
|-------|----------|------|-------|
| 1 | `00ADBF` | Cyan | Primary data series |
| 2 | `003841` | Dark Teal | Secondary series |
| 3 | `007B85` | NBG Teal | Tertiary series |
| 4 | `939793` | Medium Gray | Fourth series |
| 5 | `BEC1BE` | Light Gray | Fifth series |
| 6 | `00DFF8` | Bright Cyan | Accent/highlight |
| + | `AA0028` | NBG Red | Negative values/decreases |
| + | `73AF3C` | Green | Positive/success |

Series 3 and 4 are 1.70:1 apart; label them directly (Standard #22).

---

## Column Chart (Vertical Bars)

**Use for**: Monthly/quarterly data, time series comparisons

### Key Elements

```xml
<c:barChart>
  <c:barDir val="col"/>        <!-- "col" for vertical, "bar" for horizontal -->
  <c:grouping val="clustered"/> <!-- or "stacked" for stacked bars -->
  <c:varyColors val="0"/>
```

### Series Definition

```xml
<c:ser>
  <c:idx val="0"/>
  <c:order val="0"/>
  <c:tx>
    <c:strRef>
      <c:f>Sheet1!$B$1</c:f>
      <c:strCache>
        <c:ptCount val="1"/>
        <c:pt idx="0"><c:v>Series Name</c:v></c:pt>
      </c:strCache>
    </c:strRef>
  </c:tx>
  <c:spPr>
    <a:solidFill>
      <a:srgbClr val="00ADBF"/>  <!-- NBG Cyan -->
    </a:solidFill>
    <a:effectLst/>
  </c:spPr>
  <c:invertIfNegative val="0"/>
```

### Data Labels (NBG Style)

Above the bars: 12pt Bold `#003841`.

```xml
<c:dLbls>
  <c:numFmt formatCode="#,##0.0" sourceLinked="0"/>
  <c:spPr>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </c:spPr>
  <c:txPr>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p>
      <a:pPr>
        <a:defRPr sz="1200" b="1">
          <a:solidFill>
            <a:srgbClr val="003841"/>
          </a:solidFill>
          <a:latin typeface="Aptos"/>
        </a:defRPr>
      </a:pPr>
    </a:p>
  </c:txPr>
  <c:showVal val="1"/>
  <c:showLegendKey val="0"/>
  <c:showCatName val="0"/>
  <c:showSerName val="0"/>
  <c:showPercent val="0"/>
  <c:showBubbleSize val="0"/>
</c:dLbls>
```

### Category Axis (NBG Style)

```xml
<c:catAx>
  <c:axId val="2094734554"/>
  <c:scaling>
    <c:orientation val="minMax"/>
  </c:scaling>
  <c:delete val="0"/>
  <c:axPos val="b"/>
  <c:majorTickMark val="none"/>
  <c:minorTickMark val="none"/>
  <c:tickLblPos val="low"/>
  <c:spPr>
    <a:ln w="6350" cap="flat">  <!-- 0.5pt -->
      <a:solidFill>
        <a:srgbClr val="BEC1BE"/>  <!-- Light gray axis line -->
      </a:solidFill>
      <a:prstDash val="solid"/>
      <a:round/>
    </a:ln>
  </c:spPr>
  <c:txPr>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p>
      <a:pPr>
        <a:defRPr sz="1200" b="0">
          <a:solidFill>
            <a:srgbClr val="202020"/>  <!-- Dark text -->
          </a:solidFill>
          <a:latin typeface="Aptos"/>
        </a:defRPr>
      </a:pPr>
    </a:p>
  </c:txPr>
  <c:crossAx val="2094734552"/>
  <c:crosses val="autoZero"/>
  <c:auto val="1"/>
  <c:lblAlgn val="ctr"/>
  <c:lblOffset val="100"/>
</c:catAx>
```

### Hidden Value Axis

```xml
<c:valAx>
  <c:axId val="2094734552"/>
  <c:scaling>
    <c:orientation val="minMax"/>
  </c:scaling>
  <c:delete val="1"/>  <!-- Hide the value axis -->
  <c:axPos val="l"/>
  <c:crossAx val="2094734554"/>
  <c:crosses val="autoZero"/>
  <c:crossBetween val="between"/>
</c:valAx>
```

---

## Stacked Bar Chart

**Use for**: Comparing composition across categories (e.g., VISA/MC vs DIAS transactions)

### Key Differences from Column Chart

```xml
<c:barChart>
  <c:barDir val="col"/>
  <c:grouping val="stacked"/>  <!-- Enable stacking -->
  <c:varyColors val="0"/>
  <!-- ... series definitions ... -->
  <c:gapWidth val="35"/>  <!-- the one bar gap, stacked or not -->
  <c:overlap val="100"/>  <!-- Full overlap for stacking -->
</c:barChart>
```

### Multiple Series Colors

```xml
<!-- Series 1: Cyan, the first palette colour -->
<c:ser>
  <c:spPr>
    <a:solidFill>
      <a:srgbClr val="00ADBF"/>
    </a:solidFill>
  </c:spPr>
  <!-- ... -->
</c:ser>

<!-- Series 2: Dark Teal, the second -->
<c:ser>
  <c:spPr>
    <a:solidFill>
      <a:srgbClr val="003841"/>
    </a:solidFill>
  </c:spPr>
  <!-- ... -->
</c:ser>
```

### Stacked Data Labels (inside the segments)

Each series gets its own label colour, chosen by the contrast picker against that series' fill:
`FFFFFF` on `003841` and `007B85`, pure black `000000` on `00ADBF`, `939793`, `BEC1BE` and
`00DFF8` (white on cyan is 2.72:1; why black and not `#202020`: colors.md, Color Contrast Rules).
Put the `c:dLbls` inside each `c:ser`, not once at the plot level, so every series carries the
colour its own fill needs.

```xml
<c:dLbls>
  <c:numFmt formatCode="#,##0" sourceLinked="0"/>
  <c:txPr>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p>
      <a:pPr>
        <a:defRPr sz="1200" b="1">
          <a:solidFill>
            <a:srgbClr val="000000"/>  <!-- on the 00ADBF series; FFFFFF on 003841 -->
          </a:solidFill>
          <a:latin typeface="Aptos"/>
        </a:defRPr>
      </a:pPr>
    </a:p>
  </c:txPr>
  <c:dLblPos val="ctr"/>
  <c:showVal val="1"/>
</c:dLbls>
```

---

## Horizontal Bar Chart

**Use for**: Comparing categories side-by-side (e.g., bank transaction volumes)

### Key Settings

```xml
<c:barChart>
  <c:barDir val="bar"/>  <!-- Horizontal bars -->
  <c:grouping val="clustered"/>
  <c:varyColors val="0"/>
```

### Manual Layout (for precise positioning)

```xml
<c:layout>
  <c:manualLayout>
    <c:layoutTarget val="inner"/>
    <c:xMode val="edge"/>
    <c:yMode val="edge"/>
    <c:x val="0.023"/>     <!-- Left offset (fraction of chart width) -->
    <c:y val="0.034"/>     <!-- Top offset -->
    <c:w val="0.702"/>     <!-- Width -->
    <c:h val="0.854"/>     <!-- Height -->
  </c:manualLayout>
</c:layout>
```

### Hidden Category Axis (when using logo images instead)

```xml
<c:catAx>
  <c:delete val="1"/>  <!-- Hide category labels -->
  <c:axPos val="l"/>
  <!-- ... -->
</c:catAx>
```

### Bottom Legend

```xml
<c:legend>
  <c:legendPos val="b"/>  <!-- Bottom position -->
  <c:overlay val="0"/>
  <c:txPr>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p>
      <a:pPr>
        <a:defRPr sz="1200">
          <a:solidFill>
            <a:srgbClr val="202020"/>
          </a:solidFill>
          <a:latin typeface="Aptos"/>
          <a:cs typeface="Aptos"/>
        </a:defRPr>
      </a:pPr>
    </a:p>
  </c:txPr>
</c:legend>
```

---

## Waterfall Chart (Stacked Column Simulation)

**Use for**: Financial flows, showing how values add/subtract to reach a total

python-pptx has no native waterfall, so `nbg_chart.add_waterfall` draws a stacked column chart
with four series:

1. **Base** (invisible): lifts each floating bar to where it starts
2. **Above zero**: the part of each bar above zero
3. **Below zero**: the part of each bar below zero (all zeros while the bridge stays above it)
4. **Labels** (invisible, all zeros): a carrier stacked on top of each bar, holding the label of a
   step that sits above zero

The two visible series colour every bar by its kind, point by point with `c:dPt`: totals
`003841`, increases `00ADBF`, decreases `AA0028`. A bar that crosses zero puts its two halves in
the two visible series and has no base.

### Data Structure (the embedded workbook)

| Category | Base | Above zero | Below zero | Labels |
|----------|------|------------|------------|--------|
| Scheme incoming (total) | 0 | 2084 | 0 | 0 |
| DIAS incoming (+1624) | 2084 | 1624 | 0 | 0 |
| DIAS outgoing (-2439) | 1269 | 2439 | 0 | 0 |
| Net impact (total) | 0 | 1269 | 0 | 0 |

**Base**: the lower end of a bar that sits entirely above zero, the upper end of one entirely
below zero, and 0 for a bar that crosses zero. A decrease is still a positive height in the Above
zero series; its red comes from its `c:dPt`.

### Chart Definition

```xml
<c:barChart>
  <c:barDir val="col"/>
  <c:grouping val="stacked"/>

  <!-- Series 1: Base (invisible) -->
  <c:ser>
    <c:idx val="0"/>
    <c:order val="0"/>
    <c:tx>
      <c:strRef>
        <c:f>Sheet1!$B$1</c:f>
        <c:strCache>
          <c:ptCount val="1"/>
          <c:pt idx="0"><c:v>Base</c:v></c:pt>
        </c:strCache>
      </c:strRef>
    </c:tx>
    <c:spPr>
      <a:noFill/>  <!-- Invisible -->
      <a:ln><a:noFill/></a:ln>
    </c:spPr>
    <!-- Category and value references... -->
  </c:ser>

  <!-- Series 2: Above zero, each point in its kind's colour -->
  <c:ser>
    <c:idx val="1"/>
    <c:order val="1"/>
    <c:tx>
      <c:strRef>
        <c:f>Sheet1!$C$1</c:f>
        <c:strCache>
          <c:ptCount val="1"/>
          <c:pt idx="0"><c:v>Above zero</c:v></c:pt>
        </c:strCache>
      </c:strRef>
    </c:tx>
    <c:spPr>
      <a:solidFill>
        <a:srgbClr val="003841"/>  <!-- the total colour; each point overrides it -->
      </a:solidFill>
      <a:ln><a:noFill/></a:ln>
    </c:spPr>
    <c:invertIfNegative val="0"/>
    <c:dPt>
      <c:idx val="1"/>  <!-- an increase -->
      <c:spPr>
        <a:solidFill><a:srgbClr val="00ADBF"/></a:solidFill>
        <a:ln><a:noFill/></a:ln>
      </c:spPr>
    </c:dPt>
    <c:dPt>
      <c:idx val="2"/>  <!-- a decrease -->
      <c:spPr>
        <a:solidFill><a:srgbClr val="AA0028"/></a:solidFill>
        <a:ln><a:noFill/></a:ln>
      </c:spPr>
    </c:dPt>
    <!-- ... the same c:dPt in 003841 for the totals (idx 0 and 3), then c:dLbls ... -->
  </c:ser>

  <!-- Series 3: Below zero, coloured point by point the same way -->
  <!-- Series 4: Labels, invisible like Base, all zeros -->

  <c:gapWidth val="100"/>
  <c:overlap val="100"/>  <!-- Full overlap for stacking -->
</c:barChart>
```

### Data Labels

Each label is a `c:dLbl` that carries its text in `c:tx/c:rich`: the signed contribution
(`+1,624`, `-2,439`; a total is signed only when negative), formatted once, so no viewer
re-formats it. The series-level `c:showVal val="0"` hides every point without a `c:dLbl` of its
own. All labels are 12pt Bold.

A step that sits entirely above zero, increase or decrease, is labelled on the Labels carrier at
`inBase`, which puts the text just above its bar, in `003841`:

```xml
<c:ser>  <!-- Series 4: Labels -->
  <!-- ... c:idx, c:order, c:tx, invisible c:spPr ... -->
  <c:dLbls>
    <c:dLbl>
      <c:idx val="1"/>
      <c:tx>
        <c:rich>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p>
            <a:r>
              <a:rPr sz="1200" b="1">
                <a:solidFill>
                  <a:srgbClr val="003841"/>
                </a:solidFill>
                <a:latin typeface="Aptos"/>
              </a:rPr>
              <a:t>+1,624</a:t>
            </a:r>
          </a:p>
        </c:rich>
      </c:tx>
      <c:dLblPos val="inBase"/>  <!-- the base of a zero-height point on top of the bar -->
      <c:showLegendKey val="0"/>
      <c:showVal val="1"/>
      <c:showCatName val="0"/>
      <c:showSerName val="0"/>
      <c:showPercent val="0"/>
      <c:showBubbleSize val="0"/>
    </c:dLbl>
    <c:showLegendKey val="0"/>
    <c:showVal val="0"/>  <!-- every point without its own c:dLbl stays unlabelled -->
    <c:showCatName val="0"/>
    <c:showSerName val="0"/>
    <c:showPercent val="0"/>
    <c:showBubbleSize val="0"/>
    <c:showLeaderLines val="1"/>
  </c:dLbls>
  <!-- ... c:cat, c:val ... -->
</c:ser>
```

A total, or a step reaching below zero, is labelled on its own visible point (the Above zero part
when it has one) with `<c:dLblPos val="ctr"/>`, in the colour the contrast picker takes for its
fill: `FFFFFF` on the `003841` totals and the `AA0028` decreases, `000000` on the `00ADBF`
increases.

### Waterfall Axis (minimal)

```xml
<c:catAx>
  <c:axId val="100"/>
  <c:scaling>
    <c:orientation val="minMax"/>
  </c:scaling>
  <c:delete val="0"/>
  <c:axPos val="b"/>
  <c:majorTickMark val="none"/>  <!-- No tick marks -->
  <c:minorTickMark val="none"/>
  <c:tickLblPos val="low"/>
  <c:spPr>
    <a:ln w="6350">  <!-- 0.5pt -->
      <a:solidFill>
        <a:srgbClr val="BEC1BE"/>
      </a:solidFill>
    </a:ln>
  </c:spPr>
  <c:txPr>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p>
      <a:pPr>
        <a:defRPr sz="1200">  <!-- the category-axis size; never under the 10pt floor -->
          <a:solidFill>
            <a:srgbClr val="202020"/>
          </a:solidFill>
          <a:latin typeface="Aptos"/>
        </a:defRPr>
      </a:pPr>
    </a:p>
  </c:txPr>
</c:catAx>

<c:valAx>
  <c:axId val="200"/>
  <c:delete val="1"/>  <!-- Hide value axis completely -->
  <!-- ... -->
</c:valAx>
```

---

## Embedded Excel Workbook

Each chart references an embedded Excel file for its data.

### Chart Relationship File (chart1.xml.rels)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
                Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/package"
                Target="../embeddings/Microsoft_Excel_Worksheet1.xlsx"/>
</Relationships>
```

### Content Types Entry

Add to `[Content_Types].xml`:

```xml
<Override PartName="/ppt/charts/chart1.xml"
          ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>
```

### Creating Excel Workbook Programmatically

```javascript
// Using exceljs
const ExcelJS = require('exceljs');

const workbook = new ExcelJS.Workbook();
const sheet = workbook.addWorksheet('Sheet1');  // the sheet the chart formulas name

// Headers: the four waterfall series
sheet.getCell('A1').value = 'Category';
sheet.getCell('B1').value = 'Base';
sheet.getCell('C1').value = 'Above zero';
sheet.getCell('D1').value = 'Below zero';
sheet.getCell('E1').value = 'Labels';

// Data rows
const data = [
  ['Scheme Incoming', 0, 2084, 0, 0],
  ['DIAS Incoming', 2084, 1624, 0, 0],
  ['DIAS Outgoing', 1269, 2439, 0, 0],
  ['Net Impact', 0, 1269, 0, 0]
];

data.forEach((row, i) => {
  sheet.getCell(`A${i+2}`).value = row[0];
  sheet.getCell(`B${i+2}`).value = row[1];
  sheet.getCell(`C${i+2}`).value = row[2];
  sheet.getCell(`D${i+2}`).value = row[3];
  sheet.getCell(`E${i+2}`).value = row[4];
});

await workbook.xlsx.writeFile('Microsoft_Excel_Worksheet1.xlsx');
```

---

## Adding Charts to Slides

### Slide Relationship Entry (slide1.xml.rels)

```xml
<Relationship Id="rId3"
              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"
              Target="../charts/chart1.xml"/>
```

### Chart Frame in Slide XML

```xml
<p:graphicFrame>
  <p:nvGraphicFramePr>
    <p:cNvPr id="3" name="Chart 0"/>
    <p:cNvGraphicFramePr/>
    <p:nvPr/>
  </p:nvGraphicFramePr>
  <p:xfrm>
    <a:off x="338328" y="1665694"/>    <!-- Position in EMUs -->
    <a:ext cx="6858000" cy="4114800"/> <!-- Size in EMUs -->
  </p:xfrm>
  <a:graphic>
    <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">
      <c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
               xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
               r:id="rId3"/>
    </a:graphicData>
  </a:graphic>
</p:graphicFrame>
```

### EMU Conversion

- 1 inch = 914400 EMU
- 1 point = 12700 EMU
- 1 cm = 360000 EMU

---

## Chart Styling Summary

### NBG Font Settings

The same values as the chart style table in charts.md.

| Element | Font | Size | Bold | Color |
|---------|------|------|------|-------|
| Category labels | Aptos | 12pt | No | #202020 |
| Value-axis labels (line and area charts) | Aptos | 11pt | No | #939793 |
| Data labels (above bars) | Aptos | 12pt | Yes | #003841 |
| Data labels (inside a bar) | Aptos | 12pt | Yes | #FFFFFF on 003841, 007B85, AA0028; #000000 on 00ADBF, 939793, BEC1BE, 00DFF8 |
| Legend text | Aptos | 12pt | No | #202020 |
| Waterfall label, step above zero | Aptos | 12pt | Yes | #003841, just above the bar |
| Waterfall label, total or step below zero | Aptos | 12pt | Yes | centred in the bar, as for labels inside a bar |

### Axis Line

- Width: 6350 EMU (0.5pt)
- Color: #BEC1BE (Light Gray)
- Style: Solid

### Chart Background

```xml
<c:spPr>
  <a:noFill/>
  <a:ln><a:noFill/></a:ln>
  <a:effectLst/>
</c:spPr>
```

---

## Validation Checklist

Before repacking the PPTX:

- [ ] Chart XML is well-formed (validate with XML parser)
- [ ] All `r:id` references have corresponding relationship entries
- [ ] Excel workbook exists in `ppt/embeddings/`
- [ ] Content type override added for new charts
- [ ] Axis IDs match between chart elements (`<c:axId>` and `<c:crossAx>`)
- [ ] Data ranges in formulas match actual Excel data
- [ ] Colors use NBG palette (no off-brand colors)
