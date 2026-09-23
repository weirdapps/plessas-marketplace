"""Tests for nbg_validate.py, the NBG brand gate.

Every check has one FAIL fixture and one PASS fixture, enforced mechanically:
FAIL_CASES must name every registered check, and the golden deck (or a named PASS
fixture) must pass every one. On top of those, each false positive and false
negative fixed in the 2026-09 overhaul (VALIDATOR-1..15 and the related findings in
the decks setup review) has a regression test named for the behaviour it pins.

Fixtures are built with python-pptx directly, never with nbg_build.py: the builder
is rewritten independently, and the validator's contract has to hold for any deck,
including the PowerPoint-made ones /redesign-deck and /polish-slides receive.
`golden_prs()` is a six-slide deck that satisfies every brand rule; each FAIL
fixture breaks exactly one rule in a copy of it.

Text-fit tests force the fallback width table (DECKS_FONT_DIRS pointed at an empty
directory) so a laptop with Aptos installed and a CI runner without it measure the
same thing.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("yaml")
pytest.importorskip("pptx")
pytest.importorskip("defusedxml")

from lxml import etree  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.chart.data import CategoryChartData  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.chart import (  # noqa: E402
    XL_CHART_TYPE,
    XL_LABEL_POSITION,
    XL_LEGEND_POSITION,
    XL_MARKER_STYLE,
)
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.opc.constants import RELATIONSHIP_TYPE as RT  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.util import Emu, Pt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import nbg_tokens  # noqa: E402
import nbg_validate as nv  # noqa: E402

SCRIPT = HERE / "nbg_validate.py"
ASSETS = HERE.parent.parent / "assets"
LOGO = ASSETS / "nbg-logo-gr.png"
EMBLEM = ASSETS / "nbg-back-cover-logo.png"
ENGLISH_LOGO = ASSETS / "nbg-logo-fallback.png"
BANK_LOGOS = ASSETS / "bank-logos"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
# Written as code points: a hook refuses literal em dashes in any file.
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)
BULLET = chr(0x2022)

G = nbg_tokens.get("geometry")
PEERS = nbg_tokens.get("extended_palettes.peer_banks")


# --------------------------------------------------------------------- helpers


def inch(value: float) -> Emu:
    return Emu(int(round(value * 914400)))


def new_prs():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(G["slide"]["w_emu"]), Emu(G["slide"]["h_emu"])
    return prs


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def slide(prs, position):
    return prs.slides[position - 1]


def text(
    sld,
    x,
    y,
    w,
    h,
    content,
    *,
    size=14,
    bold=False,
    color="202020",
    font="Aptos",
    wrap=True,
    anchor=MSO_ANCHOR.TOP,
    insets=0.0,
    align=None,
):
    """A text box with brand defaults: zero insets, top anchor, run-level styling.

    auto_size = None drops the spAutoFit python-pptx puts on every new text box, as
    nbg_build does, so the box keeps the height it was given.
    """
    shape = sld.shapes.add_textbox(inch(x), inch(y), inch(w), inch(h))
    tf = shape.text_frame
    tf.auto_size = None
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = inch(insets)
    lines = content if isinstance(content, (list, tuple)) else [content]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align is not None:
            p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.name = font
        run.font.color.rgb = RGBColor.from_string(color)
    return shape


def bullets(sld, x, y, w, h, items, *, size=14, order="schema"):
    """Cyan bullets. order="builder" reproduces the old nbg_build child order."""
    shape = sld.shapes.add_textbox(inch(x), inch(y), inch(w), inch(h))
    tf = shape.text_frame
    tf.auto_size = None
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_pr = p._p.get_or_add_pPr()
        p_pr.set("marL", "228600")
        p_pr.set("indent", "-228600")
        if order == "builder":
            p.font.size = Pt(size)  # writes a:defRPr first, as nbg_build did
        if i:
            spc = etree.SubElement(p_pr, qn("a:spcBef"))
            etree.SubElement(spc, qn("a:spcPts")).set("val", "1400")
        clr = etree.SubElement(p_pr, qn("a:buClr"))
        etree.SubElement(clr, qn("a:srgbClr")).set("val", "00ADBF")
        etree.SubElement(p_pr, qn("a:buFont")).set("typeface", "Arial")
        etree.SubElement(p_pr, qn("a:buChar")).set("char", BULLET)
        run = p.add_run()
        run.text = item
        run.font.size = Pt(size)
        run.font.name = "Aptos"
        run.font.color.rgb = RGBColor.from_string("202020")
    return shape


def title(sld, content, *, y=0.5, x=0.374, w=12.585, h=0.4, size=24, bold=False):
    return text(sld, x, y, w, h, content, size=size, bold=bold, color="003841")


def no_effects(shape):
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def pill(sld, label, *, x=0.374, y=0.35, w=1.0, h=0.3, size=9, fill="007B85"):
    shape = sld.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, inch(x), inch(y), inch(w), inch(h))
    shape.adjustments[0] = 0.5
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    no_effects(shape)
    tf = shape.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = inch(0.1)
    tf.margin_top = tf.margin_bottom = 0
    run = tf.paragraphs[0].add_run()
    run.text = label.upper()
    run.font.size = Pt(size)
    run.font.bold = True
    run.font.name = "Aptos"
    run.font.color.rgb = RGBColor.from_string("FFFFFF")
    return shape


def badge(sld, x, y, label, *, size=0.28):
    shape = sld.shapes.add_shape(MSO_SHAPE.OVAL, inch(x), inch(y), inch(size), inch(size))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string("007B85")
    no_effects(shape)
    tf = shape.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = label
    run.font.size = Pt(10)
    run.font.bold = True
    run.font.name = "Aptos"
    run.font.color.rgb = RGBColor.from_string("FFFFFF")
    return shape


def box(sld, x, y, w, h, fill, *, shape=MSO_SHAPE.RECTANGLE):
    """A filled, text-free shape: a card, a chip background."""
    s = sld.shapes.add_shape(shape, inch(x), inch(y), inch(w), inch(h))
    s.fill.solid()
    s.fill.fore_color.rgb = RGBColor.from_string(fill)
    return no_effects(s)


def set_alt(shape, alt):
    shape._element.find(".//" + qn("p:cNvPr")).set("descr", alt)
    return shape


def logo(sld, kind="small", *, path=None, w=None, h=None):
    spot = {"small": G["logo_small"], "large": G["logo_large"], "back": G["logo_back"]}[kind]
    image = path or (EMBLEM if kind == "back" else LOGO)
    return sld.shapes.add_picture(
        str(image), inch(spot["x"]), inch(spot["y"]), inch(w or spot["w"]), inch(h or spot["h"])
    )


def page_number(sld, n):
    spot = G["page_number"]
    return text(
        sld,
        spot["x"],
        spot["y"],
        spot["w"],
        spot["h"],
        str(n),
        size=10,
        color="939793",
        align=PP_ALIGN.RIGHT,
        anchor=MSO_ANCHOR.MIDDLE,
    )


def source(sld, line="Source: NBG MIS, as of 31 December 2025", *, y=6.25, size=11):
    return text(sld, 0.374, y, 12.585, 0.25, line, size=size, color="5A5F5A")


def _style_axes(chart, *, font, value_visible, value_color="202020", size=12):
    chart.font.name = font
    chart.font.size = Pt(size)
    cat = chart.category_axis
    cat.tick_labels.font.size = Pt(size)
    cat.tick_labels.font.name = font
    cat.tick_labels.font.color.rgb = RGBColor.from_string("202020")
    cat.format.line.color.rgb = RGBColor.from_string("BEC1BE")
    val = chart.value_axis
    val.has_major_gridlines = False
    val.visible = value_visible
    if value_visible:
        val.tick_labels.font.size = Pt(11)
        val.tick_labels.font.name = font
        val.tick_labels.font.color.rgb = RGBColor.from_string(value_color)
        val.format.line.fill.background()


def bar_chart(
    sld,
    *,
    x=0.374,
    y=1.3,
    w=12.585,
    h=4.8,
    categories=("Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"),
    series=(("Mobile users (M)", (2.9, 3.0, 3.2, 3.3)),),
    colors=("00ADBF", "003841", "007B85", "939793", "BEC1BE", "00DFF8", "5A5F5A", "E6F5F6"),
    point_colors=None,
    font="Aptos",
    label_size=12,
    styled=True,
    zero_based=True,
    chart_type=XL_CHART_TYPE.COLUMN_CLUSTERED,
    alt="Column chart of mobile users by quarter of 2025, rising from 2.9M to 3.3M.",
):
    data = CategoryChartData()
    data.categories = list(categories)
    for name, values in series:
        data.add_series(name, values)
    frame = sld.shapes.add_chart(chart_type, inch(x), inch(y), inch(w), inch(h), data)
    chart = frame.chart
    chart.has_legend = len(series) > 1
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(12)
        chart.legend.font.name = font
    plot = chart.plots[0]
    if chart_type not in (XL_CHART_TYPE.PIE, XL_CHART_TYPE.DOUGHNUT):
        _style_axes(chart, font=font, value_visible=False)
        if zero_based:
            # As nbg_build does: an automatic axis on close values (2.9 to 3.3) starts
            # above zero in PowerPoint and truncates every bar (E2E-OUTPUT-01).
            chart.value_axis.minimum_scale = 0
    else:
        chart.font.name = font
        chart.font.size = Pt(12)
    if styled:
        for i, ser in enumerate(plot.series):
            ser.format.fill.solid()
            ser.format.fill.fore_color.rgb = RGBColor.from_string(colors[i % len(colors)])
    if point_colors:
        ser = plot.series[0]
        for i, color in enumerate(point_colors):
            ser.points[i].format.fill.solid()
            ser.points[i].format.fill.fore_color.rgb = RGBColor.from_string(color)
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.font.size = Pt(label_size)
    labels.font.bold = True
    labels.font.name = font
    labels.font.color.rgb = RGBColor.from_string("003841")
    if chart_type == XL_CHART_TYPE.COLUMN_CLUSTERED:
        labels.position = XL_LABEL_POSITION.OUTSIDE_END
    set_alt(frame, alt)
    return frame


def line_chart(
    sld,
    *,
    x=0.374,
    y=1.3,
    w=12.585,
    h=4.8,
    explicit_line=True,
    markers="hollow",
    alt="Line chart of digital sales share by quarter, 2024 against 2025, both rising.",
):
    data = CategoryChartData()
    data.categories = ["Q1", "Q2", "Q3", "Q4"]
    data.add_series("2024", (0.28, 0.30, 0.31, 0.33))
    data.add_series("2025", (0.31, 0.33, 0.35, 0.36))
    frame = sld.shapes.add_chart(
        XL_CHART_TYPE.LINE_MARKERS, inch(x), inch(y), inch(w), inch(h), data
    )
    chart = frame.chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.size = Pt(12)
    chart.legend.font.name = "Aptos"
    _style_axes(chart, font="Aptos", value_visible=True, value_color="939793")
    for ser, color in zip(chart.plots[0].series, ("00ADBF", "003841"), strict=True):
        ser.smooth = False
        if explicit_line:
            ser.format.line.color.rgb = RGBColor.from_string(color)
            ser.format.line.width = Pt(3.5)
        if markers == "hollow":
            ser.marker.style = XL_MARKER_STYLE.CIRCLE
            ser.marker.size = 6
            ser.marker.format.fill.solid()
            ser.marker.format.fill.fore_color.rgb = RGBColor.from_string("FFFFFF")
            ser.marker.format.line.color.rgb = RGBColor.from_string(color)
    set_alt(frame, alt)
    return frame


def table(sld, rows, *, x=0.374, y=1.3, w=12.585, row_h=0.4, size=12, alt=None):
    frame = sld.shapes.add_table(
        len(rows), len(rows[0]), inch(x), inch(y), inch(w), inch(row_h * len(rows))
    )
    tbl = frame.table
    for r, row in enumerate(rows):
        tbl.rows[r].height = inch(row_h)
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            header = r == 0
            fill = "003841" if header else ("F5F8F6" if r % 2 == 0 else "FFFFFF")
            cell.fill.fore_color.rgb = RGBColor.from_string(fill)
            cell.margin_left = cell.margin_right = inch(0.08)
            cell.margin_top = cell.margin_bottom = inch(0.04)
            run = cell.text_frame.paragraphs[0].add_run()
            run.text = str(value)
            run.font.size = Pt(size)
            run.font.bold = header
            run.font.name = "Aptos"
            run.font.color.rgb = RGBColor.from_string("FFFFFF" if header else "202020")
    set_alt(frame, alt or f"Table with columns {', '.join(rows[0])} and {len(rows) - 1} rows.")
    return frame


def remove(shape):
    shape._element.getparent().remove(shape._element)


def shape_with_text(sld, prefix):
    for sh in sld.shapes:
        if sh.has_text_frame and sh.text_frame.text.startswith(prefix):
            return sh
    raise AssertionError(f"no shape starting {prefix!r}")


def background_graphic(prs, make, *, master=False):
    """Draw a shape with make(scratch slide) and move it onto the Blank layout every
    golden slide uses, or onto the slide master: a background graphic that each slide
    showing it renders. python-pptx cannot add shapes to a layout directly."""
    scratch = prs.slides.add_slide(prs.slide_layouts[6])
    el = make(scratch)._element
    owner = prs.slide_master if master else prs.slide_layouts[6]
    blip = el.find(".//" + qn("a:blip"))
    if blip is not None:
        image = scratch.part.related_part(blip.get(qn("r:embed")))
        blip.set(qn("r:embed"), owner.part.relate_to(image, RT.IMAGE))
    owner.shapes._spTree.append(el)
    ids = prs.slides._sldIdLst
    last = list(ids)[-1]
    prs.part.drop_rel(last.rId)
    ids.remove(last)
    return el


DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
DSP_NS = "http://schemas.microsoft.com/office/drawing/2008/diagram"


def add_smartart(path, *, fill="007B85", color="FFFFFF", size=12, font="Aptos", drawing=True):
    """Put a three-box SmartArt diagram on slide 2 of a saved deck. PowerPoint shows the
    diagram's drawing part; drawing=False leaves it out, as some producers do."""
    a = NS_A
    boxes = "".join(
        f'<dsp:sp modelId="{{00000000-0000-0000-0000-00000000000{i}}}">'
        '<dsp:nvSpPr><dsp:cNvPr id="0" name=""/><dsp:cNvSpPr/></dsp:nvSpPr>'
        f'<dsp:spPr><a:xfrm><a:off x="{i * 2743200}" y="0"/><a:ext cx="2377440" cy="731520"/>'
        '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill></dsp:spPr>'
        f'<dsp:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="{size * 100}">'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{font}"/>'
        f"</a:rPr><a:t>{word}</a:t></a:r></a:p></dsp:txBody></dsp:sp>"
        for i, word in enumerate(("Plan", "Build", "Run"))
    )
    ext = (
        f'<dgm:extLst><a:ext uri="{DSP_NS}"><dsp:dataModelExt xmlns:dsp="{DSP_NS}" '
        'relId="rIdDr"/></a:ext></dgm:extLst>'
    )
    parts = {
        "ppt/diagrams/data1.xml": f'<dgm:dataModel xmlns:dgm="{DGM_NS}" xmlns:a="{a}">'
        f"<dgm:ptLst/><dgm:cxnLst/>{ext if drawing else ''}</dgm:dataModel>"
    }
    rels = (
        '<Relationship Id="rIdDm" Type="http://schemas.openxmlformats.org/officeDocument/'
        '2006/relationships/diagramData" Target="../diagrams/data1.xml"/>'
    )
    if drawing:
        parts["ppt/diagrams/drawing1.xml"] = (
            f'<dsp:drawing xmlns:dsp="{DSP_NS}" xmlns:a="{a}"><dsp:spTree>'
            '<dsp:nvGrpSpPr><dsp:cNvPr id="0" name=""/><dsp:cNvGrpSpPr/></dsp:nvGrpSpPr>'
            f"<dsp:grpSpPr/>{boxes}</dsp:spTree></dsp:drawing>"
        )
        rels += (
            '<Relationship Id="rIdDr" Type="http://schemas.microsoft.com/office/2007/'
            'relationships/diagramDrawing" Target="../diagrams/drawing1.xml"/>'
        )
    frame = (
        '<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="300" name="Diagram 1" '
        'descr="Three-step delivery process: plan, build, run"/><p:cNvGraphicFramePr/>'
        '<p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="341986" y="4892040"/>'
        '<a:ext cx="7680960" cy="731520"/></p:xfrm><a:graphic>'
        f'<a:graphicData uri="{DGM_NS}"><dgm:relIds xmlns:dgm="{DGM_NS}" r:dm="rIdDm" '
        'r:lo="rIdLo" r:qs="rIdQs" r:cs="rIdCs"/></a:graphicData></a:graphic></p:graphicFrame>'
    )
    with zipfile.ZipFile(path) as zf:
        blobs = {n: zf.read(n) for n in zf.namelist()}
    slide2, slide2_rels = "ppt/slides/slide2.xml", "ppt/slides/_rels/slide2.xml.rels"
    blobs[slide2] = blobs[slide2].replace(b"</p:spTree>", frame.encode() + b"</p:spTree>", 1)
    blobs[slide2_rels] = blobs[slide2_rels].replace(
        b"</Relationships>", rels.encode() + b"</Relationships>"
    )
    blobs.update({n: v.encode() for n, v in parts.items()})
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for n, data in blobs.items():
            zf.writestr(n, data)
    return path


