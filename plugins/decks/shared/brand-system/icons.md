# NBG Icon Design Specifications

## Purpose

Generate SVG icons that match exactly the visual language of the NBG iconography library. Visual consistency is mandatory. Creativity is secondary.

The official NBG icon style is **duotone**: two teal shades, stroke-based outlines with accent details. A vendored reference library lives at `../../assets/icons-duotone/` (full duotone sheet, functional set, and 17 themed sets). Read 2-3 reference icons before generating a new one to calibrate style and avoid duplicates.

## Design System Rules

### Canvas & ViewBox

- **Canvas size**: 64 x 64 px
- **viewBox**: `0 0 64 64`
- **xmlns**: `http://www.w3.org/2000/svg`
- **Root fill**: `none` (colors go on individual paths/shapes)

### Color Palette (Duotone, exactly 2 teals)

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Primary | Teal 06 | `#087681` | Main structural shape, outlines, largest/defining element |
| Accent | Teal 03 | `#13A4AD` | Detail elements, interior details, dots, highlights |
| Secondary stroke (optional) | Teal 05 | `#007B85` | Some icons use it as a third stroke shade |
| Secondary stroke (optional) | Teal 04 | `#1299A2` | Some icons use it as a third stroke shade |
| On dark backgrounds | Off-white | `#F5F8F6` | Replace teals for visibility on teal/dark fills |

Every icon must use **both** primary and accent to achieve the duotone effect. Rough balance: 60% primary / 40% accent (varies by icon).

### Stroke vs Fill System

**CRITICAL**: NBG duotone icons are **stroke-based outlines**, not solid fills.

- Main shapes: `stroke="#087681"` with `fill="none"` (outlines only, never filled)
- Small accent details (dots, indicator circles, euro cut): may use `fill="#13A4AD"` (or `#087681`)
- **Stroke width**: `3` on the 64x64 canvas (`stroke-width="3"`). Size variants: 3px large, 2px medium, 1.5px small
- **Line caps**: default (butt); do not add `stroke-linecap` unless needed
- **Line joins**: add `stroke-linejoin="round"` only when corners need softening
- No dashes or dotted lines

### Functional Icons (24px / 16px UI)

For dense in-product UI icons (not the duotone hero style):

- **Mono-color**: Black `#162020`
- Stroke-based, no fills on shapes
- `stroke-width: 1.5`
- `stroke-linecap: round`, `stroke-linejoin: round`

### Grid & Alignment

- **Inner padding**: content stays roughly within 6-58px (do not touch the 64px edge)
- **Optical centering**: balanced around the 32x32 center point
- **Generous breathing room**: avoid edge-to-edge designs

### Shape Language

- **Geometric and precise**: circles, rounded rectangles, simple paths
- Corner radius on rectangles: `rx` values around 6-7 for large containers
- **Recognizable silhouette**: readable at small sizes
- Moderate detail: not too minimal, not too complex

## Icon Generation Rules

### When User Requests an Icon

1. **Analyze the request**
   - Identify the core visual metaphor
   - Consider banking/financial context
   - Note functional purpose (navigation, status, category)

2. **Check the reference library**
   - Read 2-3 icons from the most relevant set in `../../assets/icons-duotone/`
   - Match the exact style, avoid duplicating an existing icon, calibrate detail

3. **Plan the duotone split**
   - Primary structural element(s) -> `#087681`
   - Accent/detail element(s) -> `#13A4AD`
   - Ensure the icon is recognizable at small sizes

4. **Apply NBG duotone rules strictly**
   - 64x64 canvas, `viewBox="0 0 64 64"`, root `fill="none"`
   - Outlines with `stroke="#087681"` `stroke-width="3"` `fill="none"`
   - Accent details with `#13A4AD` (stroke or small fill)
   - Both colors present

5. **Quality check before output**
   - Could this sit next to the library icons?
   - Is it recognizable at 24x24?
   - Is the duotone balance right?
   - No stylistic drift from NBG brand?

6. **Output clean SVG code only**
   - No explanations or commentary
   - No markdown formatting
   - No comments inside SVG
   - Production-ready, copy-paste safe

## Example NBG Icon Structure

### Basic Duotone Template

```svg
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Primary structural element(s) in #087681 -->
  <!-- Accent detail element(s) in #13A4AD -->
</svg>
```

### Simple (Phone / Device)

```svg
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="15.5" y="5.5" width="33" height="53" rx="6.5" stroke="#087681" stroke-width="3"/>
  <circle cx="32" cy="52" r="2" fill="#13A4AD"/>
</svg>
```

### Medium (Lock / Security)

