"""Tests for nbg_build.py, nbg_validate.py and the OOXML injectors.

Runs in CI under `pytest plugins`. Run by hand with:
    uv run --with pytest --with python-pptx --with lxml --with defusedxml \
        --with pyyaml python -m pytest test_nbg_build.py -q
"""

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

# nbg_build requires yaml at import time
pytest.importorskip("yaml")

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent))
import nbg_build  # noqa: E402

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
EXAMPLE_NAMES = ["quarterly-report", "executive-summary", "strategy-deck"]
CHART_NS = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
CHART_PART = re.compile(r"^ppt/charts/chart(\d+)\.xml$")


def _chart_part_index(name: str) -> int:
    """Sort key for chart parts, ordering chart10 after chart2.

    A named function rather than a lambda so a name that does not match fails
    here, saying which one, instead of raising AttributeError from inside a
    sort with no indication of the offending file.
    """
    match = CHART_PART.match(name)
    if match is None:
        raise AssertionError(f"not a chart part name: {name!r}")
    return int(match.group(1))


def test_normalize_slide_type_passthrough():
    """Catalog paths with slashes pass through unchanged."""
    assert nbg_build.normalize_slide_type("covers/simple_white") == "covers/simple_white"
    assert (
        nbg_build.normalize_slide_type("content/text_with_bullets") == "content/text_with_bullets"
    )


def test_normalize_slide_type_mckinsey_mapping():
    """McKinsey types map to catalog paths."""
    assert nbg_build.normalize_slide_type("cover") == "covers/quiet"
    assert nbg_build.normalize_slide_type("content") == "content/text_only"
    assert nbg_build.normalize_slide_type("back_cover") == "back_covers/quiet"
    assert nbg_build.normalize_slide_type("divider") == "dividers/quiet_white"


def test_normalize_slide_type_with_visual():
    """recommended_visual hint overrides base type."""
    assert nbg_build.normalize_slide_type("content", "bar_chart") == "charts/bar_single"
    assert nbg_build.normalize_slide_type("content", "table") == "tables/half_page"
    assert nbg_build.normalize_slide_type("content", "kpi_dashboard") == "content/text_only"


def test_normalize_slide_type_unknown_defaults():
    """Unknown types default to content/text_with_bullets."""
    assert nbg_build.normalize_slide_type("unknown_type") == "content/text_only"


def test_load_catalog_returns_valid_structure():
    """Catalog loads and has expected top-level keys."""
    catalog = nbg_build.load_catalog()
    assert "templates" in catalog
    assert "GR" in catalog["templates"] or "EN" in catalog["templates"]


def test_example_yaml_files_parse():
    """All example YAML files parse without errors."""
    import yaml

    if not EXAMPLES_DIR.exists():
        pytest.skip("Examples directory not found")

    yaml_files = list(EXAMPLES_DIR.glob("*.yaml")) + list(EXAMPLES_DIR.glob("*.yml"))
    assert len(yaml_files) > 0, "No example YAML files found"

    for yf in yaml_files:
        with open(yf) as f:
            data = yaml.safe_load(f)
        assert data is not None, f"{yf.name} parsed as empty"


# --------------------------------------------------------------- slide.chart


def test_chart_spec_reads_the_canonical_slide_chart_block():
    """`slide.chart.{type,data}` is the published contract and was never read."""
    slide = {
        "type": "chart",
        "recommended_visual": "line_chart",
        "content": {"title": "t"},
        "chart": {
            "type": "line",
            "data": {
                "categories": ["Jan", "Feb"],
                "series": [{"name": "2025", "values": [3.8, 3.7]}],
            },
        },
    }
    kind, categories, series = nbg_build._chart_spec(slide)
    assert kind == "line"
    assert categories == ["Jan", "Feb"]
    assert series == [{"name": "2025", "values": [3.8, 3.7]}]


def test_chart_spec_reads_the_readme_doughnut_shape():
    """README documents `chart.labels` + `chart.values` for a single series."""
    slide = {
        "type": "charts/pie_single",
        "chart": {"type": "doughnut", "labels": ["NBG", "Other"], "values": [27, 73]},
    }
    kind, categories, series = nbg_build._chart_spec(slide)
    assert kind == "doughnut"
    assert categories == ["NBG", "Other"]
    assert series == [{"name": "", "values": [27, 73]}]


def test_chart_spec_still_reads_the_undocumented_content_shape():
    """The shape the builder used to read keeps working."""
    slide = {
        "type": "bar_chart",
        "content": {"categories": ["a"], "series": [{"name": "s", "values": [1]}]},
    }
    kind, categories, series = nbg_build._chart_spec(slide)
    assert kind == "bar"
    assert categories == ["a"]
    assert series == [{"name": "s", "values": [1]}]