def move_slide(prs, old_index, new_index):
    ids = prs.slides._sldIdLst
    element = list(ids)[old_index]
    ids.remove(element)
    ids.insert(new_index, element)


# ---------------------------------------------------------------- the decks

COVER_TITLE = "Cards results, H1 2026"
TITLES = {
    2: "Card spend grew 14% on stronger travel demand",
    3: "Mobile users rose in every quarter of 2025",
    4: "Digital sales share climbed through 2025",
    5: "Interchange led fee income in 2025",
}
NBG_THEME = {
    "dk2": "003841",
    "lt2": "F5F8F6",
    "accent1": "00ADBF",
    "accent2": "003841",
    "accent3": "007B85",
    "accent4": "939793",
    "accent5": "BEC1BE",
    "accent6": "00DFF8",
    "hlink": "0D90FF",
    "folHlink": "59C3FF",
}


def golden_prs():
    """Six slides that satisfy every brand rule the validator checks."""
    prs = new_prs()

    s = blank(prs)  # 1 cover
    text(s, 0.374, 1.39, 12.0, 1.0, COVER_TITLE, size=48, color="003841")
    text(s, 0.374, 2.49, 12.0, 0.8, "Cards | Digital | Direct", size=24, color="007B85")
    text(s, 0.374, 4.58, 8.0, 0.4, "Athens", size=14, color="003841")
    text(s, 0.374, 4.97, 8.0, 0.4, "September 2026", size=14, color="5A5F5A")
    logo(s, "large")

    s = blank(prs)  # 2 content: pill, bullets, numbered badges
    pill(s, "Cards")
    title(s, TITLES[2], y=0.75)
    bullets(
        s,
        0.374,
        1.3,
        12.585,
        2.0,
        [
            "Travel spend rose 22% year on year",
            "Commercial banking cards grew faster than retail cards",
            "Thanks to the redesign, app ratings rose to 4.7",
        ],
    )
    for i in range(3):
        badge(s, 0.374, 3.6 + i * 0.5, str(i + 1))
        text(s, 0.8, 3.6 + i * 0.5, 11.0, 0.3, f"Priority {i + 1} is on track for December")
    logo(s, "small")
    page_number(s, 2)

    s = blank(prs)  # 3 bar chart
    title(s, TITLES[3])
    bar_chart(s)
    source(s)
    logo(s, "small")
    page_number(s, 3)

    s = blank(prs)  # 4 line chart
    title(s, TITLES[4])
    line_chart(s)
    source(s)
    logo(s, "small")
    page_number(s, 4)

    s = blank(prs)  # 5 table
    title(s, TITLES[5])
    table(
        s,
        [
            ["Fee line", "2024", "2025"],
            ["Interchange", "EUR 38M", "EUR 42M"],
            ["Annual fees", "EUR 15M", "EUR 18M"],
        ],
    )
    source(s)
    logo(s, "small")
    page_number(s, 5)

    s = blank(prs)  # 6 back cover
    logo(s, "back")
    return prs


def nbg_theme(xml: str) -> str:
    for slot, value in NBG_THEME.items():
        xml = re.sub(
            rf'(<a:{slot}>)<a:srgbClr val="[0-9A-Fa-f]{{6}}"/>',
            rf'\1<a:srgbClr val="{value}"/>',
            xml,
        )
    xml = xml.replace('<a:latin typeface="Calibri"/>', '<a:latin typeface="Aptos"/>')
    return re.sub(
        r"<a:effectStyleLst>.*?</a:effectStyleLst>",
        "<a:effectStyleLst>"
        + "<a:effectStyle><a:effectLst/></a:effectStyle>" * 3
        + "</a:effectStyleLst>",
        xml,
        flags=re.S,
    )


def patch_part(path: Path, part: str, edit) -> Path:
    """Rewrite one XML part of a saved deck in place; refuse an edit that changes nothing."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        blobs = {n: zf.read(n) for n in names}
    before = blobs[part].decode("utf-8")
    after = edit(before)
    assert after != before, f"{part}: the fixture edit changed nothing"
    blobs[part] = after.encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in names:
            zf.writestr(n, blobs[n])
    return path


def chart_part(path: Path, marker: bytes) -> str:
    with zipfile.ZipFile(path) as zf:
        for name in sorted(zf.namelist()):
            if re.match(r"ppt/charts/chart\d+\.xml$", name) and marker in zf.read(name):
                return name
    raise AssertionError(f"no chart part containing {marker!r}")


def save(prs, path: Path, *, theme=True) -> Path:
    prs.save(str(path))
    if theme:
        patch_part(path, "ppt/theme/theme1.xml", nbg_theme)
    return path


def deck(tmp_path, edit=None, *, theme=True, name="deck.pptx", patch=None):
    prs = golden_prs()
    if edit is not None:
        edit(prs)
    path = save(prs, tmp_path / name, theme=theme)
    for part, fn in (patch or {}).items():
        patch_part(path, part(path) if callable(part) else part, fn)
    return path


def results(path, only=None):
    return {r.name: r for r in nv.validate_presentation(str(path), only=only)}


def check(path, name):
    found = results(path, only=[name])
    assert name in found, f"no {name!r} check"
    return found[name]


def details(result):
    return "\n".join(result.details)


@pytest.fixture(autouse=True)
def _fallback_fonts(tmp_path_factory, monkeypatch):
    """Measure with the width table everywhere, so CI and a laptop agree."""
    empty = tmp_path_factory.mktemp("no-fonts")
    monkeypatch.setenv("DECKS_FONT_DIRS", str(empty))
    nv.reset_font_cache()


# ------------------------------------------------------------ the golden deck


@pytest.fixture(scope="module")
def golden(tmp_path_factory):
    return deck(tmp_path_factory.mktemp("golden"))


def test_the_golden_deck_passes_every_check_with_no_warnings(golden):
    found = results(golden)
    assert set(found) == set(nv.CHECK_NAMES)
    bad = {n: (r.status, r.details) for n, r in found.items() if r.status in ("fail", "warn")}
    assert not bad, bad
    skipped = {n for n, r in found.items() if r.status == "skipped"}
    assert skipped == set(PASS_CASES), skipped


@pytest.mark.parametrize("name", sorted(nv.CHECK_NAMES))
def test_every_check_examines_the_golden_deck_or_has_its_own_pass_fixture(name, golden, tmp_path):
    result = check(golden, name)
    if name in PASS_CASES:
        result = check(PASS_CASES[name](tmp_path), name)
    assert result.status == "pass", (result.status, result.message, result.details)
    assert result.examined and result.examined > 0, result.message


# --------------------------------------------------------- the FAIL fixtures


def _add(position, *args, **kwargs):
    return lambda prs: text(slide(prs, position), *args, **kwargs)


def _retitle(position, new_title, *, bold=None):
    def edit(prs):
        sld = slide(prs, position)
        shape = shape_with_text(sld, TITLES[position])
        run = shape.text_frame.paragraphs[0].runs[0]
        run.text = new_title
        if bold is not None:
            run.font.bold = bold

    return edit


def _remove_logo(position):
    def edit(prs):
        sld = slide(prs, position)
        for sh in list(sld.shapes):
            if sh.shape_type == 13:  # picture
                remove(sh)

    return edit


def _add_chart(kind, **kwargs):
    def edit(prs):
        sld = slide(prs, 2)
        bar_chart(sld, x=7.0, y=5.2, w=4.0, h=1.4, chart_type=kind, **kwargs)

    return edit


def _slides_case(tmp_path):
    path = tmp_path / "empty.pptx"
    new_prs().save(str(path))
    return path


def _dimensions_case(tmp_path):
    prs = golden_prs()
    prs.slide_width = Emu(12188952)  # Inches(13.33), a "Custom" slide size
    return save(prs, tmp_path / "dims.pptx")


def _dark_background(prs):
    fill = slide(prs, 3).background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(0x00, 0x38, 0x41)


def _shadow_patch(xml):
    return xml.replace(
        "<a:effectLst/>",
        '<a:effectLst><a:outerShdw blurRad="40000" dist="20000" dir="5400000">'
        '<a:srgbClr val="000000"><a:alpha val="38000"/></a:srgbClr></a:outerShdw></a:effectLst>',
        1,
    )


def _truncate_axis(xml):
    """Give the value axis an explicit minimum of 30 (replacing a zero minimum)."""
    head, sep, tail = xml.partition("<c:valAx>")
    if re.search(r'<c:min val="[^"]*"/>', tail.split("</c:valAx>", 1)[0]):
        tail = re.sub(r'<c:min val="[^"]*"/>', '<c:min val="30"/>', tail, count=1)
    elif "<c:scaling/>" in tail:
        tail = tail.replace("<c:scaling/>", '<c:scaling><c:min val="30"/></c:scaling>', 1)
    else:
        tail = tail.replace("<c:scaling>", '<c:scaling><c:min val="30"/>', 1)
    return head + sep + tail


def _replace_line_chart(**kwargs):
    def edit(prs):
        sld = slide(prs, 4)
        remove(sld.shapes[1])
        line_chart(sld, **kwargs)

    return edit


def _replace_bar_chart(**kwargs):
    def edit(prs):
        sld = slide(prs, 3)
        remove(sld.shapes[1])
        bar_chart(sld, **kwargs)

    return edit


BANK_FILES = {
    "nbg": "nbg.png",
    "eurobank": "eurobank.png",
    "alpha": "alpha-bank.png",
    "piraeus": "piraeus-bank.png",
}


def _bank_slide(
    prs, *, colored, logos, categories=("NBG", "Eurobank", "Alpha", "Piraeus"), pictures=None
):
    sld = blank(prs)
    title(sld, "NBG leads peers on mobile adoption")
    keys = ("nbg", "eurobank", "alpha", "piraeus")
    bar_chart(
        sld,
        h=4.0,
        categories=categories,
        series=(("Active mobile users (%)", (62, 55, 51, 49)),),
        point_colors=[PEERS[k] for k in keys] if colored else None,
        alt="Column chart of active mobile users by bank: NBG 62%, Eurobank 55%, Alpha 51%, Piraeus 49%.",
    )
    if logos:
        if pictures is None:
            pictures = [(BANK_LOGOS / BANK_FILES[k], f"{k.title()} logo") for k in keys]
        for i, (path, alt) in enumerate(pictures):
            pic = sld.shapes.add_picture(
                str(path), inch(1.6 + i * 3.1), inch(5.45), height=inch(0.35)
            )
            set_alt(pic, alt)
    source(sld, "Source: bank annual reports, 2025")
    logo(sld, "small")
    page_number(sld, len(prs.slides))
    move_slide(prs, len(prs.slides) - 1, len(prs.slides) - 2)  # keep the back cover last
    return sld


def _bank_case(tmp_path, *, colored=True, logos=True, pictures=None):
    return deck(
        tmp_path,
        lambda prs: _bank_slide(prs, colored=colored, logos=logos, pictures=pictures),
        name="banks.pptx",
    )


FAIL_CASES = {
    "Slides": _slides_case,
    "Dimensions": _dimensions_case,
    "Theme": lambda tmp: deck(tmp, theme=False),
    "Background": lambda tmp: deck(tmp, _dark_background),
    "Colors": lambda tmp: deck(
        tmp, _add(2, 0.374, 5.3, 6.0, 0.4, "Off palette text", color="FF0000")
    ),
    "Fonts": lambda tmp: deck(
        tmp, _add(2, 0.374, 5.3, 6.0, 0.4, "Wrong typeface", font="Comic Sans MS")
    ),
    "Font Sizes": lambda tmp: deck(
        tmp, _add(2, 0.374, 5.3, 6.0, 0.4, "Body text at nine points", size=9)
    ),
    "Contrast": lambda tmp: deck(tmp, _add(2, 0.374, 5.3, 6.0, 0.4, "Invisible", color="F5F8F6")),
    "Boundaries": lambda tmp: deck(tmp, _add(2, 12.0, 5.3, 2.0, 0.4, "Past the edge")),
    "Safe Zones": lambda tmp: deck(tmp, _add(2, 0.374, 6.4, 6.0, 0.8, "Into the footer")),
    # The old builder's body position on a slide without a pill: 1.1", under the
    # 1.3" floor. A box this tall is body, never the one-line subtitle allowance.
    "Content Spacing": lambda tmp: deck(
        tmp, _add(3, 0.374, 1.1, 6.0, 1.0, ["Crowds the title", "and the second line too"])
    ),
    "Text Fit": lambda tmp: deck(
        tmp, _add(2, 0.374, 5.2, 4.0, 0.3, " ".join(["Overflowing words keep coming"] * 12))
    ),
    "Text Margins": lambda tmp: deck(
        tmp, _add(2, 0.374, 5.3, 6.0, 0.4, "Default insets", insets=0.1)
    ),
    "Logo": lambda tmp: deck(tmp, _remove_logo(3)),
    "Back Cover": lambda tmp: deck(tmp, lambda prs: page_number(slide(prs, 6), 6)),
    "Thank You Check": lambda tmp: deck(tmp, _add(5, 0.374, 3.0, 6.0, 0.6, "Thank you", size=28)),
    "Decorative": lambda tmp: deck(
        tmp,
        lambda prs: box(slide(prs, 2), 10.0, 4.0, 1.5, 1.5, "00ADBF", shape=MSO_SHAPE.STAR_5_POINT),
    ),
    "Shadows": lambda tmp: deck(tmp, patch={"ppt/slides/slide2.xml": _shadow_patch}),
    "Em Dashes": lambda tmp: deck(
        tmp, _add(2, 0.374, 5.3, 8.0, 0.4, f"Growth came from mobile {EM_DASH} not branches")
    ),
    "Title Style": lambda tmp: deck(tmp, _retitle(3, TITLES[3], bold=True)),
    "Title Length": lambda tmp: deck(
        tmp,
        _retitle(
            3,
            "Mobile users rose in every quarter of 2025 as the redesign lifted adoption in all segments",
        ),
    ),
    "Slide Titles": lambda tmp: deck(tmp, _retitle(4, TITLES[3])),
    "Action Titles": lambda tmp: deck(tmp, _retitle(3, "Overview")),
    "Chart Types": lambda tmp: deck(
        tmp, _add_chart(XL_CHART_TYPE.PIE, alt="Pie chart of fee income by line.")
    ),
    "Chart Data": lambda tmp: deck(
        tmp,
        _add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            series=tuple((f"Series {i}", (1 + i, 2, 3, 4)) for i in range(10)),
            alt="Column chart with ten series.",
        ),
    ),
    "Chart Styling": lambda tmp: deck(tmp, _replace_line_chart(explicit_line=False)),
    "Zero Baseline": lambda tmp: deck(
        tmp, patch={(lambda p: chart_part(p, b"barChart")): _truncate_axis}
    ),
    "Exhibit Sources": lambda tmp: deck(
        tmp, lambda prs: remove(shape_with_text(slide(prs, 3), "Source"))
    ),
    "Alt Text": lambda tmp: deck(tmp, lambda prs: set_alt(slide(prs, 3).shapes[1], "")),
    "Bank Branding": lambda tmp: _bank_case(tmp, colored=False),
    "Number Formats": lambda tmp: deck(
        tmp, _add(2, 0.374, 5.3, 8.0, 0.4, "EUR 1,250,000 in new interchange")
    ),
    "AI Slop": lambda tmp: deck(
        tmp,
        _add(
            2, 0.374, 5.3, 12.0, 0.4, "We leverage a seamless platform, and studies show it works"
        ),
    ),
    "Official Name": lambda tmp: deck(
        tmp, _add(2, 0.374, 5.3, 8.0, 0.4, "Εθνική Τράπεζα της Ελλάδος")
    ),
    "OOXML Order": lambda tmp: deck(
        tmp,
        lambda prs: bullets(
            slide(prs, 2), 7.0, 5.2, 5.5, 1.0, ["Out of order bullet"], order="builder"
        ),
    ),
}

# Checks the golden deck cannot examine: each gets a deck built to pass it.
PASS_CASES = {
    "Bank Branding": lambda tmp: _bank_case(tmp),
}

WARNING_CHECKS = {"Theme", "Action Titles", "Number Formats", "AI Slop", "Official Name"}


def test_every_registered_check_has_a_fail_fixture():
    assert set(FAIL_CASES) == set(nv.CHECK_NAMES), set(nv.CHECK_NAMES) ^ set(FAIL_CASES)


@pytest.mark.parametrize("name", sorted(FAIL_CASES))
def test_fail_fixture(name, tmp_path):
    result = check(FAIL_CASES[name](tmp_path), name)
    expected = "warn" if name in WARNING_CHECKS else "fail"
    assert result.status == expected, (result.status, result.message, result.details)
    assert result.findings, result.message
    assert result.examined is not None and result.examined >= (0 if name == "Slides" else 1)


def test_the_registry_severities_match_the_warning_set():
    declared = {spec.name for spec in nv.CHECKS if spec.severity == "warning"}
    assert declared == WARNING_CHECKS


# ------------------------------------------- regressions: false positives


def test_decorative_accepts_numbered_badges_arrows_and_chevrons(tmp_path):
    """VALIDATOR-1: the documented 0.28" numbered oval badge blocked the build."""

    def edit(prs):
        sld = slide(prs, 2)
        box(sld, 10.0, 4.0, 0.4, 0.4, "939793", shape=MSO_SHAPE.ISOSCELES_TRIANGLE)
        box(sld, 10.6, 4.0, 0.6, 0.4, "007B85", shape=MSO_SHAPE.CHEVRON)
        box(sld, 11.4, 4.0, 0.6, 0.4, "007B85", shape=MSO_SHAPE.RIGHT_ARROW)

    result = check(deck(tmp_path, edit), "Decorative")
    assert result.status == "pass", result.details
    assert result.examined >= 7  # pill + 3 badges + 3 arrow shapes


