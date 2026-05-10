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
| Subtitle | Aptos | **36pt** | #007B85 | Regular |
| Location | Aptos | 14pt | #003841 | Regular |
| Date | Aptos | 14pt | #939793 | Regular |

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

### Metric Cards (KPIs)

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Metric Value | Aptos | **50pt** | #003841 | Bold |
| Metric Label | Aptos | **16pt** | #5A5F5A | Regular |

### Charts & Tables

| Element | Font | Size | Color | Weight |
|---------|------|------|-------|--------|
| Chart Title | Aptos | **12pt** | #202020 | Bold |
| Chart Labels | Aptos | 10pt | #202020 | Regular |
| Chart Values | Aptos | 10pt | #202020 | Bold |
| Table Header | Aptos | 11pt | #FFFFFF | Bold |
| Table Cell | Aptos | 10pt | #202020 | Regular |

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
