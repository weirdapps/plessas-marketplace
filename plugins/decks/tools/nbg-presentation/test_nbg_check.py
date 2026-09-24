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


def test_every_role_the_schema_allows_resolves_in_the_tokens():
    """PROMPTS-CONTRACTS-01 / DOCS-ACCURACY-2: role 'subtitle' was schema-valid with no
    type.subtitle token, so check and build crashed on it with a traceback."""
    import nbg_tokens

    schema = json.loads((HERE / "deck.schema.json").read_text(encoding="utf-8"))
    for role in schema["$defs"]["element"]["properties"]["role"]["enum"]:
        style = nbg_tokens.type_style(role)
        assert style["size"] >= 10, role


def test_a_custom_subtitle_element_checks_and_builds(tmp_path, monkeypatch):
    from testkit import passing_validator

    spec = deck(
        [
            {
                "type": "custom",
                "content": {"title": "Key figures for the unit"},
                "elements": [
                    {
                        "kind": "text",
                        "role": "subtitle",
                        "text": "Head of unit",
                        "x": 0.374,
                        "y": 1.4,
                        "w": 4.0,
                        "h": 0.4,
                    }
                ],
            }
        ]
    )
    assert check(tmp_path, spec).ok
    passing_validator(monkeypatch, nbg_build)
    nbg_build.build_presentation(write_spec(tmp_path, spec, "sub.yaml"), tmp_path / "sub.pptx")


def test_a_crash_on_one_slide_exits_2_naming_that_slide(tmp_path, monkeypatch, capsys):
    """Any exception a slide raises is a builder defect: exit 2 ("could not run") with
    the slide named, never a bare traceback that exits 1 as if the spec were wrong."""
    path = write_spec(tmp_path, deck([_content()]), "crash.yaml")

    def boom(_deck, _spec):
        raise KeyError("no such token")

    monkeypatch.setitem(nbg_build.RENDERERS, "content", boom)
    for argv in ([str(path), "--check"], [str(path), str(tmp_path / "crash.pptx")]):
        with pytest.raises(SystemExit) as exc:
            nbg_build.main(argv)
        assert exc.value.code == 2, argv
        err = capsys.readouterr().err
        assert "slide 2" in err and "KeyError" in err, err


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


def test_a_nested_error_does_not_also_report_its_slide_keys_as_unknown(tmp_path):
    """E2E-OUTPUT-09: an over-long KPI label failed the kpi slide's schema branch, so
    content and kpis also came back as "unknown key 'content' ... did you mean
    'content'? remove it", sending the fix loop to delete the slide's content."""
    slide = {
        "type": "kpi",
        "content": {"title": "Numbers", "source": SOURCE},
        "kpis": [
            {
                "value": "1",
                "label": "A label far longer than the sixty characters the schema allows it",
            }
        ],
    }
    report = check(tmp_path, deck([slide]))
    assert [i.path for i in report.errors] == ["slides[1].kpis[0].label"], [
        i.format() for i in report.errors
    ]


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


def test_custom_elements_must_clear_the_real_caption_and_takeaway_strip(tmp_path):
    """E2E-OUTPUT-04: check measured elements against the fixed 1.3 and 6.5 in lines,
    so the caption under the title and the takeaway strip overprinted elements it had
    accepted. The body a custom slide really has starts under its caption and ends
    above its takeaway strip and source line."""
    spec = deck(
        [
            {
                "type": "custom",
                "content": {
                    "title": "Positioned under a caption",
                    "description": "A caption under the title takes the top of the body",
                    "takeaway": "And a takeaway strip takes the bottom",
                },
                "elements": [
                    {
                        "kind": "text",
                        "text": "under the caption",
                        "x": 0.374,
                        "y": 1.3,
                        "w": 4,
                        "h": 0.5,
                    },
                    {"kind": "text", "text": "fine", "x": 0.374, "y": 2.5, "w": 4, "h": 0.5},
                    {
                        "kind": "text",
                        "text": "under the strip",
                        "x": 0.374,
                        "y": 5.9,
                        "w": 4,
                        "h": 0.5,
                    },
                ],
            }
        ]
    )
    errors = check(tmp_path, spec).errors
    assert [i.path for i in errors] == ["slides[1].elements[0]", "slides[1].elements[2]"], [
        i.format() for i in errors
    ]
    assert "caption" in errors[0].message and "takeaway" in errors[1].message


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


