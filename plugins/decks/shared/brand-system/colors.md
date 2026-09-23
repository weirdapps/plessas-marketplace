# NBG Complete Color Palette

> Machine source: [`tokens.yaml`](tokens.yaml) (`colors`, `status`, `extended_palettes`,
> `retired_colors`, `charts.palette`, `keynote.dark`). This file explains the palette and quotes
> those values; `tools/test_brand_docs.py` fails when a table here drifts from them.

> **Note**: For digital product colors (apps, web), see [pillar-ds.md](pillar-ds.md) for the complete Pillar Design System palette (Tsopanakis, resynced 2026-05-24).
>
> **Scope of this file**: presentation-system colors only (PowerPoint/PDF decks). Body text stays `#202020` (between Pillar Black `#162020` and email body `#404040`, an intentional difference optimised for projection readability). Status reds: `#AA0028` is retained for **NBG corporate charts and segment coding** (Private banking signature); `#BE4B4B` from Pillar applies to **digital products** (alerts, error states in app UI).

## Theme Colors (the theme every built deck carries)

`nbg_build.py` writes this colour scheme, named `NBG`, into every deck it builds, with Aptos as
the heading and body font and no effect styles. Anything that inherits from the theme, such as a
text box or chart a colleague adds later in PowerPoint, starts on-brand. `tools/test_brand_docs.py`
builds a deck and compares every slot with this table.

| Slot | Hex | Token |
|------|-----|-------|
| Dark 1 | `#202020` | `body_text` |
| Light 1 | `#FFFFFF` | `white` |
| Dark 2 | `#003841` | `dark_teal` |
| Light 2 | `#F5F8F6` | `off_white` |
| Accent 1 | `#00ADBF` | `charts.palette`, series 1 |
| Accent 2 | `#003841` | `charts.palette`, series 2 |
| Accent 3 | `#007B85` | `charts.palette`, series 3 |
| Accent 4 | `#939793` | `charts.palette`, series 4 |
| Accent 5 | `#BEC1BE` | `charts.palette`, series 5 |
| Accent 6 | `#00DFF8` | `charts.palette`, series 6 |
| Hyperlink | `#0D90FF` | `extended_palettes.links.hyperlink` |
| Followed hyperlink | `#59C3FF` | `extended_palettes.links.followed` |

The corporate PowerPoint template carries a different theme, "NBG Colors 2": Dark 1 black
`#000000`, Dark 2 `#007B85`, and the accents in the order `#003841`, `#007B85`, `#00ADBF`,
`#00DFF8`, `#BEC1BE`, `#939793`. Decks are never built on that template (README, Critical Rules),
so those values only matter when you read a deck that was.

## Primary Brand Colors

### Most Frequently Used

| Hex | Name | Usage | Frequency |
|-----|------|-------|-----------|
| `#00DFF8` | Bright Cyan | Feature accent: a mark or highlight, never a background, never text on white | Very High (365+) |
| `#007B85` | NBG Teal | Brand color | Very High (814+) |
| `#047A85` | Teal Variant | Legacy: allowed in existing decks, never picked for new work | High (188+) |
| `#003841` | Dark Teal | Titles, headings | High (89+) |
| `#202020` | Dark Text | Body text, and dark text on any light fill | Medium |

### Extended Palette

| Hex | Name | Usage |
|-----|------|-------|
| `#00DEF8` | Bright Cyan Alt | Logo element (GR theme) |
| `#E6F5F6` | Pale Teal Tint | Callout / takeaway strip fill |
| `#CBFAFF` | Highlight Tint | Stronger cyan highlight card |
| `#FBF3E4` | Cream Tint | Recommended-option card fill (paired with gold border) |

### Retired Colors

Seen in older decks; a new deck must not contain them (`tokens.yaml` `retired_colors`, which the
validator enforces).

| Hex | Why retired | Use instead |
|-----|-------------|-------------|
| `#595959` | Old caption grey | `#5A5F5A` |
| `#666666` | Drifted grey | `#5A5F5A` |
| `#EAF4F5` | One-off tint | `#E6F5F6` |
| `#F5F9F6` | Near-duplicate of off-white | `#F5F8F6` |
| `#252D30` | Dark background | slides are always white |
| `#0A091B` | Dark background | slides are always white |
| `#4F81BD` `#C0504D` `#9BBB59` `#8064A2` `#4BACC6` `#F79646` `#1F497D` `#EEECE1` | The Office 2007 theme a deck inherits when nothing overrides it | the NBG palette |

