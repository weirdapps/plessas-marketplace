# NBG Pillar Design System Reference

**Source**: NBG Pillar Figma Design System
**Purpose**: Digital product design tokens for integration with presentation brand system

---

## Color Palette

### Greyscale

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Black | `#162020` | 22, 32, 32 | Primary text |
| Grey 04 | `#6A6C6A` | 106, 108, 106 | Secondary text |
| Grey 03 | `#A2A6A6` | 162, 166, 166 | Disabled text |
| Grey 02 | `#E0E6E1` | 224, 230, 225 | Borders, dividers |
| Grey 01 | `#F8F9F9` | 248, 249, 249 | Light backgrounds |
| White | `#FFFFFF` | 255, 255, 255 | Backgrounds |

### Teal Scale (Primary Brand)

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Teal 08 | `#003841` | 0, 56, 65 | Darkest - titles, icons |
| Teal 07 | `#03666F` | 3, 102, 111 | Dark accent |
| Teal 06 | `#087681` | 8, 118, 129 | Secondary dark |
| Teal 05 | `#007B85` | 0, 123, 133 | **Primary brand** |
| Teal 04 | `#1299A2` | 18, 153, 162 | Interactive elements |
| Teal 03 | `#13A4AD` | 19, 164, 173 | Hover states |
| Teal 02 | `#56B5BB` | 86, 181, 187 | Light accent |
| Teal 01 | `#E6F5F6` | 230, 245, 246 | Light background |
| Teal 00 | `#F1F7F7` | 241, 247, 247 | Lightest background |

### Alert Colors

#### Success (Green)

| Name | Hex | Usage |
|------|-----|-------|
| Green Dark | `#1D8151` | Dark mode text |
| Green Medium | `#26A567` | Icons, indicators |
| Green Primary | `#34C759` | Primary success |
| Green Light | `#E9FFEA` | Success background |

#### Error (Red)

| Name | Hex | Usage |
|------|-----|-------|
| Red Dark | `#A83535` | Dark mode text |
| Red Medium | `#BE4B4B` | Primary error |
| Red Primary | `#B54747` | Icons, indicators |
| Red Light BG | `#FFDEDE` | Error background |
| Red Lightest | `#FFECEC` | Subtle error BG |

#### Warning (Orange)

| Name | Hex | Usage |
|------|-----|-------|
| Orange Dark | `#B35600` | Dark mode text |
| Orange Medium | `#D08239` | Primary warning |
| Orange Light BG | `#FFE6D0` | Warning background |
| Orange Lightest | `#FFF8F1` | Subtle warning BG |

### PFM Category Colors (Charts)

Use these for data visualization with category-based charts:

| Category | Dark | Light |
|----------|------|-------|
| Apodoxes (Receipts) | `#26A567` | `#BFECD0` |
| Apotamiefsi (Savings) | `#0091A0` | `#ACEDFF` |
| Diaskedasi (Entertainment) | `#D456D0` | `#FFD1FD` |
| Diaforetika (Other) | `#6A6C6A` | `#E0E6E1` |
| Diakopes (Holidays) | `#007B85` | `#BFEEF6` |
| Eidiki Katigoria (Special) | `#1C1F24` | `#C8CDD4` |
| Emvasma (Transfer) | `#03666F` | `#A7DADF` |
| Emvolia (Fees) | `#B54747` | `#FFC5C6` |
| Estiasi (Dining) | `#D08239` | `#FFE0B2` |
| Ygeia (Health) | `#BE4B4B` | `#FFC5C6` |
| Katastimata (Retail) | `#8E6CD0` | `#E1D1FF` |
| Metafores (Transport) | `#5D87DB` | `#C5D7FF` |
| Ola (All) | `#003841` | `#E6F5F6` |
| Paidia (Children) | `#D08239` | `#FFE0B2` |
| Super Market | `#FFC700` | `#FFF4C7` |
| Ypiresies (Services) | `#A36CB4` | `#EDD7F4` |

### Special Colors

| Name | Hex | Usage |
|------|-----|-------|
| Go For More Pink | `#FF2D77` | Marketing campaigns |
| Dark Mode BG | `#1C1F24` | Dark mode backgrounds |
| Dark Mode Surface | `#2A2D32` | Dark mode cards |

### Competitor Bank Colors

