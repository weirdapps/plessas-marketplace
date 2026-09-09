#!/usr/bin/env python3
"""
NBG Presentation Builder

Creates NBG-branded presentations from scratch using python-pptx.
Every slide is built programmatically with exact NBG brand specifications:
- White backgrounds on ALL slides
- Aptos font throughout, margin: 0, valign: top
- Pixel-perfect positioning per the brand system
- Cyan bullets, proper typography hierarchy
- Logo placement, page numbers on content slides only

Usage:
    python nbg_build.py storyline.yaml output.pptx
    python nbg_build.py storyline.yaml -o output.pptx
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

# nbg_color sits one level up, shared with nbg-keynote. These are scripts in
# hyphenated directories rather than a package, so the path is added by hand.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nbg_color import AA_NORMAL, contrast_ratio  # noqa: E402

# python-pptx and lxml are required for building presentations.
# Imported conditionally so tests that only exercise normalize_slide_type()
# and load_catalog() can run without these heavy dependencies.
try:
    from lxml.etree import SubElement
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Inches, Pt

    _HAS_PPTX = True
except ImportError:
    _HAS_PPTX = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
ASSETS_DIR = SCRIPT_DIR.parent.parent / "assets"
CATALOG_PATH = ASSETS_DIR / "slide-catalog.yaml"
TEMPLATES_DIR = ASSETS_DIR / "templates"

# Logo assets: PNG for python-pptx compatibility (SVG not supported)
LOGO_PNG = ASSETS_DIR / "nbg-logo-gr.png"
BACK_COVER_LOGO_PNG = ASSETS_DIR / "nbg-back-cover-logo.png"

# ---------------------------------------------------------------------------
# NBG Brand Constants
# ---------------------------------------------------------------------------
FONT = "Aptos"
FONT_BULLET = "Arial"

if _HAS_PPTX:
    # Colors (RGBColor objects)
    C_DARK_TEAL = RGBColor(0x00, 0x38, 0x41)  # Titles, icons
    C_TEAL = RGBColor(0x00, 0x7B, 0x85)  # Brand accent, section numbers
    C_BRIGHT_CYAN = RGBColor(0x00, 0xDF, 0xF8)  # Bright Cyan (feature accent)
    C_DARK_TEXT = RGBColor(0x20, 0x20, 0x20)  # Body text
    C_LABEL_DARK = RGBColor(0x00, 0x00, 0x00)  # Data labels on colored fills only
    C_MEDIUM_GRAY = RGBColor(0x93, 0x97, 0x93)  # Page numbers, dates
    C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)  # Backgrounds

    # Slide dimensions
    SLIDE_WIDTH = Inches(13.33)
    SLIDE_HEIGHT = Inches(7.5)

# Left gutter. LOGO_SMALL and LOGO_LARGE below already sat at 0.374 while every
# title, bumper, chart and table sat at 0.37, so the builder misaligned its own
# text from its own logo by 0.004". presentation-style-guide.md Standard #15 has
# titles touching the vertical line drawn up from the logo's left edge, so 0.374
# is the one that wins. Set it here and nowhere else.
GUTTER = 0.374
# Content width with symmetric gutters: 13.33 - 2 * GUTTER.
CONTENT_W = 12.582
# A divider's section number sits in a box this wide at the gutter, and its title
# butts against that box's right edge, per presentation-style-guide.md Standard
# #3 ("title immediately to its right"). Derived rather than written out, because
# the title used to be a hardcoded 1.86 in the statement after the number box was
# already placed with GUTTER, leaving a 0.286" gap the standard does not allow.
DIVIDER_NUMBER_W = 1.2
DIVIDER_TITLE_X = GUTTER + DIVIDER_NUMBER_W  # 1.574

# Logo positions (inches), per brand system dimensions.md
LOGO_SMALL = {"x": 0.374, "y": 7.071, "w": 0.822, "h": 0.236}
LOGO_LARGE = {"x": 0.374, "y": 6.271, "w": 2.191, "h": 0.630}
LOGO_BACK = {"x": 5.44, "y": 2.98, "w": 2.45, "h": 1.54}

# Page number position (equal margins from right and bottom edges)
PAGE_NUM = {"x": 12.71, "y": 7.1554, "w": 0.33, "h": 0.152}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _add_textbox(
    slide,
    x,
    y,
    w,
    h,
    text,
    *,
    font_size=14,
    color=None,
    bold=False,
    align=None,
    font_name=FONT,
):
    """Add a text box with NBG defaults: margin=0, valign=top, Aptos."""
    if color is None:
        color = C_DARK_TEXT
    if align is None:
        align = PP_ALIGN.LEFT
    txBox = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = txBox.text_frame
    tf.margin_left = 0
    tf.margin_top = 0
    tf.margin_right = 0
    tf.margin_bottom = 0
    tf.word_wrap = True
    tf.auto_size = None
    # python-pptx uses MSO_ANCHOR for vertical alignment
    tf.paragraphs[0].alignment = align

    # Set vertical anchor via XML (python-pptx MSO_ANCHOR)
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    if bodyPr is not None:
        bodyPr.set("anchor", "t")  # top

    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name

    return txBox


def _set_alt_text(shape, text):
    """Write OOXML alt text onto a shape's non-visual properties (`descr`).

    python-pptx exposes no API for this and seeds `descr` with the source
    filename on pictures and with nothing at all on charts and tables, so every
    deck this builder made shipped a chart a screen reader announces as "Chart
    3". EN 301 549 adopts WCAG 2.1 AA for non-web documents; see Standard #22 in
    presentation-style-guide.md for why the liability is the bank's.

    The text must not restate the slide title. A reader who has the title read
    to them and then hears it again as the chart description has learned
    nothing, so the callers below describe the SHAPE of the data instead:
    plot type, series names, category span.
    """
    cNvPr = shape._element.find(f".//{qn('p:cNvPr')}")
    if cNvPr is not None:
        cNvPr.set("descr", text)


def _chart_alt_text(chart_type, categories, series_list):
    """Alt text for a chart: what it plots, how many series, over what span."""
    names = [str(s.get("name", "")).strip() for s in series_list]
    named = ", ".join(n for n in names if n)
    parts = [f"{chart_type.replace('_', ' ')} chart"]
    parts.append(f"{len(series_list)} series" + (f" ({named})" if named else ""))
    if categories:
        span = f"{categories[0]} to {categories[-1]}" if len(categories) > 1 else str(categories[0])
        parts.append(f"{len(categories)} categories, {span}")
    return ". ".join(parts) + "."


def _table_alt_text(headers, body_rows):
    """Alt text for a table: its columns and how many rows of data it holds."""
    named = ", ".join(str(h).strip() for h in headers if str(h).strip())
    columns = f"{len(headers) or max((len(r) for r in body_rows), default=0)} columns"
    if named:
        columns += f" ({named})"
    return f"Table. {columns}. {len(body_rows)} data rows."


def _add_bumper_pill(slide, text, x=GUTTER, y=0.35):
    """Add bumper as a filled rounded-rect pill with white text (NBG pattern).

    Pill: 1.3x0.3, fill #007B85, text 9pt Bold white ALL CAPS.
    """
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x),
        Inches(y),
        Inches(1.3),
        Inches(0.3),
    )
    pill.fill.solid()
    pill.fill.fore_color.rgb = C_TEAL
    pill.line.fill.background()
    pill.shadow.inherit = False

    # Reduce corner rounding
    pill.adjustments[0] = 0.25

    tf = pill.text_frame
    tf.margin_left = Inches(0.08)
    tf.margin_top = 0
    tf.margin_right = 0
    tf.margin_bottom = 0
    tf.word_wrap = False

    p = tf.paragraphs[0]
    p.text = text.upper()
    p.font.size = Pt(9)
    p.font.color.rgb = C_WHITE
    p.font.bold = True
    p.font.name = FONT
    p.alignment = PP_ALIGN.LEFT

    # Vertical center
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    if bodyPr is not None:
        bodyPr.set("anchor", "ctr")

    return pill


def _add_logo(slide, logo_type="small"):
    """Add NBG logo to slide.

    logo_type: 'small' (content), 'large' (cover/divider), 'back_cover'
    """
    if logo_type == "back_cover":
        pos = LOGO_BACK
        path = BACK_COVER_LOGO_PNG
    elif logo_type == "large":
        pos = LOGO_LARGE
        path = LOGO_PNG
    else:
        pos = LOGO_SMALL
        path = LOGO_PNG

    if not path.exists():
        return  # Skip if logo file missing

    slide.shapes.add_picture(
        str(path),
        Inches(pos["x"]),
        Inches(pos["y"]),
        Inches(pos["w"]),
        Inches(pos["h"]),
    )


def _add_page_number(slide, number):
    """Add page number to bottom-right corner."""
    _add_textbox(
        slide,
        PAGE_NUM["x"],
        PAGE_NUM["y"],
        PAGE_NUM["w"],
        PAGE_NUM["h"],
        str(number),
        font_size=10,
        color=C_MEDIUM_GRAY,
        align=PP_ALIGN.RIGHT,
    )


def _add_bullets(slide, x, y, w, h, points, *, font_size=14):
    """Add bullet points with NBG styling: cyan bullet char, Aptos text."""
    txBox = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = txBox.text_frame
    tf.margin_left = 0
    tf.margin_top = 0
    tf.margin_right = 0
    tf.margin_bottom = 0
    tf.word_wrap = True
    tf.auto_size = None

    # Vertical anchor: top
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    if bodyPr is not None:
        bodyPr.set("anchor", "t")

    for i, point_text in enumerate(points):
        if isinstance(point_text, dict):
            point_text = point_text.get("text", str(point_text))

        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        p.text = str(point_text)
        p.font.size = Pt(font_size)
        p.font.color.rgb = C_DARK_TEXT
        p.font.name = FONT
        p.alignment = PP_ALIGN.LEFT

        # NBG bullet styling via OOXML: • in Arial, Cyan #00ADBF
        pPr = p._p.get_or_add_pPr()
        pPr.set("lvl", "0")

        buFont = SubElement(pPr, qn("a:buFont"))
        buFont.set("typeface", FONT_BULLET)

        buClr = SubElement(pPr, qn("a:buClr"))
        srgbClr = SubElement(buClr, qn("a:srgbClr"))
        srgbClr.set("val", "00ADBF")

        buChar = SubElement(pPr, qn("a:buChar"))
        buChar.set("char", "\u2022")

        # Paragraph spacing: 14pt before (except first)
        if i > 0:
            spcBef = SubElement(pPr, qn("a:spcBef"))
            spcPts = SubElement(spcBef, qn("a:spcPts"))
            spcPts.set("val", "1400")

    return txBox


# NBG chart color palette (hex strings for series coloring, per charts.md)
CHART_COLORS = ["00ADBF", "003841", "007B85", "939793", "BEC1BE", "00DFF8"]

# Light gray for axis lines and borders
C_LIGHT_GRAY_HEX = "BEC1BE"


def _is_doughnut(chart):
    """Doughnut charts have no category or value axis, and no gap_width."""
    return chart.chart_type in (XL_CHART_TYPE.DOUGHNUT, XL_CHART_TYPE.PIE)


# The dark candidate for a label sitting on a colored fill. PURE BLACK, not the
# #202020 body text: see _label_text_color for why the difference decides AA.
LABEL_DARK_HEX = "000000"


def _label_text_color(color_hex):
    """Pick white or black for a data label sitting on a colored fill.

    colors.md offers an R+G+B > 400 rule of thumb, which misreads the cyan
    #00ADBF used for chart series: dark text clears 6:1 on it where white
    manages only 2.7:1. Measure the contrast and take the better of the two.

    The dark candidate has to be pure black. For any candidate pair the worst
    case is the fill luminance where the two curves cross, and only black puts
    that crossing above the 4.5:1 AA floor:

        black   crossover at L=0.1791, best available ratio 4.583:1  clears AA
        #202020 crossover at L=0.2101, best available ratio 4.036:1  fails AA

    That is the sqrt(0.0525) - 0.05 identity: it holds for pure black and
    evaporates for any softened black. Measured over the 52 hex colors in
    brand-system/colors.md, #202020 as the dark candidate emitted a sub-AA label
    for two of them (#5D8D2F at 4.12:1, #F60037 at 4.22:1); black emits none.

    These labels are 12pt or smaller and bold, which is not WCAG "large text"
    (that needs 14pt bold or 18pt regular), so the floor is 4.5:1 and not 3:1.
    C_DARK_TEXT stays #202020 everywhere else: this is a label-on-colored-fill
    decision, not a body-text one.
    """
    white_ratio = contrast_ratio(color_hex, "FFFFFF")
    dark_ratio = contrast_ratio(color_hex, LABEL_DARK_HEX)
    if max(white_ratio, dark_ratio) < AA_NORMAL:
        raise ValueError(
            f"no AA-compliant data label color for fill #{color_hex}: white "
            f"{white_ratio:.2f}:1, black {dark_ratio:.2f}:1, both under {AA_NORMAL}:1"
        )
    return C_WHITE if white_ratio > dark_ratio else C_LABEL_DARK


def _style_chart(chart):
    """Apply NBG brand styling to a chart: no title, hidden value axis,
    no gridlines, no plot border, data labels on bars, Aptos throughout."""
    # No chart title, use slide title textbox instead
    chart.has_title = False

    # No legend by default (single-series); caller enables if multi-series
    chart.has_legend = False

    if not _is_doughnut(chart):
        # Category axis: visible, Aptos 12pt, light gray line (per charts.md)
        cat_ax = chart.category_axis
        cat_ax.tick_labels.font.size = Pt(12)
        cat_ax.tick_labels.font.name = FONT
        cat_ax.tick_labels.font.color.rgb = C_DARK_TEXT
        cat_ax.has_major_gridlines = False
        cat_ax.has_minor_gridlines = False
        cat_ax.format.line.fill.solid()
        cat_ax.format.line.fill.fore_color.rgb = RGBColor.from_string(C_LIGHT_GRAY_HEX)

        # Value axis: HIDDEN (per brand spec: valAxisHidden: true)
        val_ax = chart.value_axis
        val_ax.visible = False
        val_ax.has_major_gridlines = False
        val_ax.has_minor_gridlines = False

    # Plot area: no border, no fill
    plot = chart.plots[0]
    plot.has_data_labels = True
    data_labels = plot.data_labels
    data_labels.font.size = Pt(11)
    data_labels.font.name = FONT
    data_labels.font.bold = True
    data_labels.font.color.rgb = C_DARK_TEXT
    data_labels.show_value = True
    data_labels.show_category_name = False
    data_labels.show_series_name = False

    if _is_doughnut(chart):
        # A doughnut carries one series; the NBG sequence colors its points.
        for i, point in enumerate(plot.series[0].points):
            color_hex = CHART_COLORS[i % len(CHART_COLORS)]
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = RGBColor.from_string(color_hex)

            # Labels sit on the slice, so each takes whichever of white or
            # dark body text actually contrasts with that slice.
            label_font = point.data_label.font
            label_font.size = Pt(11)
            label_font.name = FONT
            label_font.bold = True
            label_font.color.rgb = _label_text_color(color_hex)
    else:
        # Color each series with NBG palette
        for i, series in enumerate(plot.series):
            color_hex = CHART_COLORS[i % len(CHART_COLORS)]
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = RGBColor.from_string(color_hex)


# A description caption is 0.28" tall and takes 0.12" of clearance under it.
CAPTION_SHIFT = 0.4

# Table styling, per the single table spec in brand-system/layouts.md.
TABLE_HEADER_FILL = "003841"  # header row fill, 12pt Aptos Bold white on it
TABLE_ZEBRA_FILL = "F5F8F6"  # every second body row
TABLE_FONT_SIZE = 12
TABLE_HEADER_H = 0.4
TABLE_ROW_H = 0.35
_NUMERIC_CELL = re.compile(r"^[+\-]?[\d.,]+\s*%?$")


def _add_caption(slide, content, bumper):
    """Draw `content.description` under the title. Returns (body top, body height).

    The description carried real text on three of the shipped example slides and
    was never rendered. It sits below the title rather than above the body, so
    the 0.15" title-to-content gap the validator enforces still holds, and the
    body box gives up the same height it takes: dimensions.md wants the body to
    clear the 6.85" content floor with breathing room, so nothing grows.
    """
    top = 1.3 if bumper else 1.1
    height = 5.0 if bumper else 5.2
    description = content.get("description")
    if not description:
        return top, height
    _add_textbox(
        slide,
        GUTTER,
        top,
        CONTENT_W,
        0.28,
        description,
        font_size=12,
        color=RGBColor(0x5A, 0x5F, 0x5A),
    )
    return top + CAPTION_SHIFT, height - CAPTION_SHIFT


# The exhibit source footnote. Type is 11pt Aptos in Caption Gray #5A5F5A, per
# brand-system/typography.md "Table Notes (footnote)" under Charts & Tables,
# which is the row scoping a note attached to an exhibit; Standard #11 puts the
# floor for "Footnotes, sources" at the same 11pt.
#
# Geometry: every exhibit body ends at 6.30" (1.3 + 5.0 with a bumper, 1.1 + 5.2
# without, and a caption shifts both halves by the same 0.4"), and the content
# floor is 6.85". The line sits in that band, so no exhibit gives up height for
# its own provenance. At 0.25" tall it is also under the 0.3" threshold
# check_content_safe_zones uses to exempt chrome, and below the 6.5" line
# check_content_spacing uses to exclude the footer, so it is never mistaken for
# the first content element on the slide.
SOURCE_Y = 6.55
SOURCE_H = 0.25
SOURCE_SIZE = 11
# What nbg_validate.SOURCE_PREFIX recognises, lowercased, so a spec that wrote
# the whole sentence out is not handed a second "Source:". Only the colon form
# is listed: the validator also takes a dash, and prepending to one of those
# costs a doubled prefix rather than a failed check.
SOURCE_PREFIXES = ("source:", "sources:", "πηγή:", "πηγές:")


def _source_line(content):
    """Compose `content.source` into a footnote string. None when there is none.

    The canonical shape is a mapping, because check_exhibit_sources demands two
    separate things of an exhibit footnote and naming them apart is what makes
    the second one hard to forget:

        source:
          name: "NBG MIS"
          as_of: "30 June 2026"
          basis: "constant currency"   # optional definitional caveat

    `name` and `as_of` are the two halves the check tests for: where the number
    came from, and when it was true. `basis` is the third thing a real board
    exhibit footnote carries, the caveat deciding whether two figures are
    comparable at all, and it is optional.

    A plain string is taken as the finished line, so a spec that writes the
    sentence out by hand builds rather than raising AttributeError on `.get`.
    """
    source = content.get("source")
    if not source:
        return None

    if isinstance(source, str):
        text = source.strip()
    else:
        name = str(source.get("name") or "").strip()
        as_of = str(source.get("as_of") or "").strip()
        basis = str(source.get("basis") or "").strip()
        if not name:
            return None
        text = f"{name}, as of {as_of}" if as_of else name
        if basis:
            text += f"; {basis}"

    if not text:
        return None
    return text if text.lower().startswith(SOURCE_PREFIXES) else f"Source: {text}"


def _add_source_line(slide, content):
    """Draw the exhibit's source footnote. Raises on a source with no as_of.

    An unsourced number in a board pack cannot be re-derived, cannot be
    challenged in the room and cannot be defended to a supervisor afterwards, so
    check_exhibit_sources fails the build on one. A missing `content.source` is
    left to it: the warning below names the slide, which the validator's slide
    number on its own does not, and the build then fails on the deck.

    A `source` mapping that omits `as_of` is different, and it stops the build
    here. Be strict where there is structure, lenient where there is only
    rendered text: this function can see the mapping, so it can tell a missing
    field from a badly worded sentence. The validator, reading a finished PPTX,
    can only search the line for a four-digit year, which a year inside a
    `basis` caveat ("restated for the 2025 segment change") satisfies without
    dating anything. Tightening the validator instead would false-fail
    hand-authored and third-party decks this builder never made, so the two
    halves are deliberately asymmetric: airtight on the path that produces
    almost every deck, a reasonable backstop on the ones it does not.

    A plain-string `source` carries no structure to check and is taken as
    written, on the same principle.
    """
    text = _source_line(content)
    if not text:
        print(
            f"  WARNING: exhibit slide '{content.get('title', '')[:40]}' has no "
            f"content.source, so nbg_validate.py will fail the build"
        )
        return

    source = content.get("source")
    if isinstance(source, dict) and not str(source.get("as_of") or "").strip():
        raise ValueError(
            f"exhibit slide {content.get('title', '')[:60]!r} declares content.source "
            f"with no as_of date; a source that does not say when the figure was true "
            f"is half a source"
        )

    _add_textbox(
        slide,
        GUTTER,
        SOURCE_Y,
        CONTENT_W,
        SOURCE_H,
        text,
        font_size=SOURCE_SIZE,
        color=RGBColor(0x5A, 0x5F, 0x5A),
    )


def _numeric_columns(header_row, body_rows):
    """Columns whose body cells are all numeric. Those get right-aligned."""
    width = max((len(r) for r in [header_row, *body_rows] if r), default=0)
    numeric = set()
    for col in range(width):
        cells = [str(r[col]).strip() for r in body_rows if col < len(r) and str(r[col]).strip()]
        if cells and all(_NUMERIC_CELL.match(c) for c in cells):
            numeric.add(col)
    return numeric


def _fill_table_cell(cell, text, *, align, header=False, bold=False, color=None, fill=None):
    """One table cell, per brand-system/layouts.md 'Table Styling'."""
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor.from_string(fill or "FFFFFF")
    cell.margin_left = Inches(0.08)
    cell.margin_right = Inches(0.08)
    cell.margin_top = 0
    cell.margin_bottom = 0

    p = cell.text_frame.paragraphs[0]
    p.text = text
    p.alignment = align
    p.font.size = Pt(TABLE_FONT_SIZE)
    p.font.name = FONT
    p.font.bold = header or bold
    p.font.color.rgb = C_WHITE if header else (color or C_DARK_TEXT)


def create_table_slide(prs, content, table_spec, page_number):
    """Create a table slide (`tables/*` in the slide catalog, or `type: table`).

    Two of the three shipped examples carry a `slide.table` block whose headers
    and rows were dropped on the floor: `type: table` classified as plain content
    and the builder had no table renderer at all, so the slide rendered as a bare
    title. Styling follows the single table spec in brand-system/layouts.md.

    Bumper:  Pill at (0.374, 0.35)
    Title:   24pt Dark Teal at (0.374, 0.75)
    Table:   at (0.374, 1.3), 12.582" wide, header row 0.4" and body rows 0.35"
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = C_WHITE

    bumper = content.get("bumper") or content.get("hyper_title")
    if bumper:
        _add_bumper_pill(slide, bumper)

    title_y = 0.75 if bumper else 0.5
    if content.get("title"):
        _add_textbox(
            slide,
            GUTTER,
            title_y,
            CONTENT_W,
            0.4,
            content["title"],
            font_size=24,
            color=C_DARK_TEAL,
            bold=False,
        )

    table_y, available = _add_caption(slide, content, bumper)
    _add_source_line(slide, content)

    headers = list(table_spec.get("headers") or [])
    body_rows = [list(r) for r in (table_spec.get("rows") or [])]
    if not headers and not body_rows:
        print(f"  WARNING: table slide '{content.get('title', '')[:40]}' has no rows")
        _add_logo(slide, "small")
        _add_page_number(slide, page_number)
        return slide

    n_cols = max(len(r) for r in [headers, *body_rows] if r)
    n_rows = len(body_rows) + (1 if headers else 0)

    # Shrink the rows rather than run past the content safe area.
    header_h = TABLE_HEADER_H if headers else 0.0
    row_h = TABLE_ROW_H
    if body_rows and header_h + row_h * len(body_rows) > available:
        row_h = (available - header_h) / len(body_rows)

    total_h = header_h + row_h * len(body_rows)
    table_frame = slide.shapes.add_table(
        n_rows, n_cols, Inches(GUTTER), Inches(table_y), Inches(CONTENT_W), Inches(total_h)
    )
    _set_alt_text(table_frame, _table_alt_text(headers, body_rows))
    table = table_frame.table
    # The theme table style would repaint the header and band the rows over our
    # own fills; NBG carries both itself.
    table.first_row = False
    table.horz_banding = False

    numeric = _numeric_columns(headers, body_rows)
    highlight = table_spec.get("highlight_column")

    row_index = 0
    if headers:
        table.rows[0].height = Inches(header_h)
        for col in range(n_cols):
            _fill_table_cell(
                table.cell(0, col),
                str(headers[col]) if col < len(headers) else "",
                align=PP_ALIGN.RIGHT if col in numeric else PP_ALIGN.LEFT,
                header=True,
                fill=TABLE_HEADER_FILL,
            )
        row_index = 1

    for i, row in enumerate(body_rows):
        table.rows[row_index + i].height = Inches(row_h)
        for col in range(n_cols):
            emphasised = highlight is not None and col == highlight
            _fill_table_cell(
                table.cell(row_index + i, col),
                str(row[col]) if col < len(row) else "",
                align=PP_ALIGN.RIGHT if col in numeric else PP_ALIGN.LEFT,
                bold=col == 0 or emphasised,
                color=C_TEAL if emphasised else C_DARK_TEXT,
                fill=TABLE_ZEBRA_FILL if i % 2 else "FFFFFF",
            )

    _add_logo(slide, "small")
    _add_page_number(slide, page_number)
    return slide


def create_chart_slide(
    prs, content, page_number, chart_type="bar", categories=None, series_list=None
):
    """Create a chart slide with NBG styling.

    Bumper:    Pill at (0.374, 0.35)
    Title:     24pt Dark Teal at (0.374, 0.75)
    Caption:   12pt Caption Gray under the title, when content.description is set
    Chart:     at (0.374, 1.3), 12.582" x 5.0", less any caption above it
    Logo + page number.

    `categories` and `series_list` come from `slide.chart.data` via _chart_spec().
    When they are None the older, undocumented `content.categories` /
    `content.series` pair is read instead, so a direct caller still works.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = C_WHITE

    bumper = content.get("bumper") or content.get("hyper_title")
    if bumper:
        _add_bumper_pill(slide, bumper)

    title_y = 0.75 if bumper else 0.5
    if content.get("title"):
        _add_textbox(
            slide,
            GUTTER,
            title_y,
            CONTENT_W,
            0.4,
            content["title"],
            font_size=24,
            color=C_DARK_TEAL,
            bold=False,
        )

    body_y, body_h = _add_caption(slide, content, bumper)
    _add_source_line(slide, content)

    # Build chart data
    chart_data = CategoryChartData()
    if categories is None:
        categories = content.get("categories", [])
    if series_list is None:
        series_list = content.get("series", [])
    chart_data.categories = categories

    if not series_list:
        print(
            f"  WARNING: chart slide '{content.get('title', '')[:40]}' has no series "
            f"data, so its plot area will be blank"
        )

    for s in series_list:
        chart_data.add_series(s.get("name", ""), s.get("values", []))

    # Map chart_type string to XL_CHART_TYPE
    type_map = {
        "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "bar_stacked": XL_CHART_TYPE.COLUMN_STACKED,
        "bar_horizontal": XL_CHART_TYPE.BAR_CLUSTERED,
        "line": XL_CHART_TYPE.LINE_MARKERS,
        "doughnut": XL_CHART_TYPE.DOUGHNUT,
        "pie": XL_CHART_TYPE.DOUGHNUT,  # pie remapped to doughnut per brand rules
        "pie_chart": XL_CHART_TYPE.DOUGHNUT,  # YAML compatibility
    }
    xl_type = type_map.get(chart_type, XL_CHART_TYPE.COLUMN_CLUSTERED)

    chart_y, chart_h = body_y, body_h
    chart_frame = slide.shapes.add_chart(
        xl_type,
        Inches(GUTTER),
        Inches(chart_y),
        Inches(CONTENT_W),
        Inches(chart_h),
        chart_data,
    )

    _set_alt_text(chart_frame, _chart_alt_text(chart_type, categories, series_list))

    chart = chart_frame.chart
    _style_chart(chart)

    if _is_doughnut(chart):
        # A doughnut has no bar gap, and its legend is what names the slices.
        wants_legend = True
    else:
        # Bar gap (per brand: barGapWidthPct: 35)
        chart.plots[0].gap_width = 35

        # Enable legend only for multi-series charts
        wants_legend = len(series_list) > 1

    if wants_legend:
        chart.has_legend = True
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(10)
        chart.legend.font.name = FONT
        chart.legend.font.color.rgb = C_DARK_TEXT

    _add_logo(slide, "small")
    _add_page_number(slide, page_number)
    return slide


def create_waterfall_slide(prs, content, page_number):
    """Create a waterfall chart slide using stacked bars.

    python-pptx has no native waterfall type, so we simulate it
    with an invisible base series + positive/negative series.

    Bumper:    Pill at (0.374, 0.35)
    Title:     24pt Dark Teal at (0.374, 0.75)
    Chart:     at (0.374, 1.3), 12.582" x 5.0"
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = C_WHITE

    bumper = content.get("bumper") or content.get("hyper_title")
    if bumper:
        _add_bumper_pill(slide, bumper)

    title_y = 0.75 if bumper else 0.5
    if content.get("title"):
        _add_textbox(
            slide,
            GUTTER,
            title_y,
            CONTENT_W,
            0.4,
            content["title"],
            font_size=24,
            color=C_DARK_TEAL,
            bold=False,
        )

    body_y, body_h = _add_caption(slide, content, bumper)
    _add_source_line(slide, content)

    # Waterfall data: list of {label, value} items
    # First and last are totals, middle items are deltas
    items = content.get("waterfall_items", [])
    if not items:
        _add_logo(slide, "small")
        _add_page_number(slide, page_number)
        return slide

    categories = [item.get("label", "") for item in items]
    values = [item.get("value", 0) for item in items]

    # Build invisible base + increase + decrease series
    base = []
    increase = []
    decrease = []
    running = 0

    for i, val in enumerate(values):
        is_total = items[i].get("total", False)
        if i == 0 or is_total:
            # Total bars start from 0
            base.append(0)
            increase.append(val)
            decrease.append(0)
            running = val
        elif val >= 0:
            base.append(running)
            increase.append(val)
            decrease.append(0)
            running += val
        else:
            base.append(running + val)
            increase.append(0)
            decrease.append(abs(val))
            running += val

    chart_data = CategoryChartData()
    chart_data.categories = categories
    chart_data.add_series("Base", base)
    chart_data.add_series("Increase", increase)
    chart_data.add_series("Decrease", decrease)

    chart_y, chart_h = body_y, body_h
    chart_frame = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_STACKED,
        Inches(GUTTER),
        Inches(chart_y),
        Inches(CONTENT_W),
        Inches(chart_h),
        chart_data,
    )

    _set_alt_text(
        chart_frame,
        _chart_alt_text("waterfall", categories, [{"name": "Increase"}, {"name": "Decrease"}]),
    )

    chart = chart_frame.chart
    chart.has_title = False
    chart.has_legend = False
    plot = chart.plots[0]
    plot.gap_width = 100
    plot.overlap = 100

    # Base series: invisible (no fill, no border, no data labels)
    base_series = plot.series[0]
    base_series.format.fill.background()
    base_series.format.line.fill.background()

    # Increase series: NBG Cyan (per charts.md waterfall spec)
    inc_series = plot.series[1]
    inc_series.format.fill.solid()
    inc_series.format.fill.fore_color.rgb = RGBColor.from_string("00ADBF")
    inc_series.format.line.fill.background()

    # Decrease series: NBG Red (per charts.md/ooxml-charts.md)
    dec_series = plot.series[2]
    dec_series.format.fill.solid()
    dec_series.format.fill.fore_color.rgb = RGBColor.from_string("AA0028")
    dec_series.format.line.fill.background()

    # Data labels: show values on Increase and Decrease series. Each label sits
    # inside its bar, so it takes whichever text color contrasts with that fill.
    for s, vals, fill_hex in (
        (inc_series, increase, "00ADBF"),
        (dec_series, decrease, "AA0028"),
    ):
        s.has_data_labels = True
        s.data_labels.font.size = Pt(10)
        s.data_labels.font.name = FONT
        s.data_labels.font.bold = True
        s.data_labels.font.color.rgb = _label_text_color(fill_hex)
        s.data_labels.show_value = True
        s.data_labels.show_category_name = False
        s.data_labels.show_series_name = False

        # Every category carries a point in both series, so the empty one
        # would print a stray "0" next to each bar. Delete those labels:
        # blanking the text is not enough, since showVal still wins.
        for point, val in zip(s.points, vals, strict=True):
            if val != 0:
                continue
            dLbl = point.data_label._get_or_add_dLbl()
            for child in list(dLbl):
                if child.tag != qn("c:idx"):
                    dLbl.remove(child)
            SubElement(dLbl, qn("c:delete")).set("val", "1")

    # Category axis: visible, Aptos, light gray line, no tick marks
    cat_ax = chart.category_axis
    cat_ax.tick_labels.font.size = Pt(9)
    cat_ax.tick_labels.font.name = FONT
    cat_ax.tick_labels.font.color.rgb = C_DARK_TEXT
    cat_ax.has_major_gridlines = False
    cat_ax.has_minor_gridlines = False
    cat_ax.format.line.fill.solid()
    cat_ax.format.line.fill.fore_color.rgb = RGBColor.from_string(C_LIGHT_GRAY_HEX)

    # Value axis: HIDDEN
    val_ax = chart.value_axis
    val_ax.visible = False
    val_ax.has_major_gridlines = False
    val_ax.has_minor_gridlines = False

    _add_logo(slide, "small")
    _add_page_number(slide, page_number)
    return slide


