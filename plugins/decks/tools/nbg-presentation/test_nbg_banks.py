"""Peer-bank comparisons: the builder draws each bank in its brand colour with its logo.

assets/bank-logos/README.md makes both mandatory for a chart comparing the systemic
banks, and the validator's Bank Branding check fails a chart that misses either. The
spec just names the banks: as the categories of a one-series bar, bar_horizontal or
doughnut chart, or as the series of any bar or line chart.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import nbg_build
import nbg_spec
import nbg_tokens
import pytest
from testkit import (
    EXAMPLES_DIR,
    NS,
    chart_parts,
    deck,
    inches,
    part_xml,
    passing_validator,
    slide_xml,
    write_spec,
)

A = f"{{{NS['a']}}}"
P = f"{{{NS['p']}}}"
C = f"{{{NS['c']}}}"
R_EMBED = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
SOURCE = {"name": "Illustrative figures", "as_of": "31 December 2025"}
BANKS = ["NBG", "Eurobank", "Piraeus Bank", "Alpha Bank"]
COLOURS = {"NBG": "007B85", "Eurobank": "DC2646", "Piraeus Bank": "FFC02D", "Alpha Bank": "0D488B"}


@pytest.fixture
def build(tmp_path, monkeypatch):
    passing_validator(monkeypatch, nbg_build)

    def _build(spec, name="deck"):
        out = tmp_path / f"{name}.pptx"
        nbg_build.build_presentation(write_spec(tmp_path, spec, f"{name}.yaml"), out)
        return out

    return _build


def _bank_chart(chart_type="bar", categories=None, series=None, **extra):
    categories = categories if categories is not None else BANKS
    series = series or [{"name": "Mobile share", "values": [58, 52, 49, 46][: len(categories)]}]
    return {
        "type": "chart",
        "content": {"title": "We lead the four systemic banks on mobile share", "source": SOURCE},
        "chart": {
            "type": chart_type,
            "data": {"categories": categories, "series": series},
            **extra,
        },
    }


def _point_fills(chart_root, series_index=0):
    ser = chart_root.findall(".//c:ser", NS)[series_index]
    return {
        int(pt.find("c:idx", NS).get("val")): pt.find(".//a:srgbClr", NS).get("val")
        for pt in ser.findall("c:dPt", NS)
    }


def _logos(root):
    return [
        p
        for p in root.iter(f"{P}pic")
        if (p.find(".//p:cNvPr", NS).get("descr") or "").endswith(" logo")
    ]


def _box(el):
    off, ext = el.find(".//a:xfrm/a:off", NS), el.find(".//a:xfrm/a:ext", NS)
    return (
        inches(off.get("x")),
        inches(off.get("y")),
        inches(ext.get("cx")),
        inches(ext.get("cy")),
    )


def _frame_box(root):
    frame = root.find(".//p:graphicFrame", NS)
    off, ext = frame.find("p:xfrm/a:off", NS), frame.find("p:xfrm/a:ext", NS)
    return (
        inches(off.get("x")),
        inches(off.get("y")),
        inches(ext.get("cx")),
        inches(ext.get("cy")),
    )


def _inner(chart_root):
    layout = chart_root.find(".//c:plotArea/c:layout/c:manualLayout", NS)
    assert layout is not None, "the plot area is placed exactly, so logos can line up"
    assert layout.find("c:layoutTarget", NS).get("val") == "inner"
    return tuple(float(layout.find(f"c:{k}", NS).get("val")) for k in ("x", "y", "w", "h"))


def _stretch(out, slide_no, pic):
    """How far a picture's shown aspect is from its image's own aspect."""
    from PIL import Image

    rels = part_xml(out, f"ppt/slides/_rels/slide{slide_no}.xml.rels")
    target = {r.get("Id"): r.get("Target") for r in rels}
    name = "ppt/" + target[pic.find(f".//{A}blip").get(R_EMBED)].replace("../", "")
    with zipfile.ZipFile(out) as zf:
        w_px, h_px = Image.open(io.BytesIO(zf.read(name))).size
    _, _, w, h = _box(pic)
    return abs((w / h) / (w_px / h_px) - 1)


# ---------------------------------------------------------------- tokens


def test_every_bank_has_a_palette_colour_a_logo_and_unambiguous_names():
    """Colours live once, in extended_palettes.peer_banks (what the validator checks);
    banks adds the logo and the names. Full names count anywhere; the short
    label_aliases only in a chart label, where "Alpha" beside "Eurobank" is a bank
    but "alpha release" in running text is not (VALIDATOR-9)."""
    banks = nbg_tokens.get("banks")
    peer = nbg_tokens.get("extended_palettes.peer_banks")
    assert set(banks) == set(peer)
    for key, bank in banks.items():
        assert "color" not in bank, "one colour source: extended_palettes.peer_banks"
        assert (nbg_spec.ASSETS_DIR / bank["logo"]).is_file(), bank["logo"]
        for alias in bank["names"] + bank["label_aliases"]:
            assert nbg_spec.bank_of(alias) == key, alias
    assert nbg_spec.bank_of("Market average") is None
    assert nbg_spec.bank_of("NBG and Eurobank") is None  # two banks in one label


def test_greek_and_english_names_are_recognised_without_case_or_accents():
    assert nbg_spec.bank_of("Εθνική Τράπεζα") == "nbg"
    assert nbg_spec.bank_of("ΕΤΕ") == "nbg"
    assert nbg_spec.bank_of("τράπεζα πειραιώς") == "piraeus"
    assert nbg_spec.bank_of("Άλφα") == "alpha"
    assert nbg_spec.bank_of("alpha bank") == "alpha"


@pytest.mark.parametrize("label", ["Bank", "bank", "Τράπεζα", "ΤΡΑΠΕΖΑ", "Other banks", "Trapeza"])
def test_the_word_bank_alone_names_no_bank(label):
    assert nbg_spec.bank_of(label) is None


# ---------------------------------------------------------------- banks as categories


def test_bank_bars_take_their_brand_colours_and_a_logo_centred_under_each_bar(build):
    out = build(deck([_bank_chart("bar")]))
    chart = part_xml(out, chart_parts(out)[0])
    assert _point_fills(chart) == {i: COLOURS[b] for i, b in enumerate(BANKS)}
    root = slide_xml(out, 2)
    logos = sorted(_logos(root), key=lambda p: _box(p)[0])
    assert [p.find(".//p:cNvPr", NS).get("descr") for p in logos] == [f"{b} logo" for b in BANKS]
    fx, fy, fw, fh = _frame_box(root)
    ix, iy, iw, ih = _inner(chart)
    for j, pic in enumerate(logos):
        x, y, w, h = _box(pic)
        centre = fx + (ix + iw * (j + 0.5) / len(BANKS)) * fw
        assert x + w / 2 == pytest.approx(centre, abs=0.02), BANKS[j]
        assert y >= fy + (iy + ih) * fh, f"{BANKS[j]}'s logo sits under the axis"
        assert y + h <= fy + fh + 0.01, "inside the chart's frame"
        assert _stretch(out, 2, pic) < 0.03, f"{BANKS[j]}'s logo keeps its aspect"


def test_bank_bars_laid_sideways_put_each_logo_beside_its_bar(build):
    out = build(deck([_bank_chart("bar_horizontal")]))
    chart = part_xml(out, chart_parts(out)[0])
    assert _point_fills(chart) == {i: COLOURS[b] for i, b in enumerate(BANKS)}
    root = slide_xml(out, 2)
    logos = sorted(_logos(root), key=lambda p: _box(p)[1])
    assert len(logos) == 4
    fx, fy, fw, fh = _frame_box(root)
    ix, iy, _, ih = _inner(chart)
    for j, pic in enumerate(logos):
        x, y, w, h = _box(pic)
        middle = fy + (iy + ih * (j + 0.5) / len(BANKS)) * fh
        assert y + h / 2 == pytest.approx(middle, abs=0.02), BANKS[j]
        assert x + w <= fx + ix * fw, f"{BANKS[j]}'s logo sits left of the bars"
        assert x >= fx - 0.001


def test_a_bank_doughnut_colours_each_slice_and_names_it_in_a_logo_legend(build):
    series = [{"name": "Share", "values": [0.31, 0.27, 0.24, 0.18]}]
    out = build(deck([_bank_chart("doughnut", series=series)]))
    chart = part_xml(out, chart_parts(out)[0])
    assert _point_fills(chart) == {i: COLOURS[b] for i, b in enumerate(BANKS)}
    assert chart.find(".//c:legend", NS) is None, "the logo legend replaces the chart's own"
    root = slide_xml(out, 2)
    assert len(_logos(root)) == 4
    _, fy, _, fh = _frame_box(root)
    assert min(_box(p)[1] for p in _logos(root)) >= fy + fh, "the legend row is under the chart"


# ---------------------------------------------------------------- banks as series


def test_bank_series_take_their_colours_and_a_legend_row_of_swatch_logo_and_name(build):
    series = [
        {"name": b, "values": [v, v + 2, v + 3]}
        for b, v in zip(BANKS, (40, 35, 33, 30), strict=True)
    ]
    out = build(deck([_bank_chart("line", categories=["2023", "2024", "2025"], series=series)]))
    chart = part_xml(out, chart_parts(out)[0])
    lines = [
        s.find("c:spPr/a:ln//a:srgbClr", NS).get("val")
        for s in chart.findall(".//c:lineChart/c:ser", NS)
    ]
    assert lines == [COLOURS[b] for b in BANKS]
    assert chart.find(".//c:legend", NS) is None
    root = slide_xml(out, 2)
    _, fy, _, fh = _frame_box(root)
    logos = sorted(_logos(root), key=lambda p: _box(p)[0])
    assert [p.find(".//p:cNvPr", NS).get("descr") for p in logos] == [f"{b} logo" for b in BANKS]
    texts = {"".join(t.text or "" for t in sp.iter(f"{A}t")): sp for sp in root.iter(f"{P}sp")}
    for bank in BANKS:
        assert bank in texts, f"{bank} is named in the legend"
        swatches = [
            sp
            for sp in root.iter(f"{P}sp")
            if (f := sp.find("p:spPr/a:solidFill/a:srgbClr", NS)) is not None
            and f.get("val") == COLOURS[bank]
        ]
        assert swatches, f"{bank} has a colour swatch in the legend"
        assert _box(swatches[0])[1] >= fy + fh


def test_greek_bank_names_get_the_colours_and_greek_alt_text(build):
    categories = ["Εθνική Τράπεζα", "Eurobank", "Τράπεζα Πειραιώς", "Άλφα"]
    spec = deck([_bank_chart("bar", categories=categories)], language="el")
    out = build(spec)
    chart = part_xml(out, chart_parts(out)[0])
    assert _point_fills(chart) == {0: "007B85", 1: "DC2646", 2: "FFC02D", 3: "0D488B"}
    alts = [
        p.find(".//p:cNvPr", NS).get("descr")
        for p in slide_xml(out, 2).iter(f"{P}pic")
        if p.find(".//p:cNvPr", NS).get("descr")
    ]
    assert len(alts) == 4 and all(a.startswith("Λογότυπο") for a in alts), alts


# ---------------------------------------------------------------- opt-out and check


def test_bank_logos_false_on_a_bank_chart_is_a_check_error(tmp_path):
    """The Bank Branding gate fails a comparison without one logo per bank, so a
    warning here only let check pass a deck the build then rejected."""
    spec = write_spec(tmp_path, deck([_bank_chart("bar", bank_logos=False)]), "optout.yaml")
    report = nbg_build.check(spec)
    error = next(i for i in report.errors if i.path == "slides[1].chart.bank_logos")
    assert "Bank Branding" in error.message
    with pytest.raises(nbg_build.SpecInvalid):
        nbg_build.build_presentation(spec, tmp_path / "optout.pptx", validate=False)


def test_check_refuses_bank_charts_the_builder_cannot_brand(tmp_path):
    two_series = _bank_chart(
        "bar",
        series=[{"name": "2024", "values": [1, 2, 3, 4]}, {"name": "2025", "values": [2, 3, 4, 5]}],
    )
    over_time = _bank_chart("line")
    over_time["content"] = {**over_time["content"], "title": "Our share rose every year"}
    report = nbg_build.check(write_spec(tmp_path, deck([two_series, over_time]), "refuse.yaml"))
    paths = {i.path for i in report.errors}
    assert "slides[1].chart.data.series" in paths
    assert "slides[2].chart.type" in paths


def test_highlight_category_on_a_bank_chart_is_ignored_with_a_warning(tmp_path):
    slide = _bank_chart("bar", highlight_category="NBG")
    report = nbg_build.check(write_spec(tmp_path, deck([slide]), "hl.yaml"))
    assert report.ok
    assert any(i.path == "slides[1].chart.highlight_category" for i in report.warnings)


# ---------------------------------------------------------------- the gate


def test_the_bank_example_passes_bank_branding_having_examined_the_chart(tmp_path):
    """Passing is not enough: a check that examined nothing also passes."""
    spec = EXAMPLES_DIR / "quarterly-report.yaml"
    out = tmp_path / "quarterly.pptx"
    nbg_build.build_presentation(spec, out, validate=False)
    validator = Path(nbg_build.__file__).with_name("nbg_validate.py")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(validator), str(out), "--format", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    report = json.loads(proc.stdout)
    bank = next(c for c in report["checks"] if c["name"] == "Bank Branding")
    assert bank["status"] == "pass" and bank["examined"] >= 1, bank