| Bank | Hex |
|------|-----|
| Eurobank | `#CA2029` |
| Piraeus Bank | `#FDB913` |
| Alpha Bank | `#02509C` |

---

## Typography

### Font Family

| Type | Font | Fallback |
|------|------|----------|
| Primary | Aeonik Pro | Aptos, Arial |
| Weight - Regular | 400 | Body text |
| Weight - Medium | 500 | Emphasis |
| Weight - Bold | 700 | Headings |

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

---

## Component Specifications

### Border Radius

| Component | Radius |
|-----------|--------|
| Buttons | 8px |
| Cards | 8px |
| Alerts | 8px |
| Badges (rounded) | 24px |
| Inputs | 4px |

### Shadows

```css
/* Standard shadow */
box-shadow: 0 4px 16px rgba(33, 104, 120, 0.04);

/* Elevated shadow */
box-shadow: 0 4px 16px rgba(33, 104, 120, 0.1);

/* Toast shadow */
box-shadow: 0 8px 24px rgba(33, 104, 120, 0.12);
```

### Spacing Scale

| Token | Value |
|-------|-------|
| xs | 4px |
| sm | 8px |
| md | 12px |
| lg | 16px |
| xl | 24px |
| 2xl | 32px |

---

## Alert Components

### Mobile Alerts

| Property | Value |
|----------|-------|
| Border Radius | 8px |
| Padding | 12px |
| Font Size | 12pt |
| Icon Size | 16px |
| Min Height | 48px |

### Desktop Alerts

| Property | Value |
|----------|-------|
| Border Radius | 8px |
| Padding | 16px |
| Font Size | 14pt |
| Icon Size | 20px |
| Min Height | 56px |

### Alert Types

| Type | Icon Color | Background (Light) | Background (Dark) |
|------|------------|-------------------|-------------------|
| Success | `#26A567` | `#E9FFEA` | `#1D3D2E` |
| Error | `#BE4B4B` | `#FFECEC` | `#3D1D1D` |
| Attention | `#D08239` | `#FFF8F1` | `#3D2E1D` |
| Info | `#007B85` | `#E6F5F6` | `#1D3D3D` |
| Generic | `#6A6C6A` | `#F8F9F9` | `#2A2D32` |

---

## Badge Components

### Sizes

| Size | Height | Padding H | Font Size |
|------|--------|-----------|-----------|
| Small | 20px | 8px | 10pt |
| Medium | 24px | 10px | 12pt |
| Large | 28px | 12px | 14pt |

### Badge Types

| Type | Background | Text Color |
|------|------------|------------|
| Default | `#E0E6E1` | `#162020` |
| Success | `#E9FFEA` | `#1D8151` |
| Error | `#FFECEC` | `#A83535` |
| Attention | `#FFF8F1` | `#B35600` |
| Info | `#E6F5F6` | `#007B85` |
| Selected | `#007B85` | `#FFFFFF` |

---

## PptxGenJS Integration

### Pillar DS Constants

```javascript
const PILLAR_DS = {
  colors: {
    // Greyscale
    black: '162020',
    grey04: '6A6C6A',
    grey03: 'A2A6A6',
    grey02: 'E0E6E1',
    grey01: 'F8F9F9',
    white: 'FFFFFF',

    // Teal Scale
    teal08: '003841',
    teal07: '03666F',
    teal06: '087681',
    teal05: '007B85',
    teal04: '1299A2',
    teal03: '13A4AD',
    teal02: '56B5BB',
    teal01: 'E6F5F6',
    teal00: 'F1F7F7',

    // Success
    greenDark: '1D8151',
    greenMedium: '26A567',
    greenPrimary: '34C759',
    greenLight: 'E9FFEA',

    // Error
    redDark: 'A83535',
    redMedium: 'BE4B4B',
    redPrimary: 'B54747',
    redLight: 'FFDEDE',
    redLightest: 'FFECEC',

    // Warning
    orangeDark: 'B35600',
    orangeMedium: 'D08239',
    orangeLight: 'FFE6D0',
    orangeLightest: 'FFF8F1',

    // Special
    goForMorePink: 'FF2D77',
  },

  // PFM Category chart colors (dark variants)
  chartCategoryColors: [
    '26A567', // Receipts
    '0091A0', // Savings
    'D456D0', // Entertainment
    '007B85', // Holidays
    'D08239', // Dining
    '8E6CD0', // Retail
    '5D87DB', // Transport
    'A36CB4', // Services
    'FFC700', // Super Market
    'BE4B4B', // Health
  ],

  fonts: {
    primary: 'Aeonik Pro',
    fallback: 'Aptos',
  },

  spacing: {
    xs: 0.04,  // 4px in inches
    sm: 0.08,  // 8px
    md: 0.12,  // 12px
    lg: 0.16,  // 16px
    xl: 0.24,  // 24px
  },

  borderRadius: 0.08, // 8px in inches
};
```