# ---------------------------------------------------------------------------
# Slide creation functions
# ---------------------------------------------------------------------------


def create_cover_slide(prs, content):
    """Create cover slide with NBG typography hierarchy.

    Title:    48pt Dark Teal at (0.374, 1.39)
    Subtitle: 36pt NBG Teal at (0.374, 2.27)
    Location: 14pt Dark Teal at (0.374, 4.58)
    Date:     14pt Medium Gray at (0.374, 4.97)
    Logo:     Large logo at bottom-left (covers use large)
    NO page number.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = C_WHITE

    if content.get("title"):
        _add_textbox(
            slide,
            GUTTER,
            1.39,
            7.86,
            1.00,
            content["title"],
            font_size=48,
            color=C_DARK_TEAL,
        )

    if content.get("subtitle"):
        _add_textbox(
            slide,
            GUTTER,
            2.27,
            7.86,
            0.80,
            content["subtitle"],
            font_size=36,
            color=C_TEAL,
        )

    if content.get("location"):
        _add_textbox(
            slide,
            GUTTER,
            4.58,
            4,
            0.4,
            content["location"],
            font_size=14,
            color=C_DARK_TEAL,
        )

    if content.get("date"):
        _add_textbox(
            slide,
            GUTTER,
            4.97,
            4,
            0.4,
            content["date"],
            font_size=14,
            color=C_MEDIUM_GRAY,
        )

    _add_logo(slide, "large")
    return slide


def create_divider_slide(prs, content):
    """Create section divider slide.

    Number: 60pt NBG Teal at (0.374, 2.84), in a 1.2" box
    Title:  48pt Dark Teal at (1.574, 2.84), flush to the number box's right edge
    Logo:   Large logo at bottom-left (dividers use large)
    NO page number.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = C_WHITE

    number = content.get("number", "")
    if isinstance(number, int):
        number = str(number).zfill(2)

    if number:
        _add_textbox(slide, GUTTER, 2.84, DIVIDER_NUMBER_W, 1.0, number, font_size=60, color=C_TEAL)

    if content.get("title"):
        _add_textbox(
            slide,
            DIVIDER_TITLE_X,
            2.84,
            9.5,
            1.0,
            content["title"],
            font_size=48,
            color=C_DARK_TEAL,
        )

    _add_logo(slide, "large")
    return slide


