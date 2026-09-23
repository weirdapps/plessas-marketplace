"""Tests for nbg_build.py: what the builder writes, checked in the OOXML PowerPoint reads.

Runs in CI under `pytest plugins scripts`. Run by hand with:
    uv run --no-project --python 3.12 \
        --with-requirements plugins/decks/tools/nbg-presentation/requirements.txt \
        --with pytest python -m pytest plugins/decks/tools -q

Each defect test names the review finding it closes. They assert on the built XML,
not on the builder's internals, because the defects they guard against were all
invisible to a test that trusted the builder's own view of what it had drawn.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import nbg_build
import pytest
import yaml
from nbg_color import contrast_ratio
from testkit import (
    EXAMPLES_DIR,
    NS,
    box_with_text,
    chart_parts,
    deck,
    emu,
    inches,
    part_xml,
    passing_validator,
    run_sizes,
    shape_boxes,
    shape_by_text,
    slide_xml,
    write_spec,
)

SCRIPT = Path(__file__).parent / "nbg_build.py"
A = f"{{{NS['a']}}}"
P = f"{{{NS['p']}}}"
C = f"{{{NS['c']}}}"

SOURCE = {"name": "Management accounts", "as_of": "30 June 2026"}


@pytest.fixture
def build(tmp_path, monkeypatch):
    """build(spec) -> path of the built .pptx, with the validator stubbed to pass."""
    passing_validator(monkeypatch, nbg_build)

    def _build(spec, name="deck"):
        path = write_spec(tmp_path, spec, f"{name}.yaml")
        out = tmp_path / f"{name}.pptx"
        nbg_build.build_presentation(path, out)
        return out

    return _build


def _content(title, points, **extra):
    return {"type": "content", "content": {"title": title, "points": points, **extra}}


def _chart(title, chart_type, categories, series, **chart_extra):
    return {
        "type": "chart",
        "content": {"title": title, "source": SOURCE},
        "chart": {
            "type": chart_type,
            "data": {"categories": categories, "series": series},
            **chart_extra,
        },
    }


# =============================================================== BUILD-CODE-1


# CT_TextParagraphProperties, ISO/IEC 29500-1 21.1.2.2.7: the child sequence.
PPR_ORDER = [
    "lnSpc",
    "spcBef",
    "spcAft",
    "buClrTx",
    "buClr",
    "buSzTx",
    "buSzPct",
    "buSzPts",
    "buFontTx",
    "buFont",
    "buNone",
    "buAutoNum",
    "buChar",
    "buBlip",
    "tabLst",
    "defRPr",
    "extLst",
]


def test_bullet_paragraph_properties_follow_the_schema_order(build):
    """BUILD-CODE-1 / E2E-SMOKE-4: PowerPoint drops every a:pPr child out of order,
    so the bullets and their 14pt spacing vanished while LibreOffice showed them."""
    out = build(deck([_content("Three things moved", ["One", "Two", "Three"])]))
    root = slide_xml(out, 2)
    bulleted = [p for p in root.iter(f"{A}pPr") if p.find(f"{A}buChar") is not None]
    assert len(bulleted) == 3
    for ppr in bulleted:
        tags = [etree_local(child) for child in ppr]
        positions = [PPR_ORDER.index(t) for t in tags]
        assert positions == sorted(positions), tags


def test_bullets_hang_from_a_quarter_inch_indent(build):
    """Also noticed in BUILD-CODE-1: the glyph touched the text and wrapped lines
    did not hang."""
    out = build(deck([_content("Three things moved", ["One", "Two"])]))
    for ppr in slide_xml(out, 2).iter(f"{A}pPr"):
        if ppr.find(f"{A}buChar") is None:
            continue
        assert ppr.get("marL") == "228600"
        assert ppr.get("indent") == "-228600"


def etree_local(el) -> str:
    return str(el.tag).split("}", 1)[1]


# =============================================================== BUILD-CODE-3


def test_line_series_are_stroked_in_the_palette_with_hollow_markers(build):
    """BUILD-CODE-3 / E2E-SMOKE-3 / BRAND-SSOT-3: the palette went into the area fill,
    which a line ignores, so every line inherited Office blue and red."""
    out = build(
        deck(
            [
                _chart(
                    "Volumes rose in both years",
                    "line",
                    ["Jan", "Feb", "Mar"],
                    [{"name": "2025", "values": [1, 2, 3]}, {"name": "2026", "values": [2, 3, 4]}],
                )
            ]
        )
    )
    root = part_xml(out, chart_parts(out)[0])
    series = root.findall(".//c:lineChart/c:ser", NS)
    assert len(series) == 2
    for ser, colour in zip(series, ["00ADBF", "003841"], strict=True):
        ln = ser.find("c:spPr/a:ln", NS)
        assert ln is not None, "series has no explicit stroke"
        assert ln.get("w") == "44450"  # 3.5pt
        assert ln.find("a:solidFill/a:srgbClr", NS).get("val") == colour
        marker = ser.find("c:marker", NS)
        assert marker.find("c:symbol", NS).get("val") == "circle"
        assert marker.find("c:size", NS).get("val") == "6"
        assert marker.find("c:spPr/a:solidFill/a:srgbClr", NS).get("val") == "FFFFFF"
        assert marker.find("c:spPr/a:ln/a:solidFill/a:srgbClr", NS).get("val") == colour
        # Standard #5 hollow: a 3.5pt outline on a 6pt marker left no white centre and
        # every marker read as a solid dot (lead's visual review). 2pt keeps the hole.
        assert marker.find("c:spPr/a:ln", NS).get("w") == "25400"
        assert ser.find("c:smooth", NS).get("val") == "0"


def test_every_deck_carries_the_nbg_theme(build):
    """BUILD-CODE-3 / BRAND-SSOT-6: python-pptx ships the Office theme, so anything a
    colleague added later came out Calibri and Office blue."""
    out = build(deck([_content("Three things moved", ["One"])]))
    theme = part_xml(out, "ppt/theme/theme1.xml")
    fonts = theme.find(".//a:fontScheme", NS)
    assert fonts.find("a:majorFont/a:latin", NS).get("typeface") == "Aptos"
    assert fonts.find("a:minorFont/a:latin", NS).get("typeface") == "Aptos"
    scheme = theme.find(".//a:clrScheme", NS)
    accents = [scheme.find(f"a:accent{i}/a:srgbClr", NS).get("val") for i in range(1, 7)]
    assert accents == ["00ADBF", "003841", "007B85", "939793", "BEC1BE", "00DFF8"]
    assert b"4F81BD" not in zipfile.ZipFile(out).read("ppt/theme/theme1.xml")


# =============================================================== BUILD-CODE-6


def test_a_long_bumper_gets_a_pill_as_wide_as_its_text(build):
    """BUILD-CODE-6 / E2E-SMOKE-11 / BRAND-SSOT-7: the pill was a fixed 1.3", so any
    bumper over ~16 characters ran out of it as white text on a white slide."""
    bumper = "Strategic priorities for 2026"
    out = build(deck([_content("Three priorities carry the plan", ["One"], bumper=bumper)]))
    root = slide_xml(out, 2)
    pill = shape_by_text(root, bumper.upper())
    ext = pill.find(".//a:xfrm/a:ext", NS)
    from nbg_text import metrics

    text_w = metrics().width(bumper.upper(), 9, bold=True)
    assert inches(ext.get("cx")) >= text_w + 2 * 0.1 - 0.01


def test_cover_title_and_subtitle_never_collide(build):
    """E2E-SMOKE-2 / BRAND-SSOT-1: 7.86" boxes and a 36pt subtitle, so a 30-character
    title wrapped into the subtitle on two of three shipped covers."""
    spec = {
        "slides": [
            {
                "type": "cover",
                "content": {
                    "title": "Digital Banking Performance Review",
                    "subtitle": "Retail Banking | Digital Channels",
                },
            },
            {"type": "back_cover"},
        ]
    }
    out = build(spec)
    root = slide_xml(out, 1)
    _, _, t_y, t_w, t_h = box_with_text(root, "Digital Banking Performance Review")
    _, _, s_y, s_w, _ = box_with_text(root, "Retail Banking | Digital Channels")
    assert t_w >= 12.0 - 0.001
    assert s_y >= t_y + t_h
    assert run_sizes(shape_by_text(root, "Retail Banking | Digital Channels")) == {24.0}


def test_the_cover_date_is_caption_grey_not_the_page_number_grey(build):
    """Standard #22: #939793 is 2.96:1 on white and sanctioned for page numbers only.
    A 14pt date is text, so it takes caption grey #5A5F5A (the lead's token decision);
    the validator's Contrast check failed every example's cover on it."""
    spec = {
        "slides": [
            {"type": "cover", "content": {"title": "Digital Banking Review", "date": "March 2026"}},
            {"type": "back_cover"},
        ]
    }
    root = slide_xml(build(spec), 1)
    run = shape_by_text(root, "March 2026").find(".//a:rPr", NS)
    assert run.find("a:solidFill/a:srgbClr", NS).get("val") == "5A5F5A"


# =============================================================== BUILD-CODE-12


def test_cli_exits_2_when_the_validator_cannot_run(tmp_path, monkeypatch):
    """BUILD-CODE-12: a validator crash is "could not run", not a failed check."""

    def crash(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr="Traceback (most recent call last):\n"
        )

    monkeypatch.setattr(nbg_build.subprocess, "run", crash)
    spec = write_spec(tmp_path, deck([_content("Three things moved", ["One"])]))
    monkeypatch.setattr(sys, "argv", ["nbg_build.py", str(spec), str(tmp_path / "o.pptx")])
    with pytest.raises(SystemExit) as exc:
        nbg_build.main()
    assert exc.value.code == 2


# =============================================================== BUILD-CODE-2


def test_an_unknown_chart_type_fails_the_build_and_names_the_slide(build):
    """BUILD-CODE-2: an unknown chart.type silently became a clustered column."""
    spec = deck([_chart("Volumes rose", "radar", ["Q1", "Q2"], [{"name": "s", "values": [1, 2]}])])
    with pytest.raises(Exception, match=r"(?s)slide 2.*radar"):
        build(spec)


def test_the_storyline_doughnut_chart_name_builds_a_doughnut(build):
    """BUILD-CODE-2: `doughnut_chart`, the storyline agent's own vocabulary, became a
    bullet slide with no chart at all."""
    spec = deck(
        [
            {
                "type": "doughnut_chart",
                "content": {"title": "Cards lead the fee mix", "source": SOURCE},
                "chart": {
                    "data": {
                        "categories": ["Cards", "Accounts"],
                        "series": [{"name": "Fees", "values": [60, 40]}],
                    }
                },
            }
        ]
    )
    out = build(spec)
    assert b"doughnutChart" in zipfile.ZipFile(out).read(chart_parts(out)[0])


def test_a_waterfall_reads_the_documented_chart_data_items(build):
    """E2E-SMOKE-13 / BUILD-CODE-2: chart.data was ignored and the slide shipped as a
    sourced exhibit with no chart on it."""
    spec = deck(
        [
            {
                "type": "waterfall",
                "content": {"title": "Fees bridge from 2025 to 2026", "source": SOURCE},
                "chart": {
                    "type": "waterfall",
                    "data": {
                        "items": [
                            {"label": "2025", "value": 100},
                            {"label": "Cards", "value": 12},
                            {"label": "Accounts", "value": -5},
                            {"label": "2026", "value": 107},
                        ]
                    },
                },
            }
        ]
    )
    out = build(spec)
    assert len(chart_parts(out)) == 1


# =============================================================== BUILD-CODE-4


def test_the_contents_slide_follows_standard_18(build):
    """BUILD-CODE-4 / E2E-SMOKE-12 / BRAND-SSOT-2: a 32pt bold header at y=0.36 and
    a retired grey, which failed the builder's own validator on every deck."""
    spec = deck(
        [
            {
                "type": "contents",
                "content": {
                    "title": "Agenda",
                    "sections": [
                        {"title": "Where we stand", "description": "The year so far"},
                        {"title": "What we propose"},
                        {"title": "What we need"},
                    ],
                },
            }
        ]
    )
    out = build(spec)
    root = slide_xml(out, 2)
    header = shape_by_text(root, "Agenda")
    assert run_sizes(header) == {24.0}
    assert all(r.get("b") in (None, "0") for r in header.iter(f"{A}rPr"))
    assert box_with_text(root, "Agenda")[2] == pytest.approx(0.40, abs=0.005)
    description = shape_by_text(root, "The year so far")
    colours = {c.get("val") for c in description.iter(f"{A}srgbClr")}
    assert colours == {"5A5F5A"}
    number = shape_by_text(root, "01")
    assert all(r.get("b") in (None, "0") for r in number.iter(f"{A}rPr"))


