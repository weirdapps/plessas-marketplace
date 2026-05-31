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
  left: 0.37"
  right: 0.37"
  top_title: 0.5"
  top_content: 1.1"
  bottom: 0.5"
```

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
// Distance from bottom edge: 0.19"
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
// Distance from bottom edge: 0.19" (aligned with small logo)
// Distance from right edge: 0.36"
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

## Slide Element Positions

### Cover Slide

```yaml
cover:
  title:
    x: 0.37"
    y: 1.39"
    w: 7.86"
    h: 1.56"
  subtitle:
    x: 0.37"
    y: 2.27"
    w: 7.86"
    h: 1.44"
  location:
    x: 0.37"
    y: 4.58"
  date:
    x: 0.37"
    y: 4.97"
```

### Divider Slide

```yaml
divider:
  number:
    x: 0.37"
    y: 2.84"
    w: 1.2"
    h: 1.0"
  title:
    x: 1.86"
    y: 2.84"
    w: 9.5"
    h: 1.0"
```

### Content Slide

```yaml
content:
  bumper_pill:   # Optional — rounded rect, fill 007B85, 9pt Bold white ALL CAPS
    x: 0.37"
    y: 0.35"
    w: 1.3"
    h: 0.3"
    shadow: none  # NO shadow on any element
  title:
    x: 0.37"
    y: 0.75"     # 0.5" if no bumper
    w: 12.59"
    h: 0.4"
    valign: top
    margin: 0
  body:
    x: 0.37"
    y: 1.3"      # 1.1" if no bumper
    w: 12.59"
    h: 5.0"
    valign: top
    margin: 0
```

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
| Footer exclusion | 6.85" | 7.5" | Logo (small), page number — **no content here** |

### Horizontal Boundaries

| Boundary | Value | Rule |
|----------|-------|------|
| Left margin | 0.37" | No element left edge < 0.37" |
| Right margin | 12.96" | No element right edge > 12.96" (13.33" - 0.37") |
| Content width | 12.59" | Maximum usable width |

### Overlap Prevention Rules

1. **No content below y=6.85"** — reserves space for logo and page number
2. **No content above y=1.1"** unless it IS the title or bumper pill
3. **Content y + h must not exceed 6.85"** — if it does, reduce height or reflow
4. **Footnotes/captions**: place at y=6.5" max (0.35" above footer zone)
5. **Charts/tables**: bottom edge must clear 6.85" with ≥0.1" breathing room

```javascript
const SAFE_ZONES = {
  title:   { yMin: 0.0,  yMax: 1.1  },
  content: { yMin: 1.1,  yMax: 6.85 },
  footer:  { yMin: 6.85, yMax: 7.5  },
  horizontal: { xMin: 0.37, xMax: 12.96 }
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
  left: 0.37,
  right: 0.37,
  topTitle: 0.5,
  topContent: 1.33,
  contentWidth: 12.59,

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
    numberX: 0.37,
    numberW: 1.2,
    titleX: 1.86,
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
