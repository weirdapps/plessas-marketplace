# NBG Slide Layout Catalog

> Machine source: [`tokens.yaml`](tokens.yaml) (`components`, `geometry`, `type`). This file says
> which layout or element to reach for and quotes those values; a value changes in tokens.yaml
> first.

## Slide Dimensions

```yaml
width: 13.333"
height: 7.5"
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

- Title text box: 12.0" wide x 1.0" tall, one line (Standard #13)
- Subtitle text box: 12.0" wide x 0.8" tall, one line, 0.1" below the title

### Cover Subtitle Content

The subtitle names the presenting unit(s), pipe-separated, with no trailing period:

```
Unit A | Unit B | Unit C
```

Name the units that present the deck, not a generic department string. A user's own unit list
belongs in their style preferences (`${CLAUDE_PLUGIN_DATA}/style-preferences.md`), not here.

### Colors

- Title: Dark Teal `#003841`
- Subtitle: NBG Teal `#007B85`
- Location: Dark Teal `#003841`
- Date: Caption Grey `#5A5F5A`

## Contents / TOC Slide

### Elements

| Element | Font | Size | Color | Position |
|---------|------|------|-------|----------|
| "Contents" Header | Aptos | **24pt** Regular | #003841 | 0.374", 0.40" |
| Section Number | Aptos | **18pt** Regular | #007B85 | 0.374", y (see below) |
| Section Title | Aptos | **16pt** Regular | #003841 | 1.174", y |
| Description | Aptos | **12pt** Regular | #5A5F5A | 1.174", y + 0.35" |

The title column starts at 1.174": the 0.374" gutter plus the 0.8" number column
(`tokens.yaml` `components.contents.number_w`).

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