def test_decorative_names_now_match_real_presets(tmp_path):
    """'star' and 'oval' could never match: the presets are star5 and ellipse."""
    blob = deck(
        tmp_path,
        lambda prs: box(slide(prs, 2), 9.0, 3.6, 1.2, 1.2, "E6F5F6", shape=MSO_SHAPE.OVAL),
    )
    result = check(blob, "Decorative")
    assert result.status == "fail"
    assert "ellipse" in details(result) and "Slide 2" in details(result)
    star = check(FAIL_CASES["Decorative"](tmp_path), "Decorative")
    assert "star5" in details(star)


def test_thank_you_ignores_commercial_thanks_to_and_an_agenda_q_and_a(tmp_path):
    """VALIDATOR-2 / BRAND-SSOT-11: 'commercial' failed as 'merci'. The golden deck
    already says 'Commercial banking' and 'Thanks to the redesign' on slide 2; the
    agenda below is a short slide, which makes it a closing candidate."""

    def edit(prs):
        sld = blank(prs)
        title(sld, "Agenda for today")
        bullets(sld, 0.374, 1.3, 6.0, 1.5, ["Results", "Priorities", "Q&A"])
        logo(sld, "small")
        page_number(sld, 7)
        move_slide(prs, 6, 1)

    result = check(deck(tmp_path, edit), "Thank You Check")
    assert result.status == "pass", result.details


def test_thank_you_catches_an_accented_greek_closing(tmp_path):
    """VALIDATOR-2: 'Ευχαριστούμε' passed because the list was unaccented."""
    closing = deck(tmp_path, _add(5, 0.374, 3.0, 8.0, 0.6, "Ευχαριστούμε! Ερωτήσεις;", size=28))
    result = check(closing, "Thank You Check")
    assert result.status == "fail"
    assert "Slide 5" in details(result)
    assert "Ευχαριστούμε" in details(result)  # reported as written, not folded


def test_thank_you_catches_a_q_and_a_title_on_the_closing_slide(tmp_path):
    def edit(prs):
        sld = blank(prs)
        title(sld, "Q&A")
        logo(sld, "small")
        move_slide(prs, 6, 5)

    result = check(deck(tmp_path, edit), "Thank You Check")
    assert result.status == "fail", result.details


def test_the_builder_contents_slide_is_not_a_spacing_failure(tmp_path):
    """VALIDATOR-3(a): 'Contents' at y=0.40 was read as first content above the title."""

    def edit(prs):
        sld = blank(prs)
        text(sld, 0.374, 0.40, 10.0, 0.5, "Contents", size=24, color="003841")
        for i, section in enumerate(("Results", "Digital", "Priorities")):
            y = 1.48 + i * 0.85
            text(sld, 0.374, y, 0.8, 0.4, f"0{i + 1}", size=18, color="007B85")
            text(sld, 1.174, y, 8.0, 0.35, section, size=16, color="003841")
        logo(sld, "small")
        move_slide(prs, 6, 1)

    found = results(deck(tmp_path, edit), only=["Content Spacing", "Slide Titles", "Title Style"])
    for name, result in found.items():
        assert result.status == "pass", (name, result.details)


def _key_figures(prs, section, kpis):
    sld = blank(prs)
    pill(sld, "Cards", y=0.45, w=1.5, h=0.4, size=16, fill="003841")
    text(sld, 2.0, 0.48, 5.0, 0.38, section, size=22, color="003841")
    text(sld, 0.374, 1.05, 4.0, 0.3, "Unit head: the team", size=14, color="5A5F5A")
    for cx, (value, caption) in zip((1.01, 4.92, 8.81), kpis, strict=True):
        box(sld, cx, 2.15, 3.5, 3.0, "F5F8F6")
        text(
            sld,
            cx,
            2.65,
            3.5,
            1.0,
            value,
            size=50,
            bold=True,
            color="007B85",
            align=PP_ALIGN.CENTER,
        )
        text(sld, cx + 0.3, 3.85, 2.9, 0.8, caption, size=16, color="5A5F5A", align=PP_ALIGN.CENTER)
    logo(sld, "small")
    return sld


def test_key_figures_pages_are_titled_by_their_section_title_not_the_kpi(tmp_path):
    """VALIDATOR-3(b): the 22pt title fell under 24pt, so the 50pt '26%' became the
    title and two Key Figures pages with the same first KPI 'duplicated'."""

    def edit(prs):
        _key_figures(
            prs,
            "Key figures for cards",
            [("26%", "Market share"), ("750K", "Live cards"), ("€70M", "Fees")],
        )
        _key_figures(
            prs,
            "Key figures for digital",
            [("26%", "Digital share"), ("3.3M", "Active users"), ("500K", "Sales")],
        )
        move_slide(prs, 7, 5)
        move_slide(prs, 6, 5)

    path = deck(tmp_path, edit)
    found = results(path, only=["Slide Titles", "Content Spacing", "Title Style"])
    for name, result in found.items():
        assert result.status == "pass", (name, result.details)
    with nv.load_deck(path) as loaded:
        found_titles = [nv.find_title(s) for s in loaded.slides]
    texts = [t.text if t else None for t in found_titles]
    assert "Key figures for cards" in texts and "Key figures for digital" in texts
    assert "26%" not in texts


def test_placeholder_titles_are_found(tmp_path):
    """VALIDATOR-3(c): titles in a layout placeholder carry no xfrm or size of their
    own, and every slide of a PowerPoint-made deck failed 'no title'."""
    prs = new_prs()
    for heading in (
        "Revenue grew on stronger fee income",
        "Costs fell as digital migration continued",
    ):
        sld = prs.slides.add_slide(prs.slide_layouts[5])  # Title Only
        sld.shapes.title.text = heading
        text(sld, 0.374, 2.0, 8.0, 1.0, "Body text here")
    path = save(prs, tmp_path / "placeholders.pptx")
    found = results(path, only=["Slide Titles", "Title Length", "Action Titles"])
    assert found["Slide Titles"].status == "pass", found["Slide Titles"].details
    assert found["Slide Titles"].examined == 2
    assert found["Title Length"].examined == 2
    assert found["Action Titles"].examined == 2


def test_an_off_anchor_title_is_still_examined(tmp_path):
    """VALIDATOR-3(d): a 26-word title at y=0.62 was unexamined by Title Length and
    Action Titles and misreported as a spacing defect."""
    long_title = (
        "Digital channels exceeded every target we set for the year, driven by mobile "
        "adoption, sales migration and lower cost to serve across all retail segments"
    )

    def edit(prs):
        shape = shape_with_text(slide(prs, 3), TITLES[3])
        shape.top = inch(0.62)
        shape.height = inch(0.9)
        shape.text_frame.paragraphs[0].runs[0].text = long_title

    found = results(deck(tmp_path, edit), only=["Title Length", "Action Titles"])
    assert found["Title Length"].status == "fail"
    assert found["Action Titles"].status == "warn"
    assert "Slide 3" in details(found["Title Length"])


def test_banking_vocabulary_is_not_ai_slop(tmp_path):
    """VALIDATOR-9: 'leverage ratio' and 'robust capital base' are Basel language."""
    path = deck(
        tmp_path,
        _add(
            2,
            0.374,
            5.3,
            12.0,
            0.4,
            "Leverage ratio of 5.2% reflects a robust capital base; unlock the card in the app",
        ),
    )
    result = check(path, "AI Slop")
    assert result.status == "pass", result.details


def test_ai_slop_is_a_warning_that_never_blocks(tmp_path):
    result = check(FAIL_CASES["AI Slop"](tmp_path), "AI Slop")
    assert result.status == "warn" and result.severity == "warning"
    assert "'leverage'" in details(result) and "'seamless'" in details(result)


def test_an_alpha_release_is_not_a_bank_comparison(tmp_path):
    """VALIDATOR-9: 'alpha' matched inside any sentence and 'NBG' made it two banks."""
    path = deck(
        tmp_path,
        _add(2, 0.374, 5.3, 12.0, 0.4, "NBG app alpha release reached 2,000 staff testers"),
    )
    result = check(path, "Bank Branding")
    assert result.status == "skipped", result.details


def test_white_text_on_a_separately_drawn_chip_is_readable(tmp_path):
    """VALIDATOR-8: contrast was measured against the slide, not the shape underneath."""

    def edit(prs):
        sld = slide(prs, 2)
        box(sld, 7.0, 5.2, 2.0, 0.5, "003841")
        text(sld, 7.1, 5.3, 1.8, 0.3, "Delivered", size=16, bold=True, color="FFFFFF")

    result = check(deck(tmp_path, edit), "Contrast")
    assert result.status == "pass", result.details


def test_dark_text_on_a_dark_card_is_caught(tmp_path):
    def edit(prs):
        sld = slide(prs, 2)
        box(sld, 7.0, 5.2, 2.0, 0.5, "003841")
        text(sld, 7.1, 5.3, 1.8, 0.3, "Invisible", size=14, color="003841")

    result = check(deck(tmp_path, edit), "Contrast")
    assert result.status == "fail"
    assert "#003841 on #003841" in details(result)


def _stacked(white_on_dark: bool):
    def edit(prs):
        sld = slide(prs, 3)
        remove(sld.shapes[1])
        frame = bar_chart(
            sld,
            chart_type=XL_CHART_TYPE.COLUMN_STACKED,
            series=(("Mobile", (40, 45, 50, 55)), ("Web", (35, 32, 30, 28))),
        )
        frame.chart.plots[0].data_labels.font.color.rgb = RGBColor.from_string("202020")
        if white_on_dark:
            web = frame.chart.plots[0].series[1]
            for i in range(4):
                label = web.points[i].data_label
                label.font.size = Pt(12)
                label.font.bold = True
                label.font.color.rgb = RGBColor.from_string("FFFFFF")

    return edit


