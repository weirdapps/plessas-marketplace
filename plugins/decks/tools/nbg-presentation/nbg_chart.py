#!/usr/bin/env python3
"""Native PowerPoint charts in the NBG chart style, for nbg_build.py.

Every value comes from tokens.yaml `charts`: the palette, the 12pt axis, label and
legend type, the 3.5pt line with hollow circle markers, the 55% doughnut hole, the
waterfall colours. Two things python-pptx gets wrong by default are set explicitly
on every chart, because PowerPoint shows the theme colour whenever the chart part
does not name one:

- a line series takes its colour from `c:spPr/a:ln`, not from a fill, so writing
  the palette into the fill left every line chart in Office blue and red;
- a stacked or in-bar label needs its own colour, measured against the fill it
  sits on, or it inherits #202020 and reads at 1.27:1 on a dark teal segment.

`area_line` is a line chart with an area chart under it on the same axes: python-
pptx cannot write a combination chart, so the area series are added to the plot
area as XML after the line chart is built.

A chart comparing the systemic banks (tokens.yaml `banks`) draws each bank in its
brand colour. When logos go under the category axis, the plot area is placed
exactly (a manual layout) so that nbg_build can put each logo under its own bar.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lxml import etree
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import (
    XL_CHART_TYPE,
    XL_LABEL_POSITION,
    XL_LEGEND_POSITION,
    XL_MARKER_STYLE,
    XL_TICK_LABEL_POSITION,
    XL_TICK_MARK,
)
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nbg_spec  # noqa: E402
import nbg_tokens  # noqa: E402
from nbg_color import AA_NORMAL, contrast_ratio  # noqa: E402
from nbg_text import metrics  # noqa: E402

CHARTS = nbg_tokens.load()["charts"]
FONT = str(CHARTS["font"])
PALETTE = nbg_tokens.chart_palette()
BANKS = nbg_tokens.load()["banks"]
LOGOS = nbg_tokens.load()["components"]["bank_logos"]
FIT = 0.97  # the measuring margin nbg_build uses: 97% of a width counts as full

XL_TYPES = {
    "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "bar_stacked": XL_CHART_TYPE.COLUMN_STACKED,
    "bar_horizontal": XL_CHART_TYPE.BAR_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
    "area_line": XL_CHART_TYPE.LINE_MARKERS,
    "doughnut": XL_CHART_TYPE.DOUGHNUT,
}

# The dark candidate for a label sitting on a coloured fill. PURE BLACK, not the
# #202020 body text: see label_text_color for why the difference decides AA.
LABEL_DARK_HEX = "000000"


def hexcolor(token: str) -> str:
    return str(nbg_tokens.color(token))


def rgb(token: str) -> RGBColor:
    return RGBColor.from_string(hexcolor(token))


def label_text_color(fill_hex: str) -> RGBColor:
    """White or black, whichever contrasts more with the fill a label sits on.

    colors.md offers an R+G+B > 400 rule of thumb, which misreads the cyan #00ADBF
    used for chart series: dark text clears 6:1 on it where white manages 2.7:1.
    Measure the contrast and take the better of the two.

    The dark candidate has to be pure black. For any candidate pair the worst case
    is the fill luminance where the two curves cross, and only black puts that
    crossing above the 4.5:1 AA floor:

        black   crossover at L=0.1791, best available ratio 4.583:1  clears AA
        #202020 crossover at L=0.2101, best available ratio 4.036:1  fails AA

    These labels are 12pt bold, which is not WCAG large text (that needs 14pt bold),
    so the floor is 4.5:1. Hand-specified dark text stays #202020 everywhere else.
    """
    white = contrast_ratio(fill_hex, "FFFFFF")
    dark = contrast_ratio(fill_hex, LABEL_DARK_HEX)
    if max(white, dark) < AA_NORMAL:
        raise ValueError(
            f"no AA-compliant label colour for fill #{fill_hex}: white {white:.2f}:1, "
            f"black {dark:.2f}:1, both under {AA_NORMAL}:1"
        )
    return RGBColor.from_string("FFFFFF" if white > dark else LABEL_DARK_HEX)


def default_number_format(values: list[Any]) -> str:
    """Thousands separator and the data's own precision, at most two decimals."""
    decimals = 0
    for v in values:
        if isinstance(v, float) and not v.is_integer():
            text = f"{v:.6f}".rstrip("0")
            decimals = max(decimals, min(2, len(text.split(".")[1])))
    return "#,##0" + ("." + "0" * decimals if decimals else "")


