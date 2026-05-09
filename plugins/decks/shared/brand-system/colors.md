# NBG Complete Color Palette

> **Note**: For digital product colors (apps, web), see [pillar-ds.md](pillar-ds.md) for the complete Pillar Design System palette.

## Theme Colors (NBG Colors 2)

### Core Theme Colors
| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Dark 1 (Black) | `#000000` | 0, 0, 0 | Pure black text |
| Light 1 (White) | `#FFFFFF` | 255, 255, 255 | Backgrounds |
| Dark 2 (NBG Teal) | `#007B85` | 0, 123, 133 | Primary brand, headers |
| Light 2 (Off-white) | `#F5F8F6` | 245, 248, 246 | Light backgrounds |

### Accent Colors
| Accent | Hex | RGB | Usage |
|--------|-----|-----|-------|
| Accent 1 (Dark Teal) | `#003841` | 0, 56, 65 | Primary titles, headings |
| Accent 2 (NBG Teal) | `#007B85` | 0, 123, 133 | Section numbers, highlights |
| Accent 3 (Cyan) | `#00ADBF` | 0, 173, 191 | Secondary accents |
| Accent 4 (Bright Cyan) | `#00DFF8` | 0, 223, 248 | Feature accent, bullets |
| Accent 5 (Light Gray) | `#BEC1BE` | 190, 193, 190 | Subtle elements |
| Accent 6 (Medium Gray) | `#939793` | 147, 151, 147 | Secondary text |

## Primary Brand Colors

### Most Frequently Used
| Hex | Name | Usage | Frequency |
|-----|------|-------|-----------|
| `#00DFF8` | Bright Cyan | Primary accent | Very High (365+) |
| `#007B85` | NBG Teal | Brand color | Very High (814+) |
| `#047A85` | Teal Variant | Alternative teal | High (188+) |
| `#003841` | Dark Teal | Titles, icons | High (89+) |
| `#202020` | Dark Text | Body text | Medium |

### Extended Palette
| Hex | Name | Usage |
|-----|------|-------|
| `#00DEF8` | Bright Cyan Alt | Logo element (GR theme) |
| `#F5F9F6` | Light Background | Slide backgrounds |
| `#252D30` | Dark Charcoal | Dark backgrounds |
| `#0A091B` | Near-black | Dark slides |

## Secondary Colors (Charts & Diagrams)

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Black | `#212121` | 33, 33, 33 | Alternative text |
| Aqua Light | `#3EDEF8` | 62, 222, 248 | Light accent |
| Light Grey | `#BEC1BE` | 190, 193, 190 | Subtle elements |
| Grey | `#595959` | 89, 89, 89 | Secondary text |
| Pale Grey | `#F5F8F6` | 245, 248, 246 | Light backgrounds |

## Status/Semantic Colors

| Status | Hex | RGB | Usage |
|--------|-----|-----|-------|
| Success | `#73AF3C` | 115, 175, 60 | Positive indicators |
| Alert | `#AA0028` | 170, 0, 40 | Negative indicators |
| Gold | `#D9A757` | 217, 167, 87 | Premium accent |
| Blue | `#1E478E` | 30, 71, 142 | Information |

## Status Colors (Tables & Charts Only)

| Status | Hex | RGB | Usage |
|--------|-----|-----|-------|
| Deep Red | `#CB0030` | 203, 0, 48 | Critical/negative |
| Red | `#F60037` | 246, 0, 55 | Alert/warning |
| Orange | `#FF7F1A` | 255, 127, 26 | Caution |
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

Use these colors in order for chart data series:
1. `#00ADBF` - Cyan (primary)
2. `#003841` - Dark Teal
3. `#007B85` - NBG Teal
4. `#939793` - Medium Gray
5. `#BEC1BE` - Light Gray
6. `#00DFF8` - Bright Cyan

## PFM Category Colors (from Pillar DS)

For category-based data visualization (e.g., spending categories, segments):

| Category | Dark | Light | Usage |
|----------|------|-------|-------|
| Receipts | `#26A567` | `#BFECD0` | Income, deposits |
| Savings | `#0091A0` | `#ACEDFF` | Savings, investments |
| Entertainment | `#D456D0` | `#FFD1FD` | Leisure, subscriptions |
| Holidays | `#007B85` | `#BFEEF6` | Travel, vacations |
| Dining | `#D08239` | `#FFE0B2` | Restaurants, food |
| Retail | `#8E6CD0` | `#E1D1FF` | Shopping, stores |
| Transport | `#5D87DB` | `#C5D7FF` | Travel, commute |
| Services | `#A36CB4` | `#EDD7F4` | Utilities, fees |
| Super Market | `#FFC700` | `#FFF4C7` | Groceries |
| Health | `#BE4B4B` | `#FFC5C6` | Medical, pharmacy |

