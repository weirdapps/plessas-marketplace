# NBG Typography

> Machine source: [`tokens.yaml`](tokens.yaml) (`fonts`, `type`, `line_spacing`,
> `components.bullets`). This file explains the type scale and quotes those values;
> `tools/test_brand_docs.py` fails when a row here drifts from them.

## Font Family

### Primary Font (Presentations)

- **Name**: Aptos
- **Weight**: **Regular** (preferred for all elements including titles); Bold for emphasis only
- **Display**: Aptos Display is allowed at display sizes; Aptos Regular is the default
- **Never**: Aptos SemiBold
- **Fallback**: Calibri, Tahoma

### Digital Products Font (Pillar DS)

- **Name**: Aeonik Pro
- **Weights**: Regular (400), Medium (500), Bold (700)
- **Fallback**: Aptos, Arial
- **Usage**: NBG digital products, apps, web interfaces

### Bullet Font

- **Name**: Arial
- **Purpose**: Bullet characters only

## Text Styles

### Cover Slide

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Title | Aptos | 48pt | #003841 | Regular |
| Subtitle | Aptos | **24pt** | #007B85 | Regular |
| Location | Aptos | 14pt | #003841 | Regular |
| Date | Aptos | 14pt | #939793 | Regular |

**Subtitle content**: the presenting unit(s), pipe-separated, no trailing period, for example
`Unit A | Unit B | Unit C`. Name the units that present the deck rather than a generic department
string. A user's own unit list lives in their style preferences
(`${CLAUDE_PLUGIN_DATA}/style-preferences.md`), never in this file.

### Divider Slide

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Section Number | Aptos | 60pt | #007B85 | Regular |
| Section Title | Aptos | **48pt** | #003841 | Regular |

### Contents/TOC Slide

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| "Contents" Header | Aptos | **24pt** | #003841 | Regular |
| Section Number | Aptos | **18pt** | #007B85 | Regular |
| Section Title | Aptos | **16pt** | #003841 | Regular |
| Section Description | Aptos | **12pt** | #5A5F5A | Regular |

