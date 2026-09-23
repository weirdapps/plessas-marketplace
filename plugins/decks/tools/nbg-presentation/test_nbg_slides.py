"""Every slide type in deck.schema.json, built and read back from the OOXML.

test_nbg_build.py holds the defect tests; this file checks that each slide type
draws what its spec says, and that the chrome (notes, alt text, language tags,
images) is on every slide that needs it.
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import nbg_build
import pytest
from pptx import Presentation
from testkit import (
    EXAMPLES_DIR,
    NS,
    chart_parts,
    deck,
    inches,
    part_xml,
    passing_validator,
    shape_boxes,
    shape_by_text,
    slide_xml,
    write_spec,
)

A = f"{{{NS['a']}}}"
P = f"{{{NS['p']}}}"
C = f"{{{NS['c']}}}"
SCRIPT = Path(__file__).parent / "nbg_build.py"
SOURCE = {"name": "Management accounts", "as_of": "30 June 2026"}


@pytest.fixture
def build(tmp_path, monkeypatch):
    passing_validator(monkeypatch, nbg_build)

    def _build(spec, name="deck"):
        path = write_spec(tmp_path, spec, f"{name}.yaml")
        out = tmp_path / f"{name}.pptx"
        nbg_build.build_presentation(path, out)
        return out

    return _build


def _chart_slide(chart_type, series=None, **extra):
    series = series or [{"name": "2025", "values": [1, 2]}, {"name": "2026", "values": [2, 3]}]
    return {
        "type": "chart",
        "content": {"title": f"A {chart_type} chart", "source": SOURCE},
        "chart": {
            "type": chart_type,
            "data": {"categories": ["Q1", "Q2"], "series": series},
            **extra,
        },
    }


def _shapes_with_fill(root, colour):
    return [
        sp
        for sp in root.iter(f"{P}sp")
        if (fill := sp.find("p:spPr/a:solidFill/a:srgbClr", NS)) is not None
        and fill.get("val") == colour
    ]


# ---------------------------------------------------------------- charts


@pytest.mark.parametrize(
    "chart_type,element,checks",
    [
        ("bar", "barChart", {"c:barDir": "col", "c:grouping": "clustered"}),
        (
            "bar_stacked",
            "barChart",
            {"c:barDir": "col", "c:grouping": "stacked", "c:overlap": "100"},
        ),
        ("bar_horizontal", "barChart", {"c:barDir": "bar", "c:grouping": "clustered"}),
        ("line", "lineChart", {"c:grouping": "standard"}),
    ],
)
def test_each_bar_and_line_type_writes_its_own_chart_element(build, chart_type, element, checks):
    out = build(deck([_chart_slide(chart_type)]))
    root = part_xml(out, chart_parts(out)[0])
    plot = root.find(f".//c:{element}", NS)
    assert plot is not None
    for tag, value in checks.items():
        assert plot.find(tag, NS).get("val") == value, tag
    if chart_type == "bar_horizontal":
        orientation = root.find(".//c:catAx/c:scaling/c:orientation", NS)
        assert orientation.get("val") == "maxMin", "first category must read on top"


def test_area_line_shades_only_under_the_first_series(build):
    """E2E-OUTPUT-03: a 15% area under every series blended into a brown-grey wash
    with three or more lines, bank colours worst. The area now sits under the first
    series only, and the others are plain lines."""
    series = [{"name": n, "values": [1, 2]} for n in ("A", "B", "C")]
    out = build(deck([_chart_slide("area_line", series=series)]))
    root = part_xml(out, chart_parts(out)[0])
    plot_area = root.find(".//c:plotArea", NS)
    kinds = [el.tag.split("}")[1] for el in plot_area if el.tag.endswith("Chart")]
    assert kinds == ["areaChart", "lineChart"], "the area must draw under the lines"
    area = root.findall(".//c:areaChart/c:ser", NS)
    assert len(area) == 1
    first_line = root.find(".//c:lineChart/c:ser/c:spPr/a:ln/a:solidFill/a:srgbClr", NS)
    fill = area[0].find("c:spPr/a:solidFill/a:srgbClr", NS)
    assert fill.get("val") == first_line.get("val")
    assert fill.find("a:alpha", NS).get("val") == "15000"
    area_axes = [a.get("val") for a in root.findall(".//c:areaChart/c:axId", NS)]
    line_axes = [a.get("val") for a in root.findall(".//c:lineChart/c:axId", NS)]
    assert area_axes == line_axes


def test_line_charts_show_a_muted_value_axis_and_no_labels(build):
    out = build(deck([_chart_slide("line")]))
    root = part_xml(out, chart_parts(out)[0])
    assert root.find(".//c:valAx/c:delete", NS).get("val") == "0"
    size = root.find(".//c:valAx/c:txPr//a:defRPr", NS)
    assert size.get("sz") == "1100"
    assert size.find("a:solidFill/a:srgbClr", NS).get("val") == "939793"
    assert (
        root.find(".//c:lineChart/c:dLbls", NS) is None
        or root.find(".//c:lineChart/c:dLbls/c:showVal", NS).get("val") == "0"
    )


def test_bars_hide_the_value_axis_and_label_outside_in_dark_teal(build):
    out = build(deck([_chart_slide("bar")]))
    root = part_xml(out, chart_parts(out)[0])
    # CT_Boolean: <c:delete/> with no val means true.
    assert root.find(".//c:valAx/c:delete", NS).get("val", "1") in ("1", "true")
    labels = root.find(".//c:barChart/c:dLbls", NS)
    assert labels.find("c:dLblPos", NS).get("val") == "outEnd"
    assert labels.find(".//a:defRPr/a:solidFill/a:srgbClr", NS).get("val") == "003841"


def test_the_chart_unit_is_shown_once_in_the_caption_or_above_the_chart(build):
    """DOCS-ACCURACY-3: chart.unit was documented, and used by the excel hand-off, but
    the builder never read it: the unit disappeared from every chart."""
    with_caption = _chart_slide("bar", unit="EUR m")
    with_caption["content"]["description"] = "Fee income by quarter"
    bare = _chart_slide("bar", unit="EUR m")
    bare["content"]["title"] = "A second bar chart"
    already = _chart_slide("bar", unit="EUR m")
    already["content"] = {**already["content"], "title": "A third", "description": "Fees, EUR m"}
    column = {
        "type": "two_column",
        "content": {"title": "Text beside a chart", "source": SOURCE},
        "left": {"kind": "bullets", "points": ["One"]},
        "right": {"kind": "chart", "chart": _chart_slide("bar", unit="EUR m")["chart"]},
    }
    out = build(deck([with_caption, bare, already, column]))
    texts = [[b[0] for b in shape_boxes(slide_xml(out, n))] for n in (2, 3, 4, 5)]
    assert "Fee income by quarter, EUR m" in texts[0]
    assert "EUR m" in texts[1]
    assert "Fees, EUR m" in texts[2] and "Fees, EUR m, EUR m" not in texts[2]
    assert "EUR m" in texts[3]


def test_highlight_category_paints_one_bar_in_the_accent(build):
    slide = _chart_slide(
        "bar", series=[{"name": "2026", "values": [3, 4]}], highlight_category="Q2"
    )
    out = build(deck([slide]))
    root = part_xml(out, chart_parts(out)[0])
    fills = {
        pt.find("c:idx", NS).get("val"): pt.find(".//a:srgbClr", NS).get("val")
        for pt in root.findall(".//c:ser/c:dPt", NS)
    }
    assert fills == {"0": "BEC1BE", "1": "00ADBF"}


def test_doughnut_slices_carry_their_name_and_share_with_no_colour_only_legend(build):
    """E2E-OUTPUT-05: a doughnut named its slices only in a colour-keyed legend
    (Standard #22), and its fourth slice put grey #939793 beside teal #007B85 (1.70:1).
    Each slice now shows its category and share, and the slice colours never put those
    two side by side, the ring's wrap-around included."""
    slide = {
        "type": "chart",
        "content": {"title": "The mix", "source": SOURCE},
        "chart": {
            "type": "doughnut",
            "data": {
                "categories": ["A", "B", "C", "D", "E", "F"],
                "series": [{"name": "Share", "values": [0.3, 0.2, 0.15, 0.15, 0.1, 0.1]}],
            },
        },
    }
    out = build(deck([slide]))
    root = part_xml(out, chart_parts(out)[0])
    point_labels = root.findall(".//c:ser/c:dLbls/c:dLbl", NS)
    assert len(point_labels) == 6
    for dlbl in point_labels:
        assert dlbl.find("c:showPercent", NS).get("val") == "1"
        assert dlbl.find("c:showCatName", NS).get("val") == "1"
        assert dlbl.find("c:showVal", NS).get("val") == "0"
        assert dlbl.find("c:numFmt", NS).get("formatCode") == "0%"
    assert root.find(".//c:legend", NS) is None, "the names are on the slices"
    fills = [pt.find(".//a:srgbClr", NS).get("val") for pt in root.findall(".//c:ser/c:dPt", NS)]
    ring = list(zip(fills, fills[1:] + fills[:1], strict=True))
    assert ("007B85", "939793") not in ring and ("939793", "007B85") not in ring, fills


def _doughnut(categories, values, **extra):
    return {
        "type": "doughnut",
        "data": {"categories": categories, "series": [{"name": "Share", "values": values}]},
        **extra,
    }


CHANNELS = (["Mobile", "Internet banking", "ATM", "Branch"], [0.56, 0.24, 0.13, 0.07])


def test_a_slice_name_wider_than_its_ring_wraps_between_words():
    """E2E-OUTPUT-05: 'Internet banking' ran past both edges of its dark slice on one
    line, and the letters outside it were white on white."""
    import nbg_chart

    plan = nbg_chart.ring_plan(_doughnut(*CHANNELS), (0.374, 1.6, 12.585, 4.6), None)
    assert plan.names == ["Mobile", "Internet\nbanking", "ATM", "Branch"]
    assert plan.values == [True] * 4 and not plan.legend and plan.unnamed == []


def test_a_slice_too_small_for_its_name_moves_the_names_to_a_legend():
    """A 2% slice cannot hold a name inside the ring at any wrapping: every slice then
    shows its share only, and the legend names them (charts.md allows either)."""
    import nbg_chart

    spec = _doughnut(["Cards", "Deposits", "Loans", "Other products"], [0.5, 0.3, 0.18, 0.02])
    plan = nbg_chart.ring_plan(spec, (0.374, 1.6, 12.585, 4.6), None)
    assert plan.legend and plan.unnamed == ["Other products"]
    assert plan.names == [None] * 4
    assert plan.values == [True, True, True, False], "2% has no room even for its share"


def test_a_logo_legend_keeps_the_names_that_fit_and_needs_no_chart_legend():
    """A peer-bank doughnut's logo row already names every slice (legend=False)."""
    import nbg_chart

    spec = _doughnut(["Bank A", "Bank B", "Bank C", "Bank D"], [0.5, 0.3, 0.18, 0.02])
    plan = nbg_chart.ring_plan(spec, (0.374, 1.6, 12.585, 4.6), False)
    assert not plan.legend and plan.unnamed == ["Bank D"]
    assert plan.names == ["Bank A", "Bank B", "Bank C", None]


def test_an_explicit_legend_leaves_the_slices_their_share_only():
    import nbg_chart

    plan = nbg_chart.ring_plan(_doughnut(*CHANNELS), (0.374, 1.6, 12.585, 4.6), True)
    assert plan.legend and plan.names == [None] * 4 and plan.values == [True] * 4


def test_the_doughnut_sits_in_a_centred_square_so_its_ring_is_measurable(build):
    slide = {
        "type": "chart",
        "content": {"title": "The mix", "source": SOURCE},
        "chart": _doughnut(*CHANNELS),
    }
    out = build(deck([slide]))
    root = part_xml(out, chart_parts(out)[0])
    names = [pt.find("c:v", NS).text for pt in root.findall(".//c:cat//c:pt", NS)]
    assert names == ["Mobile", "Internet\nbanking", "ATM", "Branch"]
    manual = root.find(".//c:plotArea/c:layout/c:manualLayout", NS)
    x, y, w, h = (float(manual.find(f"c:{k}", NS).get("val")) for k in ("x", "y", "w", "h"))
    ext = slide_xml(out, 2).find(".//p:graphicFrame/p:xfrm/a:ext", NS)
    frame_w, frame_h = inches(ext.get("cx")), inches(ext.get("cy"))
    assert w * frame_w == pytest.approx(h * frame_h, abs=0.01)
    assert (x + w / 2, y + h / 2) == pytest.approx((0.5, 0.5), abs=0.001)


MIX = [
    {"name": "Cards", "values": [50, 60]},
    {"name": "Loans", "values": [45, 38]},
    {"name": "Other", "values": [1, 2]},
]


def _deleted_labels(ser):
    return {
        d.find("c:idx", NS).get("val")
        for d in ser.findall("c:dLbls/c:dLbl", NS)
        if d.find("c:delete", NS) is not None
    }


def test_a_stacked_segment_too_thin_for_its_label_drops_the_label(build):
    """E2E-OUTPUT-08: a 1% segment still got a 12pt label, which overprinted the
    labels of the segments either side."""
    out = build(deck([_chart_slide("bar_stacked", series=MIX)]))
    root = part_xml(out, chart_parts(out)[0])
    cards, loans, other = root.findall(".//c:barChart/c:ser", NS)
    assert _deleted_labels(other) == {"0", "1"}
    assert _deleted_labels(cards) == set() and _deleted_labels(loans) == set()


def test_a_stacked_chart_fixes_its_axis_and_plot_so_segment_heights_are_known(build):
    """The labels sit inside the segments, so nothing needs headroom: the axis ends at
    the tallest stack (60 + 38 + 2) and the stacks use the whole plot height."""
    out = build(deck([_chart_slide("bar_stacked", series=MIX)]))
    root = part_xml(out, chart_parts(out)[0])
    scaling = root.find(".//c:valAx/c:scaling", NS)
    assert float(scaling.find("c:min", NS).get("val")) == 0
    assert float(scaling.find("c:max", NS).get("val")) == 100
    assert root.find(".//c:plotArea/c:layout/c:manualLayout", NS) is not None


def test_line_series_are_named_at_their_line_ends_not_in_a_legend(build):
    """E2E-OUTPUT-05: lines were told apart only by a colour-keyed legend."""
    series = [{"name": "2024", "values": [1, 2, 3]}, {"name": "2025", "values": [2, 3, 5]}]
    slide = _chart_slide("line", series=series)
    slide["chart"]["data"]["categories"] = ["Q1", "Q2", "Q3"]
    out = build(deck([slide]))
    root = part_xml(out, chart_parts(out)[0])
    assert root.find(".//c:legend", NS) is None
    for ser in root.findall(".//c:lineChart/c:ser", NS):
        labels = ser.findall("c:dLbls/c:dLbl", NS)
        assert [lbl.find("c:idx", NS).get("val") for lbl in labels] == ["2"], "the last point"
        label = labels[0]
        assert label.find("c:showSerName", NS).get("val") == "1"
        assert label.find("c:showVal", NS).get("val") == "0"
        assert label.find("c:dLblPos", NS).get("val") == "r"
    layout = root.find(".//c:plotArea/c:layout/c:manualLayout", NS)
    x, w = (float(layout.find(f"c:{k}", NS).get("val")) for k in ("x", "w"))
    assert x + w < 0.97, "room is kept right of the plot for the names"


def test_waterfall_step_labels_sit_above_the_bar_and_totals_inside(build):
    slide = {
        "type": "waterfall",
        "content": {"title": "The bridge", "source": SOURCE},
        "chart": {
            "type": "waterfall",
            "data": {
                "items": [
                    {"label": "Start", "value": 10},
                    {"label": "Up", "value": 2},
                    {"label": "End", "value": 12},
                ]
            },
        },
    }
    out = build(deck([slide]))
    root = part_xml(out, chart_parts(out)[0])
    series = root.findall(".//c:barChart/c:ser", NS)
    names = [s.find(".//c:tx//c:v", NS).text for s in series]
    assert names[0] == "Base" and names[-1] == "Labels"
    labels = series[-1].findall("c:dLbls/c:dLbl", NS)
    assert [lbl.find("c:idx", NS).get("val") for lbl in labels] == ["1"]
    assert labels[0].find("c:dLblPos", NS).get("val") == "inBase"
    assert "".join(t.text for t in labels[0].iter(f"{A}t")) == "+2"


def test_a_waterfall_is_four_series_with_each_bar_coloured_by_its_kind(build):
    """The bridge was eight series (a base, six kind-and-sign columns, a label
    carrier), and the validator warns past six: QA read construction as a crowded
    chart. Now the visible parts take their kind's colour point by point."""
    slide = {
        "type": "waterfall",
        "content": {"title": "The bridge crosses zero", "source": SOURCE},
        "chart": {
            "type": "waterfall",
            "data": {
                "items": [
                    {"label": "Start", "value": 10},
                    {"label": "Up", "value": 3},
                    {"label": "Down", "value": -5},
                    {"label": "Cross", "value": -12},
                    {"label": "End", "value": -4, "total": True},
                ]
            },
        },
    }
    out = build(deck([slide]))
    root = part_xml(out, chart_parts(out)[0])
    series = root.findall(".//c:barChart/c:ser", NS)
    assert [s.find(".//c:tx//c:v", NS).text for s in series] == [
        "Base",
        "Above zero",
        "Below zero",
        "Labels",
    ]

    def fills(ser):
        return {
            int(pt.find("c:idx", NS).get("val")): pt.find(".//a:srgbClr", NS).get("val")
            for pt in ser.findall("c:dPt", NS)
        }

    total, increase, decrease = "003841", "00ADBF", "AA0028"
    assert fills(series[1]) == {0: total, 1: increase, 2: decrease, 3: decrease}
    assert fills(series[2]) == {3: decrease, 4: total}


# ---------------------------------------------------------------- other slide types


def test_kpi_tiles_carry_value_label_and_sentiment_coloured_delta(build):
    slide = {
        "type": "kpi",
        "content": {"title": "Three numbers tell the story", "source": SOURCE},
        "kpis": [
            {"value": "3.3M", "label": "Active users", "delta": "+8%", "sentiment": "positive"},
            {"value": "12%", "label": "Churn", "delta": "+2 pts", "sentiment": "negative"},
            {"value": "41", "label": "NPS", "delta": "flat"},
        ],
    }
    root = slide_xml(build(deck([slide])), 2)
    assert len(_shapes_with_fill(root, "F5F8F6")) == 3
    value = shape_by_text(root, "3.3M")
    assert value.find(".//a:rPr", NS).get("sz") == "5000"
    caption = shape_by_text(root, "Active users").find(".//a:rPr", NS)
    assert caption.get("sz") == "1600" and caption.get("b") == "0"
    assert caption.find("a:solidFill/a:srgbClr", NS).get("val") == "5A5F5A"
    colours = {
        text: shape_by_text(root, text).find(".//a:rPr/a:solidFill/a:srgbClr", NS).get("val")
        for text in ("+8%", "+2 pts", "flat")
    }
    assert colours == {"+8%": "007B85", "+2 pts": "AA0028", "flat": "202020"}


def test_a_row_of_kpi_tiles_shares_one_value_size_and_one_value_line(build):
    """Standard #20 parallel comparison: same positions, same type sizes. Each tile
    centred its own stack, so a two-line caption pushed its value up out of line."""
    slide = {
        "type": "kpi",
        "content": {"title": "Three numbers, one line", "source": SOURCE},
        "kpis": [
            {"value": "2.8M", "label": "Mobile active users"},
            {"value": "78%", "label": "Transactions made in digital channels, all segments"},
            {"value": "EUR 1,250M", "label": "Fee income"},
        ],
    }
    root = slide_xml(build(deck([slide])), 2)
    values = [shape_by_text(root, v) for v in ("2.8M", "78%", "EUR 1,250M")]
    tops = {v.find(".//a:xfrm/a:off", NS).get("y") for v in values}
    sizes = {v.find(".//a:rPr", NS).get("sz") for v in values}
    assert len(tops) == 1, "every value on one line"
    assert len(sizes) == 1, "every value at one size"
    captions = [shape_by_text(root, c) for c in ("Mobile active users", "Fee income")]
    assert len({c.find(".//a:xfrm/a:off", NS).get("y") for c in captions}) == 1


def test_a_row_of_kpi_deltas_shares_one_line_when_captions_wrap_differently(build):
    """E2E-OUTPUT-10: each delta sat right under its own caption, so a two-line caption
    pushed its delta below its neighbours'."""
    slide = {
        "type": "kpi",
        "content": {"title": "Three numbers, deltas in line", "source": SOURCE},
        "kpis": [
            {"value": "2.8M", "label": "Users", "delta": "+23%", "sentiment": "positive"},
            {
                "value": "78%",
                "label": "Transactions made in digital channels, all segments",
                "delta": "+6 pts",
                "sentiment": "positive",
            },
            {"value": "41", "label": "NPS", "delta": "flat"},
        ],
    }
    root = slide_xml(build(deck([slide])), 2)
    deltas = [shape_by_text(root, d) for d in ("+23%", "+6 pts", "flat")]
    assert len({d.find(".//a:xfrm/a:off", NS).get("y") for d in deltas}) == 1


def test_cards_mark_the_recommended_option_with_a_gold_tab(build):
    slide = {
        "type": "cards",
        "content": {"title": "Two options, one pick"},
        "cards": [
            {"title": "Build", "body": "Own the platform."},
            {"title": "Partner", "body": "Launch faster.", "recommended": True},
        ],
    }
    root = slide_xml(build(deck([slide])), 2)
    assert len(_shapes_with_fill(root, "F5F8F6")) == 1
    gold = _shapes_with_fill(root, "FBF3E4")
    assert len(gold) == 1
    border = gold[0].find("p:spPr/a:ln", NS)
    assert border.get("w") == "19050" and border.find(".//a:srgbClr", NS).get("val") == "D9A757"
    assert "RECOMMENDED" in [b[0] for b in shape_boxes(root)]


def test_cards_are_as_tall_as_their_content_and_the_grid_sits_mid_body(build):
    """Short text sat in cards stretched to the full body height, most of each card
    empty (lead's visual review, strategy-deck slide 5). Cards take their content's
    height, never under components.card.min_h, and the grid is centred in the body."""
    import nbg_tokens

    slide = {
        "type": "cards",
        "content": {"title": "Four pillars, one line each"},
        "layout": "grid",
        "cards": [
            {"title": t, "body": "One short line."} for t in ("Mobile", "Data", "Open", "Cloud")
        ],
    }
    root = slide_xml(build(deck([slide])), 2)
    cards = _shapes_with_fill(root, "F5F8F6")
    assert len(cards) == 4
    boxes = []
    for card in cards:
        off, ext = card.find(".//a:xfrm/a:off", NS), card.find(".//a:xfrm/a:ext", NS)
        boxes.append((inches(off.get("y")), inches(ext.get("cy"))))
    heights = {round(h, 3) for _, h in boxes}
    assert len(heights) == 1, "every card in the grid is one height"
    height = heights.pop()
    assert nbg_tokens.get("components.card.min_h") - 0.001 <= height < 2.0
    top, bottom = min(y for y, _ in boxes), max(y + h for y, h in boxes)
    assert top - 1.3 == pytest.approx(6.5 - bottom, abs=0.02), "the grid is centred in the body"


def test_a_numbered_card_gets_an_oval_badge(build):
    slide = {
        "type": "cards",
        "content": {"title": "Two numbered ideas"},
        "cards": [{"title": "First", "number": 1}, {"title": "Second", "number": 2}],
    }
    root = slide_xml(build(deck([slide])), 2)
    badges = [
        sp
        for sp in root.iter(f"{P}sp")
        if (g := sp.find(".//a:prstGeom", NS)) is not None and g.get("prst") == "ellipse"
    ]
    assert len(badges) == 2
    assert "".join(t.text for t in badges[0].iter(f"{A}t")) == "1"


def test_process_steps_are_teal_tiles_labelled_underneath_and_joined_by_grey_arrows(build):
    """layouts.md Standard #20: rounded-square #007B85 tiles with white content, the
    16pt bold title and 14pt line under each tile, #939793 arrows between tiles."""
    slide = {
        "type": "process",
        "content": {"title": "Four steps from idea to launch"},
        "steps": [{"title": t, "body": "Short."} for t in ("Plan", "Build", "Test", "Launch")],
    }
    root = slide_xml(build(deck([slide])), 2)
    arrows = [
        sp
        for sp in root.iter(f"{P}sp")
        if sp.find(".//a:prstGeom[@prst='rightArrow']", NS) is not None
    ]
    assert len(arrows) == 3
    assert {a.find("p:spPr/a:solidFill/a:srgbClr", NS).get("val") for a in arrows} == {"939793"}
    tiles = _shapes_with_fill(root, "007B85")
    assert len(tiles) == 4 and not _shapes_with_fill(root, "F5F8F6")
    for tile, number, title in zip(
        tiles, ("01", "02", "03", "04"), ("Plan", "Build", "Test", "Launch"), strict=True
    ):
        ext = tile.find(".//a:xfrm/a:ext", NS)
        assert ext.get("cx") == ext.get("cy"), "a step tile is square"
        run = tile.find(".//a:r", NS)
        assert run.find("a:t", NS).text == number
        assert run.find("a:rPr/a:solidFill/a:srgbClr", NS).get("val") == "FFFFFF"
        label = shape_by_text(root, title)
        label_top = inches(label.find(".//a:xfrm/a:off", NS).get("y"))
        tile_bottom = inches(tile.find(".//a:xfrm/a:off", NS).get("y")) + inches(ext.get("cy"))
        assert label_top >= tile_bottom, f"{title} sits under its tile"
        rpr = label.find(".//a:rPr", NS)
        assert rpr.get("sz") == "1600" and rpr.get("b") == "1"
        assert rpr.find("a:solidFill/a:srgbClr", NS).get("val") == "003841"


def test_a_process_icon_is_drawn_white_inside_its_tile(build):
    """A line icon is supplied in brand colours; on a teal tile it must turn white."""
    import io

    from PIL import Image

    icon = EXAMPLES_DIR / "icons" / "insight.svg"
    slide = {
        "type": "process",
        "content": {"title": "Two steps with icons"},
        "steps": [{"title": "Learn", "icon": str(icon)}, {"title": "Act", "icon": str(icon)}],
    }
    out = build(deck([slide]))
    root = slide_xml(out, 2)
    # The icons carry alt text; the slide's logo is decorative (empty descr).
    pictures = [p for p in root.iter(f"{P}pic") if p.find(".//p:cNvPr", NS).get("descr")]
    assert len(pictures) == 2
    tile = _shapes_with_fill(root, "007B85")[0]
    t_off, t_ext = tile.find(".//a:xfrm/a:off", NS), tile.find(".//a:xfrm/a:ext", NS)
    p_off = pictures[0].find(".//a:xfrm/a:off", NS)
    assert int(t_off.get("x")) < int(p_off.get("x")) < int(t_off.get("x")) + int(t_ext.get("cx"))
    rels = part_xml(out, "ppt/slides/_rels/slide2.xml.rels")
    target = {r.get("Id"): r.get("Target") for r in rels}
    r_embed = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
    with zipfile.ZipFile(out) as zf:
        icons = [
            Image.open(io.BytesIO(zf.read("ppt/" + target[blip.get(r_embed)].replace("../", ""))))
            for p in pictures
            for blip in p.iter(f"{A}blip")
        ]
    pixels = [px for im in icons for px in im.convert("RGBA").getdata() if px[3] > 128]
    assert pixels and all(px[:3] == (255, 255, 255) for px in pixels), (
        "every visible pixel is white"
    )


def test_two_column_split_sets_the_column_widths(build):
    slide = {
        "type": "two_column",
        "split": "40/60",
        "content": {"title": "Words beside a table", "source": SOURCE},
        "left": {"kind": "text", "heading": "Left", "text": "A short argument."},
        "right": {
            "kind": "table",
            "heading": "Right",
            "table": {"headers": ["A", "B"], "rows": [["1", "2"]]},
        },
    }
    root = slide_xml(build(deck([slide])), 2)
    _, left_x, _, left_w, _ = next(b for b in shape_boxes(root) if b[0] == "Left")
    _, right_x, _, right_w, _ = next(b for b in shape_boxes(root) if b[0] == "Right")
    assert left_w / right_w == pytest.approx(40 / 60, rel=0.01)
    assert right_x == pytest.approx(left_x + left_w + 0.3, abs=0.001)


def test_an_image_slide_places_the_picture_with_its_alt_text(build):
    slide = {
        "type": "image",
        "content": {"title": "A picture of growth"},
        "image": {
            "path": "illustrations/Growth.png",
            "alt_text": "A rising balance",
            "caption": "Illustrative",
        },
    }
    root = slide_xml(build(deck([slide])), 2)
    pictures = [p for p in root.iter(f"{P}pic") if p.find(".//p:cNvPr", NS).get("descr")]
    assert [p.find(".//p:cNvPr", NS).get("descr") for p in pictures] == ["A rising balance"]
    assert "Illustrative" in [b[0] for b in shape_boxes(root)]


def _picture_box(root):
    pic = next(p for p in root.iter(f"{P}pic") if p.find(".//p:cNvPr", NS).get("descr"))
    off, ext = pic.find(".//a:xfrm/a:off", NS), pic.find(".//a:xfrm/a:ext", NS)
    return tuple(inches(v) for v in (off.get("x"), off.get("y"), ext.get("cx"), ext.get("cy")))


def test_a_small_raster_is_never_enlarged_past_150_dpi_and_check_warns(build, tmp_path):
    """strategy-deck slide 8 blew an 800 px illustration up to 9 in, 85 DPI, and it
    blurred (the lead's visual review). A raster now stops at its 150 DPI size,
    centred in its slot, and check says the image is too small for the slot."""
    from PIL import Image

    Image.new("RGB", (300, 150), "#007B85").save(tmp_path / "small.png")
    slide = {
        "type": "image",
        "content": {"title": "A small picture stays sharp"},
        "image": {"path": str(tmp_path / "small.png"), "alt_text": "A teal block"},
    }
    root = slide_xml(build(deck([slide])), 2)
    x, _, w, h = _picture_box(root)
    assert (w, h) == (pytest.approx(2.0, abs=0.01), pytest.approx(1.0, abs=0.01))
    assert x + w / 2 == pytest.approx(0.374 + 12.585 / 2, abs=0.02), "centred in its slot"
    report = nbg_build.check(write_spec(tmp_path, deck([slide]), "small.yaml"))
    warning = next(i for i in report.warnings if i.path == "slides[1].image.path")
    assert "150" in warning.message and "300" in warning.message


def test_an_svg_fills_its_slot_because_it_has_no_pixels_to_blur(build, tmp_path):
    slide = {
        "type": "image",
        "content": {"title": "A vector picture fills its slot"},
        "image": {"path": str(EXAMPLES_DIR / "icons" / "insight.svg"), "alt_text": "An insight"},
    }
    root = slide_xml(build(deck([slide])), 2)
    _, _, w, h = _picture_box(root)
    assert max(w, h) > 4.0, "scaled to its slot, not to a pixel size"
    report = nbg_build.check(write_spec(tmp_path, deck([slide]), "svg.yaml"))
    assert not [i for i in report.warnings if i.path == "slides[1].image.path"]


def test_an_svg_icon_is_rasterised_into_the_package(build, tmp_path):
    icon = tmp_path / "dot.svg"
    icon.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="20" fill="#087681"/></svg>',
        encoding="utf-8",
    )
    slide = {
        "type": "cards",
        "content": {"title": "Icons from SVG"},
        "cards": [{"title": "Dot", "icon": "dot.svg"}, {"title": "Also dot", "icon": str(icon)}],
    }
    out = build(deck([slide]))
    root = slide_xml(out, 2)
    alts = [p.find(".//p:cNvPr", NS).get("descr") for p in root.iter(f"{P}pic")]
    assert "Dot icon" in alts and "Also dot icon" in alts
    media = [n for n in zipfile.ZipFile(out).namelist() if n.startswith("ppt/media/")]
    assert any(n.endswith(".png") for n in media)


