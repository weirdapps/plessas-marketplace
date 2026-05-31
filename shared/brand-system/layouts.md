# NBG Slide Layout Catalog

## Slide Dimensions

```yaml
width: 13.33"
height: 7.5"
pptxgenjs: LAYOUT_WIDE
emu: 12,192,000 x 6,858,000
```

## Logo Placement (from Template)

### Small Logo - Content Slides

Use for ALL content slides, charts, tables, infographics.

| Element | Position (x, y) | Size (w x h) | Edge Distance |
|---------|-----------------|--------------|---------------|
| Small Logo | 0.374", 7.071" | 0.822" x 0.236" | 0.19" from bottom |

### Large Logo - Covers & Dividers

Use for cover slides and section dividers only.

| Element | Position (x, y) | Size (w x h) |
|---------|-----------------|--------------|
| Large Logo | 0.374", 6.271" | 2.191" x 0.630" |

### Back Cover Logo - Centered

Plain back cover with centered oval NBG building logo (NO text).

| Element | Position (x, y) | Size (w x h) | Notes |
|---------|-----------------|--------------|-------|
| Centered Oval Logo | 5.44", 2.98" | 2.45" x 1.54" | Centered on slide |

Asset: `assets/nbg-back-cover-logo.png`

## Page Numbers

### Placement

Page numbers appear on **content slides only** (not cover, dividers, back cover).

| Element | Position (x, y) | Size (w x h) | Edge Distance |
|---------|-----------------|--------------|---------------|
| Page Number | 12.71", 7.1554" | 0.33" x 0.152" | 0.29" right, 0.27" bottom |

### Styling

- **Font**: Aptos, 10pt
- **Color**: Medium Gray `#939793`
- **Alignment**: Right

### Which Slides Get Page Numbers

| Slide Type | Page Number |
|------------|-------------|
| Cover | No |
| Divider | No |
| Content | Yes |
| Chart | Yes |
| Infographic | Yes |
| Table | Yes |
| Back Cover | No |

## Standard Margins

| Edge | Value |
|------|-------|
| Left margin | 0.37" |
| Right margin | 0.37" |
| Top (title) | 0.5" |
| Top (content) | 1.33" |

## Cover Slides

### Elements

| Element | Font | Size | Position (x, y) |
|---------|------|------|-----------------|
| Title | Aptos | 48pt | 0.37", 1.39" |
| Subtitle | Aptos | **24pt** | 0.37", 2.27" |
| Location | Aptos | 14pt | 0.37", 4.58" |
| Date | Aptos | 14pt | 0.37", 4.97" |

### Dimensions

- Title text box: 7.86" wide x 1.00" tall
- Subtitle text box: 7.86" wide x 0.80" tall

### Cover Subtitle Content

The subtitle lists the organizational units, NOT the generic department name:

```
Cards | GoForMore | Embedded | Digital | SSB | Direct | Fraud | Controls
```

Never use "Cards and Digital Business" — always list the individual units separated by pipes.

### Colors

- Title: Dark Teal `#003841`
- Subtitle: NBG Teal `#007B85`
- Location: Dark Teal `#003841`
- Date: Medium Gray `#939793`

## Contents / TOC Slide

### Elements

| Element | Font | Size | Color | Position |
|---------|------|------|-------|----------|
| "Contents" Header | Aptos Bold | **32pt** | #003841 | 0.37", 0.36" |
| Section Number | Aptos Bold | **18pt** | #007B85 | 0.37", y (see below) |
| Section Title | Aptos Bold | **16pt** | #003841 | 1.10", y |
| Description | Aptos | **12pt** | #595959 | 1.10", y + 0.35" |

### Spacing

- First item Y: 1.48"
- Vertical spacing: 0.85" per item
- Max items: 6-7 (to fit with logo)

## Section Dividers

### Elements

| Element | Font | Size | Position |
|---------|------|------|----------|
| Section Number | Aptos | 60pt | 0.37", 2.84" |
| Section Title | Aptos | **48pt** | 1.86", 2.84" |