def test_a_doughnut_slice_too_small_for_its_name_is_a_warning_naming_the_slice(tmp_path):
    """The doughnut then names its slices in a legend: legal (charts.md) but not the
    direct labels Standard #22 prefers, so the author hears which slice forced it."""
    slide = {
        "type": "chart",
        "content": {"title": "Product mix", "source": SOURCE},
        "chart": {
            "type": "doughnut",
            "data": {
                "categories": ["Cards", "Deposits", "Loans", "Other products"],
                "series": [{"name": "Share", "values": [0.5, 0.3, 0.18, 0.02]}],
            },
        },
    }
    report = check(tmp_path, deck([slide]))
    assert report.ok, [i.format() for i in report.errors]
    found = [i for i in report.warnings if i.path == "slides[1].chart.data.categories"]
    assert found and "'Other products'" in found[0].message and "legend" in found[0].message


def test_stacked_labels_left_off_thin_segments_are_a_warning_naming_them(tmp_path):
    """E2E-OUTPUT-08: the value stays in the chart data; the author hears which
    labels were dropped and how to bring them back."""
    series = [
        {"name": "Cards", "values": [50, 60]},
        {"name": "Loans", "values": [45, 38]},
        {"name": "Other", "values": [1, 2]},
    ]
    slide = {
        "type": "chart",
        "content": {"title": "Cards lead the mix", "source": SOURCE},
        "chart": {"type": "bar_stacked", "data": {"categories": ["Q1", "Q2"], "series": series}},
    }
    report = check(tmp_path, deck([slide]))
    assert report.ok, [i.format() for i in report.errors]
    found = [i for i in report.warnings if i.path == "slides[1].chart.data.series"]
    assert found and "'Other' in Q1" in found[0].message and "'Other' in Q2" in found[0].message


def _svg(tmp_path, name, text='<text x="20" y="40" font-size="12">Stage one</text>'):
    """An infographic drawn the infographic-specialist way: 12 x 4.8 in, in points."""
    (tmp_path / name).write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 864 345.6">'
        f'<rect width="864" height="345.6" fill="#FFFFFF"/>{text}</svg>',
        encoding="utf-8",
    )
    return name


def _svg_slide(name, w):
    element = {
        "kind": "image",
        "path": name,
        "alt_text": "A four-stage funnel from application to approval",
        "x": 0.374,
        "y": 1.4,
        "w": w,
        "h": round(w / 2.5, 4),
    }
    return {
        "type": "custom",
        "content": {"title": "The funnel narrows at approval"},
        "elements": [element],
    }


@pytest.mark.parametrize(
    ("w", "level", "printed"), [(6.0, "error", "6.0pt"), (10.8, "warning", "10.8pt")]
)
def test_svg_text_that_prints_small_in_its_slot_is_flagged(tmp_path, w, level, printed):
    """PROMPTS-CONTRACTS-04: an infographic drawn for 12 x 4.8 in with 12pt labels was
    shrunk into whatever frame the slide left, taking its labels under the 10pt floor
    where the validator, which cannot read text inside a picture, never saw them."""
    report = check(tmp_path, deck([_svg_slide(_svg(tmp_path, "funnel.svg"), w)]))
    items = report.errors if level == "error" else report.warnings
    found = [i for i in items if i.path == "slides[1].elements[0].path"]
    assert found, [i.format() for i in report.issues]
    assert printed in found[0].message
    assert f"size_in [{w:.2f}, {w / 2.5:.2f}]" in found[0].fix


def test_svg_text_at_the_size_it_was_drawn_for_passes(tmp_path):
    report = check(tmp_path, deck([_svg_slide(_svg(tmp_path, "funnel.svg"), 12.0)]))
    assert report.ok and not report.warnings, [i.format() for i in report.issues]


@pytest.mark.parametrize(
    "text",
    [
        '<text font-size="9px">a</text>',
        '<text style="fill:#202020;font-size: 9px">a</text>',
        '<style>.label { font-size: 9px }</style><text class="label">a</text>',
        '<g font-size="6.75pt"><text>a</text></g>',
    ],
)
def test_every_way_an_svg_sets_its_text_size_is_read(tmp_path, text):
    import nbg_build as build

    assert build.svg_text_size(tmp_path / _svg(tmp_path, "t.svg", text)) == (9.0, 864.0)