def test_custom_elements_draw_where_the_spec_puts_them(build):
    slide = {
        "type": "custom",
        "content": {"title": "A layout of our own", "source": SOURCE},
        "elements": [
            {
                "kind": "shape",
                "shape": "rounded_rect",
                "x": 0.5,
                "y": 1.5,
                "w": 3,
                "h": 2,
                "fill": "teal",
                "text": "On teal",
            },
            {
                "kind": "text",
                "text": "Plain words",
                "x": 4,
                "y": 1.5,
                "w": 4,
                "h": 0.5,
                "role": "body",
            },
            {"kind": "line", "x": 4, "y": 2.2, "w": 4, "h": 0},
            {
                "kind": "chart",
                "x": 8.5,
                "y": 1.5,
                "w": 4,
                "h": 3,
                "chart": {
                    "type": "bar",
                    "data": {"categories": ["a"], "series": [{"name": "s", "values": [1]}]},
                },
            },
        ],
    }
    out = build(deck([slide]))
    root = slide_xml(out, 2)
    _, x, y, w, h = next(b for b in shape_boxes(root) if b[0] == "Plain words")
    assert (x, y, w, h) == pytest.approx((4, 1.5, 4, 0.5), abs=0.001)
    on_teal = shape_by_text(root, "On teal")
    assert on_teal.find(".//a:rPr/a:solidFill/a:srgbClr", NS).get("val") == "FFFFFF"
    assert root.find(f".//{P}cxnSp") is not None
    assert len(chart_parts(out)) == 1


