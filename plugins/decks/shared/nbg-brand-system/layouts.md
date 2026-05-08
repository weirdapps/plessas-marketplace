# NBG Slide Layout Catalog

## Slide Dimensions
```yaml
width: 13.33"
height: 7.5"
pptxgenjs: LAYOUT_WIDE
emu: 12,192,000 x 6,858,000
```

## Logo Placement (from Template)

### Small Logo - Content Slides
Use for ALL content slides, charts, tables, infographics.

| Element | Position (x, y) | Size (w x h) | Edge Distance |
|---------|-----------------|--------------|---------------|
| Small Logo | 0.374", 7.071" | 0.822" x 0.236" | 0.19" from bottom |

### Large Logo - Covers & Dividers
Use for cover slides and section dividers only.

| Element | Position (x, y) | Size (w x h) |
|---------|-----------------|--------------|
| Large Logo | 0.374", 6.271" | 2.191" x 0.630" |

### Back Cover Logo - Centered
Plain back cover with centered oval NBG building logo (NO text).

| Element | Position (x, y) | Size (w x h) | Notes |
|---------|-----------------|--------------|-------|
| Centered Oval Logo | 5.44", 2.98" | 2.45" x 1.54" | Centered on slide |

Asset: `assets/nbg-back-cover-logo.png`

## Page Numbers

### Placement
Page numbers appear on **content slides only** (not cover, dividers, back cover).

| Element | Position (x, y) | Size (w x h) | Edge Distance |
|---------|-----------------|--------------|---------------|
| Page Number | 12.71", 7.1554" | 0.33" x 0.152" | 0.29" right, 0.27" bottom |

### Styling
- **Font**: Aptos, 10pt
- **Color**: Medium Gray `#939793`
- **Alignment**: Right

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

## Standard Margins
| Edge | Value |
|------|-------|
| Left margin | 0.37" |
| Right margin | 0.37" |
| Top (title) | 0.5" |
| Top (content) | 1.33" |

## Cover Slides

### Elements
| Element | Font | Size | Position (x, y) |
|---------|------|------|-----------------|
| Title | Aptos | 48pt | 0.37", 1.39" |
| Subtitle | Aptos | **36pt** | 0.37", 2.27" |
| Location | Aptos | 14pt | 0.37", 4.58" |
| Date | Aptos | 14pt | 0.37", 4.97" |

### Dimensions
- Title text box: 7.86" wide x 1.00" tall
- Subtitle text box: 7.86" wide x 0.80" tall

### Cover Subtitle Content
The subtitle lists the organizational units, NOT the generic department name:
```
Cards | GoForMore | Embedded | Digital | SSB | Direct | Fraud | Controls
```
Never use "Cards and Digital Business" — always list the individual units separated by pipes.

### Colors
- Title: Dark Teal `#003841`
- Subtitle: NBG Teal `#007B85`
- Location: Dark Teal `#003841`
- Date: Medium Gray `#939793`

## Contents / TOC Slide

### Elements
| Element | Font | Size | Color | Position |
|---------|------|------|-------|----------|
| "Contents" Header | Aptos Bold | **32pt** | #003841 | 0.37", 0.36" |
| Section Number | Aptos Bold | **18pt** | #007B85 | 0.37", y (see below) |
| Section Title | Aptos Bold | **16pt** | #003841 | 1.10", y |
| Description | Aptos | **12pt** | #595959 | 1.10", y + 0.35" |

### Spacing
- First item Y: 1.48"
- Vertical spacing: 0.85" per item
- Max items: 6-7 (to fit with logo)

## Section Dividers

### Elements
| Element | Font | Size | Position |
|---------|------|------|----------|
| Section Number | Aptos | 60pt | 0.37", 2.84" |
| Section Title | Aptos | **48pt** | 1.86", 2.84" |

### Number Format
- Two-digit: "01", "02", "03", etc.
- Color: NBG Teal `#007B85`
- Title Color: Dark Teal `#003841`

### Divider Consistency Rule (Non-Negotiable)

**Use only ONE type of divider across the entire presentation — never mix styles.**

| Rule | Enforcement |
|------|-------------|
| Single style | All dividers must use the same layout/style throughout |
| Default | Use the standard white background divider |
| Validation | Before completing, verify all dividers match |

### Preventing Text Overlap

If the section title is long (>25 characters) and wraps to multiple lines, the description text may overlap. Fix by:
1. Shortening the title if possible
2. Pushing the description element down
3. Using line breaks intentionally

## Content Layouts

### Full Width Content
```yaml
full_width:
  title:
    x: 0.37"
    y: 0.5"
    w: 12.59"
    h: 0.6"
  content:
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

## Content Typography

| Element | Font | Size | Spacing |
|---------|------|------|---------|
| Title | Aptos | 24pt | Line: 0.9 |
| Body text | Aptos | 11-14pt | Before: 9pt |
| Bullet L1 | Aptos | 14pt | Before: 14pt |
| Bullet L2 | Aptos | 12pt | Before: 5pt |
| Footnotes | Aptos | 8pt | - |

## Back Cover / Closing Slides

**IMPORTANT**: NBG presentations should NOT use "Thank You" or "Questions" text. Use a **plain back cover** instead.

### Plain Back Cover (REQUIRED)
- White background
- Centered oval NBG building logo
- **NO text at all**
- **NO corner logo**
- **NO page number**

### What NOT to Include
- "Thank You" text
- "Questions?" text
- "Q&A" labels
- Contact information (use dedicated slides)
- Any decorative elements

## Metric Card Component

### Standard KPI Card
Light background card for displaying key metrics.

| Property | Value |
|----------|-------|
| Background | #F5F8F6 |
| Border | 1pt #333333 |
| Corner radius | 6.25% |
| Size | 1.40" x 0.80" (typical) |

### Card Elements
| Element | Font | Size | Color | Alignment |
|---------|------|------|-------|-----------|
| Value | Aptos Bold | **18pt** | #007B85 | Center |
| Label | Aptos | **9pt** | #202020 | Center |

### Usage
Place metric cards in the right margin of chart slides for key callouts.

## Infographic Patterns

### Numbered List (3x3 grid)
- 9 items with numbers 1-9
- Each: Number + Title + Description
- Numbers: Large, teal colored

### Sequential Steps (2x3 grid)
- 6 items with "01", "02", etc.
- Two-digit numbering

### KPI Dashboard
- 2x3 grid layout
- Large numbers with labels
- Use Metric Card components

### Timeline (Horizontal)
- Month/date markers
- Milestone points
- Event descriptions

## Shape Presets

| Shape | Usage |
|-------|-------|
| Rectangle | Backgrounds, containers |
| Rounded Rectangle | Cards, callouts, buttons |
| Triangle | Arrows, indicators |
| Ellipse | Icons, bullets |
| Line | Dividers, timelines |

## Communication Use Case Guide

### Executive Summaries
Cover -> Key Metrics -> Charts -> Back Cover

### Project Updates
Cover -> Contents -> Timeline -> Status -> Next Steps -> Back Cover

### Data Presentations
Cover -> Contents -> Charts (bar, line, doughnut) -> Tables -> Key Takeaways -> Back Cover

**Note**: Never use pie charts - always use doughnut.

### Strategy Decks
Cover -> Dividers -> Infographics -> Process Flows -> Timeline -> Back Cover

### Financial Reports
Cover -> Contents -> KPI Metrics -> Charts -> Tables -> Disclaimers -> Back Cover