Contents rows are Regular throughout (Standard #18); the number carries the emphasis by colour.

### Content Slide

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| **Action Title** | Aptos | **24pt** | #003841 | Regular |
| Body Text | Aptos | **16pt** | #202020 | Regular |
| Body Text (dense slides) | Aptos | 14pt | #202020 | Regular |
| Bullet L1 | Aptos | 16pt | #202020 | Regular |
| Bullet L2 | Aptos | 16pt | #202020 | Regular |
| Bullet L3 | Aptos | 16pt | #202020 | Regular |
| Caption (under a title) | Aptos | 12pt | #5A5F5A | Regular |
| Footnotes and sources | Aptos | 11pt | #5A5F5A | Regular |

Body text is 16pt, 14pt at the least (dense slides). Every bullet level uses the body size:
separate the levels by indent and bullet character, not by shrinking the type. Footnotes and
sources are caption grey, never `#939793` (2.96:1 on white, Standard #22). Sizes in this file are
the specified values; the per-element floors they must clear live in
`presentation-style-guide.md` Standard #11.

### Metric Cards (KPIs): NBG executive signature pattern

Used for "Key Figures" slides: 3-up cards (3.5" × 3.0", `#F5F8F6` fill, 1pt `#BEC1BE` border, tight corners). Observed 30+ times across reference decks.

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| KPI big number | Aptos | **50pt** | **#007B85** (NBG Teal) | **Bold** |
| KPI caption | Aptos | **14pt** | **#202020** (Dark Text) | Regular |

Examples of KPI big-number text (typical NBG executive deck): `750K`, `26%`, `€70M+`, `4.5M`, `3.3M`, `500K`.

Caption is the metric label. Keep it short, lowercase or sentence case, no period: `Live Credit Cards`, `MS in Cards Turnover`, `Fee Income`.

**Note**: earlier brand-system drafts used `#003841` for the KPI value; the actual NBG executive pattern is `#007B85` (NBG Teal). Bold + Teal makes the big number pop without competing with the dark-teal title above.

### Page Header Components (NBG executive signature)

Used on Key Figures / Progress & Priorities slides.

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Unit chip (rounded chip naming the unit) | Aptos | **16pt** | `#FFFFFF` on `#003841` fill | **Bold** |
| Section title (next to the unit chip) | Aptos | **22pt** | `#003841` | Regular |
| Owner subtitle ("Head: A. Smith") | Aptos | **14pt** | `#5A5F5A` | Regular |

The unit chip is not the section pill: the pill is the 9pt teal eyebrow above an action title
(README Quick Reference), the chip a 16pt dark-teal label in the Key Figures header.

### Status Pills (NBG executive signature)

Used on Progress & Priorities slides.

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Numbered bullet (oval) | Aptos | **10pt** | `#FFFFFF` on `#007B85` fill | **Bold** |
| Status badge ("OK"/"TBD"/"H2") | Aptos | **11pt** | `#FFFFFF` on `#008000` / `#CC0000`, `#202020` on `#CC9900` | **Bold** |
| Bullet body text | Aptos | **14pt** | `#202020` | Regular |
| "Delivered ✓" row text | Arial | **15pt** | `#008000` on `#E8F5E9` | **Bold** |

### Charts & Tables

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Chart Title | Aptos | **12pt** | #202020 | Bold |
| Chart Axis Labels | Aptos | 12pt | #202020 | Regular |
| Chart Legend | Aptos | 12pt | #202020 | Regular |
| Chart Data Labels | Aptos | 12pt | #003841 | Bold |
| Table Header (NBG executive pattern) | Aptos | **12pt** | `#FFFFFF` on `#003841` fill | **Bold** |
| Table First Column (label) | Aptos | **12pt** | `#202020` | **Bold** |
| Table Body Cell | Aptos | **12pt** | `#202020` | Regular |
| Table Numeric Cell | Aptos | **12pt** | `#202020` | Regular |
| Table Notes (footnote) | Aptos | **11pt** | `#5A5F5A` | Regular |
| In-cell positive emphasis ("+1") | Aptos | 12pt | `#007B85` | Bold |
| In-cell priority flag ("H2") | Aptos | 12pt | `#202020` in a `#CC9900` badge | Bold |

Data labels inside a filled bar take the contrast-picked colour instead (charts.md). Amber text on
white is 2.58:1, so a priority flag is dark text on an amber badge, never amber text.

**Executive table styling rules**: fills, borders and in-cell emphasis are specified once in
[layouts.md](layouts.md#table-styling-nbg-executive-signature). This file carries only the type sizes.

### Page Number

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Page Number | Aptos | **10pt** | #939793 | Regular |

## Line Spacing

| Element | Line Spacing |
|---------|--------------|
| Titles | 0.9 |
| Body Text | 1.1 |
| Bullets | 1.1 |

## Paragraph Spacing

| Element | Space Before |
|---------|--------------|
| Body Text | 9pt |
| Table Cells | 9pt |
| Bullets | 14pt (L1, every bullet after the first), 5pt (L2, L3) |

## Text Box Settings

**CRITICAL**: All text boxes use zero internal margin, top vertical anchor and left alignment
unless a layout says otherwise. The divider number and title are the one pair aligned to a shared
baseline instead (Standard #3).

## Bullet Points

```yaml
bullet:
  character: "•"
  unicode: "2022"
  font: "Arial"
  color: "#00ADBF"   # Cyan (see colors.md)
  indent: 0.25"      # hanging: the text starts 0.25" in, wrapped lines align with it
```

## Number Formatting

| Type | Format | Example |
|------|--------|---------|
| Section Numbers | Two-digit | "01", "02", "03" |
| Percentages | With symbol | "47%" |
| Currency | With symbol | "€4.2B" |
| Large Numbers | With unit | "2.3M" |

---

## Pillar DS Typography (Digital Products)

Reference for digital product consistency. See [pillar-ds.md](pillar-ds.md) for full details.

### Font: Aeonik Pro

| Weight | Value | Usage |
|--------|-------|-------|
| Regular | 400 | Body text |
| Medium | 500 | Emphasis, labels |
| Bold | 700 | Headings, titles |

### Mobile Typography

| Element | Size | Line Height | Weight |
|---------|------|-------------|--------|
| Body | 12pt | 16px | Regular |
| Label | 10pt | 14px | Medium |
| Heading | 16pt | 20px | Bold |

### Desktop Typography

| Element | Size | Line Height | Weight |
|---------|------|-------------|--------|
| Body | 14pt | 18px | Regular |
| Label | 12pt | 16px | Medium |
| Heading | 18pt | 22px | Bold |