def test_the_back_cover_is_one_emblem_and_nothing_else(build):
    root = slide_xml(build(deck([])), 2)
    assert len(list(root.iter(f"{P}pic"))) == 1
    assert not list(root.iter(f"{P}sp")) and not list(root.iter(f"{A}t"))


def test_contents_numbers_given_as_integers_are_zero_padded(build):
    slide = {
        "type": "contents",
        "content": {"sections": [{"number": 1, "title": "One"}, {"number": 2, "title": "Two"}]},
    }
    root = slide_xml(build(deck([slide])), 2)
    assert {"01", "02"} <= {b[0] for b in shape_boxes(root)}


# ---------------------------------------------------------------- chrome


def test_speaker_notes_are_written_from_slide_notes(build):
    slide = {
        "type": "content",
        "content": {"title": "Notes travel with the slide", "points": ["a"]},
        "notes": "Say this aloud.",
    }
    prs = Presentation(str(build(deck([slide]))))
    assert prs.slides[1].notes_slide.notes_text_frame.text == "Say this aloud."


def test_every_chart_table_and_picture_has_alt_text_except_the_logos(tmp_path, monkeypatch):
    passing_validator(monkeypatch, nbg_build)
    for spec in sorted(EXAMPLES_DIR.glob("*.yaml")):
        out = tmp_path / f"{spec.stem}.pptx"
        nbg_build.build_presentation(spec, out)
        with zipfile.ZipFile(out) as zf:
            slides = [
                n for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")
            ]
        for name in slides:
            root = part_xml(out, name)
            for host in ("graphicFrame", "pic"):
                for shape in root.iter(f"{P}{host}"):
                    nv = shape.find(".//p:cNvPr", NS)
                    decorative = nv.find(".//{*}decorative") is not None
                    assert decorative or nv.get("descr", "").strip(), f"{spec.name} {name}"