def _all_values(series: list[dict[str, Any]]) -> list[Any]:
    return [v for s in series for v in (s.get("values") or []) if v is not None]


# ---------------------------------------------------------------- peer banks


def bank_colours(spec: dict[str, Any]) -> tuple[list[str], list[str] | None]:
    """(colour per series, colour per point or None). A bank comparison paints each
    bank in its brand colour, per series or per point, and mutes whatever else shares
    the chart (a market average). Any other chart takes the palette in order."""
    count = len(spec["data"]["series"])
    palette = [PALETTE[i % len(PALETTE)] for i in range(count)]
    plan = nbg_spec.bank_plan(spec)
    if plan is None:
        return palette, None
    mode, banks = plan
    muted = hexcolor(CHARTS["highlight"]["muted"])
    colours = [str(BANKS[b]["color"]) if b else muted for b in banks]
    return (colours, None) if mode == "series" else (palette, colours)


def logo_path(bank: str) -> Path:
    return Path(nbg_spec.ASSETS_DIR) / str(BANKS[bank]["logo"])


def logo_width(bank: str, height: float) -> float:
    """The width a bank's logo takes at `height`, keeping its own aspect (Standard #4)."""
    from PIL import Image

    with Image.open(logo_path(bank)) as img:
        w_px, h_px = img.size
    return float(height * w_px / h_px)


@dataclass(frozen=True)
class AxisLayout:
    """Where a bank bar chart's plot sits in its frame, and where each logo goes."""

    inner: tuple[float, float, float, float]  # x, y, w, h as fractions of the frame
    anchors: list[tuple[float, float]]  # each category's logo centre, in slide inches
    logo_h: float


def _value_text(value: Any, number_format: str) -> str:
    """Roughly what a data label shows, so its width can be measured."""
    if value is None:
        return ""
    decimals = number_format.split(".")[1].count("0") if "." in number_format else 0
    if number_format.endswith("%"):
        return f"{float(value) * 100:,.{decimals}f}%"
    return f"{float(value):,.{decimals}f}"


def axis_layout(spec: dict[str, Any], box: tuple[float, float, float, float]) -> AxisLayout:
    """The plot area of a bank bar chart, leaving room for the logos: a band under the
    category labels of a column chart, a column left of them on a horizontal one.
    Raises ValueError when the frame cannot keep a readable plot beside the logos."""
    x, y, w, h = box
    categories = [str(c) for c in spec["data"]["categories"]]
    n = len(categories)
    plan = nbg_spec.bank_plan(spec)
    banks = plan[1] if plan else [None] * n
    logo_h, gap = float(LOGOS["h"]), float(LOGOS["gap"])
    m = metrics()
    axis_pt = float(nbg_tokens.get("type.chart_axis.size"))
    label_pt = float(nbg_tokens.get("type.chart_data_label.size"))
    values = spec["data"]["series"][0]["values"]
    number_format = str(spec.get("number_format") or default_number_format(values))
    if spec["type"] == "bar_horizontal":
        column = max(logo_width(b, logo_h) for b in banks if b)
        labels_w = max(m.width(c, axis_pt, False) for c in categories) / FIT + gap
        values_w = (
            max(m.width(_value_text(v, number_format), label_pt, True) for v in values) / FIT
            + 2 * gap
        )
        plot_w = w - column - gap - labels_w - values_w
        if plot_w < 1.5:
            raise ValueError(f"the bars get {plot_w:.2f} in beside the logos and labels")
        pad = 0.05
        inner = ((column + gap + labels_w) / w, pad / h, plot_w / w, (h - 2 * pad) / h)
        anchors = [
            (x + column / 2, y + h * (inner[1] + inner[3] * (j + 0.5) / n)) for j in range(n)
        ]
        return AxisLayout(inner, anchors, logo_h)
    top = m.line_height(label_pt, 1.0) + gap
    labels_h = m.line_height(axis_pt, 1.0) + gap
    plot_h = h - top - labels_h - gap - logo_h
    if plot_h < 1.0:
        raise ValueError(f"the bars get {plot_h:.2f} in above the logos")
    logo_y = y + top + plot_h + labels_h + gap + logo_h / 2
    anchors = [(x + w * (j + 0.5) / n, logo_y) for j in range(n)]
    return AxisLayout((0.0, top / h, 1.0, plot_h / h), anchors, logo_h)