---

## Mapping: Pillar DS to Presentation System

| Pillar DS | Presentation System | Notes |
|-----------|---------------------|-------|
| Teal 08 `#003841` | Dark Teal | Titles, icons (identical) |
| Teal 05 `#007B85` | NBG Teal | Primary brand (identical) |
| Black `#162020` | Dark Text | Slightly different from `#202020` |
| Grey 04 `#6A6C6A` | - | New: Secondary text |
| Grey 01 `#F8F9F9` | Off-white | Slightly different from `#F5F8F6` |
| Green Primary `#34C759` | Success | Different from `#73AF3C` |
| Red Medium `#BE4B4B` | Alert | Different from `#AA0028` |

### Recommended Approach

**IMPORTANT**: Choose your color palette based on the output medium:

| Output Medium | Color Source | Rationale |
|---------------|--------------|-----------|
| **Digital products** (apps, web) | Pillar DS exactly | Matches design system |
| **Presentations** (PowerPoint) | NBG brand colors | Optimized for projection |
| **Charts in presentations** | NBG chart colors | Consistent with slides |
| **Charts in digital products** | PFM category colors | Matches app palette |

**Do NOT mix color systems within a single deliverable.**

### Quick Color Reference by Use Case

| Use Case | Primary | Secondary | Accent |
|----------|---------|-----------|--------|
| PowerPoint slides | `#003841` | `#007B85` | `#00DFF8` |
| Mobile app | `#003841` (Teal 08) | `#007B85` (Teal 05) | `#13A4AD` (Teal 03) |
| Web dashboard | `#162020` (Black) | `#007B85` (Teal 05) | `#1299A2` (Teal 04) |

### Text Color Mapping

| Context | Pillar DS | Presentation | Note |
|---------|-----------|--------------|------|
| Primary text | `#162020` | `#202020` | Slight difference |
| Secondary text | `#6A6C6A` | `#595959` | Gray variants |
| Disabled/muted | `#A2A6A6` | `#939793` | Gray variants |

**Recommendation**: For presentations, always use the presentation system colors (`colors.md`) for consistency with existing NBG decks

---

## Icon Components

### Icon Sizes

| Size | Dimensions | Usage |
|------|------------|-------|
| Large | 64 x 64 px | Feature icons, hero sections |
| Medium | 48 x 48 px | Standard UI icons |
| Small | 32 x 32 px | Compact UI, lists |

### Icon Colors

| Element | Color | Hex |
|---------|-------|-----|
| Primary stroke | Teal 06 | `#087681` |
| Accent fill | Teal 03 | `#13A4AD` |
| Background | Transparent | - |

### Icon Categories (Digital Banking)

**Devices & Channels:**

- Mobile, Mobile Minimal, Tablet, Laptop, Computer, Devices
- No Computer (crossed out), Device Registration

**Payments & Cards:**

- Credit Card Back, Credit Card Lost, Credit Cards
- Credit Card Angle, ATM Credit Card, Mastercard
- Card Pay, New Card, Mobile Pay, E-Pay

**Communication:**

- Phone, Video Chat, Video Call, Register

**Calendar & Time:**

- Calendar, Calendar Event, Calendar Schedule, Calendar Check
- Calendar Everyday Needs, Time, Time Minimal
- 24 Hours, Alarm Clock, Stopwatch, Hourglass, Watch
- Standing Order, Subscription

**AI & Innovation:**

- AI, AI Rhombus

**Tools:**

- Calculator, Computer Apps, Computer Charts
- Screen Dimension

### Icon Design Rules (Pillar DS)

- **Stroke width**: 2px (scales with icon size)
- **Corner radius**: Rounded corners on rectangles
- **Style**: Outline with selective fills for accents
- **Two-tone**: Primary teal (#087681) + accent teal (#13A4AD)

---

**Version**: 1.0.0
**Source**: NBG Pillar Figma Design System
**Integrated**: 2026-02