def test_runs_carry_the_deck_language(build):
    en = slide_xml(
        build(
            deck(
                [{"type": "content", "content": {"title": "English words here", "points": ["a"]}}]
            ),
            "en",
        ),
        2,
    )
    assert {r.get("lang") for r in en.iter(f"{A}rPr")} == {"en-GB"}
    el = slide_xml(
        build(
            deck(
                [{"type": "content", "content": {"title": "Ελληνικά λόγια", "points": ["α"]}}],
                language="el",
            ),
            "el",
        ),
        2,
    )
    assert {r.get("lang") for r in el.iter(f"{A}rPr")} == {"el-GR"}


def test_a_title_that_wraps_pushes_the_body_down_and_warns(build, tmp_path):
    """Eighty characters of W do not fit one 24pt line, however the limit counts them."""
    title = " ".join(["WWWWWWW"] * 10)[:80]
    spec = deck([{"type": "content", "content": {"title": title, "points": ["a"]}}])
    report = nbg_build.check(write_spec(tmp_path, spec))
    assert any(i.path == "slides[1].content.title" for i in report.warnings)
    root = slide_xml(build(spec), 2)
    title_box = next(b for b in shape_boxes(root) if b[0] == title)
    body_box = next(b for b in shape_boxes(root) if b[0] == "a")
    assert title_box[4] > 0.7, "a two-line title needs a two-line box"
    assert body_box[2] >= title_box[2] + title_box[4] + 0.15 - 1e-6


