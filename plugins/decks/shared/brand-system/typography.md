# NBG Typography

## Font Family

### Primary Font (Presentations)

- **Name**: Aptos
- **Weight**: **Regular** (preferred for all elements including titles)
- **Fallback**: Calibri, Tahoma

### Digital Products Font (Pillar DS)

- **Name**: Aeonik Pro
- **Weights**: Regular (400), Medium (500), Bold (700)
- **Fallback**: Aptos, Arial
- **Usage**: NBG digital products, apps, web interfaces

### Bullet Font

- **Name**: Arial
- **Purpose**: Bullet characters only

## Text Styles

### Cover Slide

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Title | Aptos | 48pt | #003841 | Regular |
| Subtitle (NBG-template covers — `13_Cover` etc.) | Aptos | **24pt** | #007B85 | Regular |
| Subtitle (clean DIY cover on Blank — pipe-separated units list) | Aptos | **24pt** | #007B85 | Regular |
| Location | Aptos | 14pt | #003841 | Regular |
| Date | Aptos | 14pt | #939793 | Regular |

**Pipe-separated units list** (clean DIY cover signature, observed in NBG executive reference decks):
`Cards | GoForMore | Embedded | Digital | SSB | Direct | Fraud | Controls`
The full unit list is the subtitle — NOT a generic "Cards and Digital Business" string.

### Divider Slide

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Section Number | Aptos | 60pt | #007B85 | Regular |
| Section Title | Aptos | **48pt** | #003841 | Regular |

### Contents/TOC Slide

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| "Contents" Header | Aptos | **32pt** | #003841 | Bold |
| Section Number | Aptos | **18pt** | #007B85 | Bold |
| Section Title | Aptos | **16pt** | #003841 | Bold |
| Section Description | Aptos | **12pt** | #595959 | Regular |

### Content Slide

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| **Action Title** | Aptos | **24pt** | #003841 | Regular |
| Body Text | Aptos | 11pt | #202020 | Regular |
| Bullet L1 | Aptos | 14pt | #202020 | Regular |
| Bullet L2 | Aptos | 12pt | #202020 | Regular |
| Bullet L3 | Aptos | 11pt | #202020 | Regular |
| Footnotes | Aptos | 8pt | #939793 | Regular |

### Metric Cards (KPIs) — NBG executive signature pattern

Used for "Key Figures" slides — 3-up cards (3.5" × 3.0", `#F5F8F6` fill). Observed 30+ times across reference decks.

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| KPI big number | Aptos | **50pt** | **#007B85** (NBG Teal) | **Bold** |
| KPI caption | Aptos | **16pt** | **#5A5F5A** (Caption Gray) | Regular |

Examples of KPI big-number text (typical NBG executive deck): `750K`, `26%`, `€70M+`, `4.5M`, `3.3M`, `500K`.

Caption is the metric label — short, lowercase or sentence case, no period: `Live Credit Cards`, `MS in Cards Turnover`, `Fee Income`.

**Note**: earlier brand-system drafts used `#003841` for the KPI value; the actual NBG executive pattern is `#007B85` (NBG Teal). Bold + Teal makes the big number pop without competing with the dark-teal title above.

### Page Header Components (NBG executive signature)

Used on Key Figures / Progress & Priorities slides.

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Unit pill (rounded chip — "Cards", "Digital Banking") | Aptos | **16pt** | `#FFFFFF` on `#003841` fill | **Bold** |
| Section title (next to unit pill) | Aptos | **22pt** | `#003841` | Regular |
| Owner subtitle ("Head: A. Smith") | Aptos | **14pt** | `#5A5F5A` | Regular |

### Status Pills (NBG executive signature)

Used on Progress & Priorities slides.

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Numbered bullet (oval) | Aptos | **10pt** | `#FFFFFF` on `#007B85` fill | **Bold** |
| Status badge ("OK"/"TBD"/"H2") | Aptos | **11pt** | `#FFFFFF` on color fill | **Bold** |
| Bullet body text | Aptos | **14pt** | `#202020` | Regular |
| "Delivered ✓" row text | Arial | **15pt** | `#008000` | **Bold** |

### Charts & Tables

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Chart Title | Aptos | **12pt** | #202020 | Bold |
| Chart Labels | Aptos | 10pt | #202020 | Regular |
| Chart Values | Aptos | 10pt | #202020 | Bold |
| Table Header (NBG executive pattern) | Aptos | **10.5pt** | `#FFFFFF` on `#003841` fill | **Bold** |
| Table First Column (label) | Aptos | **12pt** | `#202020` | **Bold** |
| Table Body Cell | Aptos | **10.5pt** | `#202020` | Regular |
| Table Numeric Cell | Aptos | **12pt** | `#202020` | Regular |
| Table Notes (footnote) | Aptos | **10pt** | `#5A5F5A` | Regular |
| In-cell positive emphasis ("+1") | Aptos | 10.5pt | `#007B85` | Bold |
| In-cell priority flag ("H2") | Aptos | 10.5pt | `#CC9900` | Bold |

**Executive table styling rules** (from reference NBG decks):

- Zebra rows: alternate `#FFFFFF` and `#F5F8F6`
- NO custom border overrides (default thin)
- Status emphasis goes in-cell (color + bold), NOT full-cell fills

### Page Number

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Page Number | Aptos | **10pt** | #939793 | Regular |

## Line Spacing

| Element | Line Spacing |
|---------|--------------|
| Titles | 0.9 |
| Body Text | 1.1 |
| Bullets | 1.1 |

## Paragraph Spacing

| Element | Space Before |
|---------|--------------|
| Body Text | 9pt |
| Table Cells | 9pt |
| Bullets | 10pt (L1), 5pt (L2, L3) |

## Text Box Settings

**CRITICAL**: All text boxes must use:

```javascript
{
  margin: 0,  // or [0, 0, 0, 0]
  valign: 'top',
  align: 'left'  // unless specified otherwise
}
```

## Bullet Points

```yaml
bullet:
  character: "•"
  unicode: "2022"
  font: "Arial"
  color: "#00DFF8"  # Bright Cyan
```

## Number Formatting

| Type | Format | Example |
|------|--------|---------|
| Section Numbers | Two-digit | "01", "02", "03" |
| Percentages | With symbol | "47%" |
| Currency | With symbol | "€4.2B" |
| Large Numbers | With unit | "2.3M" |

---

## Pillar DS Typography (Digital Products)

Reference for digital product consistency. See [pillar-ds.md](pillar-ds.md) for full details.

### Font: Aeonik Pro

| Weight | Value | Usage |
|--------|-------|-------|
| Regular | 400 | Body text |
| Medium | 500 | Emphasis, labels |
| Bold | 700 | Headings, titles |

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