def test_stacked_labels_are_measured_against_their_own_bar(tmp_path):
    """Stacked labels sit on the bar: #202020 on dark teal is 1.27:1."""
    result = check(deck(tmp_path, _stacked(False)), "Contrast")
    assert result.status == "fail"
    assert "#202020 on #003841" in details(result)


def test_a_per_point_label_colour_overrides_the_series_labels(tmp_path):
    """The builder colours each label against its own fill through c:dLbl."""
    result = check(deck(tmp_path, _stacked(True)), "Contrast")
    assert result.status == "pass", result.details


def _carrier(label_color):
    """A stacked chart whose second series is an invisible label carrier (a:noFill),
    as nbg_build's waterfall step labels are: inside labels on nothing."""

    def edit(prs):
        sld = slide(prs, 3)
        remove(sld.shapes[1])
        frame = bar_chart(
            sld,
            chart_type=XL_CHART_TYPE.COLUMN_STACKED,
            series=(("Value", (40, 45, 50, 55)), ("Labels", (5, 5, 5, 5))),
        )
        plot = frame.chart.plots[0]
        plot.series[1].format.fill.background()
        labels = plot.series[1].data_labels
        labels.show_value = True
        labels.position = XL_LABEL_POSITION.INSIDE_BASE
        labels.font.size = Pt(12)
        labels.font.bold = True
        labels.font.color.rgb = RGBColor.from_string(label_color)

    return edit


def test_labels_inside_an_unfilled_carrier_series_are_measured_against_the_slide(tmp_path):
    """They draw on whatever is behind the chart, so they are measured, not skipped:
    white labels can only fail as white on white if they were measured at all."""
    dark = check(deck(tmp_path, _carrier("202020"), name="dark.pptx"), "Contrast")
    assert dark.status == "pass", dark.details
    white = check(deck(tmp_path, _carrier("FFFFFF"), name="white.pptx"), "Contrast")
    assert white.status == "fail" and "#FFFFFF on #FFFFFF" in details(white)
    assert "series 'Labels'" in details(white)


def test_a_valueless_chart_delete_flag_means_deleted(golden):
    """<c:delete/> with no val is true by the schema; python-pptx writes exactly that
    for a hidden axis, so the golden bar chart's value axis has no labels to measure."""
    with nv.load_deck(golden) as loaded:
        chart = next(c for c in loaded.charts() if b"barChart" in loaded.pkg.read(c.part))
        value_axis = loaded.pkg.read(chart.part).decode().split("<c:valAx>", 1)[1]
        assert "<c:delete/>" in value_axis.split("</c:valAx>", 1)[0]
        whats = [row[2] for row in nv._chart_text_rows(chart, "FFFFFF")]
    assert "valAx labels" not in whats and "catAx labels" in whats


def test_a_deck_that_opens_on_a_content_slide_is_not_told_its_cover_needs_the_large_logo(tmp_path):
    def edit(prs):
        move_slide(prs, 0, 5)  # the cover moves to the end, a content slide leads
        move_slide(prs, 4, 5)  # and the back cover stays last

    result = check(deck(tmp_path, edit), "Logo")
    assert "large logo" not in details(result)


def test_the_muted_grey_waiver_covers_page_numbers_and_axis_labels_only(tmp_path, golden):
    """VALIDATOR-8 / BRAND-SSOT-10: the 939793 waiver applied to any text anywhere.

    The golden deck keeps 939793 on its page numbers and on the line chart's value axis,
    both waived. Body copy and the cover date in 939793 are not: the cover date is
    caption grey (lead's decision, 2026-09-23)."""
    golden_contrast = check(golden, "Contrast")
    assert golden_contrast.status == "pass" and "waived" in golden_contrast.message
    body = check(
        deck(tmp_path, _add(2, 0.374, 5.3, 6.0, 0.4, "Grey body copy", color="939793")), "Contrast"
    )
    assert body.status == "fail"
    assert "939793" in details(body) and "Slide 2" in details(body)

    def grey_date(prs):
        shape = shape_with_text(slide(prs, 1), "September 2026")
        shape.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string("939793")

    date = check(deck(tmp_path, grey_date, name="date.pptx"), "Contrast")
    assert date.status == "fail" and "Slide 1" in details(date)


def test_a_pill_drawn_as_a_shape_plus_a_text_box_is_the_pill(tmp_path):
    """VALIDATOR-7: the 9pt allowance only knew nbg_build's single-shape pill."""

    def edit(prs):
        sld = slide(prs, 3)
        box(sld, 0.374, 0.12, 1.0, 0.25, "007B85", shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        text(sld, 0.474, 0.16, 0.8, 0.17, "MOBILE", size=9, bold=True, color="FFFFFF")

    found = results(deck(tmp_path, edit), only=["Font Sizes", "Contrast", "Content Spacing"])
    for name, result in found.items():
        assert result.status == "pass", (name, result.details)


def test_a_private_spec_pill_above_the_title_is_header_chrome(tmp_path):
    def edit(prs):
        sld = slide(prs, 3)
        pill(sld, "Mobile", y=0.193, h=0.307, size=12)
        shape_with_text(sld, TITLES[3]).top = inch(0.62)

    result = check(deck(tmp_path, edit), "Content Spacing")
    assert result.status == "pass", result.details


# ------------------------------------------- regressions: false negatives


def test_colors_read_chart_parts(tmp_path):
    """VALIDATOR-4 / ASSETS-CI-4: an FF0000 series passed 'All 8 colors in palette'."""
    result = check(deck(tmp_path, _replace_bar_chart(colors=("FF0000",))), "Colors")
    assert result.status == "fail"
    assert "FF0000" in details(result) and "chart" in details(result)


def test_retired_colours_fail_with_their_reason(tmp_path):
    path = deck(tmp_path, _add(2, 0.374, 5.3, 6.0, 0.4, "Old caption grey", color="595959"))
    result = check(path, "Colors")
    assert result.status == "fail"
    assert "retired caption grey" in details(result)


def test_fonts_read_chart_parts_and_forbid_semibold(tmp_path):
    chart_font = deck(tmp_path, _replace_bar_chart(font="Comic Sans MS"), name="chartfont.pptx")
    result = check(chart_font, "Fonts")
    assert result.status == "fail" and "Comic Sans MS" in details(result)
    semibold = check(
        deck(tmp_path, _add(2, 0.374, 5.3, 6.0, 0.4, "Heavy", font="Aptos SemiBold")), "Fonts"
    )
    assert semibold.status == "fail" and "Aptos SemiBold" in details(semibold)


def test_font_sizes_read_chart_text(tmp_path):
    """VALIDATOR-4: 7pt chart data labels passed."""
    result = check(deck(tmp_path, _replace_bar_chart(label_size=7)), "Font Sizes")
    assert result.status == "fail"
    assert "7" in details(result) and "chart" in details(result)


def test_the_8pt_footnote_allowance_is_gone(tmp_path):
    """PROMPTS-10 / BRAND-SSOT-10: 8pt was still accepted near the bottom of a slide."""
    path = deck(
        tmp_path, _add(3, 0.374, 5.95, 8.0, 0.2, "Note: restated for the 2025 change", size=8)
    )
    result = check(path, "Font Sizes")
    assert result.status == "fail" and "8" in details(result)


def test_sources_and_footnotes_need_11pt(tmp_path):
    def edit(prs):
        remove(shape_with_text(slide(prs, 3), "Source"))
        source(slide(prs, 3), size=10)

    result = check(deck(tmp_path, edit), "Font Sizes")
    assert result.status == "fail"
    assert "11" in details(result) and "Slide 3" in details(result)


def test_charts_and_tables_count_for_boundaries_and_safe_zones(tmp_path):
    """VALIDATOR-5: graphic frames were invisible; a chart at 7.2" passed."""

    def edit(prs):
        sld = slide(prs, 3)
        remove(sld.shapes[1])
        bar_chart(sld, h=5.9)  # bottom edge at 7.2"
        frame = slide(prs, 5).shapes[1]
        frame.left = inch(1.5)  # table right edge at 14.085"

    found = results(deck(tmp_path, edit), only=["Safe Zones", "Boundaries"])
    assert found["Safe Zones"].status == "fail"
    assert "Slide 3" in details(found["Safe Zones"]) and "Slide 5" in details(found["Safe Zones"])
    assert found["Boundaries"].status == "fail"
    assert "Slide 5" in details(found["Boundaries"])


def test_the_horizontal_gutter_is_enforced(tmp_path):
    result = check(deck(tmp_path, _add(2, 0.05, 5.3, 6.0, 0.4, "Left of the gutter")), "Safe Zones")
    assert result.status == "fail"
    assert "gutter" in details(result)


def test_sources_end_at_the_content_floor(tmp_path):
    def edit(prs):
        remove(shape_with_text(slide(prs, 3), "Source"))
        source(slide(prs, 3), y=6.55)

    result = check(deck(tmp_path, edit), "Safe Zones")
    assert result.status == "fail"
    assert "6.5" in details(result)


def test_a_dark_slide_background_fails(tmp_path):
    result = check(FAIL_CASES["Background"](tmp_path), "Background")
    assert result.status == "fail"
    assert "003841" in details(result) and "Slide 3" in details(result)


def test_an_inherited_dark_layout_background_fails(tmp_path):
    dark = (
        '<p:bg><p:bgPr><a:solidFill><a:srgbClr val="003841"/></a:solidFill>'
        "<a:effectLst/></p:bgPr></p:bg>"
    )
    path = deck(
        tmp_path,
        patch={
            "ppt/slideLayouts/slideLayout7.xml": lambda x: x.replace(
                '<p:cSld name="Blank">', f'<p:cSld name="Blank">{dark}'
            )
        },
    )
    result = check(path, "Background")
    assert result.status == "fail"
    assert "layout" in details(result)


def test_em_dashes_in_chart_text_fail_and_spaced_en_dashes_warn(tmp_path):
    chart = deck(
        tmp_path,
        _replace_bar_chart(categories=(f"Q1 {EM_DASH} old", "Q2", "Q3", "Q4")),
        name="dash-chart.pptx",
    )
    result = check(chart, "Em Dashes")
    assert result.status == "fail" and "chart" in details(result)
    spaced = check(
        deck(
            tmp_path, _add(2, 0.374, 5.3, 8.0, 0.4, f"Costs fell {EN_DASH} again"), name="en.pptx"
        ),
        "Em Dashes",
    )
    assert spaced.status == "warn"
    ranges = check(
        deck(tmp_path, _add(2, 0.374, 5.3, 8.0, 0.4, f"Plan for 2024{EN_DASH}2025"), name="r.pptx"),
        "Em Dashes",
    )
    assert ranges.status == "pass"


def test_title_style_catches_bold_off_gutter_and_a_trailing_period(tmp_path):
    bold = check(FAIL_CASES["Title Style"](tmp_path), "Title Style")
    assert bold.status == "fail" and "bold" in details(bold)

    def off_gutter(prs):
        shape_with_text(slide(prs, 3), TITLES[3]).left = inch(1.2)

    moved = check(deck(tmp_path, off_gutter, name="gutter.pptx"), "Title Style")
    assert moved.status == "fail" and "0.374" in details(moved)
    period = check(deck(tmp_path, _retitle(3, TITLES[3] + "."), name="period.pptx"), "Title Style")
    assert period.status == "warn" and "period" in details(period)


def test_title_style_exempts_the_divider_title_beside_its_number(tmp_path):
    def edit(prs):
        sld = blank(prs)
        text(sld, 0.374, 2.84, 1.2, 1.0, "01", size=60, color="007B85")
        text(sld, 1.574, 2.84, 9.5, 1.0, "Digital results", size=48, color="003841")
        logo(sld, "large")
        move_slide(prs, 6, 1)

    found = results(deck(tmp_path, edit), only=["Title Style", "Slide Titles", "Logo"])
    for name, result in found.items():
        assert result.status == "pass", (name, result.details)


def test_back_cover_extras_fail(tmp_path):
    """VALIDATOR-10: an emblem plus a page number plus a corner logo passed."""

    def edit(prs):
        page_number(slide(prs, 6), 6)
        logo(slide(prs, 6), "small")

    result = check(deck(tmp_path, edit), "Back Cover")
    assert result.status == "fail"
    assert "Slide 6" in details(result) and "picture" in details(result)


def test_slide_order_comes_from_the_slide_list_not_file_names(tmp_path):
    """VALIDATOR-15: reordering moved the back cover without the checks noticing."""
    found = results(deck(tmp_path, lambda prs: move_slide(prs, 5, 0)), only=["Back Cover", "Logo"])
    back = found["Back Cover"]
    assert back.status == "fail"
    assert "Slide 6" in details(back), details(back)
    assert found["Logo"].status == "fail"
    assert "Slide 1" in details(found["Logo"])


def test_any_picture_is_no_longer_a_logo(tmp_path):
    """VALIDATOR-10: a screenshot and no NBG logo passed 'Logo'."""

    def edit(prs):
        _remove_logo(3)(prs)
        pic = slide(prs, 3).shapes.add_picture(
            str(BANK_LOGOS / "eurobank.png"), inch(9), inch(2), inch(1), inch(1)
        )
        set_alt(pic, "Eurobank logo")

    result = check(deck(tmp_path, edit), "Logo")
    assert result.status == "fail" and "Slide 3" in details(result)


def test_logo_aspect_language_and_size_by_slide_type(tmp_path):
    stretched = deck(
        tmp_path, lambda prs: (_remove_logo(3)(prs), logo(slide(prs, 3), w=1.4)), name="s.pptx"
    )
    assert "stretched" in details(check(stretched, "Logo"))
    english = deck(
        tmp_path,
        lambda prs: (_remove_logo(3)(prs), logo(slide(prs, 3), path=ENGLISH_LOGO, h=0.822 / 4.74)),
        name="english.pptx",
    )
    assert "Greek" in details(check(english, "Logo"))
    small_cover = deck(
        tmp_path, lambda prs: (_remove_logo(1)(prs), logo(slide(prs, 1))), name="cover.pptx"
    )
    assert "large" in details(check(small_cover, "Logo"))


def test_the_pie_family_fails(tmp_path):
    def pie3d(xml):
        return xml.replace("<c:pieChart>", "<c:pie3DChart>").replace(
            "</c:pieChart>", "</c:pie3DChart>"
        )

    path = FAIL_CASES["Chart Types"](tmp_path)
    patch_part(path, chart_part(path, b"pieChart"), pie3d)
    result = check(path, "Chart Types")
    assert result.status == "fail" and "pie3DChart" in details(result)


def test_a_doughnut_is_the_sanctioned_part_to_whole_chart(tmp_path):
    path = deck(
        tmp_path, _add_chart(XL_CHART_TYPE.DOUGHNUT, alt="Doughnut chart of fee income by line.")
    )
    assert check(path, "Chart Types").status == "pass"


def test_chart_series_ceiling_warns_past_six_and_fails_past_eight(tmp_path):
    seven = deck(
        tmp_path,
        _add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            series=tuple((f"S{i}", (1, 2, 3, 4)) for i in range(7)),
            alt="Column chart with seven series.",
        ),
        name="seven.pptx",
    )
    assert check(seven, "Chart Data").status == "warn"
    assert check(FAIL_CASES["Chart Data"](tmp_path), "Chart Data").status == "fail"