def test_chart_spec_subtype_falls_back_through_type_then_visual():
    assert nbg_build._chart_spec({"type": "pie_chart"})[0] == "pie"
    assert nbg_build._chart_spec({"type": "charts/line_single"})[0] == "line"
    assert nbg_build._chart_spec({"type": "chart", "recommended_visual": "bar_chart"})[0] == "bar"
    assert nbg_build._chart_spec({"type": "chart"})[0] == "bar"


def test_classify_slide_routes_catalog_paths():
    assert nbg_build._classify_slide({"type": "charts/pie_single"}) == "chart"
    assert nbg_build._classify_slide({"type": "tables/half_page"}) == "table"
    assert nbg_build._classify_slide({"type": "table"}) == "table"
    assert nbg_build._classify_slide({"type": "waterfall_chart"}) == "waterfall"


# ------------------------------------------------------- end-to-end chart data


def _expected_chart_shapes(spec_path: Path):
    """(series_count, category_count) per chart slide, in slide order."""
    import yaml

    outline = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    presentation = outline.get("presentation") or {}
    slides = presentation.get("slides") or outline.get("slides") or []
    shapes = []
    for slide in slides:
        if nbg_build._classify_slide(slide) != "chart":
            continue
        _, categories, series = nbg_build._chart_spec(slide)
        shapes.append((len(series), len(categories)))
    return shapes


def _chart_part_shapes(pptx_path: Path):
    """(part_name, series_count, category_count) per chart part, in part order."""
    import defusedxml.ElementTree as ET

    shapes = []
    with zipfile.ZipFile(pptx_path) as zf:
        # Same pattern filters and sorts, so _chart_part_index can only fail
        # if one of the two is edited without the other.
        parts = sorted((n for n in zf.namelist() if CHART_PART.match(n)), key=_chart_part_index)
        for name in parts:
            root = ET.fromstring(zf.read(name))
            series = root.findall(f".//{CHART_NS}ser")
            category_counts = {
                len(ser.findall(f".//{CHART_NS}cat//{CHART_NS}pt")) for ser in series
            }
            shapes.append((name, len(series), max(category_counts, default=0)))
    return shapes


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_shipped_example_builds_and_its_charts_carry_data(tmp_path, name):
    """Every chart part must hold real series and categories.

    Before slide.chart was wired up, all three examples produced chart parts of
    1977 bytes with zero <c:ser>, zero <c:pt> and zero <c:v>, and the validator
    still passed the deck. build_presentation now also raises when validation
    fails, so this covers the whole pipeline.
    """
    pytest.importorskip("pptx")
    spec = EXAMPLES_DIR / f"{name}.yaml"
    if not spec.exists():
        pytest.skip(f"{spec} not found")

    out = tmp_path / f"{name}.pptx"
    nbg_build.build_presentation(spec, out)
    assert out.exists()

    expected = _expected_chart_shapes(spec)
    actual = _chart_part_shapes(out)
    assert len(actual) == len(expected), f"{len(actual)} chart parts, expected {len(expected)}"

    for (part, n_series, n_categories), (want_series, want_categories) in zip(
        actual, expected, strict=True
    ):
        assert n_series > 0, f"{part} has no <c:ser>; the plot area is blank"
        assert n_categories > 0, f"{part} has no cached categories"
        assert n_series == want_series, f"{part}: {n_series} series, spec says {want_series}"
        assert n_categories == want_categories, (
            f"{part}: {n_categories} categories, spec says {want_categories}"
        )


def test_table_slide_writes_headers_and_rows(tmp_path):
    """`slide.table` used to be dropped: type: table rendered a bare title."""
    pytest.importorskip("pptx")
    from pptx import Presentation

    prs = Presentation()
    prs.slide_width, prs.slide_height = nbg_build.SLIDE_WIDTH, nbg_build.SLIDE_HEIGHT
    nbg_build.create_table_slide(
        prs,
        {"title": "Card P&L", "bumper": "CARDS"},
        {
            "headers": ["Metric", "Q4 2024", "Change"],
            "rows": [["Interchange", "42", "+14%"], ["Annual fees", "18", "+17%"]],
            "highlight_column": 2,
        },
        1,
    )
    out = tmp_path / "table.pptx"
    prs.save(str(out))

    tables = [s for s in prs.slides[0].shapes if s.has_table]
    assert len(tables) == 1
    table = tables[0].table
    assert len(table.rows) == 3
    assert len(table.columns) == 3
    assert table.cell(0, 0).text_frame.paragraphs[0].text == "Metric"
    assert table.cell(2, 1).text_frame.paragraphs[0].text == "18"


# ----------------------------------------------------------- label contrast


def _palette_hexes():
    import nbg_validate

    return sorted(nbg_validate.NBG_GUIDELINES["colors"]["allowed"])