def test_the_theme_fonts_and_layouts_are_16_9(build):
    out = build(deck([]))
    layout = part_xml(out, "ppt/slideLayouts/slideLayout1.xml")
    widths = [int(e.get("cx")) for e in layout.iter(f"{A}ext")]
    assert max(widths) > 9144000, "layout placeholders are still laid out for 4:3"


# ---------------------------------------------------------------- direct callers and the CLI


def test_direct_helpers_render_like_a_spec_and_allow_an_untitled_slide(tmp_path):
    prs = nbg_build.new_presentation()
    nbg_build.create_content_slide(prs, {"points": ["no title here"]}, 1)
    nbg_build.create_table_slide(prs, {"title": "A table"}, {"headers": ["A"], "rows": [["1"]]}, 2)
    nbg_build.create_chart_slide(
        prs,
        {"title": "A chart"},
        3,
        chart_type="pie",
        categories=["a"],
        series_list=[{"name": "s", "values": [1]}],
    )
    out = tmp_path / "direct.pptx"
    prs.save(str(out))
    assert Presentation(str(out)).slides[0].shapes.title is None
    assert b"doughnutChart" in zipfile.ZipFile(out).read(chart_parts(out)[0])
    box = next(b for b in shape_boxes(slide_xml(out, 1)) if b[0] == "no title here")
    assert inches(1188720) == pytest.approx(box[2], abs=0.001)


