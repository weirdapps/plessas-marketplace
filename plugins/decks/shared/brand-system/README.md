# NBG Brand System

> Machine source: [`tokens.yaml`](tokens.yaml). The builder renders with it, the validator checks
> against it, and `tools/test_brand_docs.py` fails when a table here stops quoting it. A brand
> value changes in tokens.yaml first, then in the prose.

**Single Source of Truth** for all NBG presentation brand guidelines.

All agents and commands should reference these specifications. Do NOT create duplicate specifications elsewhere.

## Quick Reference

### Slide Dimensions (CRITICAL)

```yaml
width: 13.333"      # 16:9 widescreen
height: 7.5"
emu: 12,192,000 x 6,858,000
aspect_ratio: 16:9
```

### Primary Colors (hex, no #)

| Name | Hex | Usage |
|------|-----|-------|
| Dark Teal | `003841` | Titles, headings, table header fill |
| NBG Teal | `007B85` | Primary brand: subtitles, section numbers, pills, KPI values |
| Cyan | `00ADBF` | Chart series 1, bullet glyphs |
| Bright Cyan | `00DFF8` | Feature accent, a mark only: **never a background, never text on white** |
| Dark Text | `202020` | Body text, and dark text on any light fill (Standard #22) |
| Caption Grey | `5A5F5A` | Captions, sources, footnotes, TOC descriptions, table notes |
| Muted Grey | `939793` | Page numbers, process arrows, muted axis labels; never body or label text |
| Light Grey | `BEC1BE` | Dividers, axis lines, hairlines |
| White | `FFFFFF` | **ALWAYS** for slide backgrounds |
| Off-white | `F5F8F6` | Default card and KPI-card fill |

### Fonts

| Type | Font |
|------|------|
| Primary | Aptos (Regular weight) |
| Display | Aptos Display, display sizes only; Aptos Regular is the default |
| Bullets | Arial (the bullet glyph only) |
| Fallback | Calibri, Tahoma |

Never Aptos SemiBold on a slide: titles are Regular (Standard #16), emphasis is Bold.

### Typography Hierarchy

| Element | Size | Color | Weight |
|---------|------|-------|--------|
| Cover title | 48pt (44pt minimum) | 003841 | Regular |
| Cover subtitle | **24pt** | 007B85 | Regular |
| Divider number | 60pt | 007B85 | Regular |
| Divider title | **48pt** | 003841 | Regular |
| Contents header | **24pt** | 003841 | Regular |
| Contents number | 18pt | 007B85 | Regular |
| Contents title | 16pt | 003841 | Regular |
| Contents description | 12pt | 5A5F5A | Regular |
| Content title | **24pt** | 003841 | Regular |
| Body text | **16pt** (14pt minimum, up to 20pt on a sparse slide) | 202020 | Regular |
| Section pill | 9pt ALL CAPS | FFFFFF on 007B85 | Bold |
| Card title | 16pt | 003841 | Bold |
| Card body | 14pt | 202020 | Regular |
| KPI big number | **50pt** | **007B85** | **Bold** |
| KPI caption | **16pt** | **5A5F5A** | Regular |
| Owner subtitle | **14pt** | **5A5F5A** | Regular |
| Caption | 12pt | 5A5F5A | Regular |
| Source / footnote | 11pt | 5A5F5A | Regular |
| Table header | 12pt | FFFFFF on 003841 | Bold |
| Table body | 12pt | 202020 | Regular |
| Chart data label | 12pt | 003841 | Bold |
| Chart axis / legend | 12pt | 202020 | Regular |
| Page number | 10pt | 939793 | Regular |

### Geometry

| Measure | Value | Note |
|---------|-------|------|
| Left gutter | 0.374" | Standard #15: every title, pill, body block and logo starts here |
| Content width | 12.585" | 13.333 - 2 × 0.374, written 12.59" in prose |
| Right boundary | 12.959" | 13.333 - 0.374; no element's right edge passes it |
| Title y | 0.5" | 0.75" when a section pill sits above it |
| Body top | 1.3" | Standard #11: the first body element, with or without a pill |
| Footer top | 6.85" | Nothing but the logo and page number below it |
| Grid gap | 0.3" | Between columns and cards |

### Section Pill

| Property | Value |
|----------|-------|
| Shape | Rounded rectangle, fill `007B85`, no outline, no shadow |
| Text | 9pt Bold white ALL CAPS, one line, no wrap |
| Position | x 0.374", y 0.35" |
| Height | 0.3" |
| Width | Sized to its text: text width + 2 × 0.1" inset, minimum 1.0" |
| Corner radius | 0.15", half the 0.3" height, so the ends are fully rounded (Standard #12) |

### Logo Placement

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
| **ONE RENDERER** | Light-mode decks are built by `nbg_build.py` (`decks-py build`) from a deck spec. No agent writes PptxGenJS, python-pptx or OOXML by hand. See `generation-methods.md`. |
| **BUILD FROM SCRATCH** | **Never use NBG template files** (`Presentation()` not `Presentation(template)`). Templates carry phantom "Placeholder text" artifacts. |
| **White backgrounds ONLY** | Never use dark themes, dark dividers, or colored cover backgrounds. **One exception: keynote mode**, see [keynote.md](keynote.md) and Standard #21 |
| **ALWAYS use Greek logo** | Use `nbg-logo-gr.png` for ALL presentations; NEVER use the English logo |
| **NO Bright Cyan backgrounds** | `00DFF8` is TOO BRIGHT for box/card backgrounds; use `F5F8F6` (off-white) instead |
| **NO dark bg + light text** | Fails accessibility. Use light backgrounds (#F5F8F6, #FFFFFF) with dark text (#003841 titles, #202020 text). **Keynote mode inverts this** under a measured WCAG guard; see [keynote.md](keynote.md) |
| **Dark text on a light fill** | `#202020`, never a third dark (Standard #22). Measured ratios: [colors.md](colors.md#color-contrast-rules-standard-22) |
| **NO pie charts** | Always use doughnut instead |
| **NO "Thank You" slides** | Use plain back cover with centered logo |
| **Title weight** | Aptos Regular (NOT SemiBold, NOT Bold) |
| **Text boxes** | `margin: 0`, `valign: 'top'` ALWAYS |
| **Content title size** | 24pt (NOT 44pt or larger) |
| **Body text size** | 14pt minimum, 16pt preferred; the builder grows a sparse slide's bullets toward 20pt. The full per-element floor table is `presentation-style-guide.md` Standard #11. |
| **Cover subtitle** | 24pt: the presenting unit(s), pipe-separated, no trailing period (for example `Unit A \| Unit B`). A user's own unit list belongs in their style preferences, not here. |
| **Dividers** | Title only, no subtitle/description. White background. Large logo (same as cover). |
| **Line charts** | 3.5pt lines, straight segments, hollow circle markers size 6 (white fill, a 2pt ring in the series colour). A time series is an area-line, never a bare line (Standards #2.8, #5) |
| **Chart colors** | ALWAYS specify explicit NBG colors. Same `#00ADBF` for both column AND bar charts. |
| **Table numbers** | Right-aligned. Text columns left-aligned. Zebra rows: alternate #FFFFFF / #F5F8F6. |
| **NO shadows** | All shapes, pills, boxes must have no shadow |
| **Section pill** | Rounded rect, fill 007B85, 9pt Bold white ALL CAPS, sized to its text (spec above) |
| **Charts are native** | Use proper native charts, NOT shape-drawn boxes |
| **Page numbers** | On content/chart/table slides ONLY. Not on cover, dividers, back cover. Position: see Quick Reference above and [dimensions.md](dimensions.md#page-number-placement). |
| **No periods in titles** | Titles and subtitles have no trailing periods |

## Chart Color Sequence

Use in order for data series (`tokens.yaml` `charts.palette`), at most six (Standard #22):

1. `00ADBF` Cyan
2. `003841` Dark Teal
3. `007B85` NBG Teal
4. `939793` Medium Gray
5. `BEC1BE` Light Gray
6. `00DFF8` Bright Cyan

Series 3 and 4 are 1.70:1 apart, so never let those two alone carry a distinction: label them
directly (Standard #22).

### Semantic Colors

| Status | Hex |
|--------|-----|
| Positive/Growth | 73AF3C |
| Negative/Decline | AA0028 |
| Neutral | 939793 |

## Reference Files

**Precedence**: the numbered Standards in
[presentation-style-guide.md](../presentation-style-guide.md) override every file in this
directory, including this one, wherever they disagree. Cite the Standard number when you
follow it. `tokens.yaml` encodes their outcome.

| File | Contents |
|------|----------|
| [presentation-style-guide.md](../presentation-style-guide.md) | **Numbered NBG Standards. Overrides everything below.** |
| [tokens.yaml](tokens.yaml) | **Machine-readable brand**: colours, type scale, geometry, components, charts, keynote tokens |
| [colors.md](colors.md) | Complete color palette + contrast rules |
| [typography.md](typography.md) | Font specifications |
| [layouts.md](layouts.md) | Slide layout catalog, element specs (Standard #20), divider rules |
| [dimensions.md](dimensions.md) | Positioning reference |
| [charts.md](charts.md) | Chart specification |
| [icons.md](icons.md) | Icon design rules |
| [ooxml-charts.md](ooxml-charts.md) | OOXML chart reference, for reading and repairing chart XML in existing decks |
| [pillar-ds.md](pillar-ds.md) | **NBG Pillar Design System** - Digital product tokens |
| [asset-library.md](asset-library.md) | **Asset Library** - Icons, illustrations, screenshots |
| [generation-methods.md](generation-methods.md) | **Generation Methods** - the one renderer, and which tool does what |
| [keynote.md](keynote.md) | **Keynote Mode** - dark full-bleed format for stage talks (Standard #21, the ONLY exception to the rules above) |

## Asset Library

| Category | Count | Path |
|----------|-------|------|
| Icons (duotone PNG) | 338 | `assets/icons/` (20 categories) |
| Duotone icons (SVG) | 19 files | `assets/icons-duotone/` |
| Illustrations | 21 PNG, 1 PDF, 9 SVG splash | `assets/illustrations/` |
| Logos | 10 PNG, 3 SVG | `assets/logos/` |
| Screenshots | 117 | `assets/screenshots/` (5 products) |

Paths are relative to the plugin root (`${CLAUDE_PLUGIN_ROOT}`). See
[asset-library.md](asset-library.md) for complete documentation and usage rules.

## Logo Assets

**IMPORTANT: ALWAYS use the Greek logo (`nbg-logo-gr.png`) for ALL presentations, regardless of language.**

| Asset | Path | Usage |
|-------|------|-------|
| **Greek Logo (DEFAULT)** | `assets/nbg-logo-gr.png` | **ALL presentations** - this is the standard logo |
| English Logo | `assets/nbg-logo.svg` | DO NOT USE - kept for legacy only |
| English wordmark (PNG) | `assets/nbg-logo-fallback.png` | Never on slides (Standard #10); the validator fails it. Not a fallback for the Greek logo |
| Back Cover Logo | `assets/nbg-back-cover-logo.png` | Centered on back cover |

The Greek wordmark PNG is 1200 x 348 (aspect 3.448): set its width and derive the height
(Standard #4). The validator recognises these logo files (and `assets/bank-logos/`) by their
content, falling back to their pixel size: if you ever re-encode one, keep its pixel dimensions.

## Text Box Defaults

**ALWAYS apply these to all text boxes:** zero internal margin (`margin: 0`) and top vertical
anchor (`valign: top`). The one pair that shares a baseline instead is the divider number and
title (Standard #3).