def create_content_slide(prs, content, page_number):
    """Create content slide with optional bumper pill and bullet points.

    Bumper:  Pill shape at (0.374, 0.35), 1.3x0.3, #007B85, 9pt Bold white
    Title:   24pt Dark Teal Regular at (0.374, 0.75)
    Bullets: 14pt Dark Text at (0.374, 1.3), cyan bullets
    Logo:    Small logo at bottom-left
    Page number at bottom-right.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = C_WHITE

    # Bumper pill (optional section tag above title)
    bumper = content.get("bumper") or content.get("hyper_title")
    if bumper:
        _add_bumper_pill(slide, bumper)

    # Action title: 24pt Regular (NOT bold, NOT SemiBold)
    title_y = 0.75 if bumper else 0.5
    if content.get("title"):
        _add_textbox(
            slide,
            GUTTER,
            title_y,
            CONTENT_W,
            0.4,
            content["title"],
            font_size=24,
            color=C_DARK_TEAL,
            bold=False,
        )

    body_y, body_h = _add_caption(slide, content, bumper)

    # Body content: bullet points
    points = content.get("points") or content.get("paragraphs") or []
    if not points and content.get("items"):
        # Infographic slides carry {title, description} items. There is no
        # infographic renderer, and dropping them left the slide title-only, so
        # they degrade to bullets rather than vanishing.
        points = [
            f"{i.get('title', '')}: {i.get('description', '')}".strip(": ")
            if isinstance(i, dict)
            else str(i)
            for i in content["items"]
        ]
    if points:
        _add_bullets(slide, GUTTER, body_y, CONTENT_W, body_h, points)

    _add_logo(slide, "small")
    _add_page_number(slide, page_number)
    return slide


def create_contents_slide(prs, sections, page_number):
    """Create table of contents slide.

    Header: 32pt Dark Teal Bold at (0.374, 0.36)
    Items:  Number (18pt Teal) + Title (16pt Dark Teal Bold) + Desc (12pt)
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = C_WHITE

    _add_textbox(
        slide,
        GUTTER,
        0.36,
        10,
        0.70,
        "Contents",
        font_size=32,
        color=C_DARK_TEAL,
        bold=True,
    )

    for i, section in enumerate(sections):
        y = 1.48 + (i * 0.85)

        number = section.get("number", str(i + 1).zfill(2))
        _add_textbox(
            slide,
            GUTTER,
            y,
            0.60,
            0.60,
            str(number),
            font_size=18,
            color=C_TEAL,
            bold=True,
        )

        if section.get("title"):
            _add_textbox(
                slide,
                1.10,
                y,
                8,
                0.35,
                section["title"],
                font_size=16,
                color=C_DARK_TEAL,
                bold=True,
            )

        if section.get("description"):
            _add_textbox(
                slide,
                1.10,
                y + 0.35,
                8,
                0.30,
                section["description"],
                font_size=12,
                color=RGBColor(0x59, 0x59, 0x59),
            )

    _add_logo(slide, "small")
    _add_page_number(slide, page_number)
    return slide