def test_cli_accepts_dash_o_and_two_positionals_and_rejects_both(tmp_path):
    spec = write_spec(
        tmp_path, deck([{"type": "content", "content": {"title": "A title", "points": ["One"]}}])
    )
    run = lambda *a: subprocess.run(  # noqa: E731
        [sys.executable, str(SCRIPT), *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=tmp_path,
    )
    dash_o = run(str(spec), "-o", str(tmp_path / "a.pptx"))
    assert dash_o.returncode == 0, dash_o.stdout + dash_o.stderr
    assert (tmp_path / "a.pptx").exists() and not (tmp_path / "-o").exists()
    positional = run(str(spec), str(tmp_path / "b.pptx"))
    assert positional.returncode == 0 and (tmp_path / "b.pptx").exists()
    both = run(str(spec), "c.pptx", "-o", "d.pptx")
    assert both.returncode != 0 and "two output paths" in both.stderr


def test_build_raises_on_violations_and_on_a_validator_crash(tmp_path, monkeypatch):
    spec = write_spec(
        tmp_path, deck([{"type": "content", "content": {"title": "A title", "points": ["One"]}}])
    )

    def fake(returncode, stderr=""):
        def run(cmd, *args, **kwargs):
            return subprocess.CompletedProcess(cmd, returncode, "", stderr)

        return run

    monkeypatch.setattr(nbg_build.subprocess, "run", fake(1))
    with pytest.raises(ValueError, match="brand violations"):
        nbg_build.build_presentation(spec, tmp_path / "v.pptx")
    monkeypatch.setattr(
        nbg_build.subprocess, "run", fake(1, "Traceback (most recent call last):\n")
    )
    with pytest.raises(RuntimeError, match="UNVALIDATED"):
        nbg_build.build_presentation(spec, tmp_path / "c.pptx")


@pytest.mark.parametrize("name", sorted(p.stem for p in EXAMPLES_DIR.glob("*.yaml")))
def test_every_example_passes_the_validator_it_ships_with(tmp_path, name):
    """No stub: the real nbg_validate.py gates every example, as CI's render job and a
    colleague's build do. A builder change the gate rejects fails here first."""
    nbg_build.build_presentation(EXAMPLES_DIR / f"{name}.yaml", tmp_path / f"{name}.pptx")


@pytest.mark.parametrize("name", sorted(p.stem for p in EXAMPLES_DIR.glob("*.yaml")))
def test_every_example_builds_and_its_charts_carry_data(tmp_path, monkeypatch, name):
    passing_validator(monkeypatch, nbg_build)
    out = tmp_path / f"{name}.pptx"
    nbg_build.build_presentation(EXAMPLES_DIR / f"{name}.yaml", out)
    for part in chart_parts(out):
        root = part_xml(out, part)
        values = root.findall(".//c:ser/c:val//c:pt", NS)
        assert values, f"{name} {part} has no data points"
