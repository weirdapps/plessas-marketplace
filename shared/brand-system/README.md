# NBG Brand System

**Single Source of Truth** for all NBG presentation brand guidelines.

All agents and commands should reference these specifications. Do NOT create duplicate specifications elsewhere.

## Quick Reference

### Slide Dimensions (CRITICAL)

```yaml
width: 13.33"       # LAYOUT_WIDE in PptxGenJS
height: 7.5"
emu: 12,192,000 x 6,858,000
aspect_ratio: 16:9
```

### Primary Colors (no # prefix for PptxGenJS)

| Name | Hex | Usage |
|------|-----|-------|
| Dark Teal | `003841` | Titles, icons, headings |
| NBG Teal | `007B85` | Brand accent, section numbers, callout boxes |
| Cyan | `00ADBF` | Primary chart color |
| Bright Cyan | `00DFF8` | Bullets ONLY - **TOO BRIGHT for backgrounds** |
| Dark Text | `202020` | Body text |
| White | `FFFFFF` | **ALWAYS** for slide backgrounds |
| Off-white | `F5F8F6` | Light backgrounds for cards, metric boxes |

### Fonts

| Type | Font |
|------|------|
| Primary | Aptos (Regular weight) |
| Bullets | Arial |
| Fallback | Calibri, Tahoma |

### Logo Placement (from Template)

| Type | Position | Size | Usage |
|------|----------|------|-------|
| Small | 0.374", 7.071" | 0.822" x 0.236" | Content slides |
| Large | 0.374", 6.271" | 2.191" x 0.630" | Covers, dividers |
| Back Cover | 5.44", 2.98" | 2.45" x 1.54" | Centered oval |

### Page Numbers

- **Position**: 12.71", 7.1554" (0.33" x 0.152")
- **Font**: Aptos 10pt, color `939793`
- **On**: Content, chart, table, infographic slides
- **NOT on**: Cover, divider, back cover

## Critical Rules

| Rule | Enforcement |
|------|-------------|
| **White backgrounds ONLY** | Never use dark themes |
| **ALWAYS use Greek logo** | Use `nbg-logo-gr.svg` for ALL presentations - NEVER use the English logo |
| **NO Bright Cyan backgrounds** | `00DFF8` is TOO BRIGHT for box/card backgrounds - use `F5F8F6` (off-white) instead |
| **NO pie charts** | Always use doughnut instead |
| **NO "Thank You" slides** | Use plain back cover with centered logo |
| **Title weight** | Aptos Regular (NOT SemiBold) |
| **Text boxes** | `margin: 0`, `valign: 'top'` ALWAYS |
| **Content title size** | 24pt (NOT 44pt or larger) |
| **Cover subtitle** | 36pt (NOT 48pt). Lists units: `Cards \| GoForMore \| Embedded \| Digital \| SSB \| Direct \| Fraud \| Controls` — NOT "Cards and Digital Business" |
| **Line charts** | Smooth curves, 3pt lines, visible markers |
| **Chart colors** | ALWAYS specify explicit NBG colors |
| **NO shadows** | All shapes, pills, boxes must have no shadow |
| **Bumper is a pill** | Rounded rect 1.3x0.3, fill 007B85, 9pt Bold white ALL CAPS |
| **Charts are native** | Use proper Excel/python-pptx charts, NOT shape-drawn boxes |

## Typography Hierarchy

| Element | Size | Color | Weight |
|---------|------|-------|--------|
| Cover title | 48pt | 003841 | Regular |
| Cover subtitle | **36pt** | 007B85 | Regular |
| Divider number | 60pt | 007B85 | Regular |
| Divider title | **48pt** | 003841 | Regular |
| Contents header | **32pt** | 003841 | Bold |
| Content title | **24pt** | 003841 | Regular |
| Body text | 11-12pt | 202020 | Regular |
| Bumper (pill) | 9pt | FFFFFF on 007B85 | Bold |
| Metric value | **50pt** | 003841 | Bold |
| Metric label | **16pt** | 5A5F5A | Regular |
| Page number | 10pt | 939793 | Regular |

## Chart Color Sequence

Use in order for data series:

```javascript
['00ADBF', '003841', '007B85', '939793', 'BEC1BE', '00DFF8']
```

### Semantic Colors

| Status | Hex |
|--------|-----|
| Positive/Growth | 73AF3C |
| Negative/Decline | AA0028 |
| Neutral | 939793 |

## Reference Files

| File | Contents |
|------|----------|
| [colors.md](colors.md) | Complete color palette + contrast rules |
| [typography.md](typography.md) | Font specifications |
| [layouts.md](layouts.md) | Slide layout catalog + divider rules |
| [dimensions.md](dimensions.md) | Positioning reference |
| [charts.md](charts.md) | Chart configurations |
| [icons.md](icons.md) | Icon design rules |
| [ooxml-charts.md](ooxml-charts.md) | OOXML chart editing |
| [pillar-ds.md](pillar-ds.md) | **NBG Pillar Design System** - Digital product tokens |
| [asset-library.md](asset-library.md) | **Asset Library** - Icons, illustrations, screenshots |
| [generation-methods.md](generation-methods.md) | **Generation Methods** - PptxGenJS vs OOXML decision guide |

## Asset Library (NEW)

| Category | Count | Path |
|----------|-------|------|
| Icons | 338 | `assets/icons/` (20 categories) |
| Illustrations | 21 | `assets/illustrations/` |
| Logos | 10 | `assets/logos/` |
| Screenshots | 117 | `assets/screenshots/` (5 products) |

See [asset-library.md](asset-library.md) for complete documentation and usage rules.

## Logo Assets

**IMPORTANT: ALWAYS use the Greek logo (`nbg-logo-gr.svg`) for ALL presentations, regardless of language.**

| Asset | Path | Usage |
|-------|------|-------|
| **Greek Logo (DEFAULT)** | `assets/nbg-logo-gr.svg` | **ALL presentations** - this is the standard logo |
| English Logo | `assets/nbg-logo.svg` | DO NOT USE - kept for legacy only |
| PNG Fallback | `assets/nbg-logo-fallback.png` | Use when SVG rendering fails |
| Back Cover Logo | `assets/nbg-back-cover-logo.png` | Centered on back cover |
| Full Spec | `assets/NBG-PRESENTATION-SPEC.md` | Complete specification |

## PptxGenJS Constants

```javascript
const NBG = {
  colors: {
    darkTeal: '003841',
    teal: '007B85',
    cyan: '00ADBF',
    brightCyan: '00DFF8',
    darkText: '202020',
    white: 'FFFFFF',
    offWhite: 'F5F8F6',
    mediumGray: '939793',
    lightGray: 'BEC1BE',
    success: '73AF3C',
    alert: 'AA0028',
  },
  chartColors: ['00ADBF', '003841', '007B85', '939793', 'BEC1BE', '00DFF8'],
  fonts: { primary: 'Aptos', fallback: 'Arial' },
  logo: {
    small: { x: 0.374, y: 7.071, w: 0.822, h: 0.236 },
    large: { x: 0.374, y: 6.271, w: 2.191, h: 0.630 },
    backCover: { x: 5.44, y: 2.98, w: 2.45, h: 1.54 },
  },
  pageNumber: { x: 12.71, y: 7.1554, w: 0.33, h: 0.152 },
};
```

## Text Box Defaults

**ALWAYS apply these to all text boxes:**

```javascript
{
  margin: 0,
  valign: 'top',
}
```

---

**Version**: 3.4.0
**Last Updated**: February 2026