def test_a_chart_with_no_categories_fails(tmp_path):
    def empty(xml):
        return re.sub(r"<c:cat>.*?</c:cat>", "", xml, flags=re.S)

    path = deck(tmp_path, patch={(lambda p: chart_part(p, b"barChart")): empty})
    result = check(path, "Chart Data")
    assert result.status == "fail" and "categor" in details(result)


def test_line_series_without_an_explicit_line_fall_back_to_theme_colours(tmp_path):
    """ASSETS-CI-4: the shipped quarterly-report line chart rendered Office blue and red."""
    result = check(FAIL_CASES["Chart Styling"](tmp_path), "Chart Styling")
    assert result.status == "fail"
    assert "line" in details(result)


def test_markers_that_are_not_hollow_circles_warn(tmp_path):
    result = check(deck(tmp_path, _replace_line_chart(markers="auto")), "Chart Styling")
    assert result.status == "warn" and "marker" in details(result)


def test_automatic_series_colours_resolve_through_the_theme(tmp_path):
    unstyled = _replace_bar_chart(styled=False)
    assert check(deck(tmp_path, unstyled, name="nbg.pptx"), "Chart Styling").status == "pass"
    office = check(deck(tmp_path, unstyled, theme=False, name="office.pptx"), "Chart Styling")
    assert office.status == "fail" and "4F81BD" in details(office)


def test_the_office_theme_warns(tmp_path):
    result = check(FAIL_CASES["Theme"](tmp_path), "Theme")
    assert result.status == "warn"
    assert "4F81BD" in details(result) and "Calibri" in details(result)