def _manual_layout(chart: Any, inner: tuple[float, float, float, float]) -> None:
    """Place the plot area's inner rectangle (the bars, not their labels) exactly."""
    plot_area = chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    layout = plot_area.find(qn("c:layout"))
    if layout is None:
        layout = etree.Element(qn("c:layout"))
        plot_area.insert(0, layout)  # CT_PlotArea: layout? comes first
    for child in list(layout):
        layout.remove(child)
    manual = etree.SubElement(layout, qn("c:manualLayout"))
    etree.SubElement(manual, qn("c:layoutTarget")).set("val", "inner")
    etree.SubElement(manual, qn("c:xMode")).set("val", "edge")
    etree.SubElement(manual, qn("c:yMode")).set("val", "edge")
    for tag, value in zip(("c:x", "c:y", "c:w", "c:h"), inner, strict=True):
        etree.SubElement(manual, qn(tag)).set("val", f"{value:.4f}")


# ---------------------------------------------------------------- alt text

ALT = {
    "en": {
        "bar": "Column chart",
        "bar_stacked": "Stacked column chart",
        "bar_horizontal": "Horizontal bar chart",
        "line": "Line chart",
        "area_line": "Area line chart",
        "doughnut": "Doughnut chart",
        "waterfall": "Waterfall chart",
        "series": "series",
        "categories": "categories",
        "to": "to",
        "from": "from",
        "steps": "steps",
    },
    "el": {
        "bar": "Ραβδόγραμμα στηλών",
        "bar_stacked": "Σωρευτικό ραβδόγραμμα",
        "bar_horizontal": "Οριζόντιο ραβδόγραμμα",
        "line": "Γράφημα γραμμής",
        "area_line": "Γράφημα γραμμής με περιοχή",
        "doughnut": "Γράφημα δακτυλίου",
        "waterfall": "Γράφημα καταρράκτη",
        "series": "σειρές",
        "categories": "κατηγορίες",
        "to": "έως",
        "from": "από",
        "steps": "βήματα",
    },
}


def chart_alt_text(
    chart_type: str, categories: list[Any], series: list[dict[str, Any]], lang: str
) -> str:
    """What the chart plots, in how many series, over which span. Never the title."""
    words = ALT["el" if lang == "el" else "en"]
    names = ", ".join(
        str(s.get("name", "")).strip() for s in series if str(s.get("name", "")).strip()
    )
    parts = [words.get(chart_type, chart_type)]
    parts.append(f"{len(series)} {words['series']}" + (f" ({names})" if names else ""))
    if categories:
        span = (
            f"{categories[0]} {words['to']} {categories[-1]}"
            if len(categories) > 1
            else str(categories[0])
        )
        parts.append(f"{len(categories)} {words['categories']}, {span}")
    return ". ".join(parts) + "."


# ---------------------------------------------------------------- shared styling


def _set_font(
    font: Any, role: str, *, color_hex: str | None = None, bold: bool | None = None
) -> None:
    style = nbg_tokens.type_style(role)
    font.name = FONT
    font.size = Pt(style["size"])
    font.bold = style["bold"] if bold is None else bold
    font.color.rgb = RGBColor.from_string(color_hex or style["color"])


def _no_line(fmt: Any) -> None:
    fmt.line.fill.background()


