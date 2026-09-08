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