def test_shadows_inherited_from_the_theme_fail(tmp_path):
    """VALIDATOR-10: an autoshape's effectRef picks up the Office theme's shadow."""

    def edit(prs):
        shape = slide(prs, 2).shapes.add_shape(
            MSO_SHAPE.RECTANGLE, inch(9), inch(5.2), inch(1), inch(0.5)
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string("F5F8F6")
        shape.line.fill.background()

    assert check(deck(tmp_path, edit, name="nbg.pptx"), "Shadows").status == "pass"
    office = check(deck(tmp_path, edit, theme=False, name="office.pptx"), "Shadows")
    assert office.status == "fail" and "theme" in details(office)


def test_uppercase_greek_source_labels_count(tmp_path):
    """VALIDATOR-13: 'ΠΗΓΗ:' drops the accent and did not match 'πηγή'."""

    def edit(prs):
        remove(shape_with_text(slide(prs, 3), "Source"))
        source(slide(prs, 3), "ΠΗΓΗ: ΤτΕ, 2025")

    result = check(deck(tmp_path, edit), "Exhibit Sources")
    assert result.status == "pass", result.details


def test_greek_number_formats_are_read_as_greek(tmp_path):
    """VALIDATOR-13: '€1.250.000' was read as 3 decimals and '€2,3 εκ.' was ignored."""
    mixed = deck(
        tmp_path, _add(2, 0.374, 5.3, 8.0, 0.4, "€1.250.000 προμήθειες και €2,3 εκ. έσοδα")
    )
    result = check(mixed, "Number Formats")
    assert result.status == "warn"
    assert "raw and abbreviated" in details(result)
    assert "3 places" not in details(result)


def test_a_year_ending_one_bullet_is_not_the_amount_of_the_next(tmp_path):
    """'... in 2026' then 'EUR 42M ...' once read as a raw amount '2026 EUR'."""

    def edit(prs):
        bullets(
            slide(prs, 2),
            0.374,
            5.2,
            8.0,
            1.0,
            ["EUR 12.5B volume in 2026", "EUR 42M fees, up 18%", "850K downloads"],
        )

    result = check(deck(tmp_path, edit), "Number Formats")
    assert result.status == "pass", result.details
    # The two currency bullets plus the golden table's four amounts. EUR 12.5B beside
    # EUR 42M is correct (quantities three orders apart); 850K and 18% carry no
    # currency marker, so they are not sampled.
    assert result.examined == 6


def test_text_margins_fail_on_any_violation(tmp_path):
    """VALIDATOR-14: violations on fewer than half the slides reported a pass."""
    result = check(FAIL_CASES["Text Margins"](tmp_path), "Text Margins")
    assert result.status == "fail" and "Slide 2" in details(result)


def test_the_old_bullet_child_order_is_an_ooxml_error(tmp_path):
    result = check(FAIL_CASES["OOXML Order"](tmp_path), "OOXML Order")
    assert result.status == "fail" and "a:pPr" in details(result)


def _master_band(prs):
    background_graphic(prs, lambda s: box(s, 0, 7.3, 13.333, 0.2, "4F81BD"), master=True)


def test_an_off_palette_band_on_the_master_fails_colors_once(tmp_path):
    """VALIDATOR-CODE-9: layout and master shapes were never read, so an off-palette band
    on the master passed on every slide that showed it."""
    result = check(deck(tmp_path, _master_band), "Colors")
    assert result.status == "fail"
    assert "4F81BD" in details(result) and "slideMaster1.xml" in details(result)
    assert len(result.details) == 1, "judged once, not once per slide that shows it"


def test_a_layout_that_hides_master_shapes_hides_the_band(tmp_path):
    def edit(prs):
        _master_band(prs)
        prs.slide_layouts[6]._element.set("showMasterSp", "0")

    assert check(deck(tmp_path, edit), "Colors").status == "pass"


def test_hide_background_graphics_on_every_slide_hides_the_layout_band(tmp_path):
    def edit(prs):
        background_graphic(prs, lambda s: box(s, 0, 7.3, 13.333, 0.2, "4F81BD"))
        for sld in prs.slides:
            sld._element.set("showMasterSp", "0")

    assert check(deck(tmp_path, edit), "Colors").status == "pass"


def test_layout_text_is_held_to_the_font_and_size_rules(tmp_path):
    def edit(prs):
        background_graphic(
            prs,
            lambda s: text(s, 0.374, 7.0, 4.0, 0.3, "Confidential", size=8, font="Comic Sans MS"),
        )

    path = deck(tmp_path, edit)
    fonts = check(path, "Fonts")
    assert fonts.status == "fail" and "Comic Sans MS" in details(fonts)
    assert "slideLayout" in details(fonts)
    sizes = check(path, "Font Sizes")
    assert sizes.status == "fail" and "8pt" in details(sizes)


def _drop_pictures(sld):
    for shape in list(sld.shapes):
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            shape._element.getparent().remove(shape._element)


def test_a_logo_on_the_layout_is_the_logo_of_each_slide_that_shows_it(tmp_path):
    """A logo placed once on the layout failed Logo on every slide that rendered it."""

    def edit(prs):
        slides = list(prs.slides)
        for sld in slides[1:-1]:
            _drop_pictures(sld)
        background_graphic(prs, lambda s: logo(s, "small"))
        for sld in (slides[0], slides[-1]):
            sld._element.set("showMasterSp", "0")

    path = deck(tmp_path, edit)
    result = check(path, "Logo")
    assert result.status == "pass", result.details
    assert check(path, "Back Cover").status == "pass"


def test_the_back_cover_shows_the_logo_on_its_layout(tmp_path):
    result = check(deck(tmp_path, lambda prs: background_graphic(prs, logo)), "Back Cover")
    assert result.status == "fail" and "besides the emblem" in details(result)


def test_smartart_drawing_is_read_for_colours_fonts_and_sizes(tmp_path):
    """VALIDATOR-CODE-6: a diagram's boxes and text were never read, so red fills and 8pt
    Comic Sans inside SmartArt passed every check."""
    path = add_smartart(deck(tmp_path), fill="FF0000", color="FFFF00", size=8, font="Comic Sans MS")
    colors = check(path, "Colors")
    assert colors.status == "fail" and "#FF0000" in details(colors)
    assert "drawing1.xml" in details(colors)
    fonts = check(path, "Fonts")
    assert fonts.status == "fail" and "Comic Sans MS" in details(fonts)
    sizes = check(path, "Font Sizes")
    assert sizes.status == "fail" and "8pt" in details(sizes)


def test_a_brand_smartart_diagram_passes_and_is_counted(tmp_path, golden):
    before = check(golden, "Colors").examined
    path = add_smartart(deck(tmp_path))
    colors = check(path, "Colors")
    assert colors.status == "pass" and colors.examined > before
    assert check(path, "Fonts").status == "pass"
    assert check(path, "Font Sizes").status == "pass"


def test_smartart_without_a_drawing_part_is_unexamined_and_fails_strict(tmp_path):
    path = add_smartart(deck(tmp_path), fill="FF0000", drawing=False)
    results = nv.validate_presentation(str(path), only=["Colors", "Fonts", "Font Sizes"])
    for r in results:
        assert r.not_examined.get(nv.SMARTART_UNREAD) == 1, r.name
    assert nv.exit_code(results) == 0
    assert nv.exit_code(results, strict=True) == 1


NO_STYLE_TABLE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # No Style, No Grid
CUSTOM_TABLE = "{0B5E1C3A-5D2B-4C3E-9A11-7C1D2E3F4A5B}"


def _styled_table(prs, *, style=None):
    """Swap slide 5's table for one that leaves colour to its table style: no cell fills,
    no run colours, the header row and banding flags python-pptx turns on."""
    sld = slide(prs, 5)
    remove(next(sh for sh in sld.shapes if sh.has_table))
    frame = sld.shapes.add_table(3, 2, inch(0.374), inch(1.3), inch(6.0), inch(1.2))
    if style is not None:
        frame._element.find(".//" + qn("a:tableStyleId")).text = style
    for r in range(3):
        for c in range(2):
            run = frame.table.cell(r, c).text_frame.paragraphs[0].add_run()
            run.text = f"Line {r}{c}"
            run.font.size = Pt(12)
            run.font.name = "Aptos"
    set_alt(frame, "Table of fee lines by year.")


def _table_styles(header_fill):
    header = (
        f'<a:firstRow><a:tcTxStyle b="on"><a:schemeClr val="lt1"/></a:tcTxStyle>'
        f"<a:tcStyle><a:fill><a:solidFill>{header_fill}</a:solidFill></a:fill></a:tcStyle>"
        "</a:firstRow>"
    )
    style = (
        f'<a:tblStyle styleId="{CUSTOM_TABLE}" styleName="House">'
        '<a:wholeTbl><a:tcTxStyle><a:schemeClr val="dk1"/></a:tcTxStyle></a:wholeTbl>'
        f"{header}</a:tblStyle>"
    )
    return lambda xml: re.sub(
        r"<a:tblStyleLst([^>]*?)\s*/>", rf"<a:tblStyleLst\1>{style}</a:tblStyleLst>", xml
    )


def test_the_default_table_style_colours_are_measured(tmp_path):
    """VALIDATOR-CODE-8: PowerPoint's default table (Medium Style 2, Accent 1) puts white
    bold text on accent 1, cyan in the NBG theme, at about 2.2:1; with no cell fills
    written, both Contrast and Colors passed it."""
    path = deck(tmp_path, _styled_table)
    contrast = check(path, "Contrast")
    assert contrast.status == "fail" and "#FFFFFF on #00ADBF" in details(contrast)
    colors = check(path, "Colors")
    assert colors.status == "fail" and "fill from its table style" in details(colors)


def test_a_table_with_no_style_is_plain_text_on_the_slide(tmp_path):
    path = deck(tmp_path, lambda prs: _styled_table(prs, style=NO_STYLE_TABLE))
    assert check(path, "Contrast").status == "pass"
    assert check(path, "Colors").status == "pass"


def test_a_style_defined_in_the_deck_is_read_from_table_styles_xml(tmp_path):
    teal = _table_styles('<a:srgbClr val="007B85"/>')
    ok = deck(
        tmp_path,
        lambda prs: _styled_table(prs, style=CUSTOM_TABLE),
        patch={"ppt/tableStyles.xml": teal},
    )
    assert check(ok, "Contrast").status == "pass"
    assert check(ok, "Colors").status == "pass"
    bright = _table_styles('<a:schemeClr val="accent6"/>')
    bad = deck(
        tmp_path,
        lambda prs: _styled_table(prs, style=CUSTOM_TABLE),
        name="bright.pptx",
        patch={"ppt/tableStyles.xml": bright},
    )
    result = check(bad, "Contrast")
    assert result.status == "fail" and "#FFFFFF on #00DFF8" in details(result)


def test_an_unknown_table_style_is_not_examined(tmp_path):
    unknown = "{11111111-2222-3333-4444-555555555555}"
    path = deck(tmp_path, lambda prs: _styled_table(prs, style=unknown))
    for name in ("Contrast", "Colors"):
        result = check(path, name)
        assert result.not_examined.get(nv.TABLE_STYLE_UNREAD, 0) >= 6, (name, result.not_examined)


@pytest.mark.parametrize(
    ("flags", "cell", "parts"),
    [
        ({"firstRow", "bandRow"}, (0, 0), ["wholeTbl", "firstRow"]),
        ({"firstRow", "bandRow"}, (1, 0), ["wholeTbl", "band1H"]),
        ({"firstRow", "bandRow"}, (2, 1), ["wholeTbl", "band2H"]),
        ({"bandRow"}, (0, 0), ["wholeTbl", "band1H"]),
        ({"firstRow", "firstCol"}, (0, 0), ["wholeTbl", "firstCol", "firstRow", "nwCell"]),
        ({"lastRow", "bandRow", "firstRow"}, (3, 0), ["wholeTbl", "lastRow"]),
        ({"firstCol", "bandRow"}, (1, 0), ["wholeTbl", "band2H", "firstCol"]),
    ],
)
def test_table_style_parts_layer_in_powerpoint_order(flags, cell, parts):
    assert nv._style_parts(flags, *cell, rows=4, cols=2) == parts


def _grouped(prs, group_fill, *, child_fill="grp"):
    """A group on slide 2 whose one child takes the group's fill (a:grpFill) or its own."""
    sld = slide(prs, 2)
    grp = sld.shapes.add_group_shape()
    child = box(grp, 9.0, 5.3, 1.0, 0.4, "007B85")
    child.name = "Child"
    grp_sp_pr = grp._element.find(qn("p:grpSpPr"))
    fill = etree.SubElement(grp_sp_pr, qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr")).set("val", group_fill)
    if child_fill == "grp":
        sp_pr = child._element.spPr
        sp_pr.replace(sp_pr.find(qn("a:solidFill")), etree.Element(qn("a:grpFill")))


def test_a_child_painted_with_its_groups_fill_is_judged(tmp_path):
    """VALIDATOR-CODE-7: Colors skipped groups, so a:grpFill hid the colour that shows."""
    result = check(deck(tmp_path, lambda prs: _grouped(prs, "FF0000")), "Colors")
    assert result.status == "fail" and "#FF0000" in details(result)
    assert "group fill" in details(result)


def test_a_group_fill_no_child_uses_is_not_drawn(tmp_path):
    path = deck(tmp_path, lambda prs: _grouped(prs, "FF0000", child_fill="own"))
    assert check(path, "Colors").status == "pass"


def _run_color(position, color_xml):
    """Slide `position` gains a text box whose run colour is `color_xml`."""

    def edit(prs):
        shape = text(slide(prs, position), 9.0, 5.3, 3.0, 0.3, "Delivered", size=12)
        r_pr = shape._element.find(".//" + qn("a:rPr"))
        fill = r_pr.find(qn("a:solidFill"))
        fill.remove(fill[0])
        fill.append(etree.fromstring(color_xml))

    return edit


@pytest.mark.parametrize(
    ("color_xml", "hex_"),
    [
        (f'<a:hslClr xmlns:a="{NS_A}" hue="0" sat="100000" lum="50000"/>', "FF0000"),
        (f'<a:prstClr xmlns:a="{NS_A}" val="dkGreen"/>', "006400"),
        (f'<a:prstClr xmlns:a="{NS_A}" val="medVioletRed"/>', "C71585"),
    ],
)
def test_hsl_and_every_preset_colour_are_judged(tmp_path, color_xml, hex_):
    """hslClr and the presets outside a 12-name table passed as 'all NBG colours'."""
    result = check(deck(tmp_path, _run_color(2, color_xml)), "Colors")
    assert result.status == "fail" and f"#{hex_}" in details(result)


def test_an_hsl_white_is_an_nbg_colour(tmp_path):
    white = f'<a:hslClr xmlns:a="{NS_A}" hue="0" sat="0" lum="100000"/>'
    assert check(deck(tmp_path, _run_color(2, white)), "Colors").status == "pass"


def test_an_unresolvable_colour_is_not_counted_as_examined(tmp_path, golden):
    before = check(golden, "Colors").examined
    bad = f'<a:schemeClr xmlns:a="{NS_A}" val="accent9"/>'
    result = check(deck(tmp_path, _run_color(2, bad)), "Colors")
    assert result.examined == before
    assert result.not_examined == {"unresolvable colour reference": 1}


def test_tint_and_shade_work_in_linear_light_as_powerpoint_does():
    """PowerPoint draws Medium Style 2 Accent 1 on the Office theme's 4F81BD with bands
    D0D8E8 (tint 40%) and E9EDF4 (tint 20%); a plain sRGB mix gives B9CDE5 and DCE6F2."""

    def tinted(mod, val):
        el = etree.fromstring(
            f'<a:srgbClr xmlns:a="{NS_A}" val="4F81BD"><a:{mod} val="{val}"/></a:srgbClr>'
        )
        return nv._apply_modifiers("4F81BD", el)

    assert tinted("tint", 40000) == "D0D8E8"
    assert tinted("tint", 20000) == "E9EDF4"
    assert tinted("shade", 100000) == "4F81BD"


def _comic_minor(xml):
    return re.sub(r'(<a:minorFont>\s*<a:latin typeface=")[^"]*"', r'\1Comic Sans MS"', xml)


def _theme_font_run(prs):
    """Slide 2 gains a run with no typeface of its own: it draws in the theme's minor font."""
    shape = text(slide(prs, 2), 9.0, 5.3, 3.0, 0.3, "Delivered", size=12)
    r_pr = shape._element.find(".//" + qn("a:rPr"))
    r_pr.remove(r_pr.find(qn("a:latin")))


def test_text_in_a_non_brand_theme_font_fails_fonts(tmp_path):
    """VALIDATOR-CODE-4: only explicit a:latin was read, so text drawn in the theme's font,
    how PowerPoint stores most text, never reached the error-level check."""
    path = deck(tmp_path, _theme_font_run, patch={"ppt/theme/theme1.xml": _comic_minor})
    result = check(path, "Fonts")
    assert result.status == "fail" and "Comic Sans MS" in details(result)


def test_text_in_the_nbg_theme_font_passes_fonts(tmp_path):
    assert check(deck(tmp_path, _theme_font_run), "Fonts").status == "pass"


def test_chart_text_with_no_font_of_its_own_is_in_the_theme_font(tmp_path):
    def edit(prs):
        chart = next(sh for sh in slide(prs, 3).shapes if sh.has_chart).chart
        tx_pr = chart._chartSpace.find(qn("c:txPr"))
        tx_pr.getparent().remove(tx_pr)

    path = deck(tmp_path, edit, patch={"ppt/theme/theme1.xml": _comic_minor})
    result = check(path, "Fonts")
    assert result.status == "fail" and "Comic Sans MS" in details(result)
    assert "chart" in details(result)


def _covered(*, on_top=True, alpha=None):
    """Slide 2 gains a text box and a filled card over the same spot, drawn after the text
    (hiding it) or before it (a card behind its text)."""

    def edit(prs):
        sld = slide(prs, 2)

        def card():
            shape = box(sld, 9.0, 5.2, 3.0, 0.5, "003841")
            if alpha is not None:
                clr = shape._element.spPr.find(qn("a:solidFill"))[0]
                etree.SubElement(clr, qn("a:alpha")).set("val", str(alpha))

        if not on_top:
            card()
        text(sld, 9.1, 5.3, 2.8, 0.3, "Delivered in June", size=12, color="FFFFFF")
        if on_top:
            card()

    return edit


def test_text_under_an_opaque_shape_drawn_on_top_fails_text_fit(tmp_path):
    """VALIDATOR-CODE-12: a filled shape later in z-order hides the text under it, and
    every check passed it."""
    result = check(deck(tmp_path, _covered()), "Text Fit")
    assert result.status == "fail" and "hidden under" in details(result)


def test_a_card_behind_its_text_hides_nothing(tmp_path):
    assert check(deck(tmp_path, _covered(on_top=False)), "Text Fit").status == "pass"


def test_a_see_through_shape_on_top_hides_nothing(tmp_path):
    assert check(deck(tmp_path, _covered(alpha=30000)), "Text Fit").status == "pass"


def test_bank_branding_reads_chart_categories(tmp_path):
    """E2E-SMOKE-9: a four-bank chart passed as 'examined nothing'."""
    result = check(_bank_case(tmp_path, colored=False), "Bank Branding")
    assert result.status == "fail"
    for bank in ("Eurobank", "Alpha", "Piraeus"):
        assert bank in details(result)


def test_bank_branding_wants_one_logo_per_plotted_bank(tmp_path):
    result = check(_bank_case(tmp_path, logos=False), "Bank Branding")
    assert result.status == "fail" and "logo" in details(result)


def _png(path, w, h):
    from PIL import Image

    Image.new("RGB", (w, h), (0, 123, 133)).save(path)
    return path


def test_any_picture_is_not_a_bank_logo(tmp_path):
    """VALIDATOR-CODE-10: four icons beside a four-bank chart counted as four logos."""
    icon = _png(tmp_path / "icon.png", 64, 64)
    result = check(_bank_case(tmp_path, pictures=[(icon, "Growth icon")] * 4), "Bank Branding")
    assert result.status == "fail"
    assert "no logo for NBG, Eurobank, Alpha Bank, Piraeus Bank" in details(result)


def test_two_logos_of_one_bank_leave_another_bank_without_one(tmp_path):
    files = ("nbg.png", "eurobank.png", "alpha-bank.png", "alpha-bank.png")
    pictures = [(BANK_LOGOS / f, "Bank logo") for f in files]
    result = check(_bank_case(tmp_path, pictures=pictures), "Bank Branding")
    assert result.status == "fail"
    assert "no logo for Piraeus Bank" in details(result)


def test_a_redrawn_logo_counts_when_it_names_its_bank_and_keeps_the_shape(tmp_path):
    """Not the shipped file, so no hash match: the alt text names the bank and the image
    keeps the asset's aspect ratio. A picture of another shape is not that logo."""
    from PIL import Image

    sharp = tmp_path / "eurobank-large.png"
    with Image.open(BANK_LOGOS / "eurobank.png") as img:
        img.convert("RGB").resize((256, 256)).save(sharp)
    wide = _png(tmp_path / "eurobank-wide.png", 256, 128)

    def pictures(eurobank):
        return [
            (BANK_LOGOS / "nbg.png", "NBG logo"),
            (eurobank, "Eurobank logo"),
            (BANK_LOGOS / "alpha-bank.png", "Alpha Bank logo"),
            (BANK_LOGOS / "piraeus-bank.png", "Piraeus Bank logo"),
        ]

    assert check(_bank_case(tmp_path, pictures=pictures(sharp)), "Bank Branding").status == "pass"
    result = check(_bank_case(tmp_path, pictures=pictures(wide)), "Bank Branding")
    assert result.status == "fail" and "no logo for Eurobank" in details(result)


def test_bank_names_come_from_tokens(tmp_path, monkeypatch):
    """The builder and the gate read one list: a label alias added to tokens.yaml makes
    a bank to the validator as well."""
    real = nv.nbg_tokens.get

    def get(path):
        value = real(path)
        if path == "banks":
            value = {key: dict(bank) for key, bank in value.items()}
            value["eurobank"]["label_aliases"] = ["EFG"]
        return value

    monkeypatch.setattr(nv.nbg_tokens, "get", get)
    nv._bank_table.cache_clear()
    try:
        path = deck(
            tmp_path,
            lambda prs: _bank_slide(
                prs, colored=True, logos=True, categories=("NBG", "EFG", "Sector", "Market")
            ),
            name="efg.pptx",
        )
        result = check(path, "Bank Branding")
    finally:
        nv._bank_table.cache_clear()
    assert result.status == "pass" and result.examined == 1, result.message


def test_bank_branding_ignores_a_source_footnote(tmp_path):
    only_source = deck(
        tmp_path,
        _add(2, 0.374, 5.3, 8.0, 0.25, "Source: NBG and Eurobank reports, 2025", size=11),
    )
    result = check(only_source, "Bank Branding")
    assert result.status == "skipped"
    assert "0 bank name(s) found" in result.message


def test_the_official_name_drops_tis_ellados(tmp_path):
    result = check(FAIL_CASES["Official Name"](tmp_path), "Official Name")
    assert result.status == "warn" and "Εθνική Τράπεζα" in details(result)
    fine = check(
        deck(tmp_path, _add(2, 0.374, 5.3, 8.0, 0.4, "Εθνική Τράπεζα"), name="ok.pptx"),
        "Official Name",
    )
    assert fine.status == "pass"


# ------------------------------------------------------------------ text fit


def test_a_fixed_width_pill_whose_text_runs_out_of_it_fails(tmp_path):
    def edit(prs):
        pill(slide(prs, 3), "Retail and business banking", y=0.08, w=1.0, h=0.3)

    result = check(deck(tmp_path, edit), "Text Fit")
    assert result.status == "fail"
    assert "wider than" in details(result)


def test_a_cover_title_that_wraps_into_the_subtitle_fails(tmp_path):
    def edit(prs):
        shape = shape_with_text(slide(prs, 1), COVER_TITLE)
        shape.text_frame.paragraphs[0].runs[
            0
        ].text = "Cards, payments and digital banking results for the first half of 2026"

    result = check(deck(tmp_path, edit), "Text Fit")
    assert result.status == "fail" and "Slide 1" in details(result)


def test_overlapping_text_fails(tmp_path):
    result = check(
        deck(tmp_path, _add(2, 0.8, 3.65, 6.0, 0.3, "Collides with a priority line")), "Text Fit"
    )
    assert result.status == "fail" and "overlap" in details(result)


def test_a_table_that_grows_past_the_footer_fails(tmp_path):
    """PowerPoint treats row height as a minimum: long cells push the table down."""

    def edit(prs):
        sld = slide(prs, 5)
        remove(sld.shapes[1])
        wordy = " ".join(["long cell text that wraps"] * 6)
        table(sld, [["Line", "Notes"]] + [[f"Row {i}", wordy] for i in range(6)], w=6.0)

    result = check(deck(tmp_path, edit), "Text Fit")
    assert result.status == "fail" and "table" in details(result)


def test_a_grow_to_fit_text_box_that_grows_into_the_footer_fails(tmp_path):
    """python-pptx gives every new text box spAutoFit: it grows instead of overflowing."""

    def edit(prs):
        shape = slide(prs, 2).shapes.add_textbox(inch(0.374), inch(5.3), inch(4.0), inch(0.3))
        shape.text_frame.word_wrap = True
        run = shape.text_frame.paragraphs[0].add_run()
        run.text = " ".join(["A paragraph that keeps on growing"] * 10)
        run.font.size = Pt(14)
        run.font.name = "Aptos"
        run.font.color.rgb = RGBColor.from_string("202020")

    result = check(deck(tmp_path, edit), "Text Fit")
    assert result.status == "fail" and "grows" in details(result)


def test_text_fit_reports_how_it_measured(golden):
    assert "width table" in check(golden, "Text Fit").message


def test_the_fallback_width_table_is_aptos_advance_widths():
    measurer = nv.TextMeasurer()
    assert measurer.font_path is None
    # C a r d s at 1000 units per em: 692 + 531 + 334 + 561 + 486
    assert measurer.width("Cards", 1000) == pytest.approx(2604, abs=1)
    assert measurer.width("Cards", 1000, bold=True) > measurer.width("Cards", 1000)
    assert measurer.line_height(10) == pytest.approx(12.21, abs=0.01)


def test_font_discovery_searches_office_and_windows_folders(monkeypatch):
    monkeypatch.delenv("DECKS_FONT_DIRS")
    dirs = [str(d).replace("\\", "/") for d in nv.font_search_dirs()]
    assert any(d.endswith("Library/Fonts") for d in dirs)
    assert any("DFonts" in d for d in dirs)
    assert any(d.endswith("Windows/Fonts") for d in dirs)


def test_an_unloadable_font_file_falls_back_to_the_table(monkeypatch, tmp_path):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "Aptos.ttf").write_bytes(b"not a font")
    monkeypatch.setenv("DECKS_FONT_DIRS", str(fonts))
    nv.reset_font_cache()
    measurer = nv.TextMeasurer()
    assert measurer.width("Cards", 1000) == pytest.approx(2604, abs=1)
    assert "width table" in measurer.source


def test_the_pillow_path_agrees_with_the_table_when_aptos_is_installed(monkeypatch):
    """No skip either way: with Aptos found, Pillow must agree with the table."""
    monkeypatch.delenv("DECKS_FONT_DIRS")
    nv.reset_font_cache()
    measurer = nv.TextMeasurer()
    if measurer.font_path is None:
        assert "width table" in measurer.source
    else:
        assert measurer.width("Cards", 1000) == pytest.approx(2604, rel=0.01)
        assert "Aptos" in measurer.source


# --------------------------------------------------------- output and gating


def _run(path, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path), *extra],
        capture_output=True,
        text=True,
        env={**os.environ},
    )