# =============================================================== BUILD-CODE-7


def test_stacked_bar_labels_clear_aa_on_every_series(build):
    """BUILD-CODE-7 / E2E-SMOKE-8: #202020 labels inside #003841 bars, 1.27:1."""
    out = build(
        deck(
            [
                _chart(
                    "Mix shifted to cards",
                    "bar_stacked",
                    ["2024", "2025"],
                    [
                        {"name": "Cards", "values": [10, 12]},
                        {"name": "Accounts", "values": [8, 9]},
                        {"name": "Other", "values": [4, 5]},
                    ],
                )
            ]
        )
    )
    root = part_xml(out, chart_parts(out)[0])
    series = root.findall(".//c:barChart/c:ser", NS)
    assert len(series) == 3
    for ser in series:
        fill = ser.find("c:spPr/a:solidFill/a:srgbClr", NS).get("val")
        label = ser.find("c:dLbls/c:txPr//a:defRPr/a:solidFill/a:srgbClr", NS)
        assert label is not None, "no per-series label colour"
        assert contrast_ratio(fill, label.get("val")) >= 4.5


# =============================================================== BUILD-CODE-8


def test_the_builder_opens_every_text_file_with_an_explicit_encoding(tmp_path):
    """BUILD-CODE-8: open() without encoding reads a Greek spec as cp1253 on Windows.
    -X warn_default_encoding makes every such call report itself."""
    spec = write_spec(tmp_path, deck([_content("Three things moved", ["One"])]))
    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "warn_default_encoding",
            str(SCRIPT),
            str(spec),
            str(tmp_path / "o.pptx"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=tmp_path,
    )
    # The build must have got as far as reading and writing, or the absence of a
    # warning proves nothing.
    assert (tmp_path / "o.pptx").exists(), proc.stdout + proc.stderr
    ours = [
        line
        for line in proc.stderr.splitlines()
        if "EncodingWarning" in line and re.search(r"nbg_\w+\.py", line)
    ]
    assert not ours, ours