def _chart_space(chart: Any) -> None:
    """No title, square corners, transparent chart area, Aptos for every chart text."""
    chart.has_title = False
    cs = chart._chartSpace
    rounded = cs.find(qn("c:roundedCorners"))
    if rounded is None:
        # CT_ChartSpace: date1904?, lang?, roundedCorners?, AlternateContent?,
        # clrMapOvr?, pivotSource?, protection?, chart. Absent means rounded.
        rounded = etree.Element(qn("c:roundedCorners"))
        successors = (
            "c:AlternateContent",
            "c:clrMapOvr",
            "c:pivotSource",
            "c:protection",
            "c:chart",
        )
        anchor = next(el for tag in successors if (el := cs.find(qn(tag))) is not None)
        anchor.addprevious(rounded)
    rounded.set("val", "0")
    chart.font.name = FONT
    chart.font.size = Pt(nbg_tokens.get("type.chart_axis.size"))
    chart.font.color.rgb = rgb(str(nbg_tokens.get("type.chart_axis.color")))
    # Chart area: no fill, no border. spPr follows c:chart in CT_ChartSpace.
    sppr = cs.find(qn("c:spPr"))
    if sppr is None:
        sppr = etree.Element(qn("c:spPr"))
        cs.find(qn("c:chart")).addnext(sppr)
    for child in list(sppr):
        sppr.remove(child)
    etree.SubElement(sppr, qn("a:noFill"))
    ln = etree.SubElement(sppr, qn("a:ln"))
    etree.SubElement(ln, qn("a:noFill"))
    plot_area = chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    _plot_area_clear(plot_area)
    _positive_axis_ids(cs)


def _positive_axis_ids(chart_space: Any) -> None:
    """python-pptx's chart templates hard-code negative axis ids (-2068027336), which
    ST_UnsignedIntHex rejects: every such chart failed schema validation. Flip the
    sign on every id and on every reference to it."""
    for tag in ("c:axId", "c:crossAx"):
        for el in chart_space.iter(qn(tag)):
            value = int(el.get("val", "0"))
            if value < 0:
                el.set("val", str(-value))


def _plot_area_clear(plot_area: Any) -> None:
    """A transparent, borderless plot area. spPr sits after the axes in CT_PlotArea."""
    sppr = plot_area.find(qn("c:spPr"))
    if sppr is None:
        sppr = etree.SubElement(plot_area, qn("c:spPr"))
        ext = plot_area.find(qn("c:extLst"))
        if ext is not None:
            plot_area.remove(sppr)
            ext.addprevious(sppr)
    for child in list(sppr):
        sppr.remove(child)
    etree.SubElement(sppr, qn("a:noFill"))
    ln = etree.SubElement(sppr, qn("a:ln"))
    etree.SubElement(ln, qn("a:noFill"))


def _category_axis(chart: Any, *, reverse: bool = False) -> None:
    axis = chart.category_axis
    style = CHARTS["category_axis"]
    _set_font(axis.tick_labels.font, "chart_axis", color_hex=hexcolor(style["color"]))
    axis.has_major_gridlines = False
    axis.has_minor_gridlines = False
    axis.major_tick_mark = XL_TICK_MARK.NONE
    axis.minor_tick_mark = XL_TICK_MARK.NONE
    axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    axis.format.line.color.rgb = rgb(style["line"])
    axis.format.line.width = Pt(style["line_pt"])
    if reverse:
        axis.reverse_order = True


def _value_axis(chart: Any, *, visible: bool, number_format: str) -> None:
    axis = chart.value_axis
    axis.has_major_gridlines = False
    axis.has_minor_gridlines = False
    axis.major_tick_mark = XL_TICK_MARK.NONE
    axis.minor_tick_mark = XL_TICK_MARK.NONE
    if not visible:
        axis.visible = False
        return
    muted = hexcolor(CHARTS["value_axis"]["muted_color"])
    font = axis.tick_labels.font
    font.name = FONT
    font.size = Pt(CHARTS["value_axis"]["size"])
    font.bold = False
    font.color.rgb = RGBColor.from_string(muted)
    axis.tick_labels.number_format = number_format
    axis.tick_labels.number_format_is_linked = False
    axis.format.line.fill.background()


def _legend(chart: Any, show: bool) -> None:
    chart.has_legend = show
    if not show:
        return
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    _set_font(chart.legend.font, "chart_legend")


def _labels(
    labels: Any, number_format: str, *, color_hex: str | None = None, position: Any = None
) -> None:
    labels.number_format = number_format
    labels.number_format_is_linked = False
    labels.show_value = True
    labels.show_category_name = False
    labels.show_series_name = False
    labels.show_legend_key = False
    _set_font(labels.font, "chart_data_label", color_hex=color_hex)
    if position is not None:
        labels.position = position


