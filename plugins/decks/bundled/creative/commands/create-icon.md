---
description: "Generate an SVG icon (NBG duotone brand defaults)"
argument-hint: "[icon concept or description]"
allowed-tools: Write
---

<objective>
Create a custom SVG icon in the NBG duotone style. Uses NBG brand defaults unless a different brand is specified.

User request: $ARGUMENTS
</objective>

<icon_rules>

## Icon Specifications (NBG Duotone Defaults)

### Canvas

- Size: 64 x 64 px
- ViewBox: "0 0 64 64"
- Root: `fill="none"`
- Padding: content within 6-58px from edges

### Style

- **Duotone** - exactly two teals, both present in every icon
- **Stroke-based outlines** - main shapes are outlines, NOT solid fills
- **Geometric** - clean, simple shapes
- **stroke-width 3** on the 64 canvas

### Colors

| Role | Hex |
|------|-----|
| Primary (main shapes, outlines) | `#087681` |
| Accent (details, dots, highlights) | `#13A4AD` |
| On dark background | `#F5F8F6` |
| Success accent | `#26A567` |
| Alert accent | `#BE4B4B` |

### Template

```svg
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Primary structural element(s) stroke="#087681" stroke-width="3" -->
  <!-- Accent detail(s) in #13A4AD -->
</svg>
```

Reference library: `assets/icons-duotone/` (read 2-3 similar icons first). Full spec: `shared/brand-system/icons.md`.

### What NOT to use

- Solid-filled main shapes (they are outlines)
- Single-color / non-duotone icons
- Gradients
- Transparency/opacity
- Inline styles
- Complex details
- Colors outside the target brand palette
</icon_rules>

<process>
1. Analyze the icon concept
2. Check 2-3 similar icons in assets/icons-duotone/ to calibrate style
3. Plan the duotone split (primary shape #087681, accent details #13A4AD)
4. Design using simple geometric stroked shapes
5. Output clean SVG code only
</process>

<success_criteria>

- [ ] Canvas is 64x64, viewBox="0 0 64 64", root fill="none"
- [ ] Uses BOTH #087681 and #13A4AD (true duotone)
- [ ] Main shapes are strokes (stroke-width 3), large shapes never filled
- [ ] Optically centered with 6-8px padding
- [ ] Simple, geometric design, recognizable at 24x24px
- [ ] Clean, minimal SVG structure
</success_criteria>