## Secondary Colors (Charts & Diagrams)

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Black | `#212121` | 33, 33, 33 | Alternative text |
| Aqua Light | `#3EDEF8` | 62, 222, 248 | Light accent |
| Light Grey | `#BEC1BE` | 190, 193, 190 | Subtle elements |
| **Caption Grey** | **`#5A5F5A`** | 90, 95, 90 | **Captions, owner subtitles, TOC teasers, table notes (canonical secondary grey, the NBG executive signature)** |
| Pale Grey | `#F5F8F6` | 245, 248, 246 | Light backgrounds, KPI card fill |

### Grey hierarchy (avoid drift: one grey per role)

Three greys, three jobs. Do NOT introduce others (`#666666`, `#595959`, `#5B5B69`; all seen drifting across reference decks):

| Grey | Role |
|------|------|
| `#5A5F5A` | Captions, subtitles, owner lines, TOC teasers, table notes, sources, footnotes, the cover date, KPI captions; the secondary-text grey |
| `#939793` | Page numbers, process-flow arrows, muted axis labels, subtle UI marks, "partner/them" ownership coding (always with a label: against `#007B85` it is only 1.70:1) |
| `#BEC1BE` | Dividers, hairlines, axis lines |

Body text is `#202020` (never a grey).

## Status/Semantic Colors

Three status palettes, three scopes. Pick the one that matches the surface and do not mix
two of them on one slide.

| Palette | Scope |
|---------|-------|
| Official NBG Corporate | Binary positive/negative in charts and official brand graphics |
| Practical Status | Status pills and badges in DIY KPI / Progress decks |
| Graded Severity Ramp | Six-step severity scales in tables and heat-coded charts, where a two-color pair cannot carry the distinction |

### Official NBG Corporate Palette (charts, brand graphics)

| Status | Hex | RGB | Usage |
|--------|-----|-----|-------|
| Success | `#73AF3C` | 115, 175, 60 | Positive indicators (charts, official brand graphics) |
| Alert | `#AA0028` | 170, 0, 40 | Negative indicators (charts, official brand graphics) |
| Gold | `#D9A757` | 217, 167, 87 | Premium accent |
| Blue | `#1E478E` | 30, 71, 142 | Information |

### Practical Status Colors (DIY decks, status pills, "Delivered/Priorities" patterns)

These are the colors observed across reference NBG executive decks, used in status badges, "Delivered" rows, priority pills. Cleaner reading at small sizes than the chart-grade NBG palette above.