def _delete_point_label(point: Any) -> None:
    """Hide one point's label. Blanking the text is not enough: showVal still wins."""
    dlbl = point.data_label._get_or_add_dLbl()
    for child in list(dlbl):
        if child.tag != qn("c:idx"):
            dlbl.remove(child)
    etree.SubElement(dlbl, qn("c:delete")).set("val", "1")


# ---------------------------------------------------------------- chart types


def _style_bars(
    chart: Any,
    spec: dict[str, Any],
    number_format: str,
    series_colours: list[str],
    point_colours: list[str] | None,
) -> None:
    ctype = spec["type"]
    plot = chart.plots[0]
    plot.gap_width = int(CHARTS["bar"]["gap_width"])
    stacked = ctype == "bar_stacked"
    if stacked:
        plot.overlap = int(CHARTS["bar"]["overlap_stacked"])
    series_list = list(plot.series)
    highlight = spec.get("highlight_category")
    categories = [str(c) for c in spec["data"]["categories"]]
    for i, series in enumerate(series_list):
        fill = series_colours[i]
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = RGBColor.from_string(fill)
        _no_line(series.format)
        series.invert_if_negative = False
        values = spec["data"]["series"][i]["values"]
        if stacked:
            _labels(
                series.data_labels,
                number_format,
                color_hex=str(label_text_color(fill)),
                position=XL_LABEL_POSITION.CENTER,
            )
            for point, value in zip(series.points, values, strict=False):
                if value in (None, 0):
                    _delete_point_label(point)
        if point_colours is not None:
            # Each bank's bar in its brand colour; the labels sit outside, on white.
            for point, colour in zip(series.points, point_colours, strict=False):
                point.format.fill.solid()
                point.format.fill.fore_color.rgb = RGBColor.from_string(colour)
                _no_line(point.format)
        elif highlight is not None and len(series_list) == 1:
            accent = hexcolor(CHARTS["highlight"]["accent"])
            muted = hexcolor(CHARTS["highlight"]["muted"])
            for point, category in zip(series.points, categories, strict=False):
                point.format.fill.solid()
                point.format.fill.fore_color.rgb = RGBColor.from_string(
                    accent if category == str(highlight) else muted
                )
                _no_line(point.format)
    if not stacked:
        plot.has_data_labels = True
        _labels(plot.data_labels, number_format, position=XL_LABEL_POSITION.OUTSIDE_END)
    _category_axis(chart, reverse=ctype == "bar_horizontal")
    _value_axis(chart, visible=CHARTS["value_axis"]["bar"] != "hidden", number_format=number_format)


def _style_line_series(series: Any, colour: str) -> None:
    line_cfg = CHARTS["line"]
    width = Pt(line_cfg["width_pt"])
    series.format.line.color.rgb = RGBColor.from_string(colour)
    series.format.line.width = width
    series.smooth = bool(line_cfg["smooth"])
    marker = series.marker
    marker.style = XL_MARKER_STYLE.CIRCLE
    marker.size = int(line_cfg["marker_size"])
    marker.format.fill.solid()
    marker.format.fill.fore_color.rgb = rgb(line_cfg["marker_fill"])
    marker.format.line.color.rgb = RGBColor.from_string(colour)
    marker.format.line.width = width


def _style_lines(
    chart: Any, spec: dict[str, Any], number_format: str, series_colours: list[str]
) -> None:
    plot = chart.plots[0]
    plot.has_data_labels = False
    for i, series in enumerate(plot.series):
        _style_line_series(series, series_colours[i])
    _category_axis(chart)
    _value_axis(
        chart, visible=CHARTS["value_axis"]["line"] != "hidden", number_format=number_format
    )
    if spec["type"] == "area_line":
        _add_area_under_lines(chart, series_colours)