### Number Format

- Two-digit: "01", "02", "03", etc.
- Color: NBG Teal `#007B85`
- Title Color: Dark Teal `#003841`

### Divider Consistency Rule (Non-Negotiable)

**Use only ONE type of divider across the entire presentation — never mix styles.**

| Rule | Enforcement |
|------|-------------|
| Single style | All dividers must use the same layout/style throughout |
| Default | Use the standard white background divider |
| Validation | Before completing, verify all dividers match |

### Preventing Text Overlap

If the section title is long (>25 characters) and wraps to multiple lines, the description text may overlap. Fix by:

1. Shortening the title if possible
2. Pushing the description element down
3. Using line breaks intentionally

## Content Layouts

### Full Width Content

```yaml
full_width:
  title:
    x: 0.37"
    y: 0.5"
    w: 12.59"
    h: 0.6"
  content:
    x: 0.37"
    y: 1.33"
    w: 12.59"
    h: 4.5"
```

### Two Column (50/50)

```yaml
two_column_even:
  left:
    x: 0.37"
    y: 1.33"
    w: 5.5"
    h: 4.5"
  right:
    x: 6.1"
    y: 1.33"
    w: 5.5"
    h: 4.5"
```

### Two Column (40/60 - Text/Chart)

```yaml
two_column_text_chart:
  text:
    x: 0.37"
    y: 1.33"
    w: 4.5"
    h: 4.5"
  chart:
    x: 5.1"
    y: 1.2"
    w: 6.7"
    h: 4.6"
```

### Three Column

```yaml
three_column:
  col1:
    x: 0.37"
    y: 1.33"
    w: 3.6"
  col2:
    x: 4.2"
    y: 1.33"
    w: 3.6"
  col3:
    x: 8.0"
    y: 1.33"
    w: 3.6"
```

## Content Typography

| Element | Font | Size | Spacing |
|---------|------|------|---------|
| Title | Aptos | 24pt | Line: 0.9 |
| Body text | Aptos | 11-14pt | Before: 9pt |
| Bullet L1 | Aptos | 14pt | Before: 14pt |
| Bullet L2 | Aptos | 12pt | Before: 5pt |
| Footnotes | Aptos | 8pt | - |

## Back Cover / Closing Slides

**IMPORTANT**: NBG presentations should NOT use "Thank You" or "Questions" text. Use a **plain back cover** instead.

### Plain Back Cover (REQUIRED)

- White background
- Centered oval NBG building logo
- **NO text at all**
- **NO corner logo**
- **NO page number**

### What NOT to Include

- "Thank You" text
- "Questions?" text
- "Q&A" labels
- Contact information (use dedicated slides)
- Any decorative elements

## Metric Card Component — TWO patterns

### (A) Inline KPI Callout (small, for chart-slide margins)

Light background card placed in the right margin of a chart slide for a key callout.

| Property | Value |
|----------|-------|
| Background | `#F5F8F6` |
| Border | 1pt `#BEC1BE` |
| Corner radius | 6.25% |
| Size | 1.40" × 0.80" (typical) |

| Element | Font | Size | Color | Alignment |
|---------|------|------|-------|-----------|
| Value | Aptos Bold | **18pt** | `#007B85` | Center |
| Label | Aptos | **9pt** | `#202020` | Center |

### (B) Executive KPI Card — 3-up "Key Figures" pattern (signature)

Used for "Key Figures" slides — observed 30+ times across NBG executive reference decks. This is the **dominant** content pattern when the slide message is "here are the headline numbers for this unit."

**Slide composition** (3 cards, equal-width, centered):

```
Card 1: Rectangle at (1.01, 2.15, 3.5, 3.0)   fill = #F5F8F6, no border
Card 2: Rectangle at (4.92, 2.15, 3.5, 3.0)   fill = #F5F8F6, no border
Card 3: Rectangle at (8.81, 2.15, 3.5, 3.0)   fill = #F5F8F6, no border
```

