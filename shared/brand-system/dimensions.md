# NBG Slide Dimensions & Positioning

## Slide Dimensions

**PptxGenJS**: Use `pptx.layout = 'LAYOUT_WIDE'`

```yaml
slide:
  width: 13.33"
  height: 7.5"
  emu_width: 12192000
  emu_height: 6858000
  aspect_ratio: "16:9"
  pptxgenjs: "LAYOUT_WIDE"
```

## Margins & Safe Zones

```yaml
margins:
  left: 0.374"        # the Standard #15 gutter
  right: 0.374"       # mirror of the gutter; right edge at 12.956"
  top_title: 0.5"
  top_content: 1.33"   # where content starts; the 1.1" floor below is a different number
  bottom: 0.5"
```

`top_content` is where the first content block **starts**. The 1.1" in Content Safe Zones
below is the **floor** it may never cross, which is what `nbg_validate.py` enforces. Two
quantities, not two answers.

The left gutter for titles and every left-aligned text block is **0.374"**, per
`presentation-style-guide.md` Standard #15: the same vertical line the NBG logo sits on.
The right edge mirrors it at **12.956"** (`13.33 - 0.374`). `nbg_validate.py` states the same
pair, so the boundary and the placement value are one number each; there is no second,
looser pair to keep track of.

**Boundaries versus placement coordinates.** A boundary (the right edge, the safe-zone
limits) has one home, here, and Standard #15 and the agents must reference it rather than
restate it. A placement coordinate that a renderer copies literally (the gutter, the divider
title x) is restated wherever a geometry block is specified, each time with its derivation
inline, because a spec block has to be complete to be usable.

`contentWidth` below is still **12.59"** while `nbg_build.py` ships `CONTENT_W = 12.582`
(`13.33 - 2 * 0.374`). Do not change one without the other: the value appears in the agents
and the validator too, and a partial move would create a third state.

## Text Box Rules

**CRITICAL**: All text boxes must follow these rules:

| Property | Value | Reason |
|----------|-------|--------|
| `margin` | `0` | No internal padding |
| `valign` | `'top'` | Never middle or bottom |
| Height | Fit content | No oversized boxes |

### Title Box Sizing

- Single-line title: `h: 0.4"`
- Two-line title: `h: 0.7"`
- Never use large heights that leave empty space

## Logo Placement (from Template)

### Small Logo - Content Slides

Use for all content slides, charts, tables, infographics.

```javascript
const LOGO_SMALL = {
  path: 'assets/nbg-logo-gr.png',
  x: 0.374,
  y: 7.071,
  w: 0.822,
  h: 0.236
};
// Distance from bottom edge: 7.5 - (7.071 + 0.236) = 0.19"
```

### Large Logo - Covers & Dividers

Use for cover slides and section dividers only.

```javascript
const LOGO_LARGE = {
  path: 'assets/nbg-logo-gr.png',
  x: 0.374,
  y: 6.271,
  w: 2.191,
  h: 0.630
};
```

### Back Cover Logo - Centered

Plain back cover with centered oval NBG building logo (NO "Thank You" text).

```javascript
const BACK_COVER_LOGO = {
  path: 'assets/nbg-back-cover-logo.png',
  x: 5.44,   // Centered: (13.33 - 2.45) / 2
  y: 2.98,   // Centered: (7.5 - 1.54) / 2
  w: 2.45,
  h: 1.54
};
```

## Page Number Placement

Page numbers appear on **content slides only** - NOT on cover, dividers, or back cover.

```javascript
const PAGE_NUMBER = {
  x: 12.71,
  y: 7.1554,
  w: 0.33,
  h: 0.152,
  fontFace: 'Aptos',
  fontSize: 10,
  color: '939793',  // Medium Gray
  align: 'right',
  valign: 'middle',
  margin: 0
};
// Derived from the coordinates above. Do not restate these anywhere else:
//   from right edge:  13.33 - (12.71 + 0.33)   = 0.29"
//   from bottom edge: 7.5   - (7.1554 + 0.152) = 0.19"  (level with the small logo)
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

### Full Width Content

```yaml
full_width:
  x: 0.374"
  y: 1.33"
  w: 12.59"
  h: 4.5"
```

### Two Column (50/50)

```yaml
two_column_even:
  left:
    x: 0.374"
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
    x: 0.374"
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
    x: 0.374"
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

## Slide Element Positions

### Cover Slide