def _add_area_under_lines(chart: Any, colours: list[str]) -> None:
    """Put an area chart under the line chart, on the same axes: the 15% fill."""
    plot_area = chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea"))
    line_chart = plot_area.find(qn("c:lineChart"))
    series = line_chart.findall(qn("c:ser"))
    alpha = int(round(float(CHARTS["area_line"]["fill_alpha"]) * 100000))
    area = etree.Element(qn("c:areaChart"))
    etree.SubElement(area, qn("c:grouping")).set("val", "standard")
    etree.SubElement(area, qn("c:varyColors")).set("val", "0")
    offset = len(series)
    for i, ser in enumerate(series):
        colour = colours[i]
        new = etree.SubElement(area, qn("c:ser"))
        etree.SubElement(new, qn("c:idx")).set("val", str(offset + i))
        etree.SubElement(new, qn("c:order")).set("val", str(offset + i))
        tx = ser.find(qn("c:tx"))
        if tx is not None:
            new.append(copy.deepcopy(tx))
        sppr = etree.SubElement(new, qn("c:spPr"))
        fill = etree.SubElement(sppr, qn("a:solidFill"))
        clr = etree.SubElement(fill, qn("a:srgbClr"))
        clr.set("val", colour)
        etree.SubElement(clr, qn("a:alpha")).set("val", str(alpha))
        ln = etree.SubElement(sppr, qn("a:ln"))
        etree.SubElement(ln, qn("a:noFill"))
        for tag in ("c:cat", "c:val"):
            el = ser.find(qn(tag))
            if el is not None:
                new.append(copy.deepcopy(el))
    for ax_id in line_chart.findall(qn("c:axId")):
        area.append(copy.deepcopy(ax_id))
    line_chart.addprevious(area)
    legend = chart._chartSpace.find(qn("c:chart")).find(qn("c:legend"))
    if legend is not None:
        # Legend entries follow plot order, and the area chart comes first so it draws
        # under the lines: entries 0..n-1 are the area copies.
        _hide_legend_entries(legend, range(offset))


def _hide_legend_entries(legend: Any, indices: Any) -> None:
    """The area copies share the lines' names; one legend entry per series is enough."""
    anchor = legend.find(qn("c:legendPos"))
    for idx in indices:
        entry = etree.Element(qn("c:legendEntry"))
        etree.SubElement(entry, qn("c:idx")).set("val", str(idx))
        etree.SubElement(entry, qn("c:delete")).set("val", "1")
        anchor.addnext(entry)
        anchor = entry


def _point_label_shows(label: Any, number_format: str, *, percent: bool) -> None:
    """A point's own c:dLbl overrides the series labels entirely, flags included, so
    it has to say what to show (and in which format) itself."""
    dlbl = label._get_or_add_dLbl()
    flags = {
        "c:showLegendKey": "0",
        "c:showVal": "0" if percent else "1",
        "c:showCatName": "0",
        "c:showSerName": "0",
        "c:showPercent": "1" if percent else "0",
        "c:showBubbleSize": "0",
    }
    for tag, value in flags.items():
        el = dlbl.find(qn(tag))
        if el is not None:
            el.set("val", value)
    if dlbl.find(qn("c:numFmt")) is None:
        fmt = etree.Element(qn("c:numFmt"))
        fmt.set("formatCode", number_format)
        fmt.set("sourceLinked", "0")
        # CT_DLbl: idx, layout?, tx?, numFmt?, spPr?, txPr?, dLblPos?, show*...
        anchor = next(
            (
                el
                for tag in ("c:spPr", "c:txPr", "c:dLblPos", "c:showLegendKey")
                if (el := dlbl.find(qn(tag))) is not None
            ),
            None,
        )
        if anchor is not None:
            anchor.addprevious(fmt)
        else:
            dlbl.append(fmt)


def _style_doughnut(chart: Any, spec: dict[str, Any], point_colours: list[str] | None) -> None:
    plot = chart.plots[0]
    doughnut = (
        chart._chartSpace.find(qn("c:chart")).find(qn("c:plotArea")).find(qn("c:doughnutChart"))
    )
    hole = doughnut.find(qn("c:holeSize"))
    if hole is None:
        hole = etree.SubElement(doughnut, qn("c:holeSize"))
    hole.set("val", str(int(CHARTS["doughnut"]["hole_size"])))
    first = doughnut.find(qn("c:firstSliceAng"))
    if first is None:
        first = etree.Element(qn("c:firstSliceAng"))
        hole.addprevious(first)
    first.set("val", "0")
    as_percent = not spec.get("number_format")
    number_format = "0%" if as_percent else str(spec["number_format"])
    series = plot.series[0]
    for i, point in enumerate(series.points):
        fill = point_colours[i] if point_colours else PALETTE[i % len(PALETTE)]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = RGBColor.from_string(fill)
        point.format.line.color.rgb = RGBColor.from_string("FFFFFF")
        point.format.line.width = Pt(1)
        label = point.data_label
        _set_font(label.font, "chart_data_label", color_hex=str(label_text_color(fill)))
        # No position: a doughnut draws its labels on the ring, and PowerPoint does
        # not accept dLblPos on a doughnut at all (its PDF export hung on one).
        _point_label_shows(label, number_format, percent=as_percent)
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.number_format = number_format
    labels.number_format_is_linked = False
    labels.show_percentage = as_percent
    labels.show_value = not as_percent
    labels.show_category_name = False
    labels.show_series_name = False
    labels.show_legend_key = False
    _set_font(labels.font, "chart_data_label")