def create_back_cover_slide(prs):
    """Create back cover slide.

    IMPORTANT:
    - NO "Thank You" text
    - NO corner logo
    - NO page number
    - White background with centered oval NBG building logo ONLY
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = C_WHITE

    _add_logo(slide, "back_cover")
    return slide


# ---------------------------------------------------------------------------
# Catalog and type normalization (kept for backward compatibility + tests)
# ---------------------------------------------------------------------------


def load_catalog():
    """Load the slide catalog."""
    with open(CATALOG_PATH) as f:
        return yaml.safe_load(f)


def resolve_slide_index(catalog, template, slide_type):
    """Resolve a slide type path to template index (for legacy compatibility)."""
    parts = slide_type.split("/")
    slides = catalog["templates"][template]["slides"]

    current = slides
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise ValueError(f"Unknown slide type: {slide_type}")

    if isinstance(current, int):
        return current
    raise ValueError(f"Slide type {slide_type} does not resolve to an index")


def normalize_slide_type(slide_type, recommended_visual=None):
    """Convert McKinsey slide types to catalog paths.

    Handles both:
    - Simple: "covers/simple_white" (passes through)
    - McKinsey: "cover", "content", "divider", "back_cover"

    Uses recommended_visual hint when available for smarter selection.
    """
    if "/" in slide_type:
        return slide_type

    visual_mapping = {
        "bar_chart": "charts/bar_single",
        "pie_chart": "charts/pie_single",
        "line_chart": "charts/line_single",
        "waterfall_chart": "charts/bar_single",
        "comparison_chart": "charts/bar_dual",
        "kpi_dashboard": "content/text_only",
        "numbered_infographic": "content/text_only",
        "timeline": "content/text_only",
        "process": "content/text_only",
        "funnel": "content/text_only",
        "table": "tables/half_page",
        "comparison_table": "tables/comparison",
        "icons": "content/text_only",
        "none": "content/text_only",
    }

    if recommended_visual and recommended_visual in visual_mapping:
        return visual_mapping[recommended_visual]

    type_mapping = {
        "cover": "covers/quiet",
        "divider": "dividers/quiet_white",
        "content": "content/text_only",
        "chart": "charts/bar_dual",
        "infographic": "infographics/numbered_6",
        "table": "tables/half_page",
        "thankyou": "back_covers/quiet",
        "back_cover": "back_covers/quiet",
        "summary": "content/text_with_bullets",
    }

    return type_mapping.get(slide_type, "content/text_only")


# ---------------------------------------------------------------------------
# Slide type detection
# ---------------------------------------------------------------------------


def _classify_slide(slide_def):
    """Classify a slide definition into a build category.

    Returns one of: 'cover', 'divider', 'contents', 'content', 'back_cover'
    """
    raw_type = slide_def.get("type", "content")

    # Direct match on raw type
    if raw_type in ("cover", "covers") or raw_type.startswith("covers/"):
        return "cover"
    if raw_type in ("back_cover", "thankyou") or raw_type.startswith("back_covers/"):
        return "back_cover"
    if raw_type in ("divider",) or raw_type.startswith("dividers/"):
        return "divider"
    if raw_type in ("contents", "toc"):
        return "contents"
    if raw_type in ("waterfall", "waterfall_chart"):
        return "waterfall"
    if raw_type in ("chart", "bar_chart", "line_chart", "pie_chart") or raw_type.startswith(
        "charts/"
    ):
        return "chart"
    if raw_type == "table" or raw_type.startswith("tables/"):
        return "table"

    # Check recommended_visual for chart hints
    visual = slide_def.get("recommended_visual", "")
    if visual == "waterfall_chart":
        return "waterfall"
    if visual in ("bar_chart", "comparison_chart", "line_chart", "pie_chart"):
        return "chart"
    if visual in ("table", "comparison_table"):
        return "table"

    # Everything else is content (text, infographics)
    return "content"


def _chart_subtype(slide_def, chart):
    """Map a slide onto one of create_chart_slide's chart_type keys."""
    named = chart.get("type")
    if named:
        return str(named)
    for candidate in (slide_def.get("type", ""), slide_def.get("recommended_visual", "")):
        if candidate.endswith("_chart"):
            return candidate[: -len("_chart")]
        if candidate.startswith("charts/"):
            # Catalog paths: charts/pie_single, charts/bar_dual, charts/line_single
            return candidate.split("/", 1)[1].split("_", 1)[0]
    return "bar"


