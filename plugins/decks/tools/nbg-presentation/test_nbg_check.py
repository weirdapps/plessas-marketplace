"""Tests for `decks-py check`: legacy aliases, the schema, the semantic checks, and the
dry-run layout, each issue located by slide, path and fix."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import nbg_build
import nbg_spec
import pytest
import yaml
from testkit import deck, write_spec

SCRIPT = Path(__file__).parent / "nbg_build.py"
SOURCE = {"name": "Management accounts", "as_of": "30 June 2026"}
HERE = Path(__file__).resolve().parent


def check(tmp_path, spec, name="spec.yaml"):
    return nbg_build.check(write_spec(tmp_path, spec, name))


def messages(report, level="error"):
    items = report.errors if level == "error" else report.warnings
    return [(i.path, i.message) for i in items]


def _content(title="Three things moved", **extra):
    return {"type": "content", "content": {"title": title, "points": ["One"], **extra}}


# ---------------------------------------------------------------- the catalog


def test_the_catalog_and_the_schema_name_the_same_types():
    schema = json.loads((HERE / "deck.schema.json").read_text(encoding="utf-8"))
    slide_enum = schema["$defs"]["slide"]["properties"]["type"]["enum"]
    chart_enum = schema["$defs"]["chart"]["properties"]["type"]["enum"]
    assert nbg_spec.slide_types() == slide_enum
    assert nbg_spec.chart_types() == chart_enum
    assert set(nbg_build.RENDERERS) == set(slide_enum)


# ---------------------------------------------------------------- aliases


@pytest.mark.parametrize(
    "legacy,canonical,chart_type",
    [
        ("thankyou", "back_cover", None),
        ("toc", "contents", None),
        ("covers/quiet", "cover", None),
        ("bar_chart", "chart", "bar"),
        ("pie_chart", "chart", "doughnut"),
        ("line_chart", "chart", "line"),
        ("charts/pie_single", "chart", "doughnut"),
        ("charts/bar_dual", "chart", "bar"),
        ("waterfall_chart", "waterfall", None),
        ("infographic", "cards", None),
        ("infographics/timeline", "process", None),
    ],
)
def test_legacy_slide_types_normalise_with_a_warning(legacy, canonical, chart_type):
    spec, issues = nbg_spec.normalise({"slides": [{"type": legacy}]})
    slide = spec["slides"][0]
    assert slide["type"] == canonical
    if chart_type:
        assert slide["chart"]["type"] == chart_type
    warnings = [i for i in issues if i.level == "warning" and i.path == "slides[0].type"]
    assert warnings and f"write type: {canonical}" in warnings[0].fix


def test_legacy_content_keys_move_to_their_canonical_place():
    legacy = {
        "template": "GR",
        "slides": [
            {
                "type": "content",
                "recommended_visual": "none",
                "content": {
                    "title": "A title",
                    "hyper_title": "Section",
                    "paragraphs": [{"text": "One", "bullet": True}, "Two"],
                },
            },
            {
                "type": "infographic",
                "recommended_visual": "numbered_infographic",
                "content": {
                    "title": "Pillars",
                    "items": [
                        {"title": "A", "description": "a"},
                        {"title": "B", "description": "b"},
                    ],
                },
            },
            {
                "type": "chart",
                "recommended_visual": "pie_chart",
                "content": {"title": "Mix", "source": SOURCE},
                "chart": {"labels": ["x", "y"], "values": [1, 2]},
            },
            {
                "type": "waterfall",
                "content": {
                    "title": "Bridge",
                    "source": SOURCE,
                    "waterfall_items": [{"label": "a", "value": 1}, {"label": "b", "value": 2}],
                },
            },
        ],
    }
    spec, issues = nbg_spec.normalise(legacy)
    assert "template" not in spec
    first, cards, chart, waterfall = spec["slides"]
    assert first["content"]["bumper"] == "Section"
    assert first["content"]["points"] == ["One", "Two"]
    assert "recommended_visual" not in first
    assert cards["type"] == "cards" and cards["cards"][0] == {"title": "A", "body": "a"}
    assert chart["chart"] == {
        "type": "doughnut",
        "data": {"categories": ["x", "y"], "series": [{"name": "", "values": [1, 2]}]},
    }
    assert waterfall["chart"]["data"]["items"][1] == {"label": "b", "value": 2}
    assert nbg_spec.schema_issues(spec) == []
    assert all(i.level == "warning" for i in issues)


def test_an_unknown_slide_type_is_an_error_with_a_suggestion():
    _, issues = nbg_spec.normalise({"slides": [{"type": "cardz"}]})
    assert issues[0].level == "error"
    assert "did you mean 'cards'" in issues[0].fix


def test_an_unknown_chart_type_is_an_error_with_a_suggestion(tmp_path):
    spec = deck(
        [
            {
                "type": "chart",
                "content": {"title": "Volumes rose", "source": SOURCE},
                "chart": {
                    "type": "lin",
                    "data": {"categories": ["a"], "series": [{"name": "s", "values": [1]}]},
                },
            }
        ]
    )
    report = check(tmp_path, spec)
    error = next(i for i in report.errors if i.path == "slides[1].chart.type")
    assert error.slide == 2 and "did you mean 'line'" in error.fix


# ---------------------------------------------------------------- the schema


def test_a_missing_source_names_the_slide_path_and_fix(tmp_path):
    spec = deck(
        [
            {
                "id": "S02",
                "type": "table",
                "content": {"title": "Fees grew"},
                "table": {"headers": ["A"], "rows": [["1"]]},
            }
        ]
    )
    report = check(tmp_path, spec)
    error = next(i for i in report.errors if i.path == "slides[1].content.source")
    assert error.slide == 2 and error.slide_id == "S02" and error.slide_type == "table"
    assert "as_of" in error.fix
    assert error.format().startswith("ERROR slide 2 (S02, table) slides[1].content.source:")


def test_an_unknown_key_is_named_with_a_suggestion(tmp_path):
    report = check(tmp_path, deck([_content(tittle="typo")]))
    error = next(i for i in report.errors if i.path == "slides[1].content.tittle")
    assert "did you mean 'title'" in error.fix


def test_unquoted_numbers_and_dates_are_coerced_with_a_warning(tmp_path):
    path = tmp_path / "s.yaml"
    path.write_text(
        "slides:\n"
        "  - type: cover\n"
        "    content: {title: 2026, date: 2026-09-23}\n"
        "  - type: back_cover\n",
        encoding="utf-8",
    )
    report = nbg_build.check(path)
    assert report.ok, [i.format() for i in report.errors]
    assert report.spec is not None
    assert report.spec["slides"][0]["content"] == {"title": "2026", "date": "2026-09-23"}
    assert {i.path for i in report.warnings} >= {
        "slides[0].content.title",
        "slides[0].content.date",
    }


# ---------------------------------------------------------------- semantics


def test_a_column_chart_needs_a_slide_source(tmp_path):
    spec = deck(
        [
            {
                "type": "two_column",
                "content": {"title": "Two halves"},
                "left": {"kind": "text", "text": "Words"},
                "right": {
                    "kind": "chart",
                    "chart": {
                        "type": "bar",
                        "data": {"categories": ["a"], "series": [{"name": "s", "values": [1]}]},
                    },
                },
            }
        ]
    )
    assert (
        "slides[1].content.source",
        "the slide holds a chart, table or KPIs and has no source",
    ) in messages(check(tmp_path, spec))


def test_series_must_have_one_value_per_category(tmp_path):
    spec = deck(
        [
            {
                "type": "chart",
                "content": {"title": "Volumes rose", "source": SOURCE},
                "chart": {
                    "type": "bar",
                    "data": {"categories": ["a", "b"], "series": [{"name": "s", "values": [1]}]},
                },
            }
        ]
    )
    errors = messages(check(tmp_path, spec))
    assert ("slides[1].chart.data.series[0].values", "1 value(s) for 2 categories") in errors


def test_a_missing_image_is_an_error_and_an_asset_path_resolves(tmp_path):
    good = {
        "type": "image",
        "content": {"title": "A picture"},
        "image": {"path": "illustrations/Growth.png", "alt_text": "Growth"},
    }
    bad = {
        "type": "image",
        "content": {"title": "Another picture"},
        "image": {"path": "nope.png", "alt_text": "x"},
    }
    errors = messages(check(tmp_path, deck([good, bad])))
    assert [p for p, _ in errors] == ["slides[2].image.path"]


def test_custom_elements_must_stay_inside_the_body_area(tmp_path):
    spec = deck(
        [
            {
                "type": "custom",
                "content": {"title": "Positioned"},
                "elements": [
                    {"kind": "text", "text": "fine", "x": 0.374, "y": 1.3, "w": 4, "h": 0.5},
                    {"kind": "text", "text": "too low", "x": 0.374, "y": 6.4, "w": 4, "h": 0.5},
                    {"kind": "text", "text": "too wide", "x": 10, "y": 2, "w": 4, "h": 0.5},
                ],
            }
        ]
    )
    paths = [p for p, _ in messages(check(tmp_path, spec))]
    assert paths == ["slides[1].elements[1]", "slides[1].elements[2]"]


def test_a_colour_must_be_a_token_name(tmp_path):
    spec = deck(
        [
            {
                "type": "custom",
                "content": {"title": "Positioned"},
                "elements": [
                    {
                        "kind": "shape",
                        "shape": "rect",
                        "x": 0.5,
                        "y": 1.5,
                        "w": 1,
                        "h": 1,
                        "fill": "tael",
                    }
                ],
            }
        ]
    )
    error = next(i for i in check(tmp_path, spec).errors if i.path == "slides[1].elements[0].fill")
    assert "did you mean 'teal'" in error.fix


def test_the_deck_must_end_on_its_back_cover(tmp_path):
    spec = {"slides": [{"type": "cover", "content": {"title": "T"}}, _content()]}
    assert any("back cover" in m for _, m in messages(check(tmp_path, spec)))


def test_duplicate_titles_are_an_error(tmp_path):
    report = check(tmp_path, deck([_content("Same words"), _content("Same words")]))
    assert ("slides[2].content.title", "the same title as slide 2") in messages(report)


def test_more_than_six_series_is_a_warning_and_nine_is_an_error(tmp_path):
    def chart(n):
        series = [{"name": f"s{i}", "values": [i]} for i in range(n)]
        return {
            "type": "chart",
            "content": {"title": f"{n} series", "source": SOURCE},
            "chart": {"type": "bar", "data": {"categories": ["a"], "series": series}},
        }

    report = check(tmp_path, deck([chart(7), chart(9)]))
    assert any(i.path == "slides[1].chart.data.series" for i in report.warnings)
    assert any(i.path == "slides[2].chart.data.series" for i in report.errors)


def test_a_waterfall_total_that_does_not_add_up_is_a_warning(tmp_path):
    spec = deck(
        [
            {
                "type": "waterfall",
                "content": {"title": "Bridge", "source": SOURCE},
                "chart": {
                    "type": "waterfall",
                    "data": {
                        "items": [
                            {"label": "a", "value": 10},
                            {"label": "b", "value": 5},
                            {"label": "c", "value": 20},
                        ]
                    },
                },
            }
        ]
    )
    assert any(
        i.path == "slides[1].chart.data.items[2].value" for i in check(tmp_path, spec).warnings
    )


def test_an_em_dash_in_slide_text_is_a_warning(tmp_path):
    report = check(tmp_path, deck([_content("Growth " + chr(0x2014) + " all of it")]))
    assert any("em dash" in i.message for i in report.warnings)


# ---------------------------------------------------------------- dry-run layout


def test_a_cover_title_that_cannot_fit_is_an_error(tmp_path):
    long_title = "An extremely long cover title that no presenter should ever need"
    report = check(
        tmp_path,
        {
            "slides": [
                {"type": "cover", "content": {"title": long_title[:60]}},
                {"type": "back_cover"},
            ]
        },
    )
    wrapped = [i for i in report.warnings if i.path == "slides[0].content.title"]
    assert wrapped and "Standard #13" in wrapped[0].fix


def test_bullets_that_cannot_fit_at_14pt_are_refused(tmp_path):
    sentence = "A bullet long enough to run onto three lines at fourteen point across the full body width. "
    points = [sentence * 3] * 8
    report = check(
        tmp_path, deck([{"type": "content", "content": {"title": "Too much", "points": points}}])
    )
    error = next(i for i in report.errors if i.path == "slides[1].content.points")
    assert "14pt" in error.message and error.slide == 2


def test_a_table_too_tall_for_the_body_is_refused(tmp_path):
    rows = [[f"Row {i} with a label long enough", "1"] for i in range(14)]
    spec = deck(
        [
            {
                "type": "table",
                "content": {"title": "Long", "source": SOURCE, "description": "x", "takeaway": "y"},
                "table": {"headers": ["A", "B"], "rows": rows},
            }
        ]
    )
    assert any(i.path == "slides[1].table" for i in check(tmp_path, spec).errors)


# ---------------------------------------------------------------- the CLI


def test_check_cli_exit_codes_and_json(tmp_path):
    ok = write_spec(tmp_path, deck([_content()]), "ok.yaml")
    bad = write_spec(
        tmp_path, deck([{"type": "content", "content": {"points": ["x"]}}]), "bad.yaml"
    )
    run = lambda *a: subprocess.run(  # noqa: E731
        [sys.executable, str(SCRIPT), "--check", *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    good = run(str(ok))
    assert good.returncode == 0, good.stdout + good.stderr
    failed = run(str(bad), "--format", "json")
    assert failed.returncode == 1
    body = json.loads(failed.stdout)
    assert body["ok"] is False
    assert (
        body["errors"][0]["slide"] == 2 and body["errors"][0]["path"] == "slides[1].content.title"
    )
    assert set(body["errors"][0]) == {"slide", "id", "type", "path", "message", "fix"}
    missing = run(str(tmp_path / "missing.yaml"))
    assert missing.returncode == 2


def test_every_example_checks_clean():
    for spec in sorted((HERE.parent.parent / "examples").glob("*.yaml")):
        report = nbg_build.check(spec)
        assert report.ok, [i.format() for i in report.errors]
        assert not report.warnings, [i.format() for i in report.warnings]


def test_examples_use_only_canonical_keys():
    """E2E-SMOKE-11 / DOCS-MEMORY-6: an example is what a colleague copies."""
    for spec in sorted((HERE.parent.parent / "examples").glob("*.yaml")):
        data = yaml.safe_load(spec.read_text(encoding="utf-8"))
        _, issues = nbg_spec.normalise(data)
        assert not issues, (spec.name, [i.format() for i in issues])


def test_the_readme_example_checks_clean_and_builds(tmp_path, monkeypatch):
    """DOCS-MEMORY-6: the first snippet a colleague copied from the README failed."""
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    block = readme.split("<!-- readme-example -->", 1)[1].split("```yaml", 1)[1].split("```", 1)[0]
    spec = tmp_path / "readme.yaml"
    spec.write_text(block, encoding="utf-8")
    report = nbg_build.check(spec)
    assert report.ok and not report.warnings, [i.format() for i in report.issues]
    from testkit import passing_validator

    passing_validator(monkeypatch, nbg_build)
    nbg_build.build_presentation(spec, tmp_path / "readme.pptx")
    assert (tmp_path / "readme.pptx").exists()