def _json(path, *extra):
    proc = _run(path, "--format", "json", *extra)
    return proc, (json.loads(proc.stdout) if proc.stdout.strip() else None)


def test_json_output_is_the_documented_contract(tmp_path):
    proc, report = _json(FAIL_CASES["Colors"](tmp_path))
    assert proc.returncode == 1, proc.stderr
    assert set(report) >= {"file", "summary", "checks"}
    assert set(report["summary"]) >= {"passed", "failed", "warnings", "skipped"}
    assert [c["name"] for c in report["checks"]] == list(nv.CHECK_NAMES)
    colors = next(c for c in report["checks"] if c["name"] == "Colors")
    assert colors["status"] == "fail" and colors["severity"] == "error"
    assert colors["examined"] > 0
    finding = colors["details"][0]
    assert finding["slide"] == 2 and finding["severity"] == "error"
    assert "FF0000" in finding["message"]
    assert {c["status"] for c in report["checks"]} <= {"pass", "fail", "warn", "skipped"}
    assert report["summary"]["failed"] == sum(c["status"] == "fail" for c in report["checks"])


def test_a_zero_candidate_pass_is_skipped_in_json_and_text(golden, capsys):
    proc, report = _json(golden)
    assert proc.returncode == 0, proc.stdout
    banks = next(c for c in report["checks"] if c["name"] == "Bank Branding")
    assert banks["status"] == "skipped" and banks["examined"] == 0
    assert nv.main([str(golden)]) == 0
    assert "examined nothing" in capsys.readouterr().out


def test_exit_codes(tmp_path, golden):
    assert _json(golden)[0].returncode == 0
    assert _json(FAIL_CASES["Colors"](tmp_path))[0].returncode == 1
    assert _json(FAIL_CASES["AI Slop"](tmp_path))[0].returncode == 0  # a warning never blocks
    assert _run(tmp_path / "missing.pptx").returncode == 2
    junk = tmp_path / "junk.pptx"
    junk.write_bytes(b"this is not a zip file")
    assert _run(junk).returncode == 2


def _zip(path, members, compress_type=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path, "w", compress_type) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return path


def _xml_comment(n):
    return b"<r><!--" + b"x" * n + b"--></r>"


def test_the_xml_limits_are_the_ones_the_builder_shares():
    """The same numbers as the builder's tools/nbg_package.py pre-flight."""
    assert nv.MAX_MEMBERS == 5000
    assert nv.MAX_PART_BYTES == 64 * 2**20
    assert nv.MAX_XML_PART_BYTES == 16 * 2**20
    assert nv.MAX_XML_TOTAL_BYTES == 128 * 2**20
    assert nv.MAX_XML_RATIO == 100


def test_an_xml_part_over_16_mib_exits_2(tmp_path, golden, capsys):
    """VALIDATOR-CODE-11: a 64 MiB XML part was allowed, and a parsed tree costs many
    times its text (three such parts took 4.3 GB). Stored, so no ratio test fires."""
    path = tmp_path / "big.pptx"
    with zipfile.ZipFile(golden) as zf:
        blobs = {n: zf.read(n) for n in zf.namelist()}
    part = "ppt/slides/slide1.xml"
    blobs[part] = blobs[part].replace(b"</p:sld>", b"<!--" + b"x" * (17 * 2**20) + b"--></p:sld>")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for n, data in blobs.items():
            zf.writestr(n, data, compress_type=zipfile.ZIP_STORED if n == part else None)
    assert nv.main([str(path)]) == 2
    assert "16 MB" in capsys.readouterr().err


def test_every_parsed_part_gets_the_ratio_test_whatever_its_size_or_name(tmp_path):
    """The ratio test ran only on .xml/.rels parts over 1 MiB."""
    small = nv.Package(_zip(tmp_path / "small.zip", {"small.xml": _xml_comment(900 * 1024)}))
    with pytest.raises(nv.DeckError, match="zip bomb"):
        small.xml("small.xml")
    odd = nv.Package(_zip(tmp_path / "odd.zip", {"slide.bin": _xml_comment(2 * 2**20)}))
    with pytest.raises(nv.DeckError, match="zip bomb"):
        odd.xml("slide.bin")
    plain = nv.Package(_zip(tmp_path / "plain.zip", {"ok.xml": b"<r><a/><b/></r>"}))
    assert plain.xml("ok.xml") is not None


def test_parsed_xml_is_capped_across_the_package(tmp_path, monkeypatch):
    monkeypatch.setattr(nv, "MAX_XML_TOTAL_BYTES", 2**20)
    parts = {f"p{i}.xml": _xml_comment(400 * 1024) for i in range(3)}
    pkg = nv.Package(_zip(tmp_path / "many.zip", parts, zipfile.ZIP_STORED))
    pkg.xml("p0.xml")
    pkg.xml("p1.xml")
    pkg.xml("p0.xml")  # a part already parsed costs nothing more
    with pytest.raises(nv.DeckError, match="of XML"):
        pkg.xml("p2.xml")


def test_a_missing_dependency_exits_2_not_1(tmp_path, golden):
    """VALIDATOR-6: an ImportError exited 1, the same code as a brand violation."""
    fake = tmp_path / "fake" / "defusedxml"
    fake.mkdir(parents=True)
    (fake / "__init__.py").write_text("raise ImportError('defusedxml is broken on purpose')\n")
    env = {**os.environ, "PYTHONPATH": str(tmp_path / "fake")}
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(golden)], capture_output=True, text=True, env=env
    )
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "defusedxml" in proc.stderr


def test_no_ansi_colour_when_piped(tmp_path):
    proc = _run(FAIL_CASES["Colors"](tmp_path))
    assert proc.returncode == 1
    assert "\x1b[" not in proc.stdout
    assert "Colors" in proc.stdout


def test_colour_is_used_on_a_tty():
    class Tty:
        def isatty(self):
            return True

    class Pipe:
        def isatty(self):
            return False

    assert nv.use_color(Tty(), env={}) is True
    assert nv.use_color(Pipe(), env={}) is False
    assert nv.use_color(Tty(), env={"NO_COLOR": "1"}) is False


def test_the_full_fix_list_is_ordered_by_slide_and_not_truncated(tmp_path):
    """VALIDATOR-6: 12 violations printed 'Slide 10, 11, 12, 13, 2 ... and 5 more'."""

    def edit(prs):
        for _ in range(8):
            sld = blank(prs)
            title(sld, f"Extra slide number {len(prs.slides)} keeps its own title")
            text(sld, 0.374, 2.0, 6.0, 0.4, "Off palette", color="FF0000")
            logo(sld, "small")
        move_slide(prs, 5, len(prs.slides) - 1)  # back cover last again

    path = deck(tmp_path, edit)
    result = check(path, "Colors")
    slides = [f.slide for f in result.findings]
    assert len(slides) == 8
    assert slides == sorted(slides)
    out = _run(path).stdout
    section = out.split("Colors", 1)[1].split("\n\n", 1)[0]
    assert "more" not in section
    assert all(f"Slide {n}:" in section for n in slides)