def add_chart(
    slide: Any,
    spec: dict[str, Any],
    box: tuple[float, float, float, float],
    lang: str,
    alt_text: str | None = None,
    *,
    legend: bool | None = None,
    layout: AxisLayout | None = None,
) -> Any:
    """Draw spec (a deck.schema.json `chart`) into box (x, y, w, h in inches).

    legend overrides the spec's show_legend (False when a logo legend replaces it);
    layout places the plot area exactly, for logos along the category axis."""
    ctype = spec["type"]
    data = spec["data"]
    categories = [str(c) for c in data["categories"]]
    series_specs = data["series"]
    values = _all_values(series_specs)
    number_format = str(spec.get("number_format") or default_number_format(values))
    chart_data = CategoryChartData(number_format=number_format)
    chart_data.categories = categories
    for s in series_specs:
        chart_data.add_series(str(s.get("name", "")), list(s["values"]))
    x, y, w, h = box
    frame = slide.shapes.add_chart(
        XL_TYPES[ctype], Inches(x), Inches(y), Inches(w), Inches(h), chart_data
    )
    chart = frame.chart
    _chart_space(chart)
    series_colours, point_colours = bank_colours(spec)
    # A doughnut's legend is what names its slices; otherwise one series needs none.
    default_legend = ctype == "doughnut" or len(series_specs) > 1
    shown = bool(spec.get("show_legend", default_legend)) if legend is None else legend
    _legend(chart, shown)
    if ctype in ("bar", "bar_stacked", "bar_horizontal"):
        _style_bars(chart, spec, number_format, series_colours, point_colours)
    elif ctype in ("line", "area_line"):
        _style_lines(chart, spec, number_format, series_colours)
    else:
        _style_doughnut(chart, spec, point_colours)
    if layout is not None:
        _manual_layout(chart, layout.inner)
    set_alt_text(frame, alt_text or chart_alt_text(ctype, categories, series_specs, lang))
    return frame


# ---------------------------------------------------------------- waterfall