def test_an_svg_without_text_has_no_text_size(tmp_path):
    import nbg_build as build

    assert build.svg_text_size(tmp_path / _svg(tmp_path, "t.svg", "")) is None


def test_check_json_reports_every_image_slot(tmp_path):
    """So the pipeline can draw an infographic at its real slot (size_in) first time."""
    report = check(tmp_path, deck([_svg_slide(_svg(tmp_path, "funnel.svg"), 12.0)]))
    assert report.as_dict()["image_slots"] == [
        {"slide": 2, "id": None, "path": "slides[1].elements[0]", "w": 12.0, "h": 4.8}
    ]


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


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("photo.png", b"not a png at all"),
        ("renamed.jpg", b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic"),
        (
            "broken.svg",
            b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="44">\n</svg>',
        ),
    ],
)
def test_an_image_that_cannot_be_decoded_is_an_error_naming_slide_path_and_file(
    tmp_path, name, content
):
    """PROMPTS-CONTRACTS-02: an image that exists but will not decode (a renamed HEIC,
    a malformed agent-written SVG) crashed check with a traceback, and build exited 2
    blaming the environment."""
    (tmp_path / name).write_bytes(content)
    spec = deck(
        [
            {
                "type": "image",
                "content": {"title": "A picture that will not open"},
                "image": {"path": name, "alt_text": "Growth over five years"},
            }
        ]
    )
    report = check(tmp_path, spec)
    error = next(i for i in report.errors if i.path == "slides[1].image.path")
    assert name in error.message and error.slide == 2, error.format()
    with pytest.raises(nbg_build.SpecInvalid):
        nbg_build.build_presentation(write_spec(tmp_path, spec, "bad.yaml"), tmp_path / "bad.pptx")
    # The renderer itself turns the decode failure into an issue, not a traceback.
    _, errors, _ = nbg_build.render(spec, tmp_path)
    assert any(i.path == "slides[1].image.path" and name in i.message for i in errors)


def test_x_keys_carry_pipeline_notes_through_check_and_build_untouched(tmp_path, monkeypatch):
    """The pipeline keeps its working notes in the spec: top-level x-open-questions,
    slide-level x-assets. Neither is an error, a warning, or anything drawn."""
    import zipfile

    from testkit import passing_validator

    spec = deck(
        [{**_content(), "x-assets": {"icons": ["icons/money/Coins.png"], "why": "n/a"}}],
        title="Notes travel",
        **{"x-owner-notes": "internal"},
    )
    spec["x-open-questions"] = ["Is the Q2 figure final?"]
    report = check(tmp_path, spec)
    assert report.ok and not report.warnings, [i.format() for i in report.issues]
    passing_validator(monkeypatch, nbg_build)
    out = tmp_path / "x.pptx"
    nbg_build.build_presentation(write_spec(tmp_path, spec, "x.yaml"), out)
    with zipfile.ZipFile(out) as zf:
        xml = b"".join(zf.read(n) for n in zf.namelist() if n.startswith("ppt/slides/"))
    assert b"Coins" not in xml and b"Q2 figure" not in xml and b"internal" not in xml


def test_check_applies_the_validators_own_spec_rules():
    """PROMPTS-CONTRACTS-03: check passed specs the build then failed on rules it could
    read in the spec. It now uses the validator's own patterns, so a change to either
    (VALIDATOR-CODE-5 widening the as-of test, say) reaches both."""
    import nbg_validate

    assert nbg_spec.dash_problem is nbg_validate.dash_problem
    assert nbg_spec.alt_text_problem is nbg_validate.alt_text_problem
    assert nbg_spec.SOURCE_AS_OF is nbg_validate.SOURCE_AS_OF


@pytest.mark.parametrize("as_of", ["FY2025", "Q2'26", "9M25"])
def test_a_period_with_its_year_dates_an_exhibit_source(tmp_path, as_of):
    """VALIDATOR-CODE-5: the validator now reads a period with a two- or four-digit
    year as a date, and check follows it with no change of its own."""
    report = check(tmp_path, deck([_bar_slide({"name": "Management accounts", "as_of": as_of})]))
    assert report.ok, [i.format() for i in report.errors]


@pytest.mark.parametrize(
    "title", ["Growth " + chr(0x2014) + " all of it", "Growth -- all of it", "Growth --\nall of it"]
)
def test_an_em_dash_or_a_double_hyphen_in_slide_text_is_an_error(tmp_path, title):
    """The validator's Em Dashes check fails the deck on either (Standard #7)."""
    report = check(tmp_path, deck([_content(title)]))
    assert any(
        i.path == "slides[1].content.title" and "em dash" in i.message for i in report.errors
    ), [i.format() for i in report.issues]


