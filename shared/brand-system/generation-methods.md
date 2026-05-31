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

### Use `nbg_build.py` (python-pptx-based) for

- Creating presentations from YAML outlines
- Standard executive decks
- Data-driven presentations with simple charts

### Use `inject_chart_data.py` (OOXML) for

- Updating chart data in existing presentations
- Preserving original chart formatting
- Complex chart types

### Use `inject_table_data.py` (OOXML) for

- Updating table data in existing presentations
- Preserving table styling

### Use direct OOXML editing for

- Custom chart configurations
- Adding bank logos to chart slides
- Fine-grained control over positioning

## python-pptx Placeholder Pitfalls

### ⚠️ Setting `.top` on a placeholder can zero out its left/width

When `python-pptx` sets `.top` on a placeholder shape, it creates an `<a:xfrm>` element in the slide XML. If the shape did **not** already have explicit `x` and `cx` values inherited at the slide level, python-pptx writes them as `0` — **overriding the layout's correct left/width with `left=0, width=0`**. Result: the text exists in the file but renders invisible (zero width, pushed to the left edge).

**This affects any layout where you reposition placeholders programmatically** — divider subtitles are the canonical case (60pt titles wrap, you bump the subtitle down, subtitle disappears), but the same bug fires on any placeholder you `.top =` without first reading the layout-defined `x`/`cx`.

**Fix**: use direct XML manipulation to set only `y`, while explicitly preserving the layout's `x` and `cx` values. Pattern (resynced 2026-05-24 from Tsopanakis's `pillar-presenter` skill — `github.com/thomastsop00/pillar-skills`):

```python
from pptx.util import Emu
from lxml import etree

A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P_NS = 'http://schemas.openxmlformats.org/presentationml/2006/main'

def reposition_placeholder_y(shape, new_top_emu, preserve_left_emu, preserve_width_emu, height_emu):
    """
    Set y position on a placeholder without zeroing its x/cx.

    Use this INSTEAD OF `shape.top = value` whenever you reposition
    a placeholder that inherits geometry from its layout. Reads
    preserve_left_emu and preserve_width_emu from the LAYOUT'S
    placeholder definition — never guess or pass zero.
    """
    spPr = shape._element.find(f'{{{P_NS}}}spPr')
    if spPr is None:
        spPr = etree.SubElement(shape._element, f'{{{P_NS}}}spPr')

    xfrm = spPr.find(f'{{{A_NS}}}xfrm')
    if xfrm is None:
        xfrm = etree.SubElement(spPr, f'{{{A_NS}}}xfrm')

    off = xfrm.find(f'{{{A_NS}}}off')
    if off is None:
        off = etree.SubElement(xfrm, f'{{{A_NS}}}off')
    off.set('x', str(preserve_left_emu))   # preserve layout's left
    off.set('y', str(int(new_top_emu)))    # the value you actually want to change

    ext = xfrm.find(f'{{{A_NS}}}ext')
    if ext is None:
        ext = etree.SubElement(xfrm, f'{{{A_NS}}}ext')
    ext.set('cx', str(preserve_width_emu))  # preserve layout's width
    ext.set('cy', str(int(height_emu)))
```

**Retroactive repair**: if you receive a deck where placeholders are already broken (left=0, width=0), call the same function — it overwrites the bad `<a:xfrm>` with correct values.

**Where this matters in NBG decks**:
- Divider slides where the section title (60pt) wraps and shoves the subtitle off-canvas
- Any custom layout where the title placeholder has `spAutoFit` and expands beyond its default height
- Cover slides where you reposition the date/org line below a dynamically sized title

**Detection**: after building the deck, run a sanity check that every populated text-frame placeholder has non-zero `left` and `width` (or equivalently, that `<a:xfrm>/<a:off>` and `<a:ext>` carry non-zero values whenever they exist).

---

## References

- See `charts.md` for PptxGenJS chart configuration
- See `ooxml-charts.md` for OOXML chart specifications
- See `tools/nbg-presentation/README.md` for tool documentation
- Upstream credit for the placeholder XML fix: `pillar-presenter` skill at `github.com/thomastsop00/pillar-skills`
