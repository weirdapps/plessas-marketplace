# Presentation Generation Methods

This document provides guidance on when to use PptxGenJS (JavaScript library) vs OOXML editing (direct XML manipulation) vs python-pptx (Python library).

## CRITICAL RULE: Always Build From Scratch — Never Use NBG Templates

**Do NOT use `Presentation(template_path)` to inherit from NBG-Template-GR.pptx or any other template file.** Always create a blank presentation and add all elements manually:

```python
# CORRECT — from scratch
prs = Presentation()
prs.slide_width = 12192000   # 13.33" in EMU
prs.slide_height = 6858000   # 7.5" in EMU
slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
```

```javascript
// CORRECT — from scratch (PptxGenJS)
const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';
const slide = pptx.addSlide();
```

**Why**: NBG template files contain orphan "Placeholder text" textboxes, decorative freeforms, and colored background fills on master slides that leak into generated output as phantom artifacts. Building from scratch eliminates this entire class of bugs.

**What you add manually per slide**:
- Title text box at standard position (0.36, 0.81)
- Eyebrow pill if needed (rounded rect #007B85 fill, 9pt white bold ALL CAPS)
- NBG Greek logo image at bottom-left (0.374, 7.071, 0.822×0.236 for content; 0.374, 6.271, 2.191×0.630 for cover/dividers)
- Page number at bottom-right (12.23, 7.16, 10pt #939793) — content slides only
- Content shapes (charts, tables, text, cards, icons)
- Back cover: centered NBG oval logo (5.44, 2.98, 2.45×1.54)

This adds ~4 lines of code per slide but guarantees zero template artifacts.

## Quick Decision Matrix

| Scenario | Method | Why |
|----------|--------|-----|
| Create new presentation | **python-pptx / PptxGenJS from scratch** | Clean, zero artifacts |
| Update chart data only | **OOXML editing** | Preserves formatting |
| Replace text in existing deck | **OOXML editing** | Preserves layout |
| Add new slides to existing deck | **python-pptx from scratch + merge** | More reliable |
| Complex chart customization | **OOXML editing** | Full control over XML |
| Batch generation | **python-pptx / PptxGenJS** | Scalable, repeatable |

## PptxGenJS (JavaScript)

### When to Use

- **Creating new presentations from scratch**
- **Generating multiple presentations programmatically**
- **When you control the entire output**
- **Standard slide types** (text, bullets, charts, tables)

### Advantages

- Clean, readable JavaScript code
- NBG brand constants easily applied
- No XML manipulation required
- Built-in chart support
- Consistent output

### Limitations

- Limited to PptxGenJS chart types
- Some advanced PowerPoint features not supported
- Cannot edit existing presentations directly

### Example

```javascript
const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';

const slide = pptx.addSlide();
slide.addText('Title', {
  x: 0.37,
  y: 0.5,
  fontSize: 24,
  color: '003841',
  fontFace: 'Aptos'
});

pptx.writeFile('output.pptx');
```

## OOXML Editing (Advanced)

### When to Use

- **Modifying existing presentations**
- **Injecting data into chart placeholders**
- **When preserving original formatting is critical**
- **Advanced chart customization** (waterfall, complex styling)
- **Adding external images** (bank logos, etc.)

### Advantages

- Full control over XML structure
- Can modify any PowerPoint feature
- Preserves original formatting
- Access to features not in PptxGenJS

### Limitations

- Requires understanding of OOXML specification
- More error-prone
- XML syntax must be exact
- Relationship IDs must be managed carefully

### Example

```javascript
// Unzip PPTX
// Edit ppt/charts/chart1.xml
// Update embedded Excel data
// Rezip PPTX
```

### Workflow

```
1. Extract PPTX (unzip)
   └── ppt/
       ├── slides/
       ├── charts/
       ├── media/
       └── _rels/

2. Modify XML files
   - Update values in chart XML
   - Add new relationships
   - Update embedded workbook

3. Validate XML (critical!)
   - Check well-formedness
   - Verify relationship IDs match

4. Repackage PPTX (zip)
```

## Hybrid Approach

For complex scenarios, combine both methods:

### Method A: Generate + Edit

1. **Generate** base presentation with PptxGenJS
2. **Edit** specific elements via OOXML

### Method B: Template + Inject

1. Create template in PowerPoint
2. **Edit** via OOXML to inject data
3. Preserve all original styling

## Decision Flowchart

```
Need a presentation?
    │
    ├─> Creating from scratch?
    │       │
    │       └─> YES → Use PptxGenJS
    │
    ├─> Modifying existing deck?
    │       │
    │       ├─> Just updating text/numbers?
    │       │       └─> OOXML editing
    │       │
    │       └─> Restructuring slides?
    │               └─> PptxGenJS (recreate)
    │
    └─> Complex charts needed?
            │
            ├─> Standard charts (bar, line, doughnut)?
            │       └─> PptxGenJS
            │
            └─> Advanced (waterfall, custom)?
                    └─> OOXML editing
```

## Tool Selection by Task

### Use `nbg_build.py` (python-pptx-based) for:
- Creating presentations from YAML outlines
- Standard executive decks
- Data-driven presentations with simple charts

### Use `inject_chart_data.py` (OOXML) for:
- Updating chart data in existing presentations
- Preserving original chart formatting
- Complex chart types

### Use `inject_table_data.py` (OOXML) for:
- Updating table data in existing presentations
- Preserving table styling

### Use direct OOXML editing for:
- Custom chart configurations
- Adding bank logos to chart slides
- Fine-grained control over positioning

## References

- See `charts.md` for PptxGenJS chart configuration
- See `ooxml-charts.md` for OOXML chart specifications
- See `tools/nbg-presentation/README.md` for tool documentation