```svg
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="41" r="5" fill="#13A4AD"/>
  <path d="M22 28V16C22 10.4772 26.4772 6 32 6C37.5228 6 42 10.4772 42 16V18" stroke="#13A4AD" stroke-width="3"/>
  <path d="M23.5 28H20C16.6863 28 14 30.6863 14 34V48C14 51.3137 16.6863 54 20 54H44C47.3137 54 50 51.3137 50 48V34C50 30.6863 47.3137 28 44 28H28" stroke="#087681" stroke-width="3"/>
</svg>
```

### Higher complexity (Euro)

```svg
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M32 5.5C46.6355 5.5 58.5 17.3645 58.5 32C58.5 46.6355 46.6355 58.5 32 58.5C30.0489 58.5 28.1487 58.2898 26.3203 57.8906C14.4139 55.2912 5.5 44.6845 5.5 32C5.5 17.3645 17.3645 5.5 32 5.5Z" stroke="#087681" stroke-width="3"/>
  <path d="M43 22.4545C40.4698 19.7138 36.8634 18 32.8606 18C25.2056 18 19 24.268 19 32C19 39.732 25.2056 46 32.8606 46C36.8634 46 40.4698 44.2862 43 41.5455" stroke="#13A4AD" stroke-width="3"/>
  <line x1="14" y1="28.5" x2="38" y2="28.5" stroke="#13A4AD" stroke-width="3"/>
  <line x1="14" y1="36.5" x2="38" y2="36.5" stroke="#13A4AD" stroke-width="3"/>
</svg>
```

### Icon for Dark Background

Swap the two teals for off-white where contrast is needed:

```svg
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="15.5" y="5.5" width="33" height="53" rx="6.5" stroke="#F5F8F6" stroke-width="3"/>
  <circle cx="32" cy="52" r="2" fill="#F5F8F6"/>
</svg>
```

## Common Icon Categories

### Banking & Finance

- Cards, wallets, money transfers
- Account types, statements
- Loans, investments, savings

### Navigation & UI

- Arrows, chevrons, menus
- Settings, search, help
- Close, expand, collapse

### Status & Alerts

For status icons, the outline stays duotone; status meaning is carried by the accent/detail color:

- Success (green `#26A567`)
- Warning/Alert (red `#BE4B4B`)
- Information (teal `#007B85`)

## Technical Constraints

- **No inline styles** - all styling via attributes
- **No transforms** - all positioning via coordinates
- **No unnecessary groups** - flat structure preferred
- **No comments or metadata**
- **No gradients** - solid teal strokes/fills only
- **No transparency/opacity** - 100% opaque

## Quality Gate Checklist

Before outputting any icon, verify:

- [ ] Canvas is 64x64, viewBox="0 0 64 64", root fill="none"
- [ ] Uses BOTH `#087681` (primary) and `#13A4AD` (accent) - true duotone
- [ ] Main shapes are strokes (`stroke-width="3"`), not solid fills
- [ ] Large shapes are never filled
- [ ] Content has 6-58px padding, optically centered
- [ ] Simple, geometric, recognizable at 24x24
- [ ] No stylistic drift from the reference library
- [ ] Clean, minimal SVG structure, production-ready

## Behavior Rules

### Default Behavior

- Generate icon immediately without asking questions
- Output only raw SVG code
- No preamble or explanation

### What NOT to Do

- Never use solid fills on large/main shapes (they are outlines)
- Never use a single color (icons must be duotone)
- Never use gradients or patterns
- Never add excessive detail
- Never use colors outside the NBG duotone palette
- Never use transparency/opacity
- Never output explanations with the SVG code

## Color Mapping by Context

| Context | Primary | Accent |
|---------|---------|--------|
| Standard icon on white | `#087681` | `#13A4AD` |
| Icon on dark/teal background | `#F5F8F6` | `#F5F8F6` |
| Functional 24/16px UI icon | `#162020` (mono, stroke 1.5) | n/a |
| Success/positive | `#087681` | `#26A567` |
| Alert/negative | `#087681` | `#BE4B4B` |

---

## External Logos (Non-NBG)

For competitive analysis, interbank comparisons, and market context slides, external bank logos are available:

### Greek Bank Logos

Location: `assets/bank-logos/`

| Bank | File | Usage |
|------|------|-------|
| Alpha Bank | `alpha-bank.png` | Interbank transaction charts |
| Piraeus Bank | `piraeus-bank.png` | Market share comparisons |
| Eurobank | `eurobank.png` | Competitive analysis |

### Usage in OOXML Editing

When adding external logos to slides via XML:

1. Copy PNG files to `ppt/media/` folder
2. Add relationship entries in slide `.rels` file
3. Add `<p:pic>` elements to slide XML

See `assets/bank-logos/README.md` for detailed XML snippets and positioning guidelines.

### Positioning for Horizontal Bar Charts

When replacing chart category labels with logos:

```
Logo size: 350,000 x 350,000 EMU (~0.38")
X position: 450,000 EMU (aligned left)
Y positions: Spaced at 1,300,000 EMU intervals
```