```javascript
// PFM Category chart colors (dark variants)
const PFM_CHART_COLORS = [
  '26A567', '0091A0', 'D456D0', '007B85', 'D08239',
  '8E6CD0', '5D87DB', 'A36CB4', 'FFC700', 'BE4B4B'
];
```

## Background Guidelines

### IMPORTANT: White Backgrounds Only
**User preference: ALWAYS use white backgrounds. Never use dark themes.**

### Light Theme (REQUIRED)
| Element | Color |
|---------|-------|
| Slide background | `#FFFFFF` (white) - **ALWAYS** |
| Title text | `#003841` |
| Body text | `#202020` |
| Accents | `#007B85` or `#00DFF8` |
| **Metric cards** | `#F5F8F6` (light gray background) |
| **Info cards** | `#F5F8F6` (light gray background) |

### Card Backgrounds
| Card Type | Background | Border |
|-----------|------------|--------|
| Metric card | `#F5F8F6` | 1pt `#333333` |
| Info card | `#F5F8F6` | None |
| Highlight card | `#CBFAFF` | None |

### Dark Theme (DO NOT USE)
Dark backgrounds are not used per user preference. All slides should be white.

## PptxGenJS Color Configuration

```javascript
// NBG Colors (no # prefix for PptxGenJS)
const NBG_COLORS = {
  // Primary Brand
  darkTeal: '003841',
  teal: '007B85',
  tealVariant: '047A85',
  cyan: '00ADBF',
  brightCyan: '00DFF8',
  brightCyanAlt: '00DEF8',

  // Neutrals
  black: '000000',
  darkText: '202020',
  charcoal: '252D30',
  mediumGray: '939793',
  lightGray: 'BEC1BE',
  offWhite: 'F5F8F6',
  offWhiteAlt: 'F5F9F6',
  white: 'FFFFFF',

  // Status
  success: '73AF3C',
  alert: 'AA0028',
  gold: 'D9A757',
  blue: '1E478E',

  // Links
  hyperlink: '0D90FF',
  followedLink: '59C3FF',
};

// Chart colors array
const NBG_CHART_COLORS = [
  '00ADBF', '003841', '007B85', '939793', 'BEC1BE', '00DFF8'
];
```

## Color Usage Quick Reference

| Purpose | Recommended Color |
|---------|------------------|
| Slide background | `#FFFFFF` (White) - **ALWAYS** |
| Slide title | `#003841` (Dark Teal) |
| Body text | `#202020` (Dark Text) |
| Section numbers | `#007B85` (NBG Teal) |
| Bullet points | `#00DFF8` (Bright Cyan) |
| Primary accent | `#007B85` (NBG Teal) |
| Bright accent | `#00DFF8` (Bright Cyan) |
| Subtle elements | `#939793` (Medium Gray) |
| **Card background** | `#F5F8F6` (Off-white) |
| **Metric value** | `#007B85` (NBG Teal) |
| **Metric label** | `#202020` (Dark Text) |
| TOC description | `#595959` (Gray) |
| Page number | `#939793` (Medium Gray) |
| Icons | `#003841` (Dark Teal) |

---

## Color Contrast Rules (Non-Negotiable)

**NEVER place light text on light backgrounds or dark text on dark backgrounds.** Always verify text/background contrast:

| Background Color | Text Color to Use |
|-----------------|-------------------|
| Dark Teal `#003841` | White `#FFFFFF` |
| NBG Teal `#007B85` | White `#FFFFFF` |
| White `#FFFFFF` | Dark Teal `#003841` |
| Off-white `#F5F8F6` | Dark Teal `#003841` |

**Rule of thumb:** If the background fill is light (R+G+B > 400), text MUST be dark `#003841`. If background is dark (R+G+B < 400), text MUST be white.

### Cover Slide Contrast — CRITICAL

Cover layouts may have overlapping graphic elements. Rules:
1. All cover text must have sufficient contrast against BOTH the background AND any decorative graphics
2. Use **Dark Teal `#003841`** for the main title — readable on light backgrounds
3. Use **NBG Teal `#007B85`** for the subtitle — ensures visibility
4. **Never use white or light colors** for cover text on white backgrounds
5. **Always set explicit colors** — never rely on theme/inherited colors for covers

### Icon Contrast

| Background | Icon Color |
|------------|------------|
| Light (white, off-white) | Dark Teal `#003841` |
| Dark (teal, dark teal) | White `#FFFFFF` |
| Accent (for callouts) | NBG Teal `#007B85` |
