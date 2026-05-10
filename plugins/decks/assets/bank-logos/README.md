# Greek Bank Logos

This directory contains official logos for major Greek banks, for use in competitive analysis slides, interbank transaction visualizations, and market comparison charts.

## Available Logos

| Bank | File | Format | Size |
|------|------|--------|------|
| Alpha Bank | `alpha-bank.png` | PNG | 64x64px |
| Piraeus Bank | `piraeus-bank.png` | PNG | 64x64px |
| Eurobank | `eurobank.png` | PNG | 64x64px |
| Composite (all banks) | `greek-banks-composite.svg` | SVG | - |

## Usage in OOXML

When adding bank logos to slides via XML editing:

### 1. Copy logo files to media folder

```bash
cp alpha-bank.png /path/to/unpacked/ppt/media/
```

### 2. Add relationship in slide .rels file

```xml
<Relationship Id="rId11"
              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
              Target="../media/alpha-bank.png"/>
```

### 3. Add picture element to slide XML

```xml
<p:pic>
  <p:nvPicPr>
    <p:cNvPr id="50" name="AlphaLogo"/>
    <p:cNvPicPr>
      <a:picLocks noChangeAspect="1"/>
    </p:cNvPicPr>
    <p:nvPr/>
  </p:nvPicPr>
  <p:blipFill>
    <a:blip r:embed="rId11"/>
    <a:stretch>
      <a:fillRect/>
    </a:stretch>
  </p:blipFill>
  <p:spPr>
    <a:xfrm>
      <a:off x="450000" y="2200000"/>   <!-- Position in EMUs -->
      <a:ext cx="350000" cy="350000"/>  <!-- Size in EMUs -->
    </a:xfrm>
    <a:prstGeom prst="rect">
      <a:avLst/>
    </a:prstGeom>
  </p:spPr>
</p:pic>
```

## Positioning Guidelines

When using logos next to horizontal bar charts (e.g., interbank transaction comparison):

| Bank | Y Position (EMU) | Notes |
|------|------------------|-------|
| First row (Alpha) | 2,200,000 | ~2.4" from top |
| Second row (Piraeus) | 3,500,000 | ~3.8" from top |
| Third row (Eurobank) | 4,800,000 | ~5.2" from top |

Recommended size: 350,000 x 350,000 EMU (~0.38" square)

## Extracting from Composite SVG

If you need to extract individual logos from the composite SVG:

```javascript
const sharp = require('sharp');

// Extract Alpha Bank (adjust viewBox as needed)
await sharp('greek-banks-composite.svg')
  .extract({ left: 0, top: 0, width: 64, height: 64 })
  .png()
  .toFile('alpha-bank.png');
```

## Brand Colors (MANDATORY for charts)

When comparing systemic banks in charts/tables, each bank **MUST** use its official brand color:

| Bank | Hex | Color |
|------|-----|-------|
| NBG | `#007B85` | Teal |
| Eurobank | `#CA2029` | Red |
| Piraeus Bank | `#FDB913` | Yellow |
| Alpha Bank | `#02509C` | Blue |

## Logo Aspect Ratios

| Bank | Dimensions | Shape | Notes |
|------|-----------|-------|-------|
| NBG | 96x62px | **Oval** (1.55:1) | DO NOT resize to square — always preserve aspect ratio |
| Eurobank | 64x64px | Square | |
| Piraeus Bank | 64x64px | Square | |
| Alpha Bank | 64x64px | Square | |

## Chart Axis Usage

When bank logos replace text axis labels in charts:

- Logos must be **centered** under/beside their respective bars
- Use `addBankLogo()` helper to handle NBG's oval aspect ratio automatically
- Hide the category axis text labels (`catAxisHidden: true`)

## Legal Note

These logos are property of their respective banks. Use only for internal NBG presentations showing competitive analysis or interbank relationships.