| Status | Hex | Light variant | Usage |
|--------|-----|---------------|-------|
| **OK / Delivered** | `#008000` | `#E8F5E9` | Status pill (text white on #008000), "Delivered" row accent stripe + pale fill |
| **TBD / In progress** | `#CC9900` | `#FFFFCC` | Amber priority pill (text `#202020` on #CC9900: white is 2.58:1 and fails Standard #22) |
| **Warning / Risk** | `#CC0000` | n/a | Severe priority indicator (text white) |

**When to use which palette**: see the scope table at the top of this section.

### Recommended-option highlight (comparison slides): gold, one convention

When one option among several is THE recommendation, mark it in **gold `#D9A757`** (Premium accent): a 1.5pt gold border, optional `#FBF3E4` cream fill, and a small gold "RECOMMENDED" tab/pill with `#202020` ALL-CAPS text (white on gold is 2.18:1 and fails Standard #22).

**Use gold, not green.** Green (`#008000` / `#73AF3C`) is already the Delivered / OK / Success color, so a green "recommended" badge collides with status coding on any slide that carries both. Gold is otherwise reserved for premium/selected and stays unambiguous. Pick ONE convention per deck and keep it; do not mix a green "recommended" pill with the gold treatment. Component geometry: see `layouts.md → Recommended-Option Highlight`.

## Graded Severity Ramp (tables and heat-coded charts)

A six-step ramp for severity or heat scales. Not a substitute for the corporate palette:
a plain positive/negative pair in a chart stays `#73AF3C` / `#AA0028`.

| Status | Hex | RGB | Usage |
|--------|-----|-----|-------|
| Deep Red | `#CB0030` | 203, 0, 48 | Critical/negative |
| Red | `#F60037` | 246, 0, 55 | Alert/warning |
| Orange | `#FF7F1A` | 255, 127, 26 | Caution; also the warning-flag square (`layouts.md`) |
| Yellow | `#FFDC00` | 255, 220, 0 | Attention |
| Green | `#5D8D2F` | 93, 141, 47 | Success |
| Bright Green | `#90DC48` | 144, 220, 72 | Strong positive |

## Segment/Division Colors

| Segment | Hex | RGB | Usage |
|---------|-----|-----|-------|
| Business | `#0D90FF` | 13, 144, 255 | Business banking |
| Corporate | `#73AF3C` | 115, 175, 60 | Corporate segment |
| Premium | `#D9A757` | 217, 167, 87 | Premium/private banking |
| Private | `#AA0028` | 170, 0, 40 | Private banking |

## Link Colors

| Type | Hex |
|------|-----|
| Hyperlink | `#0D90FF` |
| Followed Link | `#59C3FF` |

## Chart Color Sequence

Use these colors in order for chart data series, at most six (Standard #22):

1. `#00ADBF` - Cyan (primary)
2. `#003841` - Dark Teal
3. `#007B85` - NBG Teal
4. `#939793` - Medium Gray
5. `#BEC1BE` - Light Gray
6. `#00DFF8` - Bright Cyan

Series 3 and 4 are 1.70:1 apart: never let those two alone carry a distinction; label the series
directly (Standard #22).

## PFM Category Colors

> **Moved to `pillar-ds.md`** (resynced 2026-05-24 from Tsopanakis live repo).
>
> For category-based data visualisation (spending categories, PFM segments, budget breakdowns), use the **16-category palette** in [pillar-ds.md → PFM Category Colors](pillar-ds.md#pfm-category-colors-charts). The older 10-category set that previously lived here has been retired: it was outdated and did not match the live Pillar Figma source.
>
> Quick access for chart series (Main shades). The categorical ceiling in Standard #22
> applies: this is a lookup table for category colours, not licence to plot 16 series.
>
> ```javascript
> // Pillar PFM Category chart colors, Main shades
> const PFM_CHART_COLORS = [
>   'B99C34', '44C7B3', '905567', '8D7349', '19B4E2', 'AC1D44',
>   'A1AC20', '4B7398', '9D4F16', '547723', '2C76BD', 'D08239',
>   '658A8D', '525CBE', '26A567', '8681B1'
> ];
> ```

## Background Guidelines

### IMPORTANT: White Backgrounds Only

**Standard #2: ALWAYS use white backgrounds. Never use dark themes.** Keynote mode (Standard #21) is the one exception.

### Light Theme (REQUIRED)

| Element | Color |
|---------|-------|
| Slide background | `#FFFFFF` (white) - **ALWAYS** |
| Title text | `#003841` |
| Body text | `#202020` |
| Accents | `#007B85`; `#00DFF8` only as a mark, never as text |
| **Metric cards** | `#F5F8F6` (light gray background) |
| **Info cards** | `#F5F8F6` (light gray background) |

### Card Backgrounds

| Card Type | Background | Border |
|-----------|------------|--------|
| Metric card (KPI tile) | `#F5F8F6` | None |
| Info card | `#F5F8F6` | None |
| Highlight card | `#CBFAFF` | None |
| Callout / takeaway strip | `#E6F5F6` | None |
| Recommended-option card | `#FBF3E4` | 1.5pt `#D9A757` (gold) |

Only the recommended option carries a border. Every other card, KPI tiles included, is its fill
alone: no border, no shadow.

**Tint hierarchy**: `#F5F8F6` = default card; `#E6F5F6` = soft pale-teal takeaway/callout strip (the bottom "bottom line" bar); `#CBFAFF` = stronger cyan highlight card; `#FBF3E4` + gold border = the recommended option (see Recommended-option highlight above). Pick `#E6F5F6` for takeaway strips consistently; do not drift to `#EAF4F5` or other one-off tints.

### Dark Theme (DO NOT USE)

Dark backgrounds are not used (Standard #2). All slides are white.

## Color Values for Code

The builder, the validator and the keynote compositor read every value on this page from
`tokens.yaml`; there is no second constants table to keep in step. Anything that needs the
palette in code loads it through `tools/nbg_tokens.py` (`color("teal")`, `chart_palette()`,
`allowed_colors()`, `retired_colors()`).

## Color Usage Quick Reference

| Purpose | Recommended Color |
|---------|------------------|
| Slide background | `#FFFFFF` (White) - **ALWAYS** |
| Slide title | `#003841` (Dark Teal) |
| Body text | `#202020` (Dark Text) |
| Section numbers (divider) | `#007B85` (NBG Teal) |
| Bullet points | `#00ADBF` (Cyan) |
| Primary accent | `#007B85` (NBG Teal) |
| Bright accent | `#00DFF8` (Bright Cyan), a mark only |
| Subtle elements | `#939793` (Medium Gray) |
| **KPI card background** | `#F5F8F6` (Off-white) |
| **KPI big number** | `#007B85` (NBG Teal), **50pt Aptos BOLD** |
| **KPI caption** | `#5A5F5A` (Caption Grey), 16pt under the big number |
| **Owner subtitle** | `#5A5F5A` (Caption Gray), the NBG executive signature |
| **Unit chip (Key Figures header)** | fill `#003841` (Dark Teal), text white |
| TOC description | `#5A5F5A` (Caption Gray) |
| Page number | `#939793` (Medium Gray) |
| Icons | As drawn: duotone `#087681` + `#13A4AD`, no tint (`icons.md`); a process step's icon is white on its teal tile |
| **Status: OK** | `#008000` fill, white text, DIY status pills |
| **Status: TBD** | `#CC9900` fill, `#202020` text, DIY status pills |
| **Status: Warn** | `#CC0000` fill, white text, DIY status pills |
| **Delivered row stripe + pale fill** | accent `#008000` + body `#E8F5E9` |

---

## Color Contrast Rules (Standard #22)

**Measure, never estimate.** Text needs **4.5:1** against whatever it sits on, or **3:1** only at
18pt+ regular or 14pt+ bold (WCAG 2.1 AA, Standard #22). Compute it with WCAG relative luminance:
`tools/nbg_color.py` has `contrast_ratio()` and `min_ratio()`. Rules of thumb based on R+G+B,
HSL lightness or YIQ put white text on the primary chart cyan, the status amber and the corporate
green; do not use them.

**On a light fill, dark text is `#202020`**, the body-text colour. Do not introduce a third dark.
On a white slide, titles stay `#003841` (12.79:1) and body text `#202020` (16.29:1).

Every palette fill, measured (`tools/test_brand_docs.py` recomputes each ratio):

| Fill | White text | `#202020` text | Use |
|------|-----------:|---------------:|-----|
| `#003841` Dark Teal | 12.79 | 1.27 | white |
| `#007B85` NBG Teal | 5.03 | 3.24 | white |
| `#00ADBF` Cyan | 2.72 | 6.00 | `#202020` |
| `#00DFF8` Bright Cyan | 1.63 | 10.02 | `#202020` |
| `#F5F8F6` Off-white | 1.07 | 15.24 | `#202020` |
| `#E6F5F6` Pale Teal Tint | 1.12 | 14.55 | `#202020` |
| `#CBFAFF` Highlight Tint | 1.13 | 14.48 | `#202020` |
| `#FBF3E4` Cream Tint | 1.10 | 14.77 | `#202020` |
| `#BEC1BE` Light Grey | 1.82 | 8.97 | `#202020` |
| `#939793` Medium Gray | 2.96 | 5.50 | `#202020` |
| `#5A5F5A` Caption Grey | 6.52 | 2.50 | white |
| `#73AF3C` Success | 2.65 | 6.15 | `#202020` |
| `#AA0028` Alert | 7.66 | 2.13 | white |
| `#D9A757` Gold | 2.18 | 7.46 | `#202020` |
| `#1E478E` Blue | 8.95 | 1.82 | white |
| `#008000` OK | 5.14 | 3.17 | white |
| `#E8F5E9` OK tint | 1.12 | 14.48 | `#202020` |
| `#CC9900` TBD | 2.58 | 6.30 | `#202020` |
| `#FFFFCC` TBD tint | 1.03 | 15.85 | `#202020` |
| `#CC0000` Warning / Risk | 5.89 | 2.77 | white |
| `#CB0030` Deep Red | 5.86 | 2.78 | white |
| `#F60037` Red | 4.22 | 3.86 | white, large text only |
| `#FF7F1A` Orange | 2.53 | 6.44 | `#202020` |
| `#FFDC00` Yellow | 1.36 | 12.02 | `#202020` |
| `#5D8D2F` Green | 3.95 | 4.12 | white, large text only |
| `#90DC48` Bright Green | 1.68 | 9.71 | `#202020` |
| `#0D90FF` Business | 3.26 | 5.00 | `#202020` |
| `#C8323C` Ownership: ask | 5.28 | 3.09 | white |
| `#FAEBEC` Ownership: ask fill | 1.16 | 14.09 | `#202020` |
| `#E6F4F5` Ownership: band | 1.13 | 14.45 | `#202020` |

"Large text only" means no colour clears 4.5:1 on that fill: put only 18pt+ regular or 14pt+ bold
text on it, or put the text beside the swatch instead.

The builder's automatic chart-label picker is a separate case: it chooses pure black or pure white
by luminance (threshold 0.179), which clears AA on any fill. That is a property of the picker, not
a brand colour; hand-specified dark text stays `#202020` (Standard #22).

### Cover Slide Contrast: CRITICAL

Cover layouts may have overlapping graphic elements. Rules:

1. All cover text must have sufficient contrast against BOTH the background AND any decorative graphics
2. Use **Dark Teal `#003841`** for the main title: readable on light backgrounds
3. Use **NBG Teal `#007B85`** for the subtitle (5.03:1 on white)
4. **Never use white or light colors** for cover text on white backgrounds
5. **Always set explicit colors**: never rely on theme/inherited colors for covers

### Icon Contrast

The icon PNGs in `assets/icons/` and the duotone SVGs share one style: two teals, `#087681` and
`#13A4AD`, drawn for white and light fills. Place them as they are; never recolour one to a single
tint. The builder makes one change itself: a process step redraws its icon white on its teal tile.
A new icon for a dark fill swaps both teals for off-white `#F5F8F6` (`icons.md`).

---

## Dark-Mode Tokens: Keynote Mode ONLY

These apply **only** to the dark full-bleed keynote format (Standard #21, spec in
[keynote.md](keynote.md)). They are not available to normal decks, documents, emails or charts.
Every token maps to a light-mode colour above; do not introduce new ones. Machine source:
`tokens.yaml` → `keynote.dark`.

| Token | Hex | Maps from | Usage |
|-------|-----|-----------|-------|
| `ink` | `#FFFFFF` | `#003841` | Primary text, hero numbers |
| `ink-2` | `#DFE6E6` | `#202020` | Body and support text |
| `ink-3` | `#96A6A8` | `#5A5F5A` | Source notes, metadata |
| `accent` | `#00DFF8` | `#007B85` | Kicker, emphasis line, highlighted stat or bar |
| `accent-bar` | `#00BED2` | `#00ADBF` | Default bar fill |
| `accent-mute` | `#008292` | `#BEC1BE` | Non-highlighted bars |
| `ground-top` | `#00161B` | `#FFFFFF` | Gradient top, scrim base |
| `ground-bot` | `#003841` | `#F5F8F6` | Gradient bottom (the brand Dark Teal) |
| `negative` | `#FF5263` | `#AA0028` | Negative statistic; `AA0028` is unreadable on dark |
| `rule` | `#788C8E` | `#BEC1BE` | Chart baseline |

**Bright Cyan `#00DFF8` is still banned as a background.** In keynote mode it is only ever text or a
mark sitting on dark ground, which is the one place it works.

Contrast in keynote mode is **measured, not assumed**: the compositor samples the 90th-percentile
luminance under each text box and deepens a feathered scrim until WCAG clears (4.5:1 under 48px,
3:1 at or above). Over photography no fixed colour rule can stand in for that measurement.