```yaml
cover:
  title:
    x: 0.374"
    y: 1.39"
    w: 7.86"
    h: 1.56"
  subtitle:
    x: 0.374"
    y: 2.27"
    w: 7.86"
    h: 1.44"
  location:
    x: 0.374"
    y: 4.58"
  date:
    x: 0.374"
    y: 4.97"
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

### Content Slide

```yaml
content:
  bumper_pill:   # Optional. Rounded rect, fill 007B85, 9pt Bold white ALL CAPS
    x: 0.374"    # Standard #15 gutter
    y: 0.35"
    w: 1.3"
    h: 0.3"
    shadow: none  # NO shadow on any element
  title:
    x: 0.374"    # Standard #15 gutter, never 0.37 and never 0.5
    y: 0.75"     # 0.5" if no bumper
    w: 12.59"
    h: 0.4"      # title bottom lands at 0.9", per Standard #11
    valign: top
    margin: 0
  body:
    x: 0.374"
    y: 1.3"      # 1.1" if no bumper
    w: 12.59"
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
       │  BUMPER / TITLE ZONE                 │
       │  (0.0" – 1.1")                       │
 1.10" ├──────────────────────────────────────┤
       │                                      │
       │  CONTENT SAFE AREA                   │
       │  (1.1" – 6.85")                      │
       │                                      │
       │  Max content height: 5.75"           │
       │                                      │
 6.85" ├──────────────────────────────────────┤
       │  FOOTER EXCLUSION ZONE               │
       │  Logo (y=7.071") / PageNum (y=7.155")│
 7.50" └──────────────────────────────────────┘
```

### Zone Boundaries

| Zone | Y Start | Y End | Contains |
|------|---------|-------|----------|
| Title zone | 0.0" | 1.1" | Bumper pill, slide title |
| Content safe area | 1.1" | 6.85" | Body text, charts, tables, images, icons |
| Footer exclusion | 6.85" | 7.5" | Logo (small), page number, **no content here** |

### Horizontal Boundaries

| Boundary | Value | Rule |
|----------|-------|------|
| Left boundary | 0.374" | No element left edge < 0.374", the gutter |
| Right boundary | 12.956" | No element right edge > 12.956" (13.33" - 0.374") |
| Content width | 12.59" | Maximum usable width |

### Overlap Prevention Rules

1. **No content below y=6.85"**: reserves space for logo and page number
2. **No content above y=1.1"** unless it IS the title or bumper pill
3. **Content y + h must not exceed 6.85"**: if it does, reduce height or reflow
4. **Footnotes/captions**: place at y=6.5" max (0.35" above footer zone)
5. **Charts/tables**: bottom edge must clear 6.85" with ≥0.1" breathing room

```javascript
const SAFE_ZONES = {
  title:   { yMin: 0.0,  yMax: 1.1  },
  content: { yMin: 1.1,  yMax: 6.85 },
  footer:  { yMin: 6.85, yMax: 7.5  },
  horizontal: { xMin: 0.374, xMax: 12.956 }
};

// Validation helper
function isInContentZone(element) {
  return element.y >= SAFE_ZONES.content.yMin
      && (element.y + element.h) <= SAFE_ZONES.content.yMax
      && element.x >= SAFE_ZONES.horizontal.xMin
      && (element.x + element.w) <= SAFE_ZONES.horizontal.xMax;
}
```

## PptxGenJS Layout Constants

```javascript
const LAYOUT = {
  // Margins
  left: 0.374,        // Standard #15 gutter; place left-aligned elements here
  right: 0.374,       // mirror of the gutter
  topTitle: 0.5,
  topContent: 1.33,
  contentWidth: 12.59,   // nbg_build.py ships 12.582; see the note above before changing

  // Small logo (content slides)
  logo: {
    x: 0.374,
    y: 7.071,
    w: 0.822,
    h: 0.236
  },

  // Large logo (covers/dividers)
  logoLarge: {
    x: 0.374,
    y: 6.271,
    w: 2.191,
    h: 0.630
  },

  // Back cover centered logo
  backCoverLogo: {
    x: 5.44,
    y: 2.98,
    w: 2.45,
    h: 1.54
  },

  // Page number (content slides only)
  pageNumber: {
    x: 12.71,
    y: 7.1554,
    w: 0.33,
    h: 0.152
  },

  // Cover positions
  cover: {
    titleY: 1.39,
    subtitleY: 2.27,
    locationY: 4.58,
    dateY: 4.97
  },

  // Divider positions
  divider: {
    numberX: 0.374,
    numberW: 1.2,
    titleX: 1.574,   # 0.374 + 1.2, see the divider block above
    centerY: 2.84
  },

  // Content positions (tight title, top-aligned)
  content: {
    titleY: 0.5,
    titleH: 0.4,   // Tight fit
    bodyY: 1.1,    // Close to title
    bodyW: 12.59
  }
};

// TEXT BOX DEFAULTS (apply to ALL text)
const TEXT_DEFAULTS = {
  margin: 0,       // No internal padding
  valign: 'top',   // ALWAYS top-aligned
};
```