def test_label_text_color_clears_aa_on_the_two_fills_that_used_to_fail():
    """#5D8D2F and #F60037 got a 4.12:1 and a 4.22:1 label from the old picker."""
    pytest.importorskip("pptx")
    from nbg_color import contrast_ratio

    for fill in ("5D8D2F", "F60037"):
        chosen = nbg_build._label_text_color(fill)
        ratio = contrast_ratio(fill, f"{chosen}")
        assert ratio >= 4.5, f"#{fill}: label at {ratio:.2f}:1"


def test_label_text_color_clears_aa_across_the_whole_palette():
    """Pure black as the dark candidate puts the worst case at 4.583:1."""
    pytest.importorskip("pptx")
    from nbg_color import contrast_ratio

    worst = (None, 99.0)
    for fill in _palette_hexes():
        ratio = contrast_ratio(fill, f"{nbg_build._label_text_color(fill)}")
        if ratio < worst[1]:
            worst = (fill, ratio)
        assert ratio >= 4.5, f"#{fill}: label at {ratio:.2f}:1"
    assert worst[1] >= 4.5, worst


def test_label_dark_candidate_is_pure_black():
    """Softening it to #202020 drops the worst case to 4.036:1, under AA."""
    assert nbg_build.LABEL_DARK_HEX == "000000"


# --------------------------------------------------------------- the validator


@pytest.fixture(scope="module")
def built_example(tmp_path_factory):
    pytest.importorskip("pptx")
    spec = EXAMPLES_DIR / "quarterly-report.yaml"
    if not spec.exists():
        pytest.skip("quarterly-report.yaml not found")
    out = tmp_path_factory.mktemp("validated") / "quarterly-report.pptx"
    nbg_build.build_presentation(spec, out)
    return out


def _result(results, name):
    match = [r for r in results if r.name == name]
    assert match, f"no {name!r} check in {[r.name for r in results]}"
    return match[0]


def test_font_size_check_reports_a_non_empty_sizes_used_list(built_example):
    """It walked a:rPr, which nbg_build never writes, and printed 'Sizes used: '."""
    import nbg_validate

    results = nbg_validate.validate_presentation(str(built_example))
    font_sizes = _result(results, "Font Sizes")
    assert font_sizes.examined and font_sizes.examined > 0
    sizes = font_sizes.message.split("Sizes used:", 1)[1].strip()
    assert sizes, "'Sizes used:' is still empty"
    assert "24.0pt" in sizes


def test_contrast_and_title_checks_examine_something(built_example):
    """All three rPr-only checks measured nothing on every deck this repo makes."""
    import nbg_validate

    results = nbg_validate.validate_presentation(str(built_example))
    for name in ("Contrast", "Title Length"):
        assert _result(results, name).examined, f"{name} examined nothing"


def test_every_passing_check_declares_what_it_examined(built_example):
    import nbg_validate

    results = nbg_validate.validate_presentation(str(built_example))
    missing = [r.name for r in results if r.passed and r.examined is None]
    assert not missing, f"passing checks with no candidate count: {missing}"


def test_a_check_that_examined_nothing_is_not_counted_as_a_pass():
    import nbg_validate

    empty = nbg_validate.ValidationResult("Empty", True, "nothing to look at", examined=0)
    real = nbg_validate.ValidationResult("Real", True, "looked at 3", examined=3)
    assert empty.skipped and not real.skipped
    assert nbg_validate.print_results([empty, real], "x") is True


def test_contrast_check_measures_a_real_ratio(tmp_path):
    """A deliberately unreadable slide must be caught, ratio and all."""
    pytest.importorskip("pptx")
    import nbg_validate
    from pptx import Presentation
    from pptx.dml.color import RGBColor

    prs = Presentation()
    prs.slide_width, prs.slide_height = nbg_build.SLIDE_WIDTH, nbg_build.SLIDE_HEIGHT
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = nbg_build.C_WHITE
    # Off White text on a white slide: 1.05:1, invisible. The old check had this
    # exact branch and its body was `pass`.
    nbg_build._add_textbox(
        slide, 1, 1, 6, 0.5, "invisible", font_size=14, color=RGBColor(0xF5, 0xF8, 0xF6)
    )
    out = tmp_path / "bad.pptx"
    prs.save(str(out))

    contrast = _result(nbg_validate.validate_presentation(str(out)), "Contrast")
    assert not contrast.passed
    assert any("F5F8F6" in d and "on #FFFFFF" in d for d in contrast.details), contrast.details


def test_validator_exit_codes_split_failure_from_crash(tmp_path):
    """0 clean, 1 a check failed, 2 the validator could not finish."""
    script = Path(__file__).parent / "nbg_validate.py"
    missing = subprocess.run(
        [sys.executable, str(script), str(tmp_path / "nope.pptx")],
        capture_output=True,
        text=True,
    )
    assert missing.returncode == 2, missing.stderr