def test_an_em_dash_nothing_draws_is_only_a_warning(tmp_path):
    """Speaker notes and alt text never reach slide text, so the validator never
    reads them; check still points the dash out."""
    slide = {**_content(), "notes": "Pause here " + chr(0x2014) + " then go on"}
    report = check(tmp_path, deck([slide]))
    assert report.ok and any(i.path == "slides[1].notes" for i in report.warnings)


def test_a_spaced_en_dash_in_slide_text_is_a_warning(tmp_path):
    report = check(tmp_path, deck([_content("Growth " + chr(0x2013) + " all of it")]))
    assert report.ok and any("en dash" in i.message for i in report.warnings)


def test_an_em_dash_in_an_x_key_is_nothing(tmp_path):
    slide = {**_content(), "x-assets": {"why": "Chosen " + chr(0x2014) + " for now"}}
    report = check(tmp_path, deck([slide]))
    assert report.ok and not report.warnings, [i.format() for i in report.issues]


def _bar_slide(source):
    return {
        "type": "chart",
        "content": {"title": "Fees rose in the second quarter", "source": source},
        "chart": {
            "type": "bar",
            "data": {"categories": ["Q1", "Q2"], "series": [{"name": "Fees", "values": [1, 2]}]},
        },
    }


def test_an_undated_source_on_an_exhibit_is_an_error(tmp_path):
    """The validator's Exhibit Sources check fails a chart or table slide whose source
    line has no year or date; check accepted as_of: latest."""
    report = check(tmp_path, deck([_bar_slide({"name": "Management accounts", "as_of": "latest"})]))
    found = [i for i in report.errors if i.path == "slides[1].content.source.as_of"]
    assert found and "date" in found[0].message, [i.format() for i in report.issues]


def test_a_year_anywhere_in_the_source_line_dates_it(tmp_path):
    """The validator reads the whole line: 'Annual report 2025, as of Q4' is dated."""
    report = check(tmp_path, deck([_bar_slide({"name": "Annual report 2025", "as_of": "Q4"})]))
    assert report.ok, [i.format() for i in report.errors]


def test_an_undated_source_on_a_text_slide_is_a_warning(tmp_path):
    slide = _content(source={"name": "Internal analysis", "as_of": "latest"})
    report = check(tmp_path, deck([slide]))
    assert report.ok and any(i.path == "slides[1].content.source.as_of" for i in report.warnings)


@pytest.mark.parametrize(
    ("alt", "words"),
    [
        ("growth.png", "filename"),
        ("Picture 3", "autoname"),
        ("Image of a rising arrow", "image of"),
        ("Growth came from cards", "repeats"),
    ],
)
def test_alt_text_the_validator_rejects_is_an_error(tmp_path, alt, words):
    """Alt Text fails a filename, an autoname, an 'image of' opening, and a caption
    repeated from the slide; check let all four through."""
    slide = {
        "type": "image",
        "content": {"title": "Growth came from cards"},
        "image": {"path": "illustrations/Growth.png", "alt_text": alt},
    }
    report = check(tmp_path, deck([slide]))
    found = [i for i in report.errors if i.path == "slides[1].image.alt_text"]
    assert found and words in found[0].message, [i.format() for i in report.issues]


# ---------------------------------------------------------------- dry-run layout


def test_a_cover_title_or_subtitle_that_wraps_is_an_error(tmp_path):
    """Standard #13 keeps each on one line, and the validator's Text Fit fails a
    wrapped one: a warning here let check pass a deck the build then rejected."""
    long_title = "An extremely long cover title that no presenter should ever need"
    long_subtitle = (
        "First placeholder segment | Second placeholder segment | Third placeholder segment"
        " | Fourth"
    )
    report = check(
        tmp_path,
        {
            "slides": [
                {"type": "cover", "content": {"title": long_title[:60], "subtitle": long_subtitle}},
                {"type": "back_cover"},
            ]
        },
    )
    assert not report.ok
    for field in ("title", "subtitle"):
        wrapped = [i for i in report.errors if i.path == f"slides[0].content.{field}"]
        assert wrapped and "Standard #13" in wrapped[0].fix, field


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