def _chart_spec(slide_def):
    """Resolve a chart slide's type and data from the published contract.

    The canonical shape, used by all three shipped examples and documented in
    tools/nbg-presentation/README.md:

        - type: chart
          chart:
            type: line
            data:
              categories: ["Jan", "Feb"]
              series:
                - name: "2025"
                  values: [3.8, 3.7]

    Nothing read `slide.chart` at all before this, so every chart in every
    shipped example rendered with zero series and zero categories while the
    validator called the deck clean. Two other shapes are accepted so that
    anything working today keeps working: the README's single-series doughnut
    (`chart.labels` plus `chart.values`) and the undocumented
    `content.categories` / `content.series` pair the builder used to read.

    Returns (chart_type, categories, series), series as {"name", "values"} dicts.
    """
    chart = slide_def.get("chart") or {}
    content = slide_def.get("content") or {}
    data = chart.get("data") or {}

    categories = data.get("categories") or chart.get("labels") or content.get("categories") or []
    series = data.get("series") or content.get("series") or []
    if not series and chart.get("values"):
        # README doughnut shape: a bare value list with no series name.
        series = [{"name": chart.get("name", ""), "values": chart["values"]}]

    return _chart_subtype(slide_def, chart), list(categories), list(series)


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------


def build_presentation(outline_path, output_path):
    """Build NBG presentation from YAML outline.

    Creates every slide from scratch with python-pptx. No template extraction.
    White backgrounds, exact NBG positioning, proper typography.
    """
    outline_path = Path(outline_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().resolve()

    with open(outline_path) as f:
        outline = yaml.safe_load(f)

    # Support both McKinsey and simple formats
    if "presentation" in outline:
        presentation = outline["presentation"]
        # `presentation` may carry the slides itself, or it may carry only the
        # framing metadata (title / audience / purpose / main_recommendation)
        # with `slides` left at the top level. All three shipped examples are
        # the second shape, so reading `presentation.slides` alone raised
        # "No slides defined in outline" on every one of them.
        slides = presentation.get("slides") or outline.get("slides", [])
        print("\n[McKinsey Quality] Using Pyramid Principle structure")
        if presentation.get("main_recommendation"):
            print(f"  Main recommendation: {presentation['main_recommendation'][:60]}...")
    else:
        slides = outline.get("slides", [])

    if not slides:
        raise ValueError("No slides defined in outline")

    print("\nNBG Presentation Builder")
    print(f"{'=' * 50}")
    print(f"Slides: {len(slides)}")
    print(f"Output: {output_path}")
    print(f"{'=' * 50}\n")

    # Create presentation from scratch
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    page_number = 0

    for slide_def in slides:
        category = _classify_slide(slide_def)
        content = slide_def.get("content", {})

        if category == "cover":
            create_cover_slide(prs, content)
            print(f"  [cover] {content.get('title', '')[:50]}")

        elif category == "divider":
            create_divider_slide(prs, content)
            print(f"  [divider] {content.get('number', '')} {content.get('title', '')[:50]}")

        elif category == "contents":
            page_number += 1
            sections = content.get("sections", [])
            create_contents_slide(prs, sections, page_number)
            print(f"  [contents] {len(sections)} sections")

        elif category == "chart":
            page_number += 1
            chart_subtype, categories, series_list = _chart_spec(slide_def)
            create_chart_slide(
                prs,
                content,
                page_number,
                chart_type=chart_subtype,
                categories=categories,
                series_list=series_list,
            )
            print(
                f"  [chart:{chart_subtype}] {len(series_list)} series x "
                f"{len(categories)} categories: {content.get('title', '')[:40]}"
            )

        elif category == "table":
            page_number += 1
            table_spec = slide_def.get("table") or {}
            create_table_slide(prs, content, table_spec, page_number)
            print(
                f"  [table] {len(table_spec.get('rows') or [])} rows: "
                f"{content.get('title', '')[:40]}"
            )

        elif category == "waterfall":
            page_number += 1
            create_waterfall_slide(prs, content, page_number)
            print(f"  [waterfall] {content.get('title', '')[:50]}")

        elif category == "back_cover":
            create_back_cover_slide(prs)
            print("  [back_cover]")

        else:  # content
            page_number += 1
            create_content_slide(prs, content, page_number)
            visual = slide_def.get("recommended_visual", "")
            label = f" ({visual})" if visual else ""
            print(f"  [content{label}] {content.get('title', '')[:50]}")

    prs.save(str(output_path))

    print(f"\n{'=' * 50}")
    print(f"Created: {output_path}")
    print(f"{'=' * 50}\n")

    # Validate. The return code used to be discarded entirely, so a validator
    # that died on a missing import printed its traceback and the build still
    # exited 0 with "Validating..." as its last word.
    validate_script = SCRIPT_DIR / "nbg_validate.py"
    if not validate_script.exists():
        raise RuntimeError(f"validator missing: {validate_script}; the deck is UNVALIDATED")

    print("Validating...")
    proc = subprocess.run(
        [sys.executable, str(validate_script), str(output_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)

    # nbg_validate exits 0 clean, 1 when a check failed, 2 when it could not
    # finish. An import-time crash never reaches its own handler, so it exits 1
    # with a traceback; that is the third case and it is not a failed check.
    crashed = proc.returncode not in (0, 1) or "Traceback (most recent call last)" in (
        proc.stderr or ""
    )
    if crashed:
        raise RuntimeError(
            f"nbg_validate.py could not run (exit {proc.returncode}); "
            f"the deck at {output_path} is UNVALIDATED"
        )
    if proc.returncode != 0:
        raise ValueError(f"nbg_validate.py found brand violations in {output_path}")
    print("Validation passed.")


EXAMPLE_OUTLINE = """Example outline.yaml:

presentation:
  title: "Presentation Title"
  audience: "Board of Directors"
  main_recommendation: "Lead with the answer"

  slides:
    - type: cover
      content:
        title: "Presentation Title"
        subtitle: "Subtitle"
        date: "March 2026"

    - type: content
      key_message: "The key insight"
      so_what: "Why it matters"
      content:
        title: "Action title that tells the story"
        bumper: "SECTION TAG"
        points:
          - "First bullet point"
          - "Second bullet point"

    - type: chart
      content:
        title: "Action title that tells the story"
        source:            # required on every chart and table slide
          name: "NBG MIS"
          as_of: "30 June 2026"
          basis: "constant currency"   # optional caveat
      chart:
        type: bar
        data:
          categories: ["Q1", "Q2"]
          series:
            - name: "2026"
              values: [12, 15]

    - type: back_cover
      content: {}
"""


def main():
    parser = argparse.ArgumentParser(
        prog="nbg_build.py",
        description=(
            "Build an NBG-branded presentation from a YAML outline. White "
            "backgrounds, Aptos font, pixel-perfect positioning."
        ),
        epilog=EXAMPLE_OUTLINE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("spec", help="YAML outline")
    # The documented call is two positionals. Keep it, and add -o, because
    # `nbg_build.py spec.yaml -o out.pptx` used to write a file named "-o".
    parser.add_argument("output", nargs="?", help="output .pptx path")
    parser.add_argument("-o", "--output-file", dest="output_file", help="output .pptx path")
    args = parser.parse_args()

    if args.output_file and args.output:
        parser.error(f"two output paths given: {args.output!r} and {args.output_file!r}")
    output = args.output_file or args.output
    if not output:
        parser.error("an output path is required, as the second positional or with -o")

    try:
        build_presentation(args.spec, output)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