def test_the_validator_runs_in_utf8_mode(tmp_path, monkeypatch):
    """BUILD-CODE-8: every build reported UNVALIDATED on Windows because the
    validator subprocess printed Greek and ticks to a cp1252 pipe."""
    calls = passing_validator(monkeypatch, nbg_build)
    spec = write_spec(tmp_path, deck([_content("Three things moved", ["One"])]))
    nbg_build.build_presentation(spec, tmp_path / "o.pptx")
    cmd, kwargs = calls[-1]
    assert cmd[1:3] == ["-X", "utf8"]
    assert kwargs.get("encoding") == "utf-8"


# =============================================================== BUILD-CODE-9


def test_a_greek_bumper_is_capitalised_without_the_tonos(build):
    """BUILD-CODE-9: str.upper() keeps the tonos, a spelling error on every pill."""
    spec = deck(
        [_content("Τα αποτελέσματα ξεπέρασαν τον στόχο", ["Ένα"], bumper="Ευρήματα")],
        language="el",
    )
    out = build(spec)
    texts = [b[0] for b in shape_boxes(slide_xml(out, 2))]
    assert "ΕΥΡΗΜΑΤΑ" in texts, texts


def test_a_greek_deck_gets_greek_boilerplate(build):
    """BUILD-CODE-9: English "Source:" and "Contents" on Greek board exhibits."""
    spec = deck(
        [
            {
                "type": "contents",
                "content": {
                    "sections": [{"title": "Πού βρισκόμαστε"}, {"title": "Τι προτείνουμε"}]
                },
            },
            {
                "type": "table",
                "content": {
                    "title": "Οι προμήθειες αυξήθηκαν",
                    "source": {"name": "Λογιστήριο", "as_of": "30 Ιουνίου 2026"},
                },
                "table": {"headers": ["Μέγεθος", "2026"], "rows": [["Προμήθειες", "12"]]},
            },
        ],
        language="el",
    )
    out = build(spec)
    contents = [b[0] for b in shape_boxes(slide_xml(out, 2))]
    assert "Περιεχόμενα" in contents
    table_texts = [b[0] for b in shape_boxes(slide_xml(out, 3))]
    assert any(t.startswith("Πηγή: Λογιστήριο") for t in table_texts), table_texts