Number and title share one baseline (Standard #3); see the divider block in dimensions.md for how.

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
| Body text | Aptos | 16pt (14pt dense) | Before: 9pt, line 1.1 |
| Bullet L1 | Aptos | 16pt | Before: 14pt (none on the first), hanging indent 0.25" |
| Bullet L2 | Aptos | 16pt | Before: 5pt |
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
| Border | None (only the recommended card carries one) |
| Corners | Tight, radius 0.04" (Standard #12) |
| Size | 1.40" × 0.80" (typical) |

| Element | Font | Size | Color | Alignment |
|---------|------|------|-------|-----------|
| Value | Aptos Bold | **18pt** | `#007B85` | Center |
| Label | Aptos | **12pt** | `#202020` | Center |

### (B) Executive KPI Card: 3-up "Key Figures" pattern (signature)

Used for "Key Figures" slides, observed 30+ times across NBG executive reference decks. This is the **dominant** content pattern when the slide message is "here are the headline numbers for this unit."

**Slide composition** (3 cards, equal-width, centered):

```
Card 1: Rounded rect at (1.01, 2.15, 3.5, 3.0)   fill = #F5F8F6, no border, radius 0.04"
Card 2: Rounded rect at (4.92, 2.15, 3.5, 3.0)   fill = #F5F8F6, no border, radius 0.04"
Card 3: Rounded rect at (8.81, 2.15, 3.5, 3.0)   fill = #F5F8F6, no border, radius 0.04"
```

KPI cards are their `#F5F8F6` fill alone: no border, no shadow. The only bordered card on any
slide is the recommended option (gold, below); a highlighted card changes its fill to `#CBFAFF`.

**Inside each card** (offsets relative to card x):

| Element | Position (within card) | Font | Size | Color | Weight | Align |
|---|---|---|---|---|---|---|
| Big number | (card_x, 2.65, 3.5, 1.0) | Aptos | **50pt** | `#007B85` | **Bold** | Center |
| Caption | (card_x + 0.30, 3.85, 2.9, 0.8) | Aptos | **16pt** | `#5A5F5A` | Regular | Center |

**Page header** (above the cards):

| Element | Position | Font | Size | Color | Weight |
|---|---|---|---|---|---|
| Unit chip (rounded, names the unit) | (0.374, 0.45, ~1.4–2.3, 0.4), fill `#003841` | Aptos | 16pt | white | **Bold** |
| Section title (next to the chip) | (~1.92–2.82, 0.48, 5.0, 0.38) | Aptos | 22pt | `#003841` | Regular |
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

## Element Specs (Standard #20)

Standard #20 picks elements by what a slide must say. These are the element specs behind that
table, on the one chassis, in the house palette. Every value below is either a token (named) or
a measured Standard #22 pair.

### Process flow: a journey, or who owns which step

| Part | Spec |
|---|---|
| Step tile | Rounded square, tight corners (radius 0.04"), fill `#007B85`, white line icon (5.03:1) |
| Step label | Under each tile: 16pt Bold `#003841` title, optional 14pt `#202020` line |
| Arrow | Between tiles, a right-pointing arrow in `#939793` (the process-arrow grey) |
| Ownership | A 0.06" stripe on each tile's left edge in the owner's colour: `#003841` for one party, `#BEC1BE` for the other (7.04:1 apart, opposite ends of the lightness range) |
| Legend | A chip top-right naming each owner beside its stripe colour, 11pt `#202020` |

The owner is also named in the step label: colour is never the only signal (Standard #22). Never
code ownership with `#007B85` against `#939793`, which are 1.70:1 apart. The stripe is a
sanctioned edge stripe because it carries meaning tied to the legend; the two-party ownership
coding below has the only other one.

### Parallel comparison: here are the alternatives

- Every option gets the same card or slide: same geometry from the grid (2-up 6.142" or 3-up
  3.995" wide), same order of fields, same type sizes (card title 16pt Bold `#003841`, body 14pt
  `#202020`).
- Across slides the positions are identical, so the reader compares by flipping; only the labels
  and one accent change.
- The recommended option takes the gold treatment above; the others stay in the default card.

### Stat tile: here are the headline numbers

| Part | Spec |
|---|---|
| Tile | `#F5F8F6` fill, no border, no shadow, tight corners (a metric card) |
| Value | 50pt Bold `#007B85` (`type.kpi_value`); tiles under about 2" tall use the inline KPI callout (18pt) instead |
| Caption | The metric label under the value, per the Key Figures card above |
| Delta (optional) | Signed (`+0.5` / `-0.5`), 14pt Bold: positive `#007B85`, negative `#AA0028`, neutral `#202020` (`components.kpi.delta`); the corporate green `#73AF3C` is 2.65:1 on white and never carries text |

### Warning flag: these are the risks

| Part | Spec |
|---|---|
| Mark | A small `#FF7F1A` square (about 0.12") beside the flagged item |
| Label | ALL CAPS, 11pt Bold `#202020`, next to the square ("AT RISK", "REJECTED") |

The label text is dark, never orange: `#FF7F1A` is 2.53:1 on white. The square and the word
travel together, because to a colour-blind reader the square alone says nothing (Standard #22).

### Takeaway strip: the bottom line

| Part | Spec |
|---|---|
| Bar | Full content width (x 0.374", w 12.585"), fill `#E6F5F6` (`colors.takeaway_tint`), no border, ending at or above y 6.5" |
| Text | One line, 14pt Bold `#003841` (`components.takeaway_strip`, 11.42:1 on the tint) |

In a deck spec the strip is `content.takeaway` on any content slide type; the builder draws it.

### Two-party ownership coding: what we ask of the other division, what we lead

For a deck that separates what another division is asked to decide from what our division leads
itself. Each party has one theme, applied the same way on every page, so a reader tells in two
seconds whether an item is an ask or a commitment.

| Part | Asks (the other division) | Our division |
|---|---|---|
| Card and row fill | `ownership_ask_fill` (`#FAEBEC`) | `off_white` (`#F5F8F6`) |
| Left accent bar, 0.08" wide, the card's or row's full height | `ownership_ask` (`#C8323C`) | `bright_cyan` (`#00DFF8`) |
| Section header bar, full content width, 0.35" tall | `ownership_ask`, white 12pt Bold text (5.28:1) | `teal` (`#007B85`), white 12pt Bold text (5.03:1) |
| Badge naming the division | An `ownership_ask` box, 0.3" tall, the division's name in white 11pt Bold | A `teal` box, the same |
| Table rows | All `ownership_ask_fill`, never zebra-striped: every row is an ask | Alternating `off_white` and `white` |
| Card text | Title 16pt Bold `dark_teal` (11.06:1), body 14pt `body_text` (14.09:1) | Title 16pt Bold `dark_teal` (11.96:1), body 14pt `body_text` (15.24:1) |

**Footer band.** `ownership_band` (`#E6F4F5`) at full content width (x 0.374", w 12.585"), 0.45"
tall for one line, ending at 6.5" (at 6.15" when the slide carries a source line). It holds one
sentence in 14pt `dark_teal` (11.34:1) saying what our division leads in parallel. It closes an
asks page, and the detail stays on our division's own page. It takes the takeaway strip's place
on that page, never sits beside one: the two tints are 1.01:1 apart and would read as one bar.

- **One party per page.** An asks page and an our-work page, never mixed; the footer band is the
  only mention of our work on an asks page. A topic with both gets two pages, so the asks page
  can be shown on its own in a meeting with the other division.
- **Group the asks by product, not by decision type.** Every asks section header stays
  `ownership_ask`, whatever kind of decision it holds (policy, scoring, capital): they are all
  asks, and grouping by product maps each one to its owner on the other side.
- **The badge names the division**, never a generic "ASK". Its text is never under 10pt (the
  validator's floor) and is set at 11pt, Standard #11's badge-label minimum; size the box for it
  (0.3" tall, the text's width plus 0.2").
- **Colour is never the only signal** (Standard #22): the badge and the section header name the
  party. The bright-cyan bar is 1.52:1 against its off-white card, under the 3:1 a meaningful
  graphic needs, so it only decorates; the asks bar clears 4.57:1 against its fill.
- The accent bar is the second sanctioned edge stripe, after the process-flow ownership stripe:
  both carry a meaning that a label also states.

Built with the `custom` slide type: `shape` and `text` elements take these colour token names in
`fill` and `text_color`. A `table` element always stripes its rows (`white` and `zebra_tint`,
which is the `off_white` value), which is right for our division's tables. Draw an asks table as
rows instead: per row a `rect` in `ownership_ask_fill`, 0.36" tall with a 0.04" gap, its accent
bar, and its cells as 12pt `text` elements with `anchor: middle` (first column Bold), all under a
column-header row in `dark_teal` with white 12pt Bold text. Those rows are shapes, so the builder
does not ask for a source: give the slide `content.source` whenever they carry figures. An asks
page with one card, repeated per ask:

```yaml
- type: custom
  id: S12
  content:
    title: "Product A needs two decisions from the other division"
  elements:
    # section header bar
    - {kind: shape, shape: rect, x: 0.374, y: 1.3, w: 12.585, h: 0.35, fill: ownership_ask, text: "PRODUCT A: 2 ASKS", text_color: white, size: 12, bold: true, align: left}
    # one asks card: fill, accent bar, badge (the other division's name), title, body
    - {kind: shape, shape: rounded_rect, x: 0.374, y: 1.85, w: 6.142, h: 1.3, fill: ownership_ask_fill}
    - {kind: shape, shape: rect, x: 0.374, y: 1.85, w: 0.08, h: 1.3, fill: ownership_ask}
    - {kind: shape, shape: rounded_rect, x: 5.166, y: 1.97, w: 1.2, h: 0.3, fill: ownership_ask, text: "DIVISION", text_color: white, size: 11, bold: true}
    - {kind: text, role: card_title, x: 0.624, y: 1.97, w: 4.35, h: 0.32, text: "The first decision we ask for"}
    - {kind: text, role: card_body, x: 0.624, y: 2.37, w: 5.74, h: 0.66, text: "Why it matters, in two lines at most"}
    # footer band: what our division leads in parallel
    - {kind: shape, shape: rect, x: 0.374, y: 6.05, w: 12.585, h: 0.45, fill: ownership_band, text: "In parallel, our division leads the rest of the product plan.", text_color: dark_teal, size: 14, align: left}
```

## Clean Executive Cover: signature

The cover is clean and white with NO decorative shapes. No template ships with the plugin:
`nbg_build.py` builds every slide on a blank layout, so the cover carries only what is listed here.

Positions: [dimensions.md → Cover Slide](dimensions.md#cover-slide) and
[Large Logo](dimensions.md#large-logo---covers--dividers). Type and color:

| Element | Font | Size | Color | Weight |
|---|---|---|---|---|
| Title | Aptos | **48pt** | `#003841` | Regular |
| Subtitle (presenting units) | Aptos | **24pt** | `#007B85` | Regular |
| Location | Aptos | 14pt | `#003841` | Regular |
| Date | Aptos | 14pt | `#5A5F5A` | Regular |
| **NBG logo (large)** | n/a | n/a | n/a | always Greek logo (`assets/nbg-logo-gr.png`) |

**Subtitle convention**: the presenting unit(s), pipe-separated, no trailing period, e.g.
`Unit A | Unit B`. NOT a generic department-name string.

**Decoration policy**: white background, NO colored bars, NO decorative shapes. Decoration is purely typographic (size/weight/color contrast).

## Lean Divider: signature

A white divider on a blank layout (the master-layout dividers of older NBG templates carried
dark-teal fills that break the "white backgrounds only" rule):

Positions: [dimensions.md → Divider Slide](dimensions.md#divider-slide). Type and color:

| Element | Font | Size | Color | Weight |
|---|---|---|---|---|
| Section number (e.g. "01") | Aptos | **60pt** | `#007B85` | Regular |
| Section title (e.g. "Organization & People") | Aptos | **48pt** | `#003841` | Regular |
| **NBG logo (large, same as cover)** | n/a | n/a | n/a | Greek logo |

White background. No description text. No page number on dividers.

> NBG executive decks often dispense with section dividers entirely (most reference decks have ZERO dividers). Use sparingly.

## Progress & Priorities: 2-column split (NBG executive signature)

Used in Progress & Priorities slides. Same page header as Key Figures (unit chip + title + owner subtitle).

```
LEFT half (Delivered):                   RIGHT half (Priorities):
    "Delivered" header (16pt #003841)        "Priorities" header (16pt #003841)
    Row 1: ✓ stripe + #E8F5E9 fill           Row 1: oval bullet + body + status badge
    Row 2: ...                               Row 2: ...
    (5-7 rows max)                           (5-7 numbered priorities max)
```

LEFT column x range: 0.374 → 5.87 (width 5.5)
RIGHT column x range: 6.37 → 12.959 (width 6.589)

## Table Styling (NBG executive signature)

A table starts at the gutter (x 0.374") and may span the content width (12.585").

**This is the single table spec.** `typography.md` and `charts.md` point here.

- **Header row**: fill `#003841`, **12pt Aptos Bold WHITE**, height 0.4"
- **Body rows alternate (zebra)**: `#FFFFFF` and `#F5F8F6`, height 0.35"
- **Cell inset**: 0.08"
- **First column** (label): 12pt Aptos **Bold** `#202020`
- **Other body cells**: 12pt Aptos Regular `#202020`
- **Numeric value cells**: 12pt, right-aligned (text columns left-aligned); emphasis carried by weight rather than size
- **In-cell positive emphasis** ("+1"): `#007B85` Bold
- **Neutral dashes**: `#5A5F5A` (`#939793` is 2.96:1 on white, Standard #22)
- **Priority flags** ("H2"): `#202020` Bold in a small `#CC9900` badge (amber text on white is 2.58:1)
- **Notes column**: 11pt `#5A5F5A` Regular
- **Borders**: 1pt `#FFFFFF`, so the zebra rows carry the structure
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
