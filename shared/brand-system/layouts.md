# NBG Slide Layout Catalog

## Slide Dimensions

```yaml
width: 13.33"
height: 7.5"
pptxgenjs: LAYOUT_WIDE
emu: 12,192,000 x 6,858,000
```

## Logo Placement (from Template)

Positions and sizes: [dimensions.md](dimensions.md#logo-placement-from-template). Which logo
goes on which slide, and always the Greek asset:

| Slide type | Logo | Asset |
|------------|------|-------|
| Content, chart, table, infographic, contents | Small | `assets/nbg-logo-gr.png` |
| Cover, section divider | Large | `assets/nbg-logo-gr.png` |
| Back cover | Centered oval, no text | `assets/nbg-back-cover-logo.png` |

## Page Numbers

### Placement

Page numbers appear on **content slides only** (not cover, dividers, back cover).

Position, size and the derived edge distances live in
[dimensions.md](dimensions.md#page-number-placement). Do not restate them here.

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

See [dimensions.md](dimensions.md#margins--safe-zones). The left gutter for placing text is
0.374" (Standard #15).

## Cover Slides

### Elements

Positions: [dimensions.md → Cover Slide](dimensions.md#cover-slide).

| Element | Font | Size |
|---------|------|------|
| Title | Aptos | 48pt |
| Subtitle | Aptos | **24pt** |
| Location | Aptos | 14pt |
| Date | Aptos | 14pt |

### Dimensions

- Title text box: 7.86" wide x 1.00" tall
- Subtitle text box: 7.86" wide x 0.80" tall

### Cover Subtitle Content

The subtitle lists the organizational units, NOT the generic department name:

```
Cards | GoForMore | Embedded | Digital | SSB | Direct | Fraud | Controls
```

Never use "Cards and Digital Business"; always list the individual units separated by pipes.

### Colors

- Title: Dark Teal `#003841`
- Subtitle: NBG Teal `#007B85`
- Location: Dark Teal `#003841`
- Date: Medium Gray `#939793`

## Contents / TOC Slide

### Elements

| Element | Font | Size | Color | Position |
|---------|------|------|-------|----------|
| "Contents" Header | Aptos | **24pt** Regular | #003841 | 0.374", 0.40" |
| Section Number | Aptos Bold | **18pt** | #007B85 | 0.374", y (see below) |
| Section Title | Aptos Bold | **16pt** | #003841 | 1.10", y |
| Description | Aptos | **12pt** | #5A5F5A | 1.10", y + 0.35" |

### Spacing

- First item Y: 1.48"
- Vertical spacing: 0.85" per item
- Max items: 6-7 (to fit with logo)

## Section Dividers

### Elements

Positions: [dimensions.md → Divider Slide](dimensions.md#divider-slide). The number is the
leftmost element and takes the 0.374" gutter; the title sits to its right and is the one
title that does not start at the gutter (Standard #15).

| Element | Font | Size |
|---------|------|------|
| Section Number | Aptos | 60pt |
| Section Title | Aptos | **48pt** |

### Number Format

- Two-digit: "01", "02", "03", etc.
- Color: NBG Teal `#007B85`
- Title Color: Dark Teal `#003841`

### Divider Consistency Rule (Non-Negotiable)

**Use only ONE type of divider across the entire presentation; never mix styles.**

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

Full width, two column 50/50, two column 40/60 and three column are specified in
[dimensions.md](dimensions.md#content-areas), together with the content-slide title and body
boxes. This catalog describes when to reach for each one; the coordinates have one home.

| Layout | Reach for it when |
|--------|-------------------|
| Full width | One chart, one table, or one idea carries the slide |
| Two column 50/50 | Two comparable blocks of equal weight |
| Two column 40/60 | Text on the left arguing over a chart on the right |
| Three column | Three parallel items, typically KPI cards |

## Content Typography

| Element | Font | Size | Spacing |
|---------|------|------|---------|
| Title | Aptos | 24pt | Line: 0.9 |
| Body text | Aptos | 14pt | Before: 9pt |
| Bullet L1 | Aptos | 14pt | Before: 14pt |
| Bullet L2 | Aptos | 14pt | Before: 5pt |
| Footnotes | Aptos | 11pt | - |

Sizes match [typography.md](typography.md#content-slide); the floors behind them are
Standard #11.

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

## Metric Card Component: TWO patterns

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
| Label | Aptos | **12pt** | `#202020` | Center |

### (B) Executive KPI Card: 3-up "Key Figures" pattern (signature)

Used for "Key Figures" slides, observed 30+ times across NBG executive reference decks. This is the **dominant** content pattern when the slide message is "here are the headline numbers for this unit."

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
| Unit pill (rounded chip) | (0.374, 0.45, ~1.4–2.3, 0.4), fill `#003841` | Aptos | 16pt | white | **Bold** |
| Section title (next to pill) | (~1.92–2.82, 0.48, 5.0, 0.38) | Aptos | 22pt | `#003841` | Regular |
| Owner subtitle ("Head: A. Smith") | (0.374, 1.05, 4.0, 0.3) | Aptos | 14pt | `#5A5F5A` | Regular |

Big-number examples (typical NBG executive deck): `750K`, `26%`, `€70M+`, `4.5M`, `3.3M`, `500K`. Caption examples: `Live Credit Cards`, `MS in Cards Turnover`, `Fee Income`.

## Status Pills (NBG executive signature, Progress & Priorities slides)

Used to flag commitment status on right-half "Priorities" lists.

| Element | Position | Fill | Text |
|---|---|---|---|
| Numbered bullet (oval) | (6.37, 2.12+i*row, 0.28, 0.28) | `#007B85` | white 10pt **Bold** ("1", "2", ...) |
| Status badge (right-aligned rounded rect) | (12.34, 2.12+i*row, 0.62, 0.26) | `#008000` (OK) / `#CC9900` (TBD) / `#CC0000` (Warn) | 11pt **Bold**: white on green and red, `#202020` on the amber (Standard #22) |
| Bullet body text | (6.75, 2.12+i*row, 5.49, 0.28) | n/a | Aptos 14pt `#202020` Regular |

**Left half, "Delivered" rows** (paired with Priorities right):

| Element | Position | Fill | Text |
|---|---|---|---|
| Accent stripe | (0.374, ..., 0.05, 0.52) | `#008000` | n/a |
| Row body | (0.42, ..., 5.45, 0.52) | `#E8F5E9` | Arial 15pt **Bold** `#008000` ("✓ <delivered item>") |

## Recommended-Option Highlight (comparison slides)

When one option among several is the recommendation, mark it with the **gold** treatment, never green (green is reserved for Delivered/OK status; see `colors.md → Recommended-option highlight`).

| Element | Spec |
|---|---|
| Card border | 1.5pt `#D9A757` (gold) around the recommended card only |
| Card fill | `#FBF3E4` (cream); optional, for extra pull |
| "RECOMMENDED" tab | small rounded pill/tab, fill `#D9A757`, `#202020` ALL-CAPS Aptos 11pt Bold, notched at the card's top edge |

One convention per deck: pick the gold treatment and keep it consistent. Do not also place a green "recommended" pill elsewhere in the same deck. The non-recommended options stay in the default `#F5F8F6` card with no border.

## Clean Executive Cover (DIY on Blank Page): signature

When a clean executive cover is needed (clean, white, NO decorative shapes), build on the **Blank Page** layout (Master 9 in the internal NBG template, the only cover-grade layout with a fully white background; the template is not bundled, and `assets/slide-catalog.yaml` records the index mapping):

Positions: [dimensions.md → Cover Slide](dimensions.md#cover-slide) and
[Large Logo](dimensions.md#large-logo---covers--dividers). Type and color:

| Element | Font | Size | Color | Weight |
|---|---|---|---|---|
| Title | Aptos | **48pt** | `#003841` | Regular |
| Subtitle (pipe-separated unit list) | Aptos | **24pt** | `#007B85` | Regular |
| Location | Aptos | 14pt | `#003841` | Regular |
| Date | Aptos | 14pt | `#939793` | Regular |
| **NBG logo (large)** | n/a | n/a | n/a | always Greek logo (`assets/nbg-logo-gr.png`) |

**Subtitle convention**: pipe-separated unit list, e.g. `Cards | GoForMore | Embedded | Digital | SSB | Direct | Fraud | Controls`. NOT a generic department-name string.

**Decoration policy**: white background, NO colored bars, NO decorative shapes. Decoration is purely typographic (size/weight/color contrast).

> The internal NBG template ALSO carries master-layout covers (`13_Cover`, `14_Cover`, `24_Cover`) which carry pre-baked decorative bands. These work, but the NBG executive default favours the DIY-on-Blank approach because it stays purely white. Use master-layout covers only when you specifically want the layout's pre-baked visual.

## Lean Divider (DIY on Blank Page): signature

The bundled `1_Divider` / `6_Divider` master layouts have **dark-teal background fills** that violate the "white backgrounds only" rule. For a white divider, build on **Blank Page**:

Positions: [dimensions.md → Divider Slide](dimensions.md#divider-slide). Type and color:

| Element | Font | Size | Color | Weight |
|---|---|---|---|---|
| Section number (e.g. "01") | Aptos | **60pt** | `#007B85` | Regular |
| Section title (e.g. "Organization & People") | Aptos | **48pt** | `#003841` | Regular |
| **NBG logo (large, same as cover)** | n/a | n/a | n/a | Greek logo |

White background. No description text. No page number on dividers.

> NBG executive decks often dispense with section dividers entirely (most reference decks have ZERO dividers). Use sparingly.

## Progress & Priorities: 2-column split (NBG executive signature)

Used in Progress & Priorities slides. Same page header as Key Figures (unit pill + title + owner subtitle).

```
LEFT half (Delivered):                   RIGHT half (Priorities):
    "Delivered" header (16pt #003841)        "Priorities" header (16pt #003841)
    Row 1: ✓ stripe + #E8F5E9 fill           Row 1: oval bullet + body + status badge
    Row 2: ...                               Row 2: ...
    (5-7 rows max)                           (5-7 numbered priorities max)
```

LEFT column x range: 0.374 → 5.87 (width 5.5)
RIGHT column x range: 6.37 → 12.956 (width 6.59)

## Table Styling (NBG executive signature)

From a reference deck slide 4 (10×7 table at (0.37, 1.65, 12.41, 4.03)):

**This is the single table spec.** `typography.md` and `charts.md` point here.

- **Header row**: fill `#003841`, **12pt Aptos Bold WHITE**
- **Body rows alternate (zebra)**: `#FFFFFF` and `#F5F8F6`
- **First column** (label): 12pt Aptos **Bold** `#202020`
- **Other body cells**: 12pt Aptos Regular `#202020`
- **Numeric value cells**: 12pt, emphasis carried by weight rather than size
- **In-cell positive emphasis** ("+1"): `#007B85` Bold
- **Neutral dashes**: `#939793`
- **Priority flags** ("H2"): `#CC9900` Bold
- **Notes column**: 11pt `#5A5F5A` Regular
- **Borders**: default thin (no custom override)
- **NO full-cell status fills**: emphasis is in-cell color + bold, not row coloring

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

## Element Sequences (starting points, NOT separate formats)

There is ONE NBG deck format (see `presentation-style-guide.md` Standard #20). The rows below are **common element sequences**, not deck-type templates: every deck uses the same chassis (cover, logo, page numbers, palette, cards) and simply selects the elements its message needs. Start from the closest sequence, then add or drop elements by what each slide must say; never invent a new format per topic.

| Communication need | Common element sequence (adapt freely) |
|---|---|
| Executive summary | Cover → Key metrics → Charts → Back Cover |
| Project update | Cover → Contents → Timeline → Status → Next steps → Back Cover |
| Data presentation | Cover → Contents → Charts (bar, line, doughnut) → Tables → Key takeaways → Back Cover |
| Strategy | Cover → (Dividers) → Infographics → Process flows → Timeline → Back Cover |
| Financial report | Cover → Contents → KPI metrics → Charts → Tables → Disclaimers → Back Cover |

**Note**: Never use pie charts, always use doughnut. Dividers are optional (most NBG decks use none).
