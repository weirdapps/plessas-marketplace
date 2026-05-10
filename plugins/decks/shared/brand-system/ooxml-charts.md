# OOXML Chart Reference for NBG Presentations

This document provides detailed specifications for creating and editing charts directly in Office Open XML (OOXML) format within PowerPoint presentations. Use this when editing existing presentations via XML manipulation.

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
  <c:lang val="en-US"/>
  <c:roundedCorners val="1"/>  <!-- 0 for waterfall charts -->
  <c:style val="2"/>
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
        <a:defRPr sz="1200" b="0">
          <a:solidFill>
            <a:srgbClr val="202020"/>
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
  <c:majorTickMark val="out"/>
  <c:minorTickMark val="none"/>
  <c:tickLblPos val="low"/>
  <c:spPr>
    <a:ln w="12700" cap="flat">
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
        <a:defRPr sz="1000" b="0">
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
  <c:gapWidth val="40"/>
  <c:overlap val="100"/>  <!-- Full overlap for stacking -->
</c:barChart>
```

### Multiple Series Colors

```xml
<!-- Series 1: Dark Teal -->
<c:ser>
  <c:spPr>
    <a:solidFill>
      <a:srgbClr val="003841"/>
    </a:solidFill>
  </c:spPr>
  <!-- ... -->
</c:ser>

<!-- Series 2: NBG Teal -->
<c:ser>
  <c:spPr>
    <a:solidFill>
      <a:srgbClr val="007B85"/>
    </a:solidFill>
  </c:spPr>
  <!-- ... -->
</c:ser>
```

### Stacked Data Labels (White on Bar)

```xml
<c:txPr>
  <a:bodyPr wrap="square" lIns="38100" tIns="19050" rIns="38100" bIns="19050" anchor="ctr">
    <a:spAutoFit/>
  </a:bodyPr>
  <a:lstStyle/>
  <a:p>
    <a:pPr>
      <a:defRPr sz="1200" b="0">
        <a:solidFill>
          <a:schemeClr val="bg1"/>  <!-- White text on colored bars -->
        </a:solidFill>
        <a:latin typeface="Aptos"/>
      </a:defRPr>
    </a:pPr>
  </a:p>
</c:txPr>
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
        <a:defRPr sz="1100">
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

## Waterfall Chart (Stacked Bar Simulation)

**Use for**: Financial flows, showing how values add/subtract to reach a total

Waterfall charts in OOXML are created using a stacked bar chart with three series:

1. **Base** (invisible) - positions the colored bars
2. **Increase** (cyan) - positive additions
3. **Decrease** (red) - subtractions

### Data Structure (Excel)

| Category | Base | Increase | Decrease |
|----------|------|----------|----------|
| Start Item | 0 | 2084 | 0 |
| Add Item | 2084 | 1624 | 0 |
| Subtract Item | 1269 | 0 | 2439 |
| Net Total | 0 | 1269 | 0 |

**Base calculation**: For each row, Base = previous running total after that row's change

### Chart Definition

```xml
<c:barChart>
  <c:barDir val="col"/>
  <c:grouping val="stacked"/>
  <c:varyColors val="0"/>

  <!-- Series 1: Base (invisible) -->
  <c:ser>
    <c:idx val="0"/>
    <c:order val="0"/>
    <c:tx>
      <c:strRef>
        <c:f>Waterfall!$B$1</c:f>
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
    <c:invertIfNegative val="0"/>
    <!-- Category and value references... -->
  </c:ser>

  <!-- Series 2: Increase (Cyan) -->
  <c:ser>
    <c:idx val="1"/>
    <c:order val="1"/>
    <c:tx>
      <c:strRef>
        <c:f>Waterfall!$C$1</c:f>
        <c:strCache>
          <c:ptCount val="1"/>
          <c:pt idx="0"><c:v>Increase</c:v></c:pt>
        </c:strCache>
      </c:strRef>
    </c:tx>
    <c:spPr>
      <a:solidFill>
        <a:srgbClr val="00ADBF"/>  <!-- NBG Cyan -->
      </a:solidFill>
      <a:ln><a:noFill/></a:ln>
    </c:spPr>
    <!-- ... -->
  </c:ser>

  <!-- Series 3: Decrease (Red) -->
  <c:ser>
    <c:idx val="2"/>
    <c:order val="2"/>
    <c:tx>
      <c:strRef>
        <c:f>Waterfall!$D$1</c:f>
        <c:strCache>
          <c:ptCount val="1"/>
          <c:pt idx="0"><c:v>Decrease</c:v></c:pt>
        </c:strCache>
      </c:strRef>
    </c:tx>
    <c:spPr>
      <a:solidFill>
        <a:srgbClr val="AA0028"/>  <!-- NBG Red -->
      </a:solidFill>
      <a:ln><a:noFill/></a:ln>
    </c:spPr>
    <!-- ... -->
  </c:ser>

  <c:gapWidth val="100"/>
  <c:overlap val="100"/>  <!-- Full overlap for stacking -->
</c:barChart>
```