**Inside each card** (offsets relative to card x):

| Element | Position (within card) | Font | Size | Color | Weight | Align |
|---|---|---|---|---|---|---|
| Big number | (card_x, 2.65, 3.5, 1.0) | Aptos | **50pt** | `#007B85` | **Bold** | Center |
| Caption | (card_x + 0.30, 3.85, 2.9, 0.8) | Aptos | **16pt** | `#5A5F5A` | Regular | Center |

**Page header** (above the cards):

| Element | Position | Font | Size | Color | Weight |
|---|---|---|---|---|---|
| Unit pill (rounded chip) | (0.37, 0.45, ~1.4–2.3, 0.4) — fill `#003841` | Aptos | 16pt | white | **Bold** |
| Section title (next to pill) | (~1.92–2.82, 0.48, 5.0, 0.38) | Aptos | 22pt | `#003841` | Regular |
| Owner subtitle ("Head: A. Smith") | (0.37, 1.05, 4.0, 0.3) | Aptos | 14pt | `#5A5F5A` | Regular |

Big-number examples (typical NBG executive deck): `750K`, `26%`, `€70M+`, `4.5M`, `3.3M`, `500K`. Caption examples: `Live Credit Cards`, `MS in Cards Turnover`, `Fee Income`.

## Status Pills (NBG executive signature — Progress & Priorities slides)

Used to flag commitment status on right-half "Priorities" lists.

| Element | Position | Fill | Text |
|---|---|---|---|
| Numbered bullet (oval) | (6.37, 2.12+i*row, 0.28, 0.28) | `#007B85` | white 10pt **Bold** ("1", "2", ...) |
| Status badge (right-aligned rounded rect) | (12.34, 2.12+i*row, 0.62, 0.26) | `#008000` (OK) / `#CC9900` (TBD) / `#CC0000` (Warn) | white 11pt **Bold** ("OK"/"TBD"/"H2") |
| Bullet body text | (6.75, 2.12+i*row, 5.49, 0.28) | — | Aptos 14pt `#202020` Regular |

**Left half — "Delivered" rows** (paired with Priorities right):

| Element | Position | Fill | Text |
|---|---|---|---|
| Accent stripe | (0.37, ..., 0.05, 0.52) | `#008000` | — |
| Row body | (0.42, ..., 5.45, 0.52) | `#E8F5E9` | Arial 15pt **Bold** `#008000` ("✓ <delivered item>") |

## Clean Executive Cover (DIY on Blank Page) — signature

When a clean executive cover is needed (clean, white, NO decorative shapes), build on the **Blank Page** layout (Master 9 in NBG-Template-GR.pptx — the only cover-grade layout with a fully white background):

| Element | Position | Font | Size | Color | Weight |
|---|---|---|---|---|---|
| Title | (0.37, 1.36, 7.86, 0.81) | Aptos | **48pt** | `#003841` | Regular |
| Subtitle (pipe-separated unit list) | (0.37, 2.40, 12.59, 0.80) | Aptos | **24pt** | `#007B85` | Regular |
| Location | (0.37, 4.0, 4.0, 0.3) | Aptos | 14pt | `#003841` | Regular |
| Date | (0.37, 4.4, 4.0, 0.3) | Aptos | 14pt | `#939793` | Regular |
| **NBG logo (large)** | **(0.37, 6.27, 2.19, 0.63)** | — | — | — | always Greek logo (`assets/nbg-logo-gr.png`) |

**Subtitle convention**: pipe-separated unit list, e.g. `Cards | GoForMore | Embedded | Digital | SSB | Direct | Fraud | Controls`. NOT a generic department-name string.

**Decoration policy**: white background, NO colored bars, NO decorative shapes. Decoration is purely typographic (size/weight/color contrast).

> The bundled NBG-Template-GR.pptx ALSO ships master-layout covers (`13_Cover`, `14_Cover`, `24_Cover`) which carry pre-baked decorative bands. These work, but the NBG executive default favours the DIY-on-Blank approach because it stays purely white. Use master-layout covers only when you specifically want the layout's pre-baked visual.