# ------------------------------------------------- build/validate integration


def _minimal_spec(tmp_path):
    spec = tmp_path / "spec.yaml"
    spec.write_text(
        "template: GR\n"
        "slides:\n"
        "  - type: cover\n"
        "    content:\n"
        '      title: "T"\n'
        "  - type: content\n"
        "    content:\n"
        '      title: "A title"\n'
        "      points:\n"
        '        - "One"\n'
        "  - type: back_cover\n",
        encoding="utf-8",
    )
    return spec


def _fake_run(returncode, stderr=""):
    def run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args, returncode=returncode, stdout="", stderr=stderr
        )

    return run


def test_build_raises_when_the_validator_cannot_run(tmp_path, monkeypatch):
    """An import-time crash exits 1 with a traceback. That is not a failed check.

    The observed case was ModuleNotFoundError: No module named 'defusedxml',
    after which nbg_build printed the traceback and still exited 0.
    """
    pytest.importorskip("pptx")
    monkeypatch.setattr(
        nbg_build.subprocess,
        "run",
        _fake_run(1, "Traceback (most recent call last):\nModuleNotFoundError: defusedxml\n"),
    )
    with pytest.raises(RuntimeError, match="UNVALIDATED"):
        nbg_build.build_presentation(_minimal_spec(tmp_path), tmp_path / "o.pptx")


def test_build_raises_when_validation_finds_violations(tmp_path, monkeypatch):
    pytest.importorskip("pptx")
    monkeypatch.setattr(nbg_build.subprocess, "run", _fake_run(1))
    with pytest.raises(ValueError, match="brand violations"):
        nbg_build.build_presentation(_minimal_spec(tmp_path), tmp_path / "o.pptx")


def test_build_is_quiet_when_validation_passes(tmp_path, monkeypatch):
    pytest.importorskip("pptx")
    monkeypatch.setattr(nbg_build.subprocess, "run", _fake_run(0))
    nbg_build.build_presentation(_minimal_spec(tmp_path), tmp_path / "o.pptx")
    assert (tmp_path / "o.pptx").exists()


# ------------------------------------------------------------------- the CLI


