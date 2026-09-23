# NBG Slide Dimensions & Positioning

> Machine source: [`tokens.yaml`](tokens.yaml) (`geometry`, `components`). This file explains the
> geometry and quotes those values; `tools/test_brand_docs.py` fails when a key row here drifts
> from them.

## Slide Dimensions

```yaml
slide:
  width: 13.333"      # 16:9 widescreen
  height: 7.5"
  emu_width: 12192000
  emu_height: 6858000
  aspect_ratio: "16:9"
```

## Margins & Safe Zones

```yaml
margins:
  left: 0.374"        # the Standard #15 gutter
  right: 0.374"       # mirror of the gutter; right boundary at 12.959"
  top_title: 0.5"
  body_top: 1.3"      # Standard #11: the first body element, with or without a pill
  bottom: 0.5"
```

`body_top` is where the first body element **starts**, on every content slide. The 1.1" in
Content Safe Zones below is the **floor** nothing but the title and pill may cross. Two
quantities, not two answers.

The left gutter for titles and every left-aligned text block is **0.374"**, per
`presentation-style-guide.md` Standard #15: the same vertical line the NBG logo sits on.
The right boundary mirrors it at **12.959"** (`13.333 - 0.374`), so the content width is
**12.585"** (`13.333 - 2 × 0.374`), written 12.59" where prose rounds it.

**Boundaries versus placement coordinates.** A boundary (the right edge, the safe-zone
limits) has one home, here, and Standard #15 and the agents must reference it rather than
restate it. A placement coordinate that a renderer copies literally (the gutter, the divider
title x) is restated wherever a geometry block is specified, each time with its derivation
inline, because a spec block has to be complete to be usable.

## Text Box Rules

**CRITICAL**: All text boxes must follow these rules:

| Property | Value | Reason |
|----------|-------|--------|
| `margin` | `0` | No internal padding |
| `valign` | `'top'` | Never middle or bottom (the divider pair is aligned to a shared baseline instead) |
| Height | Fit content | No oversized boxes |

### Title Box Sizing

- Single-line title: `h: 0.4"`
- Two-line title: `h: 0.7"`
- Never use large heights that leave empty space

## Logo Placement (from Template)

### Small Logo - Content Slides

Use for all content slides, charts, tables, infographics.

```yaml
logo_small:
  path: assets/nbg-logo-gr.png
  x: 0.374
  y: 7.071
  w: 0.822
  h: 0.236
# Distance from bottom edge: 7.5 - (7.071 + 0.236) = 0.19"
```

### Large Logo - Covers & Dividers

Use for cover slides and section dividers only.

```yaml
logo_large:
  path: assets/nbg-logo-gr.png
  x: 0.374
  y: 6.271
  w: 2.191
  h: 0.630
```