# =============================================================== BUILD-CODE-10


MALFORMED = {
    "empty": ("", "the spec is empty"),
    "top_level_list": ("- type: cover\n  content: {title: X}\n", "mapping"),
    "slides_is_mapping": ("slides:\n  type: cover\n", "slides"),
    "type_null": ("slides:\n  - type:\n    content: {title: X}\n", "slides[0].type"),
    "content_null": ("slides:\n  - type: cover\n    content:\n", "slides[0].content"),
    "values_strings": (
        "slides:\n  - type: chart\n    content: {title: Volumes rose, source: {name: MIS, as_of: '2026'}}\n"
        "    chart: {type: bar, data: {categories: [Q1, Q2], series: [{name: s, values: ['12%', '15%']}]}}\n",
        "slides[0].chart.data.series[0].values",
    ),
    "length_mismatch": (
        "slides:\n  - type: chart\n    content: {title: Volumes rose, source: {name: MIS, as_of: '2026'}}\n"
        "    chart: {type: bar, data: {categories: [Q1, Q2, Q3, Q4], series: [{name: s, values: [1, 2, 3]}]}}\n",
        "slides[0].chart.data.series[0].values",
    ),
    "rows_as_strings": (
        "slides:\n  - type: table\n    content: {title: Assets grew, source: {name: MIS, as_of: '2026'}}\n"
        "    table: {headers: [Metric, Value], rows: ['Assets, 78.5']}\n",
        "slides[0].table.rows[0]",
    ),
    "source_list": (
        "slides:\n  - type: chart\n    content: {title: Volumes rose, source: [MIS, '2026']}\n"
        "    chart: {type: bar, data: {categories: [Q1], series: [{name: s, values: [1]}]}}\n",
        "slides[0].content.source",
    ),
    "control_char": (
        'slides:\n  - type: content\n    content:\n      title: "Revenue \\x01 grew"\n      points: [a]\n',
        "slides[0].content.title",
    ),
    "bumper_yaml_bool": (
        "slides:\n  - type: content\n    content:\n      bumper: YES\n      title: Revenue grew\n      points: [a]\n",
        "slides[0].content.bumper",
    ),
    "unquoted_colon": (
        "slides:\n  - type: cover\n    content:\n      title: Q3: the year\n",
        "line 4",
    ),
}


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_a_malformed_spec_gets_a_located_message_not_a_traceback(tmp_path, name):
    """BUILD-CODE-10: 10 of 16 plausible specs died with a bare Python message."""
    text, where = MALFORMED[name]
    spec = tmp_path / f"{name}.yaml"
    spec.write_text(text, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(spec), str(tmp_path / "o.pptx")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=tmp_path,
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode == 1, output
    assert "Traceback" not in output, output
    assert where in output, output
    assert "Fix:" in output, output
    assert not (tmp_path / "o.pptx").exists()


# =============================================================== BUILD-CODE-13


def test_every_titled_slide_has_a_real_title_placeholder(build):
    """BUILD-CODE-13: no slide had a title placeholder, so the Accessibility Checker
    flagged every slide and screen readers could not navigate by title."""
    out = build(deck([_content("Three things moved", ["One"])]))
    for number, title in ((1, "Test deck"), (2, "Three things moved")):
        root = slide_xml(out, number)
        ph = root.find(".//p:sp/p:nvSpPr/p:nvPr/p:ph", NS)
        assert ph is not None and ph.get("type") in ("title", "ctrTitle"), number
        sp = ph.getparent().getparent().getparent()
        assert "".join(t.text for t in sp.iter(f"{A}t")) == title
        first_shape = root.find(".//p:spTree", NS)[2]
        assert first_shape is sp, "the title must be first in reading order"


def test_logos_are_decorative_and_never_named_by_filename(build):
    out = build(deck([_content("Three things moved", ["One"])]))
    for number in (1, 2, 3):
        for pic in slide_xml(out, number).iter(f"{P}pic"):
            nv = pic.find("p:nvPicPr/p:cNvPr", NS)
            assert not nv.get("descr", "").endswith(".png")
            decorative = nv.find(".//{*}decorative")
            assert decorative is not None and decorative.get("val") == "1"


# =============================================================== E2E-SMOKE-7


def test_core_properties_come_from_the_spec_not_the_python_pptx_template(build):
    spec = deck([_content("Three things moved", ["One"])], title="Quarterly review")
    out = build(spec)
    from pptx import Presentation

    props = Presentation(str(out)).core_properties
    assert props.title == "Quarterly review"
    assert props.last_modified_by != "Steve Canny"
    assert "python-pptx" not in (props.comments or "")
    assert "python-pptx" not in (props.subject or "")
    now = datetime.now(UTC).replace(tzinfo=None)
    assert props.created > now - timedelta(days=1)
    assert props.modified > now - timedelta(days=1)


def test_the_slide_size_is_exactly_16_9_widescreen(build):
    """Also noticed: Inches(13.33) is 12,188,952 EMU and the template said 4:3."""
    out = build(deck([_content("Three things moved", ["One"])]))
    size = part_xml(out, "ppt/presentation.xml").find("p:sldSz", NS)
    assert size.get("cx") == "12192000" and size.get("cy") == "6858000"
    assert size.get("type") is None


# =============================================================== E2E-SMOKE-15


def test_currency_columns_are_right_aligned_like_percentages(build):
    spec = deck(
        [
            {
                "type": "table",
                "content": {"title": "Net fees grew in every line", "source": SOURCE},
                "table": {
                    "headers": ["Line", "2025", "Change"],
                    "rows": [
                        ["Interchange", "EUR 42M", "+14%"],
                        ["Annual fees", "€ 18,5 εκατ.", "+17%"],
                    ],
                },
            }
        ]
    )
    out = build(spec)
    root = slide_xml(out, 2)
    cells = root.findall(".//a:tbl/a:tr", NS)[1].findall("a:tc", NS)
    aligns = [tc.find(".//a:pPr", NS).get("algn") for tc in cells]
    assert aligns == ["l", "r", "r"]


def test_the_chart_number_format_reaches_the_data_labels(build):
    out = build(
        deck(
            [
                _chart(
                    "Volumes rose",
                    "bar",
                    ["Q1", "Q2"],
                    [{"name": "s", "values": [1.25, 2.5]}],
                    number_format="#,##0.0",
                )
            ]
        )
    )
    root = part_xml(out, chart_parts(out)[0])
    fmt = root.find(".//c:dLbls/c:numFmt", NS)
    assert fmt is not None
    assert fmt.get("formatCode") == "#,##0.0" and fmt.get("sourceLinked") == "0"


# =============================================================== DOCS-MEMORY-8


def test_no_shape_inherits_a_theme_shadow(build):
    """DOCS-MEMORY-8: python-pptx leaves p:style effectRef idx=2 on every autoshape,
    which LibreOffice draws as a drop shadow the brand forbids."""
    out = build(deck([_content("Three things moved", ["One"], bumper="Key finding")]))
    for number in (1, 2, 3):
        for ref in slide_xml(out, number).iter(f"{A}effectRef"):
            assert ref.get("idx") == "0", f"slide {number}"


# =============================================================== also noticed


def test_the_source_line_ends_on_the_6_5_inch_floor(build):
    out = build(deck([_chart("Volumes rose", "bar", ["Q1"], [{"name": "s", "values": [1]}])]))
    for text, _, y, _, h in shape_boxes(slide_xml(out, 2)):
        if text.startswith("Source:"):
            assert y + h <= 6.5 + 1e-6
            break
    else:
        raise AssertionError("no source line")


def test_the_logo_keeps_the_wordmark_aspect_ratio(build):
    """Also noticed: both logo boxes stretched the 1200x348 wordmark by about 1%."""
    out = build(deck([_content("Three things moved", ["One"])]))
    for number in (1, 2):
        for pic in slide_xml(out, number).iter(f"{P}pic"):
            ext = pic.find(".//a:xfrm/a:ext", NS)
            assert int(ext.get("cx")) / int(ext.get("cy")) == pytest.approx(1200 / 348, rel=0.003)


def test_the_page_number_is_a_slide_number_field_at_the_physical_position(build):
    """Also noticed: page numbers counted content slides, so slide 3 printed "1"."""
    out = build(
        deck(
            [
                {"type": "divider", "content": {"number": 1, "title": "Where we stand"}},
                _content("Three things moved", ["One"]),
            ]
        )
    )
    root = slide_xml(out, 3)
    fields = list(root.iter(f"{A}fld"))
    assert len(fields) == 1 and fields[0].get("type") == "slidenum"
    assert "".join(t.text for t in fields[0].iter(f"{A}t")) == "3"


def test_a_short_decks_contents_page_carries_no_page_number(build):
    """Standard #18: no page number on the contents page when the deck is short."""
    spec = deck(
        [{"type": "contents", "content": {"sections": [{"title": "One"}, {"title": "Two"}]}}]
    )
    out = build(spec)
    root = slide_xml(out, 2)
    assert not list(root.iter(f"{A}fld"))
    corner = [b for b in shape_boxes(root) if b[1] > 12.5 and b[2] > 7.0]
    assert not corner, corner


def test_the_waterfall_category_axis_respects_the_10pt_floor(build):
    """BRAND-SSOT-8: the waterfall axis was set at 9pt, under Standard #11's floor."""
    spec = deck(
        [
            {
                "type": "waterfall",
                "content": {
                    "title": "Fees bridge from 2025 to 2026",
                    "source": SOURCE,
                    "waterfall_items": [
                        {"label": "2025", "value": 100},
                        {"label": "Cards", "value": 12},
                        {"label": "2026", "value": 112, "total": True},
                    ],
                },
            }
        ]
    )
    out = build(spec)
    root = part_xml(out, chart_parts(out)[0])
    sizes = [
        int(r.get("sz")) for r in root.find(".//c:catAx", NS).iter(f"{A}defRPr") if r.get("sz")
    ]
    assert sizes and min(sizes) >= 1000


def test_a_waterfall_total_below_zero_is_drawn_as_a_total(build):
    """Also noticed: when the running total went negative the invisible base went
    negative too, and the closing total was drawn in the increase colour."""
    spec = deck(
        [
            {
                "type": "waterfall",
                "content": {
                    "title": "The year closed below zero",
                    "source": SOURCE,
                    "waterfall_items": [
                        {"label": "Start", "value": 10},
                        {"label": "Loss", "value": -15},
                        {"label": "End", "value": -5, "total": True},
                    ],
                },
            }
        ]
    )
    out = build(spec)
    root = part_xml(out, chart_parts(out)[0])
    # Which visible series carry a non-zero value for the third category, "End"?
    last_colours = set()
    for ser in root.findall(".//c:barChart/c:ser", NS):
        pt = ser.find("c:val//c:pt[@idx='2']/c:v", NS)
        fill = ser.find("c:spPr/a:solidFill/a:srgbClr", NS)
        if pt is not None and float(pt.text) != 0 and fill is not None:
            last_colours.add(fill.get("val"))
    assert last_colours == {"003841"}


def test_divider_number_and_title_share_a_baseline(build):
    """BRAND-SSOT-14: 60pt and 48pt boxes top-anchored at one y put the baselines
    about 0.16" apart; Standard #3 wants one baseline."""
    out = build(deck([{"type": "divider", "content": {"number": 1, "title": "Where we stand"}}]))
    root = slide_xml(out, 2)
    _, _, n_y, _, _ = box_with_text(root, "01")
    _, _, t_y, _, _ = box_with_text(root, "Where we stand")
    from nbg_text import ASCENT_EM

    number_baseline = n_y + 60 * ASCENT_EM / 72
    title_baseline = t_y + 48 * ASCENT_EM / 72
    assert number_baseline == pytest.approx(title_baseline, abs=0.01)


def test_chart_legend_and_labels_use_the_brand_type_scale(build):
    out = build(
        deck(
            [
                _chart(
                    "Both years grew",
                    "bar",
                    ["Q1", "Q2"],
                    [{"name": "2025", "values": [1, 2]}, {"name": "2026", "values": [2, 3]}],
                )
            ]
        )
    )
    root = part_xml(out, chart_parts(out)[0])
    legend_sizes = {r.get("sz") for r in root.find(".//c:legend", NS).iter(f"{A}defRPr")}
    assert legend_sizes == {"1200"}
    label_sizes = {
        r.get("sz") for dlbls in root.iter(f"{C}dLbls") for r in dlbls.iter(f"{A}defRPr")
    }
    assert label_sizes == {"1200"}


def test_the_doughnut_hole_is_55_percent(build):
    out = build(
        deck(
            [
                _chart(
                    "Cards lead the fee mix",
                    "doughnut",
                    ["Cards", "Accounts"],
                    [{"name": "Fees", "values": [60, 40]}],
                )
            ]
        )
    )
    root = part_xml(out, chart_parts(out)[0])
    assert root.find(".//c:doughnutChart/c:holeSize", NS).get("val") == "55"


# Label positions PowerPoint accepts per chart element. The schema allows dLblPos on
# every chart; PowerPoint does not, and a doughnut slice label with dLblPos="ctr" hung
# its PDF export at that slide (found by exporting the examples from PowerPoint).
POWERPOINT_LABEL_POSITIONS = {
    "barChart:clustered": {"ctr", "inEnd", "inBase", "outEnd"},
    "barChart:stacked": {"ctr", "inEnd", "inBase"},
    "lineChart:standard": {"t", "b", "l", "r", "ctr"},
    "areaChart:standard": set(),
    "doughnutChart:": set(),
}


def test_every_label_position_is_one_powerpoint_supports(tmp_path, monkeypatch):
    passing_validator(monkeypatch, nbg_build)
    checked = 0
    for spec in sorted(EXAMPLES_DIR.glob("*.yaml")):
        out = tmp_path / f"{spec.stem}.pptx"
        nbg_build.build_presentation(spec, out)
        for part in chart_parts(out):
            for plot in part_xml(out, part).find(".//c:plotArea", NS):
                tag = plot.tag.split("}")[1]
                if not tag.endswith("Chart"):
                    continue
                grouping = plot.find("c:grouping", NS)
                key = f"{tag}:{grouping.get('val') if grouping is not None else ''}"
                allowed = POWERPOINT_LABEL_POSITIONS[key]
                for pos in plot.iter(f"{C}dLblPos"):
                    checked += 1
                    assert pos.get("val") in allowed, f"{spec.name} {part} {key}: {pos.get('val')}"
    assert checked, "no label positions examined"


def test_a_greek_deck_writes_greek_separators_in_tables_and_waterfall_labels(build):
    """E2E-OUTPUT-02 / DOCS-ACCURACY-1: presentation.language el is documented to drive
    number formats, yet table cells read 1,234.5 and waterfall steps +1,000.25."""
    table = {
        "type": "table",
        "content": {"title": "Οι όγκοι ανά κανάλι", "source": SOURCE},
        "table": {"headers": ["Κανάλι", "Όγκος", "Πελάτες"], "rows": [["Κάρτες", 1234.5, 2500000]]},
    }
    waterfall = {
        "type": "waterfall",
        "content": {"title": "Η γέφυρα των εσόδων", "source": SOURCE},
        "chart": {
            "type": "waterfall",
            "data": {
                "items": [
                    {"label": "Αρχή", "value": 1250.5},
                    {"label": "Άνοδος", "value": 1000.25},
                    {"label": "Τέλος", "value": 2250.75},
                ]
            },
        },
    }
    out = build(deck([table, waterfall], language="el"))
    cells = [b[0] for b in shape_boxes(slide_xml(out, 2))]
    cell_text = " ".join(
        "".join(t.text or "" for t in tc.iter(f"{A}t")) for tc in slide_xml(out, 2).iter(f"{A}tc")
    )
    assert "1.234,5" in cell_text and "2.500.000" in cell_text, (cells, cell_text)
    labels = [
        "".join(t.text or "" for t in dlbl.iter(f"{A}t"))
        for dlbl in part_xml(out, chart_parts(out)[0]).iter(f"{C}dLbl")
    ]
    labels = [label for label in labels if label]
    assert sorted(labels) == sorted(["1.250,50", "+1.000,25", "2.250,75"]), labels


@pytest.mark.parametrize("chart_type", ["bar", "bar_horizontal", "bar_stacked"])
def test_bars_with_close_values_start_their_axis_at_zero(build, chart_type):
    """E2E-OUTPUT-01: 93, 91, 90 and 88 drew on an axis PowerPoint started near 86, so a
    2-point gap looked like a doubling, and the Zero Baseline check passed it."""
    out = build(
        deck(
            [
                _chart(
                    "Contactless share is above 88% in every segment",
                    chart_type,
                    ["Retail", "Affluent", "Premium", "Business"],
                    [{"name": "Share", "values": [93, 91, 90, 88]}],
                )
            ]
        )
    )
    root = part_xml(out, chart_parts(out)[0])
    minimum = root.find(".//c:valAx/c:scaling/c:min", NS)
    assert minimum is not None and float(minimum.get("val")) == 0.0


def test_a_waterfall_of_positive_totals_starts_its_axis_at_zero(build):
    spec = deck(
        [
            {
                "type": "waterfall",
                "content": {"title": "Fees rose from 68 to 80", "source": SOURCE},
                "chart": {
                    "type": "waterfall",
                    "data": {
                        "items": [
                            {"label": "Q4 2024", "value": 68},
                            {"label": "Interchange", "value": 6},
                            {"label": "Annual fees", "value": 3},
                            {"label": "FX", "value": 3},
                            {"label": "Q4 2025", "value": 80},
                        ]
                    },
                },
            }
        ]
    )
    out = build(spec)
    root = part_xml(out, chart_parts(out)[0])
    assert float(root.find(".//c:valAx/c:scaling/c:min", NS).get("val")) == 0.0


def test_bars_with_a_negative_value_keep_the_automatic_axis(build):
    out = build(
        deck(
            [
                _chart(
                    "Margins moved both ways", "bar", ["A", "B"], [{"name": "M", "values": [3, -2]}]
                )
            ]
        )
    )
    root = part_xml(out, chart_parts(out)[0])
    assert root.find(".//c:valAx/c:scaling/c:min", NS) is None


def test_a_chart_with_no_series_is_an_error_not_a_blank_plot(build):
    """ARCHITECTURE-5: a chart slide with no data built green with an empty plot."""
    spec = deck([_chart("Volumes rose", "bar", ["Q1"], [])])
    with pytest.raises(Exception, match=r"slide 2"):
        build(spec)


def test_contents_that_cannot_fit_is_refused(build):
    """BUILD-CODE-4: long agendas ran off the slide."""
    sections = [{"title": f"Section {i}", "description": "A long teaser line"} for i in range(8)]
    spec = deck([{"type": "contents", "content": {"sections": sections}}])
    with pytest.raises(Exception, match=r"(?s)slide 2.*contents"):
        build(spec)


# =============================================================== examples


def test_no_example_cover_carries_a_divisions_unit_list():
    """E2E-SMOKE also-noticed / BRAND-SSOT-4: the quarterly-report cover listed one
    division's internal units in a public repo."""
    for spec in EXAMPLES_DIR.glob("*.yaml"):
        text = spec.read_text(encoding="utf-8")
        assert "GoForMore" not in text and "SSB" not in text, spec.name


def test_label_dark_candidate_is_pure_black():
    """Softening it to #202020 drops the worst case to 4.036:1, under AA."""
    assert nbg_build.LABEL_DARK_HEX == "000000"


def test_label_text_color_clears_aa_on_the_two_fills_that_used_to_fail():
    for fill in ("5D8D2F", "F60037"):
        chosen = nbg_build._label_text_color(fill)
        assert contrast_ratio(fill, str(chosen)) >= 4.5, fill


def test_environment_is_utf8_capable():
    """Guard for the Greek tests above: they write UTF-8 spec files explicitly."""
    assert "utf" in (sys.getfilesystemencoding() or "").lower() or os.name == "nt"
    assert yaml.safe_load("x: π")["x"] == "π"
    assert emu(1) == 914400
