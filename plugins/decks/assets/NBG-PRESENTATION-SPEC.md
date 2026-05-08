# NBG PowerPoint Template Specification

**Single Source of Truth**: For detailed specifications, see [`shared/nbg-brand-system/README.md`](../shared/nbg-brand-system/README.md)

This document provides a quick reference for NBG presentation creation. For comprehensive documentation, refer to the brand system files.

---

## Quick Reference

### Slide Dimensions
```
Width:  13.33" (12,192,000 EMU)
Height: 7.5"  (6,858,000 EMU)
Layout: LAYOUT_WIDE (16:9)
```

### Essential Colors
| Purpose | Hex | Color Name |
|---------|-----|------------|
| Title text | `003841` | Dark Teal |
| Body text | `202020` | Dark Text |
| Brand accent | `007B85` | NBG Teal |
| Bullets | `00DFF8` | Bright Cyan |
| Backgrounds | `FFFFFF` | White (always) |
| Cards | `F5F8F6` | Off-white |

**Chart Colors** (in order):
```javascript
['00ADBF', '003841', '007B85', '939793', 'BEC1BE', '00DFF8']
```

### Typography
| Element | Font | Size |
|---------|------|------|
| Cover title | Aptos | 48pt |
| Content title | Aptos | 24pt |
| Body text | Aptos | 11-12pt |
| Divider number | Aptos | 60pt |
| Page number | Aptos | 10pt |

**Text Boxes**: Always use zero margins (`margin: 0`)

### Logo Positioning
| Type | Position (x, y) | Size (w × h) |
|------|-----------------|--------------|
| Small (content) | 0.374", 7.071" | 0.822" × 0.236" |
| Large (covers) | 0.374", 6.271" | 2.191" × 0.630" |
| Back cover (centered) | 5.44", 2.98" | 2.45" × 1.54" |

### Page Numbers
- **Position**: 12.71", 7.1554"
- **Size**: 0.33" × 0.152"
- **On slides**: Content, charts, tables, infographics
- **Not on**: Cover, dividers, back cover

---

## Critical Rules

### MUST DO
- Use **LAYOUT_WIDE** (13.33" x 7.5")
- Use **white backgrounds** (`#FFFFFF`)
- Use **Aptos** font (Arial fallback)
- Use **action titles** (full sentences, not labels)
- Use **doughnut charts** (never pie)
- Set text box **margins to 0**

### MUST NOT DO
- Use pie charts (use doughnut)
- Include "Thank You" text on back cover
- Put page numbers on covers/dividers
- Use dark backgrounds
- Use fonts other than Aptos/Arial

---

## Brand System Reference

For complete specifications, see these files:

| Topic | File |
|-------|------|
| **All Specifications** | `shared/nbg-brand-system/README.md` |
| Colors | `shared/nbg-brand-system/colors.md` |
| Typography | `shared/nbg-brand-system/typography.md` |
| Layouts | `shared/nbg-brand-system/layouts.md` |
| Dimensions | `shared/nbg-brand-system/dimensions.md` |
| Charts | `shared/nbg-brand-system/charts.md` |
| Icons | `shared/nbg-brand-system/icons.md` |
| OOXML Charts | `shared/nbg-brand-system/ooxml-charts.md` |
| Pillar DS | `shared/nbg-brand-system/pillar-ds.md` |

---

## PptxGenJS Configuration

```javascript
const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';

// NBG Colors (no # prefix for PptxGenJS)
const NBG_COLORS = {
  darkTeal: '003841',
  teal: '007B85',
  cyan: '00ADBF',
  brightCyan: '00DFF8',
  darkText: '202020',
  white: 'FFFFFF',
  offWhite: 'F5F8F6',
  mediumGray: '939793',
  lightGray: 'BEC1BE',
};

// Chart colors
const NBG_CHART_COLORS = [
  '00ADBF', '003841', '007B85', '939793', 'BEC1BE', '00DFF8'
];

// Default text style
const textStyle = {
  fontFace: 'Aptos',
  fontSize: 12,
  color: '202020',
  margin: 0,
};

// Logo (content slides)
const NBG_LOGO = { x: 0.374, y: 7.071, w: 0.822, h: 0.236 };

// Page number
const NBG_PAGE_NUMBER = { x: 12.71, y: 7.1554, w: 0.33, h: 0.152 };
```

---

## Slide Types Quick Reference

| Type | Key Elements |
|------|--------------|
| **Cover** | Title 48pt, subtitle, date, location |
| **Divider** | Number 60pt teal + title 48pt |
| **Content** | Action title 24pt + bullets/text |
| **Chart** | Title + chart (doughnut/bar/line) |
| **Infographic** | Numbered items, process flows |
| **Table** | Header row + data rows |
| **Back Cover** | Centered oval logo only |

---

## Template Assets

| Asset | Path |
|-------|------|
| Greek logo | `assets/nbg-logo-gr.svg` |
| English logo | `assets/nbg-logo.svg` |
| Back cover logo | `assets/nbg-back-cover-logo.png` |
| Slide catalog | `assets/slide-catalog.yaml` |
| Template (GR) | `assets/templates/NBG-Template-GR.pptx` |
| Template (EN) | `assets/templates/NBG-Template-EN.pptx` |

---

## Validation

Run validation to ensure brand compliance:

```bash
python tools/nbg-presentation/nbg_validate.py presentation.pptx
```

Checks: dimensions, colors, fonts, logos, back cover format, chart types, text margins.