def waterfall_segments(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each bar as {label, value, kind, start, end}. First and last are totals by default."""
    out = []
    running = 0.0
    last = len(items) - 1
    for i, item in enumerate(items):
        value = float(item["value"])
        total = bool(item.get("total", i in (0, last)))
        if total:
            start, end, kind = 0.0, value, "total"
        else:
            start, end = running, running + value
            kind = "increase" if value >= 0 else "decrease"
        running = end
        out.append(
            {"label": str(item["label"]), "value": value, "kind": kind, "start": start, "end": end}
        )
    return out


def _split(start: float, end: float) -> tuple[float, float, float]:
    """(invisible base, visible positive part, visible negative part) of one bar.

    A stacked column stacks positive values up from zero and negative values down
    from zero, each in series order, so a floating bar that crosses zero needs its
    two halves in two series and no base at all.
    """
    lo, hi = min(start, end), max(start, end)
    if lo >= 0:
        return lo, hi - lo, 0.0
    if hi <= 0:
        return hi, 0.0, lo - hi
    return 0.0, hi, lo


def _format_delta(value: float, kind: str, number_format: str) -> str:
    decimals = number_format.split(".")[1].count("0") if "." in number_format else 0
    text = f"{abs(value):,.{decimals}f}"
    if kind == "total":
        return f"-{text}" if value < 0 else text
    return f"+{text}" if value >= 0 else f"-{text}"


def add_waterfall(
    slide: Any,
    spec: dict[str, Any],
    box: tuple[float, float, float, float],
    lang: str,
    alt_text: str | None = None,
) -> Any:
    """A bridge drawn as a stacked column with an invisible base (python-pptx has no
    native waterfall). Totals dark teal, increases cyan, decreases alert red; every
    label is the signed contribution, written as text so it reads right in any viewer.

    Four series: the invisible base, the part of each bar above zero, the part below
    zero, and an empty label carrier. Each visible part takes its kind's colour point
    by point, so the chart never looks like more than the one exhibit it is.

    A step's label sits just above its bar, on the carrier stacked on top: inside a
    thin bar a centred label runs over both edges. Totals, and steps below zero, keep
    a centred label in the bar."""
    cfg = CHARTS["waterfall"]
    segments = waterfall_segments(spec["data"]["items"])
    values = [s["value"] for s in segments]
    number_format = str(spec.get("number_format") or default_number_format(values))
    colours = {
        "total": hexcolor(cfg["total_color"]),
        "increase": hexcolor(cfg["increase_color"]),
        "decrease": hexcolor(cfg["decrease_color"]),
    }
    parts = [_split(seg["start"], seg["end"]) for seg in segments]
    chart_data = CategoryChartData(number_format=number_format)
    chart_data.categories = [s["label"] for s in segments]
    chart_data.add_series("Base", [b for b, _, _ in parts])
    chart_data.add_series("Above zero", [pos for _, pos, _ in parts])
    chart_data.add_series("Below zero", [neg for _, _, neg in parts])
    chart_data.add_series("Labels", [0.0] * len(segments))
    x, y, w, h = box
    frame = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_STACKED, Inches(x), Inches(y), Inches(w), Inches(h), chart_data
    )
    chart = frame.chart
    _chart_space(chart)
    chart.has_legend = False
    plot = chart.plots[0]
    plot.gap_width = int(cfg["gap_width"])
    plot.overlap = 100
    base_series, above_zero, below_zero, carrier = plot.series
    for invisible in (base_series, carrier):
        invisible.format.fill.background()
        _no_line(invisible.format)
    for series in (above_zero, below_zero):
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = RGBColor.from_string(colours["total"])
        _no_line(series.format)
        series.invert_if_negative = False
    for index, (seg, (_, pos, neg)) in enumerate(zip(segments, parts, strict=True)):
        for series, part in ((above_zero, pos), (below_zero, neg)):
            if part:
                point = series.points[index]
                point.format.fill.solid()
                point.format.fill.fore_color.rgb = RGBColor.from_string(colours[seg["kind"]])
                _no_line(point.format)
    above = hexcolor(str(nbg_tokens.get("type.chart_data_label.color")))
    for index, (seg, (_, pos, neg)) in enumerate(zip(segments, parts, strict=True)):
        floating_above_zero = seg["kind"] != "total" and neg == 0
        if floating_above_zero:
            label = carrier.points[index].data_label
            position, colour = XL_LABEL_POSITION.INSIDE_BASE, above
        else:
            holder = above_zero if pos != 0 or neg == 0 else below_zero
            label = holder.points[index].data_label
            position, colour = XL_LABEL_POSITION.CENTER, str(label_text_color(colours[seg["kind"]]))
        tf = label.text_frame
        tf.text = _format_delta(seg["value"], seg["kind"], number_format)
        for run in tf.paragraphs[0].runs:
            _set_font(run.font, "chart_data_label", color_hex=colour)
        label.position = position
    _category_axis(chart)
    _value_axis(chart, visible=False, number_format=number_format)
    words = ALT["el" if lang == "el" else "en"]
    default_alt = (
        f"{words['waterfall']}. {words['from']} {segments[0]['label']} "
        f"{_format_delta(segments[0]['value'], 'total', number_format)} {words['to']} "
        f"{segments[-1]['label']} {_format_delta(segments[-1]['value'], 'total', number_format)}, "
        f"{len(segments)} {words['steps']}."
    )
    set_alt_text(frame, alt_text or default_alt)
    return frame


def set_alt_text(shape: Any, text: str) -> None:
    """Write OOXML alt text (p:cNvPr/@descr). python-pptx exposes no API for it."""
    nv = shape._element.find(f".//{qn('p:cNvPr')}")
    if nv is not None:
        nv.set("descr", text)
