# NBG Duotone Icons

The official NBG icon style is **duotone**: two teal shades, stroke-based outlines with accent details.

## Style specification

| Role | Token | Hex |
|------|-------|-----|
| Primary (outlines, main shapes) | Teal 06 | `#087681` |
| Accent (fills, details, highlights) | Teal 03 | `#13A4AD` |
| Secondary stroke (some icons) | Teal 05 | `#007B85` |
| Secondary stroke (some icons) | Teal 04 | `#1299A2` |

- Canvas 64x64, `viewBox="0 0 64 64"`
- Stroke widths scale with size: 3px (large), 2px (medium), 1.5px (small)
- `stroke-linejoin: round` where applicable
- Outlines only on main shapes, accent details may use fills
- Functional icons (24px / 16px) are mono `#162020`, stroke 1.5, no fills

Full generation rules: `../../shared/brand-system/icons.md`. To generate a new icon on brand, use the `create-icon` command or the `icon-designer` agent.

## Contents

- `icons-duotone-library.svg` reference sheet, full duotone set (~116 icons x 3 sizes)
- `icons-functional-library.svg` mono functional icon set
- `sets/` 17 themed icon sets (currency, device, social, QR, PFM, card and transaction states, progress, table statuses, bank and browser logos, product icons)

## Provenance

Vendored from the NBG Pillar Design System (Pillar DS assets). This is an internalized copy held in this repo, with no runtime dependency on any external repository. Update by re-exporting from the Pillar DS Figma source.
