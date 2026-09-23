# Greek Bank Logos

This directory contains official logos for major Greek banks, for use in competitive analysis slides, interbank transaction visualizations, and market comparison charts.

## Available Logos

| Bank | File | Format | Size |
|------|------|--------|------|
| NBG | `nbg.png` | PNG | 96x62px (oval) |
| Alpha Bank | `alpha-bank.png` | PNG | 64x64px |
| Piraeus Bank | `piraeus-bank.png` | PNG | 64x64px |
| Eurobank | `eurobank.png` | PNG | 64x64px |
| Composite (all banks) | `greek-banks-composite.svg` | SVG | - |

## Placing Logos in a Deck

Logos go into a deck through the deck spec, never by editing slide XML. Use `image` elements in a
`custom` slide (or an `image` column), with a path relative to the plugin's `assets/` folder and
alt text naming the bank:

```yaml
- kind: image
  path: bank-logos/alpha-bank.png
  alt_text: Alpha Bank
  x: 0.374
  y: 2.4
  w: 0.3
  h: 0.3
```

`nbg_build.py` embeds the file. On a peer-bank chart (bank names as the categories or series) it
also places every bank's logo and colour itself, so a spec needs no image elements there. Give
every logo in a comparison the same height, 0.3" (tokens.yaml `components.bank_logos.h`), and let
the width follow the file (Standard #4): NBG's mark is an oval at 96x62 (1.55:1), so at a 0.3"
height it is 0.47" wide, never a 0.3" square.

## Brand Colors (MANDATORY for charts)

When comparing systemic banks in charts/tables, each bank **MUST** use its official brand color
(resynced 2026-05-24 from the Pillar design system, `shared/brand-system/pillar-ds.md`):

| Bank | Hex | Color |
|------|-----|-------|
| NBG | `#007B85` | Teal |
| Eurobank | `#DC2646` | Red |
| Piraeus Bank | `#FFC02D` | Yellow |
| Alpha Bank | `#0D488B` | Blue |

A bank's colour never carries its identity alone: label the bar or series with the bank's name or
logo as well (Standard #22).

## Logo Aspect Ratios

| Bank | Dimensions | Shape | Notes |
|------|-----------|-------|-------|
| NBG | 96x62px | **Oval** (1.55:1) | DO NOT resize to square; always preserve aspect ratio |
| Eurobank | 64x64px | Square | |
| Piraeus Bank | 64x64px | Square | |
| Alpha Bank | 64x64px | Square | |

## Chart Axis Usage

When bank logos replace text axis labels in charts:

- Logos must be **centered** under/beside their respective bars
- Keep each logo's aspect ratio (the NBG oval is wider than it is tall)
- Hide the category axis text labels only when every category has its logo

## Legal Note

These logos are property of their respective banks. Use only for internal NBG presentations showing competitive analysis or interbank relationships.