def test_cli_accepts_dash_o_instead_of_writing_a_file_named_dash_o(tmp_path):
    """`nbg_build.py spec.yaml -o out.pptx` used to create a file called '-o'."""
    pytest.importorskip("pptx")
    script = Path(__file__).parent / "nbg_build.py"
    out = tmp_path / "cli.pptx"
    proc = subprocess.run(
        [sys.executable, str(script), str(_minimal_spec(tmp_path)), "-o", str(out)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out.exists()
    assert not (tmp_path / "-o").exists()


def test_cli_still_accepts_the_documented_two_positionals(tmp_path):
    pytest.importorskip("pptx")
    script = Path(__file__).parent / "nbg_build.py"
    out = tmp_path / "positional.pptx"
    proc = subprocess.run(
        [sys.executable, str(script), str(_minimal_spec(tmp_path)), str(out)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert out.exists()


def test_cli_rejects_two_conflicting_output_paths(tmp_path):
    script = Path(__file__).parent / "nbg_build.py"
    proc = subprocess.run(
        [sys.executable, str(script), "s.yaml", "a.pptx", "-o", "b.pptx"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert proc.returncode != 0
    assert "two output paths" in proc.stderr


# --------------------------------------------------- injector namespace safety

REAL_SLIDE_ROOT = (
    '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" '
    'xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main" '
    'mc:Ignorable="p14 a14">'
)


def _pptx_with_a_powerpoint_flavoured_slide(tmp_path):
    """A one-table deck whose slide declares the namespaces a real deck carries."""
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_table(2, 2, Inches(1), Inches(1), Inches(4), Inches(1))
    plain = tmp_path / "plain.pptx"
    prs.save(str(plain))

    with zipfile.ZipFile(plain) as zf:
        names = zf.namelist()
        blobs = {n: zf.read(n) for n in names}

    xml = blobs["ppt/slides/slide1.xml"].decode("utf-8")
    start = xml.index("<p:sld ")
    xml = xml[:start] + REAL_SLIDE_ROOT + xml[xml.index(">", start) + 1 :]
    if not xml.startswith("<?xml"):
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml
    blobs["ppt/slides/slide1.xml"] = xml.encode("utf-8")

    real = tmp_path / "real.pptx"
    with zipfile.ZipFile(real, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in names:
            zf.writestr(n, blobs[n])
    return real


def test_table_injection_preserves_foreign_namespace_prefixes(tmp_path):
    """ElementTree renamed mc to ns1 and dropped p14, leaving mc:Ignorable dangling."""
    pytest.importorskip("pptx")
    pytest.importorskip("defusedxml")
    import inject_table_data

    source = _pptx_with_a_powerpoint_flavoured_slide(tmp_path)
    config = tmp_path / "cfg.json"
    config.write_text(
        json.dumps(
            {
                "tables": [
                    {
                        "slide": 0,
                        "table_index": 0,
                        "data": {"headers": ["Metric", "NBG"], "rows": [["Assets", "78.5"]]},
                        "highlight_column": 1,
                    }
                ]
            }
        )
    )
    out = tmp_path / "out.pptx"
    inject_table_data.inject_table_data(str(source), str(config), str(out))

    with zipfile.ZipFile(out) as zf:
        after = zf.read("ppt/slides/slide1.xml").decode("utf-8")

    for prefix in ("a", "r", "p", "mc", "p14", "a14"):
        assert f'xmlns:{prefix}="' in after, f"xmlns:{prefix} was dropped"
    assert 'mc:Ignorable="p14 a14"' in after
    assert not re.search(r"\bns\d+:", after), "a namespace prefix was renamed"
    # The declaration is preserved verbatim and python-pptx writes it with
    # single quotes, so accept either quoting.
    assert re.search(r"standalone=['\"]yes['\"]", after), after[:90]
    assert ">Assets<" in after and ">78.5<" in after


def test_declared_namespaces_reads_every_prefix():
    pytest.importorskip("defusedxml")
    from ooxml_ns import declared_namespaces

    found = dict(declared_namespaces(REAL_SLIDE_ROOT.encode("utf-8")))
    assert set(found) == {"a", "r", "p", "mc", "p14", "a14"}


# ------------------------------------------ 2026 executive-presentation checks
#
# Every check below is break-tested: the fixture is deliberately violated, the
# check is watched failing, and a passing variant proves the failure came from
# the violation rather than from the check being broken. _patched_pptx refuses
# an edit that changes nothing, so a break-test cannot silently prove nothing.


def _deck(tmp_path, name, build):
    """A minimal NBG-dimensioned deck, built by `build(prs)`."""
    pytest.importorskip("pptx")
    from pptx import Presentation

    prs = Presentation()
    prs.slide_width, prs.slide_height = nbg_build.SLIDE_WIDTH, nbg_build.SLIDE_HEIGHT
    build(prs)
    out = tmp_path / name
    prs.save(str(out))
    return out


def _patched_pptx(source, dest, part, replace):
    """Copy a pptx, rewriting one XML part through `replace`.

    Asserts the rewrite actually changed the part. A break-test whose edit
    silently missed is the same defect as a check that examined nothing: it
    reports green having done no work.
    """
    with zipfile.ZipFile(source) as zf:
        names = zf.namelist()
        blobs = {n: zf.read(n) for n in names}

    before = blobs[part].decode("utf-8")
    after = replace(before)
    assert after != before, f"{part}: the break-test edit changed nothing"
    blobs[part] = after.encode("utf-8")

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in names:
            zf.writestr(n, blobs[n])
    return dest


def _check(pptx_path, name):
    import nbg_validate

    return _result(nbg_validate.validate_presentation(str(pptx_path)), name)


# ------------------------------------------------------------- slide titles


def test_slide_titles_pass_on_a_shipped_deck(built_example):
    titles = _check(built_example, "Slide Titles")
    assert titles.passed, titles.details
    assert titles.examined == 10, titles.message  # 11 slides, back cover is text-free


def test_slide_titles_catch_a_duplicate(tmp_path):
    """Two slides with one title cannot be told apart in minutes or in the room."""

    def build(prs):
        for page in (1, 2):
            nbg_build.create_content_slide(
                prs, {"title": "Cards performance held up", "points": ["a"]}, page
            )

    titles = _check(_deck(tmp_path, "dup.pptx", build), "Slide Titles")
    assert not titles.passed
    assert any("duplicates slide 1" in d for d in titles.details), titles.details


def test_slide_titles_catch_a_missing_title(tmp_path):
    """A body slide with bullets and no title fails; a text-free back cover does not."""

    def build(prs):
        nbg_build.create_content_slide(prs, {"points": ["a bullet, but no title"]}, 1)
        nbg_build.create_back_cover_slide(prs)

    titles = _check(_deck(tmp_path, "untitled.pptx", build), "Slide Titles")
    assert not titles.passed
    assert any("no title" in d for d in titles.details), titles.details
    assert "1 text-free slide(s) exempt" in titles.message


# ---------------------------------------------------------- exhibit sources


def test_exhibit_sources_fire_on_the_shipped_deck_and_do_not_block(built_example):
    """All three shipped examples carry unsourced exhibits. It reports, not blocks."""
    import nbg_validate

    results = nbg_validate.validate_presentation(str(built_example))
    sources = _result(results, "Exhibit Sources")
    assert not sources.passed
    assert sources.warned and sources.severity == "warning"
    assert any("no source line" in d for d in sources.details), sources.details
    # A warning is not a failure: the build still passes.
    assert nbg_validate.print_results(results, str(built_example)) is True


def test_exhibit_sources_pass_with_a_dated_source_line(tmp_path):
    def build(prs):
        slide = nbg_build.create_chart_slide(
            prs,
            {"title": "Volume grew"},
            1,
            chart_type="bar",
            categories=["Q1"],
            series_list=[{"name": "2025", "values": [3]}],
        )
        nbg_build._add_textbox(
            slide, 0.374, 6.5, 8, 0.25, "Source: NBG MIS, December 2025", font_size=11
        )

    sources = _check(_deck(tmp_path, "sourced.pptx", build), "Exhibit Sources")
    assert sources.passed, sources.details
    assert sources.examined == 1


def test_exhibit_sources_reject_a_source_with_no_as_of_date(tmp_path):
    """ "Source: NBG MIS" does not say whether the number is current."""

    def build(prs):
        slide = nbg_build.create_chart_slide(
            prs,
            {"title": "Volume grew"},
            1,
            chart_type="bar",
            categories=["Q1"],
            series_list=[{"name": "s", "values": [3]}],
        )
        nbg_build._add_textbox(slide, 0.374, 6.5, 8, 0.25, "Source: NBG MIS", font_size=11)

    sources = _check(_deck(tmp_path, "undated.pptx", build), "Exhibit Sources")
    assert not sources.passed
    assert any("no as-of date" in d for d in sources.details), sources.details


# ----------------------------------------------------------------- alt text


def test_alt_text_passes_once_the_builder_describes_its_charts(built_example):
    alt = _check(built_example, "Alt Text")
    assert alt.passed, alt.details
    assert alt.examined == 3, alt.message  # 2 charts + 1 table
    assert "11 brand logo(s) exempt as decorative" in alt.message


def test_alt_text_catches_a_stripped_descr(tmp_path, built_example):
    out = _patched_pptx(
        built_example,
        tmp_path / "noalt.pptx",
        "ppt/slides/slide4.xml",
        lambda x: re.sub(r'(name="Chart 3") descr="[^"]*"', r"\1", x),
    )
    alt = _check(out, "Alt Text")
    assert not alt.passed
    assert any("has no alt text" in d for d in alt.details), alt.details


def test_alt_text_rejects_a_filename_which_is_what_python_pptx_writes(tmp_path, built_example):
    """descr="nbg-logo-gr.png" passes an emptiness test and describes nothing."""
    out = _patched_pptx(
        built_example,
        tmp_path / "filename.pptx",
        "ppt/slides/slide4.xml",
        lambda x: re.sub(r'(name="Chart 3") descr="[^"]*"', r'\1 descr="chart-4.png"', x),
    )
    alt = _check(out, "Alt Text")
    assert not alt.passed
    assert any("is a filename or an autoname" in d for d in alt.details), alt.details


def test_alt_text_rejects_a_lead_in_and_a_duplicated_caption(tmp_path, built_example):
    lead_in = _patched_pptx(
        built_example,
        tmp_path / "leadin.pptx",
        "ppt/slides/slide4.xml",
        lambda x: re.sub(
            r'(name="Chart 3") descr="[^"]*"', r'\1 descr="Image of monthly volume"', x
        ),
    )
    alt = _check(lead_in, "Alt Text")
    assert not alt.passed
    assert any('opens with "image of"' in d for d in alt.details), alt.details

    caption = "Monthly transaction volume shows consistent growth trajectory"
    duplicate = _patched_pptx(
        built_example,
        tmp_path / "dupcaption.pptx",
        "ppt/slides/slide4.xml",
        lambda x: re.sub(r'(name="Chart 3") descr="[^"]*"', rf'\1 descr="{caption}"', x),
    )
    alt = _check(duplicate, "Alt Text")
    assert not alt.passed
    assert any("repeats a caption" in d for d in alt.details), alt.details


# ------------------------------------------------------------ zero baseline


def _bar_chart_part(pptx_path):
    """The chart part holding the bar chart, so the test never hardcodes an index."""
    with zipfile.ZipFile(pptx_path) as zf:
        for name in sorted(n for n in zf.namelist() if CHART_PART.match(n)):
            if b"barChart" in zf.read(name):
                return name
    raise AssertionError("no bar chart part found")


def test_zero_baseline_passes_when_the_axis_is_automatic(built_example):
    """nbg_build writes no c:min, so the axis auto-scales from zero."""
    baseline = _check(built_example, "Zero Baseline")
    assert baseline.passed, baseline.details
    assert baseline.examined == 1, baseline.message


def _truncate_value_axis(chart_xml, minimum="30"):
    """Put an explicit c:min on the VALUE axis of a chart part.

    It has to target `c:valAx` by hand, and the shape of the edit is not
    obvious: the value axis nbg_build writes carries a SELF-CLOSED
    `<c:scaling/>`, while the CATEGORY axis carries a populated
    `<c:scaling><c:orientation val="minMax"/></c:scaling>`. The first version of
    this break-test replaced the first populated scaling block in the part,
    which is the category axis, where a minimum means nothing. The check
    correctly stayed green and this test failed.

    That is the argument for break-testing in one place: the edit was broken,
    not the check, and only watching the check fail could say which.
    """
    head, sep, tail = chart_xml.partition("<c:valAx>")
    assert sep, "chart part has no value axis"
    if "<c:scaling/>" in tail:
        tail = tail.replace("<c:scaling/>", f'<c:scaling><c:min val="{minimum}"/></c:scaling>', 1)
    else:
        tail = tail.replace("<c:scaling>", f'<c:scaling><c:min val="{minimum}"/>', 1)
    return head + sep + tail


def test_zero_baseline_catches_a_truncated_bar_axis(tmp_path, built_example):
    out = _patched_pptx(
        built_example,
        tmp_path / "truncated.pptx",
        _bar_chart_part(built_example),
        _truncate_value_axis,
    )
    baseline = _check(out, "Zero Baseline")
    assert not baseline.passed
    assert any("starts at 30, not zero" in d for d in baseline.details), baseline.details


def test_zero_baseline_leaves_a_truncated_line_chart_alone(tmp_path, built_example):
    """A line chart encodes value as position, so a non-zero start is legitimate."""
    with zipfile.ZipFile(built_example) as zf:
        line_part = next(
            n
            for n in sorted(x for x in zf.namelist() if CHART_PART.match(x))
            if b"lineChart" in zf.read(n)
        )
    out = _patched_pptx(built_example, tmp_path / "line.pptx", line_part, _truncate_value_axis)
    baseline = _check(out, "Zero Baseline")
    assert baseline.passed, baseline.details


def test_zero_baseline_is_read_by_parsing_not_by_searching_the_text(built_example):
    """The substring "c:min" is in c:minorTickMark on every chart this builder writes."""
    with zipfile.ZipFile(built_example) as zf:
        parts = [n for n in zf.namelist() if CHART_PART.match(n)]
        assert parts
        assert all(b"c:min" in zf.read(n) for n in parts), "the trap this check avoids is gone"
    assert _check(built_example, "Zero Baseline").passed


# ----------------------------------------------------------- number formats


def test_number_formats_read_table_cells_not_only_shapes(built_example):
    """A walk over p:sp alone saw 3 of the deck's 11 amounts: the table was invisible."""
    numbers = _check(built_example, "Number Formats")
    assert numbers.passed, numbers.details
    assert numbers.examined == 11, numbers.message


def test_number_formats_catch_raw_digits_beside_abbreviations(tmp_path):
    def build(prs):
        nbg_build.create_content_slide(
            prs,
            {"title": "Fee income by line", "points": ["EUR 1,250,000 interchange", "EUR 2.3M FX"]},
            1,
        )

    numbers = _check(_deck(tmp_path, "mixed.pptx", build), "Number Formats")
    assert not numbers.passed
    assert numbers.warned
    assert any("raw and abbreviated" in d for d in numbers.details), numbers.details


def test_number_formats_catch_inconsistent_decimals_within_one_unit(tmp_path):
    def build(prs):
        nbg_build.create_content_slide(
            prs, {"title": "Fee income by line", "points": ["EUR 2.3M", "EUR 4M", "EUR 11M"]}, 1
        )

    numbers = _check(_deck(tmp_path, "decimals.pptx", build), "Number Formats")
    assert not numbers.passed
    assert any("decimal precisions" in d for d in numbers.details), numbers.details


def test_number_formats_do_not_flag_mixed_magnitudes_or_non_currency(tmp_path):
    """EUR 12.5B beside EUR 42M is correct; 2026, page 3 and 18% are not currency."""

    def build(prs):
        nbg_build.create_content_slide(
            prs,
            {
                "title": "Volume and fees",
                "points": ["EUR 12.5B volume in 2026", "EUR 42M fees, up 18%", "850K downloads"],
            },
            1,
        )

    numbers = _check(_deck(tmp_path, "magnitudes.pptx", build), "Number Formats")
    assert numbers.passed, numbers.details
    assert numbers.examined == 2, numbers.message


# ------------------------------------------------------------------ ai slop


def test_ai_slop_passes_on_the_shipped_decks(built_example):
    slop = _check(built_example, "AI Slop")
    assert slop.passed, slop.details
    assert slop.examined == 10, slop.message


def test_ai_slop_fires_on_a_cluster(tmp_path):
    def build(prs):
        nbg_build.create_content_slide(
            prs,
            {
                "title": "Our approach to payments",
                "points": ["We leverage a seamless platform", "Studies show it works"],
            },
            1,
        )

    slop = _check(_deck(tmp_path, "slop.pptx", build), "AI Slop")
    assert not slop.passed
    assert any("'leverage'" in d and "'seamless'" in d for d in slop.details), slop.details


def test_ai_slop_ignores_a_lone_hit(tmp_path):
    """A single "robust" in a technical sentence is fine; flagging it trains people
    to ignore the check."""

    def build(prs):
        nbg_build.create_content_slide(
            prs, {"title": "Risk framework", "points": ["The model is robust to rate shocks"]}, 1
        )

    slop = _check(_deck(tmp_path, "lone.pptx", build), "AI Slop")
    assert slop.passed, slop.details
    assert slop.examined == 1


def test_ai_slop_matches_through_a_curly_apostrophe(tmp_path):
    def build(prs):
        nbg_build.create_content_slide(
            prs,
            {
                "title": "Market context",
                "points": ["In today’s fast-paced world", "we must unlock value"],
            },
            1,
        )

    slop = _check(_deck(tmp_path, "curly.pptx", build), "AI Slop")
    assert not slop.passed, slop.message


# ------------------------------------------------------------ action titles


def test_action_titles_pass_on_the_shipped_decks(built_example):
    titles = _check(built_example, "Action Titles")
    assert titles.passed, titles.details
    assert titles.examined == 6, titles.message


def test_action_titles_flag_a_topic_label(tmp_path):
    def build(prs):
        nbg_build.create_content_slide(prs, {"title": "Overview", "points": ["a"]}, 1)
        nbg_build.create_content_slide(prs, {"title": "Q3 Results", "points": ["b"]}, 2)

    titles = _check(_deck(tmp_path, "labels.pptx", build), "Action Titles")
    assert not titles.passed
    assert titles.warned
    assert len(titles.details) == 2, titles.details
    assert all("is a topic label" in d for d in titles.details), titles.details


def test_action_titles_flag_an_overlong_title(tmp_path):
    long_title = " ".join(["word"] * 16)

    def build(prs):
        nbg_build.create_content_slide(prs, {"title": long_title, "points": ["a"]}, 1)

    titles = _check(_deck(tmp_path, "long.pptx", build), "Action Titles")
    assert not titles.passed
    assert any("runs 16 words" in d for d in titles.details), titles.details


def test_action_titles_leave_divider_and_cover_titles_alone(tmp_path):
    """A divider title is a noun phrase by Standard #3, so it is not a content title."""

    def build(prs):
        nbg_build.create_cover_slide(prs, {"title": "Overview"})
        nbg_build.create_divider_slide(prs, {"number": "01", "title": "Recommendations"})

    titles = _check(_deck(tmp_path, "chrome.pptx", build), "Action Titles")
    assert titles.passed, titles.details
    assert titles.examined == 0 and titles.skipped, titles.message


# ------------------------------------------------------- the severity tier


def test_a_warning_reports_without_blocking_and_is_never_counted_as_a_pass():
    import nbg_validate

    warning = nbg_validate.ValidationResult(
        "W", False, "found something", ["a finding"], severity="warning"
    )
    error = nbg_validate.ValidationResult("E", False, "broke")
    assert warning.warned and not warning.passed
    assert not error.warned
    assert nbg_validate.print_results([warning], "x") is True
    assert nbg_validate.print_results([error], "x") is False


def test_every_new_check_declares_what_it_examined_when_it_passes(built_example):
    """The whole point of the rebuild: a pass with nothing measured is not a pass."""
    import nbg_validate

    new_checks = {
        "Slide Titles",
        "Exhibit Sources",
        "Alt Text",
        "Zero Baseline",
        "Number Formats",
        "AI Slop",
        "Action Titles",
    }
    results = nbg_validate.validate_presentation(str(built_example))
    names = {r.name for r in results}
    assert new_checks <= names, new_checks - names
    for result in results:
        if result.name in new_checks and result.passed:
            assert result.examined is not None, f"{result.name} passed without a count"


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_a_zero_candidate_pass_is_reported_as_unverified(tmp_path_factory, name):
    """strategy-deck has no charts, so Zero Baseline must show a circle, not a tick."""
    pytest.importorskip("pptx")
    import nbg_validate

    spec = EXAMPLES_DIR / f"{name}.yaml"
    if not spec.exists():
        pytest.skip(f"{spec} not found")
    out = tmp_path_factory.mktemp(f"zero-{name}") / f"{name}.pptx"
    nbg_build.build_presentation(spec, out)

    results = nbg_validate.validate_presentation(str(out))
    for result in results:
        if result.passed and result.examined == 0:
            assert result.skipped, f"{result.name} measured nothing and still read as a pass"