The wordmark PNG is 1200 × 348 (aspect 3.448): set the width and derive the height, never both
(Standard #4).

### Back Cover Logo - Centered

Plain back cover with centered oval NBG building logo (NO "Thank You" text).

```yaml
logo_back:
  path: assets/nbg-back-cover-logo.png
  x: 5.44    # centred: (13.333 - 2.45) / 2
  y: 2.98    # centred: (7.5 - 1.54) / 2
  w: 2.45
  h: 1.54
```

## Page Number Placement

Page numbers appear on **content slides only** - NOT on cover, dividers, or back cover.

```yaml
page_number:
  x: 12.71
  y: 7.1554
  w: 0.33
  h: 0.152
  font: Aptos 10pt, color 939793 (Medium Gray), right-aligned, middle anchor, margin 0
# Derived from the coordinates above. Do not restate these anywhere else:
#   from right edge:  13.333 - (12.71 + 0.33)  = 0.29"
#   from bottom edge: 7.5    - (7.1554 + 0.152) = 0.19"  (level with the small logo)
```

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

## Content Areas

Every grid is derived from three tokens: the gutter (0.374"), the content width (12.585") and the
grid gap (0.3"). Columns therefore span the full width to the 12.959" right boundary, as
Standard #2.7 ("fill the slide") requires.

### Full Width Content

```yaml
full_width:
  x: 0.374"
  y: 1.3"
  w: 12.585"
  h: 4.5"
```

### Two Column (50/50)

```yaml
two_column_even:      # w = (12.585 - 0.3) / 2
  left:
    x: 0.374"
    y: 1.3"
    w: 6.142"
    h: 4.5"
  right:
    x: 6.817"         # 12.959 - 6.142
    y: 1.3"
    w: 6.142"
    h: 4.5"
```

### Two Column (40/60 - Text/Chart)

```yaml
two_column_text_chart:   # 40% / 60% of (12.585 - 0.3)
  text:
    x: 0.374"
    y: 1.3"
    w: 4.914"
    h: 4.5"
  chart:
    x: 5.588"            # 0.374 + 4.914 + 0.3
    y: 1.3"
    w: 7.371"            # ends at 12.959
    h: 4.6"
```

### Three Column

```yaml
three_column:            # w = (12.585 - 2 × 0.3) / 3
  col1:
    x: 0.374"
    y: 1.3"
    w: 3.995"
  col2:
    x: 4.669"            # 0.374 + 3.995 + 0.3
    y: 1.3"
    w: 3.995"
  col3:
    x: 8.964"            # 12.959 - 3.995
    y: 1.3"
    w: 3.995"
```

## Slide Element Positions

### Cover Slide

```yaml
cover:
  title:
    x: 0.374"
    y: 1.39"
    w: 12.0"      # Standard #13: one line, up to 12.0" wide
    h: 1.0"
  subtitle:
    x: 0.374"
    y: 2.49"      # title bottom + 0.1"; below the measured title if it grows
    w: 12.0"
    h: 0.8"
  location:
    x: 0.374"
    y: 4.58"
    w: 8.0"
    h: 0.4"
  date:
    x: 0.374"
    y: 4.97"
    w: 8.0"
    h: 0.4"
```

### Divider Slide

```yaml
divider:
  number:
    x: 0.374"
    y: 2.84"
    w: 1.2"
    h: 1.0"
  title:
    x: 1.574"    # 0.374 gutter + 1.2 number-box width, immediately right of the number
    y: 2.84"
    w: 9.5"
    h: 1.0"
```

**Number and title share one baseline** (Standard #3). A 60pt number and a 48pt title in two
top-anchored boxes at the same y do not: the larger type's baseline sits lower. Anchor both boxes
to the bottom with equal bottoms (3.84"), or move the title box down by the ascent difference.

### Content Slide

```yaml
content:
  section_pill:  # Optional. Rounded rect, fill 007B85, 9pt Bold white ALL CAPS
    x: 0.374"    # Standard #15 gutter
    y: 0.35"
    w: text width + 2 × 0.1" inset, minimum 1.0"   # sized to its text, one line, no wrap
    h: 0.3"
    radius: 0.15 # Standard #12
    shadow: none  # NO shadow on any element
  title:
    x: 0.374"    # Standard #15 gutter, never 0.37 and never 0.5
    y: 0.75"     # 0.5" if no pill
    w: 12.585"
    h: 0.4"      # the box ends at 1.15" with a pill (0.9" without); the text stays above 1.1"
    valign: top
    margin: 0
  body:
    x: 0.374"
    y: 1.3"      # Standard #11, with or without a pill
    w: 12.585"
    h: 5.0"
    valign: top
    margin: 0
```

This block is the single home for content-slide geometry. `layouts.md` and
`generation-methods.md` point here rather than repeating it.

## Content Safe Zones (Non-Negotiable)

Elements must stay within their designated vertical zones to prevent overlap with titles, logos, and page numbers.

```
 0.00" ┌──────────────────────────────────────┐
       │  PILL / TITLE ZONE                   │
       │  (0.0" – 1.1")                       │
 1.10" ├──────────────────────────────────────┤
       │  (breathing room: body starts 1.3")  │
       │  CONTENT SAFE AREA                   │
       │  (1.1" – 6.85")                      │
       │                                      │
       │  Footnotes and sources end at 6.5"   │
       │                                      │
 6.85" ├──────────────────────────────────────┤
       │  FOOTER EXCLUSION ZONE               │
       │  Logo (y=7.071") / PageNum (y=7.155")│
 7.50" └──────────────────────────────────────┘
```

### Zone Boundaries

| Zone | Y Start | Y End | Contains |
|------|---------|-------|----------|
| Title zone | 0.0" | 1.1" | Section pill, slide title |
| Content safe area | 1.1" | 6.85" | Body text, charts, tables, images, icons; the first body element starts at 1.3" |
| Footer exclusion | 6.85" | 7.5" | Logo (small), page number, **no content here** |

### Horizontal Boundaries

| Boundary | Value | Rule |
|----------|-------|------|
| Left boundary | 0.374" | No element left edge < 0.374", the gutter |
| Right boundary | 12.959" | No element right edge > 12.959" (13.333" - 0.374") |
| Content width | 12.585" | Maximum usable width (12.59" rounded) |

### Overlap Prevention Rules

1. **No content below y=6.85"**: reserves space for logo and page number
2. **No content above y=1.1"** unless it IS the title or section pill; body content starts at 1.3"
3. **Content y + h must not exceed 6.85"**: if it does, reduce height or reflow
4. **Footnotes/captions**: place at y=6.5" max (0.35" above footer zone)
5. **Charts/tables**: bottom edge must clear 6.85" with ≥0.1" breathing room

```yaml
safe_zones:
  title:      {y_min: 0.0,  y_max: 1.1}
  content:    {y_min: 1.1,  y_max: 6.85}   # first body element at 1.3
  footer:     {y_min: 6.85, y_max: 7.5}
  horizontal: {x_min: 0.374, x_max: 12.959}
```

## Values for Code

The builder and validator read every coordinate on this page from `tokens.yaml` (`geometry`,
`components`) through `tools/nbg_tokens.py`; there is no second constants table to keep in step.