### Selective Data Labels

Hide labels for zero values by using individual `<c:dLbl>` elements:

```xml
<c:dLbls>
  <!-- Delete label for index 2 (zero value) -->
  <c:dLbl>
    <c:idx val="2"/>
    <c:delete val="1"/>
  </c:dLbl>

  <!-- Custom positioning for total label -->
  <c:dLbl>
    <c:idx val="3"/>
    <c:layout>
      <c:manualLayout>
        <c:x val="0"/>
        <c:y val="-0.19"/>  <!-- Above the bar -->
      </c:manualLayout>
    </c:layout>
    <c:numFmt formatCode="#,##0" sourceLinked="0"/>
    <c:txPr>
      <a:bodyPr/>
      <a:lstStyle/>
      <a:p>
        <a:pPr>
          <a:defRPr sz="1400" b="1">  <!-- Larger, bold for total -->
            <a:solidFill>
              <a:schemeClr val="tx1">
                <a:lumMod val="75000"/>
                <a:lumOff val="25000"/>
              </a:schemeClr>
            </a:solidFill>
            <a:latin typeface="Aptos"/>
          </a:defRPr>
        </a:pPr>
      </a:p>
    </c:txPr>
    <c:showVal val="1"/>
  </c:dLbl>

  <!-- Default labels -->
  <c:numFmt formatCode="#,##0" sourceLinked="0"/>
  <c:txPr>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p>
      <a:pPr>
        <a:defRPr sz="1000" b="1">
          <a:solidFill>
            <a:schemeClr val="bg1"/>  <!-- White text inside bars -->
          </a:solidFill>
          <a:latin typeface="Aptos"/>
        </a:defRPr>
      </a:pPr>
    </a:p>
  </c:txPr>
  <c:showVal val="1"/>
</c:dLbls>
```

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
    <a:ln w="12700">
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
        <a:defRPr sz="900">
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
const sheet = workbook.addWorksheet('Waterfall');

// Headers
sheet.getCell('A1').value = 'Category';
sheet.getCell('B1').value = 'Base';
sheet.getCell('C1').value = 'Increase';
sheet.getCell('D1').value = 'Decrease';

// Data rows
const data = [
  ['Scheme Incoming', 0, 2084, 0],
  ['DIAS Incoming', 2084, 1624, 0],
  ['DIAS Outgoing', 1269, 0, 2439],
  ['Net Impact', 0, 1269, 0]
];

data.forEach((row, i) => {
  sheet.getCell(`A${i+2}`).value = row[0];
  sheet.getCell(`B${i+2}`).value = row[1];
  sheet.getCell(`C${i+2}`).value = row[2];
  sheet.getCell(`D${i+2}`).value = row[3];
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

| Element | Font | Size | Bold | Color |
|---------|------|------|------|-------|
| Category labels | Aptos | 10pt | No | #202020 |
| Data labels (column) | Aptos | 12pt | No | #202020 |
| Data labels (on bar) | Aptos | 12pt | No | White (bg1) |
| Legend text | Aptos | 11pt | No | #202020 |
| Waterfall labels | Aptos | 10pt | Yes | White (bg1) |
| Waterfall total | Aptos | 14pt | Yes | #404040 |

### Axis Line

- Width: 12700 EMU (1pt)
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