def test_list_checks_prints_every_check_with_its_rule(capsys):
    assert nv.main(["--list-checks", "--format", "json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in listed] == list(nv.CHECK_NAMES)
    for entry in listed:
        assert entry["severity"] in ("error", "warning")
        assert entry["rule"] and entry["source"] and entry["candidates"], entry


def test_strict_fails_a_skipped_universal_check(tmp_path):
    prs = new_prs()
    blank(prs)  # one empty slide: nothing for most checks to examine
    path = save(prs, tmp_path / "bare.pptx")
    proc, report = _json(path, "--strict")
    skipped_universal = [
        c["name"]
        for c in report["checks"]
        if c["status"] == "skipped" and nv.CHECKS_BY_NAME[c["name"]].universal
    ]
    assert skipped_universal
    assert proc.returncode == 1


def test_failing_results_still_say_what_they_examined(tmp_path):
    """VALIDATOR-14: failure paths never set examined, so '3 of N' was unknowable."""
    result = check(FAIL_CASES["Colors"](tmp_path), "Colors")
    assert result.examined and result.examined > 1


def test_validator_md_documents_every_check():
    doc = (HERE / "VALIDATOR.md").read_text(encoding="utf-8")
    for name in nv.CHECK_NAMES:
        assert re.search(rf"^\| {re.escape(name)} \|", doc, re.M), (
            f"VALIDATOR.md has no row for {name}"
        )


def test_the_brand_comes_from_tokens_not_a_second_copy():
    """BRAND-SSOT-10: the validator carried its own allow-list, with retired greys."""
    assert not hasattr(nv, "NBG_GUIDELINES")
    assert nv.allowed_colors() == nbg_tokens.allowed_colors()
    assert "595959" not in nv.allowed_colors()


# ------------------------------------------- what the rebuilt nbg_build writes


def _placeholder_title(sld, content, *, x, y, w, h, size):
    """A title placeholder with its own geometry and size, as nbg_build now writes one."""
    ph = sld.shapes.title
    ph.left, ph.top, ph.width, ph.height = inch(x), inch(y), inch(w), inch(h)
    tf = ph.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = content
    run.font.size = Pt(size)
    run.font.name = "Aptos"
    run.font.color.rgb = RGBColor.from_string("003841")
    return ph


def test_title_placeholders_on_every_slide_take_their_role_from_their_size(tmp_path):
    """nbg_build puts a title placeholder on the cover, the dividers and every body
    slide. A 48pt placeholder is a cover or divider title (Standard #3 keeps its noun
    phrase out of Action Titles); a 24pt one is an action title."""
    prs = new_prs()
    cover = prs.slides.add_slide(prs.slide_layouts[5])
    _placeholder_title(cover, "Quarterly report", x=0.374, y=1.39, w=12.0, h=1.0, size=48)
    divider = prs.slides.add_slide(prs.slide_layouts[5])
    text(divider, 0.374, 2.84, 1.2, 1.0, "02", size=60, color="007B85")
    _placeholder_title(divider, "Recommendations", x=1.574, y=2.84, w=9.5, h=1.0, size=48)
    body = prs.slides.add_slide(prs.slide_layouts[5])
    _placeholder_title(body, "Overview", x=0.374, y=0.5, w=12.585, h=0.4, size=24)
    path = save(prs, tmp_path / "placeholders.pptx")
    with nv.load_deck(path) as loaded:
        found_titles = [nv.find_title(s) for s in loaded.slides]
    assert [t.is_content if t else None for t in found_titles] == [False, False, True]
    actions = check(path, "Action Titles")
    assert actions.examined == 1
    assert "Overview" in details(actions) and "Recommendations" not in details(actions)
    style = check(path, "Title Style")
    assert style.status == "pass", style.details  # the divider title follows its number


def test_a_picture_marked_decorative_in_powerpoint_needs_no_alt_text(tmp_path):
    def add(marked):
        def edit(prs):
            pic = slide(prs, 2).shapes.add_picture(
                str(BANK_LOGOS / "eurobank.png"), inch(10), inch(5.3), inch(0.4), inch(0.4)
            )
            if marked:
                c_nv_pr = pic._element.find(".//" + qn("p:cNvPr"))
                ext = etree.SubElement(etree.SubElement(c_nv_pr, qn("a:extLst")), qn("a:ext"))
                ext.set("uri", "{C183D7F6-B498-43B3-948B-1728B52AA6E4}")
                flag = etree.SubElement(
                    ext, "{http://schemas.microsoft.com/office/drawing/2017/decorative}decorative"
                )
                flag.set("val", "1")

        return edit

    marked = check(deck(tmp_path, add(True), name="marked.pptx"), "Alt Text")
    assert marked.status == "pass" and "marked decorative" in marked.message
    unmarked = check(deck(tmp_path, add(False), name="unmarked.pptx"), "Alt Text")
    assert unmarked.status == "fail" and "filename" in details(unmarked)


def _area_line(xml):
    """Turn the golden line chart into nbg_build's area_line: an areaChart fill and a
    lineChart stroke per series, in one plot area, sharing the axes."""
    found = re.search(r"<c:lineChart>.*?</c:lineChart>", xml, re.S)
    assert found, "no lineChart in the chart part"
    line = found.group(0)
    fills = []
    for ser in re.findall(r"<c:ser>.*?</c:ser>", line, re.S):
        ser = re.sub(r"<c:marker>.*?</c:marker>", "", ser, flags=re.S)
        ser = re.sub(r"<c:smooth[^>]*/>", "", ser)
        ser = re.sub(
            r"<c:spPr>.*?</c:spPr>",
            '<c:spPr><a:solidFill><a:srgbClr val="00ADBF"><a:alpha val="15000"/></a:srgbClr>'
            "</a:solidFill><a:ln><a:noFill/></a:ln></c:spPr>",
            ser,
            count=1,
            flags=re.S,
        )
        fills.append(ser)
    axes = "".join(re.findall(r'<c:axId val="-?\d+"/>', line))
    area = f'<c:areaChart><c:grouping val="standard"/><c:varyColors val="0"/>{"".join(fills)}{axes}</c:areaChart>'
    return xml.replace(line, area + line, 1)


def _four_series_line_chart(prs):
    sld = slide(prs, 4)
    remove(sld.shapes[1])
    data = CategoryChartData()
    data.categories = ["Q1", "Q2", "Q3", "Q4"]
    colors = ("00ADBF", "003841", "007B85", "939793")
    for i in range(4):
        data.add_series(f"Segment {i + 1}", (1 + i, 2 + i, 3 + i, 4 + i))
    frame = sld.shapes.add_chart(
        XL_CHART_TYPE.LINE_MARKERS, inch(0.374), inch(1.3), inch(12.585), inch(4.8), data
    )
    chart = frame.chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.font.size = Pt(12)
    chart.legend.font.name = "Aptos"
    _style_axes(chart, font="Aptos", value_visible=True, value_color="939793")
    for ser, color in zip(chart.plots[0].series, colors, strict=True):
        ser.smooth = False
        ser.format.line.color.rgb = RGBColor.from_string(color)
        ser.format.line.width = Pt(3.5)
        ser.marker.style = XL_MARKER_STYLE.CIRCLE
        ser.marker.size = 6
        ser.marker.format.fill.solid()
        ser.marker.format.fill.fore_color.rgb = RGBColor.from_string("FFFFFF")
        ser.marker.format.line.color.rgb = RGBColor.from_string(color)
    set_alt(frame, "Line chart of four segments by quarter, all rising.")


def test_an_area_line_chart_counts_each_series_once(tmp_path):
    """Four series drawn as area plus line are eight c:ser elements; counting elements
    warned 'past 6 series' on a four-series chart."""
    # Located by a series name: the replaced golden chart stays in the package as an
    # orphan part, and the first part mentioning lineChart is that orphan.
    path = deck(
        tmp_path,
        _four_series_line_chart,
        patch={(lambda p: chart_part(p, b"Segment 1")): _area_line},
    )
    with zipfile.ZipFile(path) as zf:
        assert zf.read(chart_part(path, b"Segment 1")).count(b"<c:ser>") == 8
    found = results(path, only=["Chart Data", "Chart Styling", "Colors"])
    for name, result in found.items():
        assert result.status == "pass", (name, result.details)


def test_a_rich_text_data_label_is_measured_by_its_own_run_colour(tmp_path):
    """Waterfall labels are custom rich text (the signed delta), coloured on the run."""

    def edit(prs):
        sld = slide(prs, 3)
        remove(sld.shapes[1])
        label = bar_chart(sld).chart.plots[0].series[0].points[0].data_label
        label.text_frame.text = "+0.1M"
        run = label.text_frame.paragraphs[0].runs[0]
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor.from_string("FFFFFF")
        label.position = XL_LABEL_POSITION.OUTSIDE_END

    result = check(deck(tmp_path, edit), "Contrast")
    assert result.status == "fail"
    assert "#FFFFFF on #FFFFFF" in details(result) and "label 1" in details(result)


def test_a_one_slide_view_plus_back_cover_passes_every_check_even_strict(tmp_path):
    """/create-infographic builds [one slide, back cover]: no cover and no contents is
    not a violation, and slide 1 is not held to the cover rules when it is a body slide."""
    prs = new_prs()
    s = blank(prs)
    title(s, TITLES[3])
    bar_chart(s)
    source(s)
    logo(s, "small")
    page_number(s, 1)
    logo(blank(prs), "back")
    found = nv.validate_presentation(str(save(prs, tmp_path / "view.pptx")))
    bad = {r.name: r.details for r in found if r.status in ("fail", "warn")}
    assert not bad, bad
    assert nv.exit_code(found, strict=True) == 0


# ------------------------------------------------- verification pass, round 2

APOS = chr(0x2019)


@pytest.mark.parametrize(
    "as_of",
    ["FY25", "FY 25", "1Q26", "Q2'26", f"Q2{APOS}26", "Q3 26", "9M25", "1H26", "H1 '26", "H2 26"],
)
def test_period_style_as_of_values_date_a_source(tmp_path, as_of):
    """VALIDATOR-CODE-5: the schema accepts '9M25' or 'Q2'26' as as_of; the gate did not."""

    def edit(prs):
        remove(shape_with_text(slide(prs, 3), "Source"))
        source(slide(prs, 3), f"Source: NBG MIS, {as_of}")

    result = check(deck(tmp_path, edit), "Exhibit Sources")
    assert result.status == "pass", result.details


@pytest.mark.parametrize("as_of", ["H1", "FY", "Q3", "latest", "9M"])
def test_a_period_without_a_year_still_dates_nothing(tmp_path, as_of):
    def edit(prs):
        remove(shape_with_text(slide(prs, 3), "Source"))
        source(slide(prs, 3), f"Source: NBG MIS, {as_of}")

    result = check(deck(tmp_path, edit), "Exhibit Sources")
    assert result.status == "fail" and "no as-of date" in details(result)


@pytest.mark.parametrize(
    "words",
    [
        "Μια ευχάριστη έκπληξη στις πωλήσεις",  # pleasant
        "Οι πελάτες είναι ευχαριστημένοι",  # satisfied
        "Η ευχαρίστηση του πελάτη ανέβηκε",  # satisfaction
    ],
)
def test_ordinary_greek_eucharist_words_are_not_a_thank_you(tmp_path, words):
    """VALIDATOR-CODE-1: ευχαριστ\\w* matched 'pleasant' and 'satisfied' on a closing slide."""
    result = check(deck(tmp_path, _add(5, 0.374, 3.0, 8.0, 0.4, words)), "Thank You Check")
    assert result.status == "pass", result.details


@pytest.mark.parametrize("words", ["Ευχαριστώ", "Σας ευχαριστούμε πολύ", "ΕΥΧΑΡΙΣΤΟΥΜΕ"])
def test_greek_thanking_forms_are_a_thank_you(tmp_path, words):
    result = check(deck(tmp_path, _add(5, 0.374, 3.0, 8.0, 0.6, words, size=28)), "Thank You Check")
    assert result.status == "fail" and words in details(result)


@pytest.mark.parametrize(
    "ending",
    ["στα €4,2 δισ.", "στα €120 εκατ.", "πάνω από 750 χιλ.", "στα €2,3 εκ."],
)
def test_a_greek_number_abbreviation_is_not_a_closing_period(tmp_path, ending):
    """E2E-OUTPUT-09: 'δισ.' ends an abbreviation, not a sentence."""
    result = check(
        deck(tmp_path, _retitle(3, f"Τα έσοδα από κάρτες έφτασαν {ending}")), "Title Style"
    )
    assert result.status == "pass", result.details


def test_no_shipped_rule_is_justified_by_one_persons_preference():
    """SECURITY-PUBLIC-6: a public validator states design reasons, not whose taste
    they were, and cites numbered Standards, not the removed Part 2."""
    for path in (SCRIPT, HERE / "VALIDATOR.md"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\bthe owner\b|\bPart 2\b", text), path.name


@pytest.mark.parametrize("fmt", ["text", "json"])
def test_a_windows_code_page_console_does_not_crash_the_report(tmp_path, fmt):
    """VALIDATOR-CODE-3: on cp1252 the ✓ and Greek text raised UnicodeEncodeError after
    validating, and the crash exited 1, the 'a check failed' code, with empty JSON."""
    path = deck(tmp_path, _add(2, 0.374, 5.3, 8.0, 0.4, "Εθνική Τράπεζα της Ελλάδος"))
    env = {**os.environ, "PYTHONIOENCODING": "cp1252:strict"}
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--format", fmt], capture_output=True, env=env
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")  # only a warning
    out = proc.stdout.decode("utf-8")
    if fmt == "json":
        report = json.loads(out)
        official = next(c for c in report["checks"] if c["name"] == "Official Name")
        assert official["status"] == "warn" and "Εθνική" in official["details"][0]["message"]
    else:
        assert "Official Name" in out


def test_a_failure_while_printing_exits_2_not_1(tmp_path, monkeypatch, golden):
    """The report is part of running: if it cannot be written, the deck is unvalidated."""

    def broken(*args, **kwargs):
        raise OSError("stdout is gone")

    monkeypatch.setattr(nv, "print_results", broken)
    assert nv.main([str(golden)]) == 2


def _style_colored_text(fill):
    """An autoshape whose text takes its colour from p:style fontRef (lt1, white), with
    no colour on the run: how PowerPoint writes text typed into a shape."""

    def edit(prs):
        shape = box(slide(prs, 2), 7.0, 5.2, 3.0, 0.6, fill)
        run = shape.text_frame.paragraphs[0].add_run()
        run.text = "Delivered on time"
        run.font.size = Pt(14)
        run.font.name = "Aptos"

    return edit


def test_shape_style_text_colour_outranks_the_deck_default(tmp_path):
    """VALIDATOR-CODE-2: fontRef ranked below the deck default (black), so white text on
    a teal shape failed and invisible white text on an off-white shape passed."""
    teal = check(deck(tmp_path, _style_colored_text("007B85"), name="teal.pptx"), "Contrast")
    assert teal.status == "pass", teal.details
    light = check(deck(tmp_path, _style_colored_text("F5F8F6"), name="light.pptx"), "Contrast")
    assert light.status == "fail" and "#FFFFFF on #F5F8F6" in details(light)


def test_close_bar_values_on_an_automatic_axis_fail(tmp_path):
    """E2E-OUTPUT-01: with no c:min, PowerPoint starts the axis for 2.9..3.3 near 2.7, so
    every bar is truncated; the check passed because it only read an explicit minimum."""
    result = check(deck(tmp_path, _replace_bar_chart(zero_based=False)), "Zero Baseline")
    assert result.status == "fail"
    assert "automatic" in details(result) and "Slide 3" in details(result)


def test_spread_bar_values_on_an_automatic_axis_start_at_zero(tmp_path):
    """PowerPoint puts zero on an automatic axis when the data spread is wide (the
    lowest value under five sixths of the highest), so that chart is fine."""
    spread = _replace_bar_chart(zero_based=False, series=(("Users (M)", (1.2, 2.0, 2.9, 3.3)),))
    result = check(deck(tmp_path, spread), "Zero Baseline")
    assert result.status == "pass", result.details


def test_negative_bars_need_zero_at_the_top(tmp_path):
    """All-negative close values truncate at the top; an explicit negative minimum is
    fine (the old check failed any non-zero minimum, including -120 on negative data)."""
    close = (("Net outflow (EUR M)", (-100, -104, -102, -98)),)
    auto = check(
        deck(tmp_path, _replace_bar_chart(zero_based=False, series=close), name="a.pptx"),
        "Zero Baseline",
    )
    assert auto.status == "fail"

    def floor_below(xml):
        head, sep, tail = xml.partition("<c:valAx>")
        return (
            head
            + sep
            + re.sub(
                r"<c:scaling/>",
                '<c:scaling><c:max val="0"/><c:min val="-120"/></c:scaling>',
                tail,
                count=1,
            )
        )

    path = deck(
        tmp_path,
        _replace_bar_chart(zero_based=False, series=close),
        name="b.pptx",
        patch={(lambda p: chart_part(p, b"Net outflow")): floor_below},
    )
    assert check(path, "Zero Baseline").status == "pass"


def test_the_names_the_spec_checker_imports_stay_put():
    """nbg_spec imports these so `check` and this gate agree; renaming one breaks it."""
    assert nv.SOURCE_AS_OF.search("30 June 2026") and nv.SOURCE_AS_OF.search("9M25")
    assert nv.SOURCE_PREFIX.match(nv.fold("ΠΗΓΗ: ΤτΕ"))
    assert nv.ALT_TEXT_PLACEHOLDER.match("chart-4.png") and nv.ALT_TEXT_LEAD_IN.match("Image of x")
    assert nv.alt_text_problem("Chart 3") and nv.alt_text_problem("Volume rose 12% in 2025") is None
    assert nv.alt_text_problem("Same text", ["same TEXT"])
    assert nv.dash_problem(f"a {EM_DASH} b") == ("error", "em dash")
    assert nv.dash_problem("a -- b") == ("error", "em dash")
    assert nv.DOUBLE_HYPHEN == " -- " and nv.EM_DASH == EM_DASH
    assert nv.dash_problem(f"a {EN_DASH} b") == ("warning", "spaced en dash used as a dash")
    assert nv.dash_problem(f"2024{EN_DASH}2025") is None


# ------------------ validator tests that lived in test_nbg_build.py, ported here


def test_exhibit_sources_reject_a_source_with_no_as_of_date(tmp_path):
    """'Source: NBG MIS' does not say whether the number is current."""

    def edit(prs):
        remove(shape_with_text(slide(prs, 3), "Source"))
        source(slide(prs, 3), "Source: NBG MIS")

    result = check(deck(tmp_path, edit), "Exhibit Sources")
    assert result.status == "fail" and "no as-of date" in details(result)


@pytest.mark.parametrize(
    ("alt", "expected"),
    [
        ("chart-4.png", "is a filename or an autoname"),  # what python-pptx writes
        ("Image of monthly volume", 'opens with "image of"'),
        (TITLES[3], "repeats a caption"),  # read out twice by a screen reader
    ],
)
def test_alt_text_rejects_descriptions_that_describe_nothing(tmp_path, alt, expected):
    result = check(deck(tmp_path, lambda prs: set_alt(slide(prs, 3).shapes[1], alt)), "Alt Text")
    assert result.status == "fail" and expected in details(result)


def test_zero_baseline_leaves_a_truncated_line_chart_alone(tmp_path):
    """A line encodes value as position, so a non-zero start is legitimate."""
    path = deck(tmp_path, patch={(lambda p: chart_part(p, b"lineChart")): _truncate_axis})
    assert check(path, "Zero Baseline").status == "pass"


def test_zero_baseline_is_read_by_parsing_not_by_searching_the_text(golden):
    """'c:min' is also a substring of c:minorTickMark, on every chart python-pptx writes."""
    with zipfile.ZipFile(golden) as zf:
        assert b"c:minorTickMark" in zf.read(chart_part(golden, b"barChart"))
    result = check(golden, "Zero Baseline")
    assert result.status == "pass" and result.examined == 1


def test_number_formats_catch_inconsistent_decimals_within_one_unit(tmp_path):
    """'EUR 2.3M' beside the golden table's 'EUR 42M' reads as two confidence levels."""
    path = deck(tmp_path, _add(2, 0.374, 5.3, 8.0, 0.4, "EUR 2.3M in new FX fees"))
    result = check(path, "Number Formats")
    assert result.status == "warn" and "decimal precisions" in details(result)


def test_ai_slop_ignores_a_lone_hit_and_reads_through_a_curly_apostrophe(tmp_path):
    lone = check(
        deck(
            tmp_path,
            _add(2, 0.374, 5.3, 8.0, 0.4, "Card payments settle seamlessly"),
            name="1.pptx",
        ),
        "AI Slop",
    )
    assert lone.status == "pass", lone.details
    curly = f"In today{chr(0x2019)}s fast-paced world we must unlock value"
    matched = check(deck(tmp_path, _add(2, 0.374, 5.3, 12.0, 0.4, curly), name="2.pptx"), "AI Slop")
    assert matched.status == "warn", matched.message


def test_slide_titles_catch_a_missing_title_and_exempt_the_text_free_back_cover(tmp_path):
    path = deck(tmp_path, lambda prs: remove(shape_with_text(slide(prs, 4), TITLES[4])))
    result = check(path, "Slide Titles")
    assert result.status == "fail"
    assert "Slide 4" in details(result) and "no title" in details(result)
    assert "1 text-free slide(s) exempt" in result.message


def test_bank_branding_counts_a_body_mention_without_calling_it_a_comparison(tmp_path):
    """Only a chart that plots two or more banks has marks to colour."""
    path = deck(tmp_path, _add(2, 0.374, 5.3, 8.0, 0.4, "Eurobank and NBG both grew mobile users"))
    result = check(path, "Bank Branding")
    assert result.status == "skipped" and "2 bank name(s) found" in result.message


def test_print_results_returns_false_only_when_something_failed(capsys):
    warning = nv.ValidationResult("W", False, "found", ["a finding"], severity="warning")
    error = nv.ValidationResult("E", False, "broke")
    empty = nv.ValidationResult("S", True, "nothing to look at", examined=0)
    assert warning.warned and not warning.passed and warning.status == "warn"
    assert empty.skipped and empty.status == "skipped"
    assert nv.print_results([warning, empty], "x", color=False) is True
    assert nv.print_results([error], "x", color=False) is False
    assert "examined nothing" in capsys.readouterr().out


def test_font_sizes_report_the_sizes_used(golden):
    """It once walked a:rPr only and printed an empty 'Sizes used:'."""
    result = check(golden, "Font Sizes")
    used = result.message.split("Sizes used:", 1)[1]
    assert "9.0pt" in used and "24.0pt" in used and "48.0pt" in used
