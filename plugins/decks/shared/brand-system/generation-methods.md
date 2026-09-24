# Presentation Generation Methods

> Machine source for every brand value a method applies: [`tokens.yaml`](tokens.yaml). The flow
> and contracts are in the plugin's `ARCHITECTURE.md`.

## CRITICAL RULE: One Renderer

Every light-mode NBG deck is built by **`nbg_build.py`**, run through the plugin launcher:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" check deck.yaml             # schema and semantic check, no build
bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" build deck.yaml deck.pptx   # render, then validate
```

The input is a **deck spec** (`deck.yaml`), validated against
`tools/nbg-presentation/deck.schema.json`. The builder renders it with the values in
`tokens.yaml` and runs `nbg_validate.py` on the result; exit 1 means spec or brand violations.

- **No agent writes PptxGenJS, python-pptx or OOXML by hand.** A deck made that way bypasses the
  tested renderer, its tokens and its validator.
- **A layout the named slide types cannot express** uses the `custom` slide type: positioned
  elements (text, bullets, shapes, images, charts, tables) that the builder still renders with
  brand tokens and the validator still checks.
- **Images** (icons, infographics, mockups, logos) enter through the spec: the `image` slide type,
  an `image` column, a `custom` image element, or `cards[].icon` / `steps[].icon`. Relative paths
  resolve against the spec file, then the plugin's `assets/`.
- **Keynote mode** (Standard #21) is the one exception: `decks-py keynote`, a Pillow compositor
  with its own YAML (`keynote.md`).

## CRITICAL RULE: Always Build From Scratch, Never Use NBG Templates

**Do NOT open a template file** (`Presentation(template_path)`). No template ships with this
plugin, and the builder never opens one: it starts from a blank presentation at 13.333" × 7.5"
and adds every element itself.

**Why**: NBG template files contain orphan "Placeholder text" textboxes, decorative freeforms, and
colored background fills on master slides that leak into generated output as phantom artifacts.
Building from scratch eliminates this entire class of bugs.

**What the builder adds per slide** (coordinates in [dimensions.md](dimensions.md)):

- Title text box ([Content Slide](dimensions.md#content-slide))
- Section pill if the slide has a `bumper` (rounded rect #007B85, 9pt white bold ALL CAPS, sized to its text)
- NBG Greek logo image at bottom-left ([Logo Placement](dimensions.md#logo-placement-from-template))
- Page number at bottom-right, 10pt #939793, content slides only
  ([Page Number Placement](dimensions.md#page-number-placement))
- Content shapes (charts, tables, text, cards, icons), each exhibit with its dated source line
- Back cover: centered NBG oval logo ([Back Cover Logo](dimensions.md#back-cover-logo---centered))

## Which Tool Does What

| Task | Method |
|------|--------|
| Create a new deck | Write `deck.yaml`, then `decks-py check` and `decks-py build` |
| Redesign an existing deck | `decks-py extract old.pptx` (text, notes, tables and chart data as markdown), rewrite it as `deck.yaml`, build |
| Check any deck before it ships | `decks-py validate deck.pptx`, then `decks-py render deck.pptx <outdir>` and look at every slide image |
| A bespoke layout | The `custom` slide type in `deck.yaml` |
| A stage keynote | `decks-py keynote talk.yaml` (Standard #21) |
| An iPhone mockup of a screenshot | `decks-py mockup screenshot.png out.png`, then place it through the spec |

`decks-py render` needs LibreOffice. It reports when Aptos was substituted, in which case the
render cannot be trusted for text fit (exit 4).

## Reading and Repairing Existing Decks

A deck a colleague edited in PowerPoint is data to read, not a file to patch: extract it, fix the
spec, rebuild. When you must look inside one:

- [ooxml-charts.md](ooxml-charts.md) shows what the NBG chart style looks like in chart XML, for
  checking or repairing a chart.
- `tools/nbg-presentation/README.md` documents the low-level tools, including the chart and table
  data injectors.

## python-pptx Placeholder Pitfalls

This matters only when code repositions a **placeholder** in an existing deck; the builder never
does, because it places free shapes on a blank layout.

### ⚠️ Setting `.top` on a placeholder can zero out its left/width

When `python-pptx` sets `.top` on a placeholder shape, it creates an `<a:xfrm>` element in the slide XML. If the shape did **not** already have explicit `x` and `cx` values inherited at the slide level, python-pptx writes them as `0`, **overriding the layout's correct left/width with `left=0, width=0`**. Result: the text exists in the file but renders invisible (zero width, pushed to the left edge).

**This affects any layout where you reposition placeholders programmatically**: divider subtitles are the canonical case (60pt titles wrap, you bump the subtitle down, subtitle disappears), but the same bug fires on any placeholder you `.top =` without first reading the layout-defined `x`/`cx`.

**Fix**: use direct XML manipulation to set only `y`, while explicitly preserving the layout's `x` and `cx` values. Pattern (resynced 2026-05-24 from Tsopanakis's `pillar-presenter` skill at `github.com/thomastsop00/pillar-skills`):

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
    placeholder definition, never guess or pass zero.
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

**Retroactive repair**: if you receive a deck where placeholders are already broken (left=0, width=0), call the same function: it overwrites the bad `<a:xfrm>` with correct values.

**Detection**: every populated text-frame placeholder should have non-zero `left` and `width` (or equivalently, `<a:xfrm>/<a:off>` and `<a:ext>` carry non-zero values whenever they exist).

---

## References

- `ARCHITECTURE.md` (plugin root): the flow from brief to deck, the launcher, where state lives
- `charts.md`: the chart specification
- `ooxml-charts.md`: the chart style in OOXML, for existing decks
- `tools/nbg-presentation/README.md`: builder, validator and tool documentation
- Upstream credit for the placeholder XML fix: `pillar-presenter` skill at `github.com/thomastsop00/pillar-skills`