## Lean Divider (DIY on Blank Page) — signature

The bundled `1_Divider` / `6_Divider` master layouts have **dark-teal background fills** that violate the "white backgrounds only" rule. For a white divider, build on **Blank Page**:

| Element | Position | Font | Size | Color | Weight |
|---|---|---|---|---|---|
| Section number (e.g. "01") | (0.37, 2.84, 1.4, 0.9) | Aptos | **60pt** | `#007B85` | Regular |
| Section title (e.g. "Organization & People") | (1.86, 2.88, 10.0, 0.9) | Aptos | **48pt** | `#003841` | Regular |
| **NBG logo (large — same as cover)** | **(0.37, 6.27, 2.19, 0.63)** | — | — | — | Greek logo |

White background. No description text. No page number on dividers.

> NBG executive decks often dispense with section dividers entirely (most reference decks have ZERO dividers). Use sparingly.

## Progress & Priorities — 2-column split (NBG executive signature)

Used in Progress & Priorities slides. Same page header as Key Figures (unit pill + title + owner subtitle).

```
LEFT half (Delivered):                   RIGHT half (Priorities):
    "Delivered" header (16pt #003841)        "Priorities" header (16pt #003841)
    Row 1: ✓ stripe + #E8F5E9 fill           Row 1: oval bullet + body + status badge
    Row 2: ...                               Row 2: ...
    (5-7 rows max)                           (5-7 numbered priorities max)
```

LEFT column x range: 0.37 → 5.87 (width 5.5)
RIGHT column x range: 6.37 → 12.96 (width 6.59)

## Table Styling (NBG executive signature)

From a reference deck slide 4 (10×7 table at (0.37, 1.65, 12.41, 4.03)):

- **Header row**: fill `#003841`, **10.5pt Aptos Bold WHITE**
- **Body rows alternate (zebra)**: `#FFFFFF` and `#F5F8F6`
- **First column** (label): 12pt Aptos **Bold** `#202020`
- **Other body cells**: 10.5pt Aptos Regular `#202020`
- **Numeric value cells**: 12pt (slightly larger than label cells for emphasis)
- **In-cell positive emphasis** ("+1"): `#007B85` Bold
- **Neutral dashes**: `#939793`
- **Priority flags** ("H2"): `#CC9900` Bold
- **Notes column**: 10pt `#5A5F5A` Regular
- **Borders**: default thin (no custom override)
- **NO full-cell status fills** — emphasis is in-cell color + bold, not row coloring

## Infographic Patterns

### Numbered List (3x3 grid)

- 9 items with numbers 1-9
- Each: Number + Title + Description
- Numbers: Large, teal colored

### Sequential Steps (2x3 grid)

- 6 items with "01", "02", etc.
- Two-digit numbering

### KPI Dashboard

- 2x3 grid layout
- Large numbers with labels
- Use Metric Card components

### Timeline (Horizontal)

- Month/date markers
- Milestone points
- Event descriptions

## Shape Presets

| Shape | Usage |
|-------|-------|
| Rectangle | Backgrounds, containers |
| Rounded Rectangle | Cards, callouts, buttons |
| Triangle | Arrows, indicators |
| Ellipse | Icons, bullets |
| Line | Dividers, timelines |

## Communication Use Case Guide

### Executive Summaries

Cover -> Key Metrics -> Charts -> Back Cover

### Project Updates

Cover -> Contents -> Timeline -> Status -> Next Steps -> Back Cover

### Data Presentations

Cover -> Contents -> Charts (bar, line, doughnut) -> Tables -> Key Takeaways -> Back Cover

**Note**: Never use pie charts - always use doughnut.

### Strategy Decks

Cover -> Dividers -> Infographics -> Process Flows -> Timeline -> Back Cover

### Financial Reports

Cover -> Contents -> KPI Metrics -> Charts -> Tables -> Disclaimers -> Back Cover
