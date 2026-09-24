"""The brand-system prose must quote shared/brand-system/tokens.yaml.

tokens.yaml is the machine-readable brand; the markdown in shared/brand-system/
explains it to people and agents. Before tokens.yaml existed the same values were
restated in more than ten places and drifted into three brands (a 36pt cover
subtitle, a 32pt bold contents header, three line-chart specs). This test pins the
key rows of the docs to the tokens, so a value that changes in one place and not
the other fails here, naming the row.

It is a curated mapping, not a full-text scan: each entry names a document, a
heading, a row label and the token it must quote. Add an entry when a doc grows a
row that restates a token. A heading or row that goes missing fails loudly too,
because a check that finds nothing to compare has not checked anything.
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

import nbg_color  # noqa: E402  (sits next to this file)
import nbg_tokens  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "shared" / "brand-system"
EMU_PER_INCH = 914400

HEX = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{6}(?![0-9A-Fa-f])")
NUM = re.compile(r"\d+(?:\.\d+)?")


# ---------------------------------------------------------------- doc parsing


def read(doc: str) -> str:
    return (DOCS / doc).read_text(encoding="utf-8")


def standard(number: int) -> str:
    """The text of numbered Standard `number` in presentation-style-guide.md."""
    guide = (DOCS.parent / "presentation-style-guide.md").read_text(encoding="utf-8")
    found = re.search(rf"^## {number}\. .*?(?=^## \d+\. |\Z)", guide, re.S | re.M)
    assert found, f"presentation-style-guide.md has no Standard #{number}"
    return found.group(0)


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line index, level, text) for every markdown heading outside fenced code,
    where a '# comment' line is not a heading."""
    found, fenced = [], False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fenced = not fenced
            continue
        m = re.match(r"^(#+)\s+(.*)$", ln)
        if m and not fenced:
            found.append((i, len(m.group(1)), m.group(2).strip()))
    return found


def section(doc: str, heading: str) -> str:
    """The text under the first heading that starts with `heading`, up to the next
    heading of the same or a higher level. Fails if the heading is missing."""
    lines = read(doc).splitlines()
    heads = _headings(lines)
    for n, (i, level, text) in enumerate(heads):
        if text.startswith(heading):
            end = next((j for j, lv, _ in heads[n + 1 :] if lv <= level), len(lines))
            return "\n".join(lines[i + 1 : end])
    raise AssertionError(f"{doc}: no heading starting with {heading!r}")


def clean(cell: str) -> str:
    return re.sub(r"[*`]", "", cell).strip()


def table_rows(doc: str, heading: str) -> list[dict[str, str]]:
    """Every row of every pipe table under `heading`, keyed by its header cells."""
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for ln in section(doc, heading).splitlines():
        if not ln.strip().startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if header is None:
            header = [clean(c) for c in cells]
        elif all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        else:
            rows.append(dict(zip(header, cells, strict=False)))
    return rows


def row(doc: str, heading: str, label: str) -> dict[str, str]:
    """The table row under `heading` whose first cell reads `label`."""
    for r in table_rows(doc, heading):
        first = clean(next(iter(r.values())))
        if first == label:
            return r
    raise AssertionError(f"{doc} › {heading}: no table row {label!r}")


def yaml_blocks(doc: str, heading: str) -> list[Any]:
    """Every ```yaml block under `heading`, parsed."""
    text = section(doc, heading)
    return [yaml.safe_load(b) for b in re.findall(r"```yaml\n(.*?)```", text, re.S)]


def yaml_block(doc: str, heading: str, key: str) -> Any:
    for block in yaml_blocks(doc, heading):
        if isinstance(block, dict) and key in block:
            return block[key]
    raise AssertionError(f"{doc} › {heading}: no yaml block with key {key!r}")


def nums(value: Any) -> list[float]:
    """The numbers in a cell, ignoring colour codes (`#202020`, `BEC1BE`)."""
    text = re.sub(r"#[0-9A-Fa-f]{6}", " ", str(value))
    text = re.sub(
        r"(?<![0-9A-Za-z])(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{6}(?![0-9A-Za-z])", " ", text
    )
    return [float(n) for n in NUM.findall(text)]


def num(value: Any) -> float:
    found = nums(value)
    assert found, f"no number in {value!r}"
    return found[0]


def hexes(value: str) -> list[str]:
    return [h.upper() for h in HEX.findall(value)]


def tok(path: str) -> Any:
    return nbg_tokens.get(path)


def hex_of(name: str) -> str:
    return nbg_tokens.color(name)


# ---------------------------------------------------------------- type scale

# (document, heading, row label, tokens.yaml type role)
TYPE_ROWS = [
    ("README.md", "Typography Hierarchy", "Cover title", "cover_title"),
    ("README.md", "Typography Hierarchy", "Cover subtitle", "cover_subtitle"),
    ("README.md", "Typography Hierarchy", "Divider number", "divider_number"),
    ("README.md", "Typography Hierarchy", "Divider title", "divider_title"),
    ("README.md", "Typography Hierarchy", "Contents header", "contents_header"),
    ("README.md", "Typography Hierarchy", "Contents number", "contents_number"),
    ("README.md", "Typography Hierarchy", "Contents title", "contents_title"),
    ("README.md", "Typography Hierarchy", "Contents description", "contents_description"),
    ("README.md", "Typography Hierarchy", "Content title", "title"),
    ("README.md", "Typography Hierarchy", "Body text", "body"),
    ("README.md", "Typography Hierarchy", "Section pill", "pill"),
    ("README.md", "Typography Hierarchy", "Card title", "card_title"),
    ("README.md", "Typography Hierarchy", "Card body", "card_body"),
    ("README.md", "Typography Hierarchy", "KPI big number", "kpi_value"),
    ("README.md", "Typography Hierarchy", "KPI caption", "kpi_label"),
    ("README.md", "Typography Hierarchy", "Owner subtitle", "subtitle"),
    ("README.md", "Typography Hierarchy", "Caption", "caption"),
    ("README.md", "Typography Hierarchy", "Source / footnote", "source"),
    ("README.md", "Typography Hierarchy", "Table header", "table_header"),
    ("README.md", "Typography Hierarchy", "Table body", "table_body"),
    ("README.md", "Typography Hierarchy", "Chart data label", "chart_data_label"),
    ("README.md", "Typography Hierarchy", "Category axis / legend", "chart_axis"),
    ("README.md", "Typography Hierarchy", "Page number", "page_number"),
    ("typography.md", "Cover Slide", "Title", "cover_title"),
    ("typography.md", "Cover Slide", "Subtitle", "cover_subtitle"),
    ("typography.md", "Cover Slide", "Location", "cover_location"),
    ("typography.md", "Cover Slide", "Date", "cover_date"),
    ("typography.md", "Divider Slide", "Section Number", "divider_number"),
    ("typography.md", "Divider Slide", "Section Title", "divider_title"),
    ("typography.md", "Contents/TOC Slide", '"Contents" Header', "contents_header"),
    ("typography.md", "Contents/TOC Slide", "Section Number", "contents_number"),
    ("typography.md", "Contents/TOC Slide", "Section Title", "contents_title"),
    ("typography.md", "Contents/TOC Slide", "Section Description", "contents_description"),
    ("typography.md", "Content Slide", "Action Title", "title"),
    ("typography.md", "Content Slide", "Body Text", "body"),
    ("typography.md", "Content Slide", "Body Text (dense slides)", "body_dense"),
    ("typography.md", "Content Slide", "Caption (under a title)", "caption"),
    ("typography.md", "Content Slide", "Footnotes and sources", "footnote"),
    ("typography.md", "Metric Cards", "KPI big number", "kpi_value"),
    ("typography.md", "Metric Cards", "KPI caption", "kpi_label"),
    ("typography.md", "Page Header Components", 'Owner subtitle ("Head: A. Smith")', "subtitle"),
    ("typography.md", "Charts & Tables", "Category Axis Labels", "chart_axis"),
    ("typography.md", "Charts & Tables", "Chart Legend", "chart_legend"),
    ("typography.md", "Charts & Tables", "Chart Data Labels", "chart_data_label"),
    ("typography.md", "Charts & Tables", "Table Header (NBG executive pattern)", "table_header"),
    ("typography.md", "Charts & Tables", "Table Body Cell", "table_body"),
    ("typography.md", "Page Number", "Page Number", "page_number"),
]


@pytest.mark.parametrize(("doc", "heading", "label", "role"), TYPE_ROWS)
def test_type_rows_quote_the_type_scale(doc, heading, label, role):
    r = row(doc, heading, label)
    want = nbg_tokens.type_style(role)
    where = f"{doc} › {heading} › {label}"
    size_cell = r["Size"]
    sizes = nums(size_cell)
    assert sizes and sizes[0] == want["size"], (
        f"{where}: size {size_cell!r}, tokens type.{role}.size = {want['size']}"
    )
    if "minimum" in size_cell:
        assert len(sizes) > 1 and sizes[1] == want.get("min_size"), (
            f"{where}: minimum in {size_cell!r}, tokens type.{role}.min_size = {want.get('min_size')}"
        )
    if "sparse" in size_cell:
        assert len(sizes) > 1 and sizes[-1] == want.get("max_size"), (
            f"{where}: sparse-slide size in {size_cell!r}, tokens type.{role}.max_size = "
            f"{want.get('max_size')}"
        )
    colour = hexes(r["Color"])
    assert colour and colour[0] == want["color"], (
        f"{where}: colour {r['Color']!r}, tokens type.{role}.color = {want['color']}"
    )
    bold = "bold" in clean(r["Weight"]).lower()
    assert bold == want["bold"], (
        f"{where}: weight {r['Weight']!r}, tokens type.{role}.bold = {want['bold']}"
    )


@pytest.mark.parametrize(
    ("doc", "heading", "label"),
    [
        ("typography.md", "Charts & Tables", "Value Axis Labels (line and area-line charts)"),
        ("README.md", "Typography Hierarchy", "Value axis (line and area-line charts)"),
    ],
)
def test_value_axis_rows_quote_the_chart_tokens(doc, heading, label):
    """One 12pt #202020 row stood for every axis label, while the builder draws the
    line and area-line value axis at charts.value_axis: 11pt in the muted grey."""
    axis = tok("charts.value_axis")
    r = row(doc, heading, label)
    assert nums(r["Size"]) == [axis["size"]], f"{doc} › {label}: size {r['Size']!r}"
    assert hexes(r["Color"]) == [hex_of(axis["muted_color"])], f"{doc} › {label}: {r['Color']!r}"
    assert "bold" not in clean(r["Weight"]).lower(), f"{doc} › {label}: {r['Weight']!r}"


def test_chart_title_row_is_labelled_existing_decks_only():
    """The builder draws no chart title and the deck spec has no field for one (the
    slide's action title and caption name the chart), so the typography row serves
    hand-built decks only and has to say so."""
    schema_path = DOCS.parent.parent / "tools" / "nbg-presentation" / "deck.schema.json"
    defs = json.loads(schema_path.read_text(encoding="utf-8"))["$defs"]
    for name in ("chart", "waterfall_chart"):
        assert "title" not in defs[name]["properties"], f"deck.schema.json {name} has a title"
    labels = [clean(next(iter(r.values()))) for r in table_rows("typography.md", "Charts & Tables")]
    title = next((label for label in labels if label.startswith("Chart Title")), None)
    assert title, "typography.md › Charts & Tables has no Chart Title row"
    assert "existing decks only" in title, title
    item = next(ln for ln in standard(16).splitlines() if ln.startswith("- Chart titles"))
    assert "existing decks only" in item, f"Standard #16: {item}"


def test_line_spacing_quotes_the_tokens():
    assert num(row("typography.md", "Line Spacing", "Titles")["Line Spacing"]) == tok(
        "line_spacing.title"
    )
    assert num(row("typography.md", "Line Spacing", "Body Text")["Line Spacing"]) == tok(
        "line_spacing.body"
    )


def test_bullet_spec_quotes_the_tokens():
    bullets = tok("components.bullets")
    spacing = row("typography.md", "Paragraph Spacing", "Bullets")["Space Before"]
    assert num(spacing) == bullets["space_before_pt"], spacing
    block = yaml_block("typography.md", "Bullet Points", "bullet")
    assert block["character"] == bullets["glyph"]
    assert block["font"] == bullets["glyph_font"]
    assert hexes(block["color"]) == [hex_of(bullets["glyph_color"])]
    assert num(block["indent"]) == pytest.approx(bullets["indent_emu"] / EMU_PER_INCH, abs=0.001)


def test_font_rows_quote_the_tokens():
    fonts = tok("fonts")
    assert fonts["primary"] in row("README.md", "Fonts", "Primary")["Font"]
    assert fonts["display"] in row("README.md", "Fonts", "Display")["Font"]
    assert fonts["bullet_glyph"] in row("README.md", "Fonts", "Bullets")["Font"]
    fallback = ", ".join(fonts["fallback"])
    assert clean(row("README.md", "Fonts", "Fallback")["Font"]) == fallback
    assert f"**Fallback**: {fallback}" in section("typography.md", "Primary Font (Presentations)")


# ---------------------------------------------------------------- colours

# (document, heading, row label, colour token)
COLOUR_ROWS = [
    ("README.md", "Primary Colors", "Dark Teal", "dark_teal"),
    ("README.md", "Primary Colors", "NBG Teal", "teal"),
    ("README.md", "Primary Colors", "Cyan", "cyan"),
    ("README.md", "Primary Colors", "Bright Cyan", "bright_cyan"),
    ("README.md", "Primary Colors", "Dark Text", "body_text"),
    ("README.md", "Primary Colors", "Caption Grey", "caption_grey"),
    ("README.md", "Primary Colors", "Muted Grey", "muted_grey"),
    ("README.md", "Primary Colors", "Light Grey", "light_grey"),
    ("README.md", "Primary Colors", "White", "white"),
    ("README.md", "Primary Colors", "Off-white", "off_white"),
    ("colors.md", "Most Frequently Used", "#00DFF8", "bright_cyan"),
    ("colors.md", "Most Frequently Used", "#007B85", "teal"),
    ("colors.md", "Most Frequently Used", "#047A85", "teal_variant"),
    ("colors.md", "Most Frequently Used", "#003841", "dark_teal"),
    ("colors.md", "Most Frequently Used", "#202020", "body_text"),
    ("colors.md", "Extended Palette", "#E6F5F6", "takeaway_tint"),
    ("colors.md", "Extended Palette", "#CBFAFF", "highlight_tint"),
    ("colors.md", "Extended Palette", "#FBF3E4", "gold_tint"),
    ("colors.md", "Grey hierarchy", "#5A5F5A", "caption_grey"),
    ("colors.md", "Grey hierarchy", "#939793", "muted_grey"),
    ("colors.md", "Grey hierarchy", "#BEC1BE", "light_grey"),
    ("colors.md", "Official NBG Corporate Palette", "Success", "success"),
    ("colors.md", "Official NBG Corporate Palette", "Alert", "alert"),
    ("colors.md", "Official NBG Corporate Palette", "Gold", "gold"),
    ("colors.md", "Official NBG Corporate Palette", "Blue", "info_blue"),
    ("colors.md", "Two-Party Ownership Coding", "#C8323C", "ownership_ask"),
    ("colors.md", "Two-Party Ownership Coding", "#FAEBEC", "ownership_ask_fill"),
    ("colors.md", "Two-Party Ownership Coding", "#E6F4F5", "ownership_band"),
]


@pytest.mark.parametrize(("doc", "heading", "label", "token"), COLOUR_ROWS)
def test_colour_rows_quote_the_palette(doc, heading, label, token):
    r = row(doc, heading, label)
    found = hexes(" ".join(r.values()))
    want = hex_of(token)
    assert found and found[0] == want, (
        f"{doc} › {heading} › {label}: {found[:1]}, tokens colors.{token} = {want}"
    )


def test_corporate_status_pair_matches_the_status_tokens():
    corporate = tok("status.corporate")
    assert hexes(row("colors.md", "Official NBG Corporate Palette", "Success")["Hex"]) == [
        corporate["positive"].upper()
    ]
    assert hexes(row("colors.md", "Official NBG Corporate Palette", "Alert")["Hex"]) == [
        corporate["negative"].upper()
    ]


def test_practical_status_rows_quote_the_tokens():
    practical = tok("status.practical")
    heading = "Practical Status Colors"
    ok = row("colors.md", heading, "OK / Delivered")
    assert hexes(ok["Hex"]) == [practical["ok"]["fill"]]
    assert hexes(ok["Light variant"]) == [practical["ok"]["tint"]]
    tbd = row("colors.md", heading, "TBD / In progress")
    assert hexes(tbd["Hex"]) == [practical["tbd"]["fill"]]
    assert hexes(tbd["Light variant"]) == [practical["tbd"]["tint"]]
    assert practical["tbd"]["text"] in hexes(tbd["Usage"])
    risk = row("colors.md", heading, "Warning / Risk")
    assert hexes(risk["Hex"]) == [practical["risk"]["fill"]]


def test_severity_ramp_quotes_the_tokens():
    found = [hexes(r["Hex"])[0] for r in table_rows("colors.md", "Graded Severity Ramp")]
    assert found == [h.upper() for h in tok("status.severity_ramp")]


def test_segment_and_link_colours_quote_the_tokens():
    segments = {
        clean(r["Segment"]).lower(): hexes(r["Hex"])[0]
        for r in table_rows("colors.md", "Segment/Division Colors")
    }
    assert segments == {k: v.upper() for k, v in tok("extended_palettes.segments").items()}
    links = {clean(r["Type"]): hexes(r["Hex"])[0] for r in table_rows("colors.md", "Link Colors")}
    want = tok("extended_palettes.links")
    assert links == {
        "Hyperlink": want["hyperlink"].upper(),
        "Followed Link": want["followed"].upper(),
    }


def _numbered_hexes(doc: str, heading: str) -> list[str]:
    return [hexes(ln)[0] for ln in section(doc, heading).splitlines() if re.match(r"^\d+\.\s", ln)]


@pytest.mark.parametrize("doc", ["README.md", "colors.md"])
def test_chart_sequence_quotes_the_chart_palette(doc):
    assert _numbered_hexes(doc, "Chart Color Sequence") == nbg_tokens.chart_palette()


def test_charts_md_sequence_table_quotes_the_chart_palette():
    found = [hexes(r["Hex"])[0] for r in table_rows("charts.md", "Color Sequence")]
    assert found == nbg_tokens.chart_palette()


THEME_SLOTS = {
    "Dark 1": "dk1",
    "Light 1": "lt1",
    "Dark 2": "dk2",
    "Light 2": "lt2",
    **{f"Accent {i}": f"accent{i}" for i in range(1, 7)},
    "Hyperlink": "hlink",
    "Followed hyperlink": "folHlink",
}


def _presentation_module(name: str) -> Any:
    """A module from tools/nbg-presentation/ (the builder's folder), imported by name."""
    folder = str(Path(__file__).resolve().parent / "nbg-presentation")
    if folder not in sys.path:
        sys.path.insert(0, folder)
    return importlib.import_module(name)


def _built_theme() -> dict[str, str]:
    """Slot name -> hex of the colour scheme nbg_build writes, read back from the deck."""
    pytest.importorskip("pptx")
    nbg_build = _presentation_module("nbg_build")
    from lxml import etree
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT

    part = nbg_build.new_presentation().slide_master.part.part_related_by(RT.THEME)
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    scheme = etree.fromstring(part.blob).find(f".//{a}clrScheme")
    return {slot.tag.removeprefix(a): slot.find(f"{a}srgbClr").get("val") for slot in scheme}


def test_theme_table_quotes_the_theme_the_builder_writes():
    built = _built_theme()
    assert set(built) == set(THEME_SLOTS.values()), sorted(built)
    listed = {clean(r["Slot"]): hexes(r["Hex"])[0] for r in table_rows("colors.md", "Theme Colors")}
    assert listed == {label: built[slot] for label, slot in THEME_SLOTS.items()}


OWNERSHIP = "Two-party ownership coding"
OWNERSHIP_TOKENS = {"ownership_ask", "ownership_ask_fill", "ownership_band"}


def test_ownership_coding_quotes_the_colour_tokens():
    """Every `token` (`#HEX`) pair in the layouts.md element spec names a colour token
    with that value, and all three ownership tokens are among them."""
    text = section("layouts.md", OWNERSHIP)
    pairs = re.findall(r"`([a-z][a-z0-9_]*)` \(`#([0-9A-Fa-f]{6})`\)", text)
    assert pairs, "no `token` (`#hex`) pair in the ownership spec"
    for name, value in pairs:
        assert hex_of(name) == value.upper(), f"{name} is {hex_of(name)}; the spec says {value}"
    assert OWNERSHIP_TOKENS <= {name for name, _ in pairs}


# (text colour, fill, the ratio the spec quotes)
OWNERSHIP_TEXT = [
    ("white", "ownership_ask", 5.28),
    ("white", "teal", 5.03),
    ("dark_teal", "ownership_ask_fill", 11.06),
    ("body_text", "ownership_ask_fill", 14.09),
    ("dark_teal", "off_white", 11.96),
    ("body_text", "off_white", 15.24),
    ("dark_teal", "ownership_band", 11.34),
]


@pytest.mark.parametrize(("text", "fill", "quoted"), OWNERSHIP_TEXT)
def test_ownership_coding_text_clears_wcag_aa(text, fill, quoted):
    ratio = nbg_color.contrast_ratio(hex_of(text), hex_of(fill))
    assert ratio >= nbg_color.AA_NORMAL, f"{text} on {fill} is {ratio:.2f}:1"
    assert ratio == pytest.approx(quoted, abs=0.006), f"{text} on {fill} is {ratio:.2f}:1"
    assert f"{quoted:.2f}:1" in section("layouts.md", OWNERSHIP), (
        f"the ownership spec does not quote {quoted:.2f}:1 for {text} on {fill}"
    )


def test_ownership_coding_example_passes_the_spec_check():
    """The spec's YAML recipe goes through the same schema and semantic check as a real
    deck (body area, colour names), so a recipe that drifts from the schema fails here
    rather than in a colleague's build."""
    pytest.importorskip("jsonschema")
    nbg_spec = _presentation_module("nbg_spec")
    (slide,) = yaml_blocks("layouts.md", OWNERSHIP)[0]
    deck = {
        "presentation": {"title": "Ownership coding", "language": "en"},
        "slides": [
            {"type": "cover", "id": "S01", "content": {"title": "Ownership coding"}},
            slide,
            {"type": "back_cover", "id": "S99"},
        ],
    }
    spec, issues = nbg_spec.normalise(deck)
    issues += nbg_spec.schema_issues(spec) + nbg_spec.semantic_issues(spec, DOCS)
    errors = [i.format() for i in issues if i.level == "error"]
    assert not errors, errors
    used = {el.get(key) for el in slide["elements"] for key in ("fill", "text_color")}
    assert used >= OWNERSHIP_TOKENS


def test_retired_colour_table_matches_the_tokens_both_ways():
    listed: set[str] = set()
    for r in table_rows("colors.md", "Retired Colors"):
        listed.update(hexes(r["Hex"]))
    assert listed == set(nbg_tokens.retired_colors())


def test_card_backgrounds_quote_the_component_tokens():
    """Cards are their fill alone; only the recommended option carries a border
    (lead's decision, 2026-09-23: KPI tiles and plain cards have no border)."""
    card = tok("components.card")
    heading = "Card Backgrounds"
    metric = row("colors.md", heading, "Metric card (KPI tile)")
    assert hexes(metric["Background"]) == [hex_of(card["fill"])]
    for r in table_rows("colors.md", heading):
        if clean(r["Card Type"]) != "Recommended-option card":
            assert clean(r["Border"]) == "None", r
    assert not card["shadow"]
    assert hexes(row("colors.md", heading, "Highlight card")["Background"]) == [
        hex_of(card["highlight_fill"])
    ]
    strip = row("colors.md", heading, "Callout / takeaway strip")
    assert hexes(strip["Background"]) == [hex_of(tok("components.takeaway_strip.fill"))]
    rec = row("colors.md", heading, "Recommended-option card")
    assert hexes(rec["Background"]) == [hex_of(card["recommended"]["fill"])]
    assert hexes(rec["Border"]) == [hex_of(card["recommended"]["border"])]
    assert num(rec["Border"]) == card["recommended"]["border_pt"]


KEYNOTE_NAMES = {
    "ink": "ink",
    "ink-2": "ink_2",
    "ink-3": "ink_3",
    "accent": "accent",
    "accent-bar": "accent_bar",
    "accent-mute": "accent_mute",
    "ground-top": "ground_from",
    "ground-bot": "ground_to",
    "negative": "negative",
    "rule": "rule",
}


@pytest.mark.parametrize(
    ("doc", "heading"), [("colors.md", "Dark-Mode Tokens"), ("keynote.md", "Palette: dark tokens")]
)
def test_keynote_dark_tokens_quote_the_tokens(doc, heading):
    dark = tok("keynote.dark")
    found = {clean(r["Token"]): hexes(r["Hex"])[0] for r in table_rows(doc, heading)}
    assert found == {name: dark[key].upper() for name, key in KEYNOTE_NAMES.items()}


# ------------------------------------------------ contrast pairs (Standard #22)


def _contrast_rows() -> list[dict[str, str]]:
    rows = [
        r for r in table_rows("colors.md", "Color Contrast Rules") if "Fill" in r and "Use" in r
    ]
    assert len(rows) >= 20, f"colors.md contrast table has only {len(rows)} rows"
    return rows


@pytest.mark.parametrize("r", _contrast_rows(), ids=lambda r: clean(r["Fill"]))
def test_every_prescribed_text_colour_clears_wcag_aa(r):
    """colors.md used to prescribe text colours with an R+G+B rule of thumb that put
    white on the primary chart cyan. Every row is now recomputed here."""
    fill = hexes(r["Fill"])[0]
    white = nbg_color.contrast_ratio("FFFFFF", fill)
    dark = nbg_color.contrast_ratio("202020", fill)
    assert float(r["White text"]) == pytest.approx(white, abs=0.006), (
        f"{fill}: white is {white:.2f}"
    )
    assert float(r["#202020 text"]) == pytest.approx(dark, abs=0.006), (
        f"{fill}: #202020 is {dark:.2f}"
    )
    use = clean(r["Use"])
    ratio = white if use.startswith("white") else dark
    if "large text only" in use:
        assert max(white, dark) < nbg_color.AA_NORMAL, (
            f"{fill}: a colour clears 4.5:1, drop 'large text only'"
        )
        assert ratio >= nbg_color.AA_LARGE, f"{fill}: {use} is {ratio:.2f}"
    else:
        assert ratio >= nbg_color.AA_NORMAL, f"{fill}: {use} is {ratio:.2f}, under 4.5:1"
        best = "white" if white >= dark else "#202020"
        assert use == best, f"{fill}: prescribes {use} but {best} has more contrast"


def test_contrast_table_covers_every_palette_fill():
    listed = {hexes(r["Fill"])[0] for r in _contrast_rows()}
    t = nbg_tokens.load()
    colours = t["colors"]
    fills = {
        str(colours[k]).upper()
        for k in colours
        if k not in ("white", "black", "body_text", "teal_variant")
    }
    for status in t["status"]["practical"].values():
        fills.update(str(status[k]).upper() for k in ("fill", "tint") if k in status)
    fills.update(str(h).upper() for h in t["status"]["severity_ramp"])
    fills.add(str(t["extended_palettes"]["segments"]["business"]).upper())
    missing = fills - listed
    assert not missing, f"colors.md contrast table has no row for {sorted(missing)}"


# ---------------------------------------------------------------- geometry


def test_readme_geometry_quotes_the_tokens():
    g = tok("geometry")
    heading = "Geometry"
    assert num(row("README.md", heading, "Left gutter")["Value"]) == g["gutter"]
    assert num(row("README.md", heading, "Content width")["Value"]) == g["content_w"]
    assert num(row("README.md", heading, "Right boundary")["Value"]) == g["right_boundary"]
    title = row("README.md", heading, "Title y")
    assert nums(title["Value"])[0] == g["title"]["y"]
    assert nums(title["Note"])[0] == g["title"]["y_with_pill"]
    assert num(row("README.md", heading, "Body top")["Value"]) == g["body_top"]
    assert num(row("README.md", heading, "Footer top")["Value"]) == g["footer_top"]
    assert num(row("README.md", heading, "Grid gap")["Value"]) == g["grid_gap"]


def test_readme_pill_quotes_the_tokens():
    pill = tok("components.pill")
    style = nbg_tokens.type_style("pill")
    heading = "Section Pill"
    assert hexes(row("README.md", heading, "Shape")["Value"]) == [hex_of(pill["fill"])]
    text = row("README.md", heading, "Text")["Value"]
    assert num(text) == style["size"] and "Bold" in text and "ALL CAPS" in text and style["caps"]
    assert nums(row("README.md", heading, "Position")["Value"]) == [pill["x"], pill["y"]]
    assert num(row("README.md", heading, "Height")["Value"]) == pill["h"]
    width = nums(row("README.md", heading, "Width")["Value"])
    assert width[1] == pill["pad_x"] and width[2] == pill["min_w"], width
    assert num(row("README.md", heading, "Corner radius")["Value"]) == pill["radius_in"]


@pytest.mark.parametrize(
    ("label", "token"),
    [("Small", "logo_small"), ("Large", "logo_large"), ("Back Cover", "logo_back")],
)
def test_readme_logo_placement_quotes_the_tokens(label, token):
    r = row("README.md", "Logo Placement", label)
    want = tok(f"geometry.{token}")
    assert nums(r["Position"]) + nums(r["Size"]) == [want["x"], want["y"], want["w"], want["h"]]


def test_readme_page_number_quotes_the_tokens():
    text = section("README.md", "Page Numbers")
    want = tok("geometry.page_number")
    position = next(ln for ln in text.splitlines() if "Position" in ln)
    assert nums(position) == [want["x"], want["y"], want["w"], want["h"]]
    font = next(ln for ln in text.splitlines() if "Font" in ln)
    style = nbg_tokens.type_style("page_number")
    assert num(font) == style["size"] and hexes(font) == [style["color"]]


def test_dimensions_boundaries_quote_the_tokens():
    g = tok("geometry")
    heading = "Horizontal Boundaries"
    assert num(row("dimensions.md", heading, "Left boundary")["Value"]) == g["gutter"]
    assert num(row("dimensions.md", heading, "Right boundary")["Value"]) == g["right_boundary"]
    assert num(row("dimensions.md", heading, "Content width")["Value"]) == g["content_w"]
    assert (
        num(row("dimensions.md", "Zone Boundaries", "Title zone")["Y End"])
        == g["title_zone_bottom"]
    )
    assert (
        num(row("dimensions.md", "Zone Boundaries", "Footer exclusion")["Y Start"])
        == g["footer_top"]
    )
    margins = yaml_block("dimensions.md", "Margins & Safe Zones", "margins")
    assert num(margins["left"]) == g["gutter"]
    assert num(margins["top_title"]) == g["title"]["y"]
    assert num(margins["body_top"]) == g["body_top"]
    slide = yaml_block("dimensions.md", "Slide Dimensions", "slide")
    assert num(slide["width"]) == g["slide"]["w"] and num(slide["height"]) == g["slide"]["h"]
    assert slide["emu_width"] == g["slide"]["w_emu"] and slide["emu_height"] == g["slide"]["h_emu"]


@pytest.mark.parametrize(
    ("heading", "key", "token"),
    [
        ("Small Logo - Content Slides", "logo_small", "logo_small"),
        ("Large Logo - Covers & Dividers", "logo_large", "logo_large"),
        ("Back Cover Logo - Centered", "logo_back", "logo_back"),
        ("Page Number Placement", "page_number", "page_number"),
    ],
)
def test_dimensions_placements_quote_the_tokens(heading, key, token):
    block = yaml_block("dimensions.md", heading, key)
    want = tok(f"geometry.{token}")
    for axis in ("x", "y", "w", "h"):
        assert num(block[axis]) == want[axis], f"dimensions.md › {heading} › {axis}"


def test_dimensions_cover_and_divider_quote_the_tokens():
    cover = yaml_block("dimensions.md", "Cover Slide", "cover")
    want = tok("components.cover")
    for part in ("title", "location", "date"):
        for axis in ("x", "y", "w", "h"):
            assert num(cover[part][axis]) == want[part][axis], f"cover.{part}.{axis}"
    sub = cover["subtitle"]
    assert num(sub["x"]) == want["subtitle"]["x"]
    assert num(sub["w"]) == want["subtitle"]["w"] and num(sub["h"]) == want["subtitle"]["h"]
    assert num(sub["y"]) == pytest.approx(
        want["title"]["y"] + want["title"]["h"] + want["subtitle"]["gap_below_title"], abs=0.001
    )
    divider = yaml_block("dimensions.md", "Divider Slide", "divider")
    for part in ("number", "title"):
        for axis in ("x", "y", "w", "h"):
            assert num(divider[part][axis]) == tok(f"components.divider.{part}.{axis}"), (
                f"divider.{part}.{axis}"
            )
    assert tok("components.divider.same_baseline")
    assert "share one baseline" in section("dimensions.md", "Divider Slide")


def test_dimensions_content_slide_quotes_the_tokens():
    content = yaml_block("dimensions.md", "Content Slide", "content")
    g = tok("geometry")
    pill = tok("components.pill")
    assert num(content["section_pill"]["x"]) == pill["x"]
    assert num(content["section_pill"]["y"]) == pill["y"]
    assert num(content["section_pill"]["h"]) == pill["h"]
    assert nums(content["section_pill"]["w"]) == [2, pill["pad_x"], pill["min_w"]]
    assert num(content["section_pill"]["radius"]) == pill["radius_in"]
    assert num(content["title"]["y"]) == g["title"]["y_with_pill"]
    assert (
        num(content["title"]["w"]) == g["content_w"]
        and num(content["title"]["h"]) == g["title"]["h"]
    )
    assert (
        num(content["body"]["y"]) == g["body_top"] and num(content["body"]["w"]) == g["content_w"]
    )


def test_dimensions_grids_are_derived_from_gutter_width_and_gap():
    """The grids used to stop at 11.6in: a 1.73in right margin against 0.374in left."""
    g = tok("geometry")
    gutter, width, gap, right = g["gutter"], g["content_w"], g["grid_gap"], g["right_boundary"]
    two = yaml_block("dimensions.md", "Two Column (50/50)", "two_column_even")
    w2 = (width - gap) / 2
    assert num(two["left"]["x"]) == gutter
    assert num(two["left"]["w"]) == pytest.approx(w2, abs=0.001)
    assert num(two["right"]["x"]) + num(two["right"]["w"]) == pytest.approx(right, abs=0.001)
    split = yaml_block("dimensions.md", "Two Column (40/60", "two_column_text_chart")
    assert num(split["text"]["w"]) == pytest.approx(0.4 * (width - gap), abs=0.001)
    assert num(split["chart"]["x"]) == pytest.approx(
        gutter + num(split["text"]["w"]) + gap, abs=0.001
    )
    assert num(split["chart"]["x"]) + num(split["chart"]["w"]) == pytest.approx(right, abs=0.001)
    three = yaml_block("dimensions.md", "Three Column", "three_column")
    w3 = (width - 2 * gap) / 3
    for col in ("col1", "col2", "col3"):
        assert num(three[col]["w"]) == pytest.approx(w3, abs=0.001), col
    assert num(three["col1"]["x"]) == gutter
    assert num(three["col2"]["x"]) == pytest.approx(gutter + w3 + gap, abs=0.001)
    assert num(three["col3"]["x"]) + num(three["col3"]["w"]) == pytest.approx(right, abs=0.001)
    full = yaml_block("dimensions.md", "Full Width Content", "full_width")
    assert num(full["x"]) == gutter and num(full["w"]) == width


def test_layouts_contents_slide_quotes_the_tokens():
    """layouts.md put the title column at 1.10in; the builder draws it at the gutter
    plus the number column, 1.174in."""
    c = tok("components.contents")
    heading = "Contents / TOC Slide"
    header = row("layouts.md", heading, '"Contents" Header')
    assert nums(header["Position"]) == [c["header"]["x"], c["header"]["y"]]
    number = row("layouts.md", heading, "Section Number")
    assert num(number["Position"]) == tok("geometry.gutter")
    title_x = tok("geometry.gutter") + c["number_w"]
    for label in ("Section Title", "Description"):
        assert num(row("layouts.md", heading, label)["Position"]) == pytest.approx(
            title_x, abs=0.001
        )
    spacing = section("layouts.md", "Contents / TOC Slide")
    first = next(ln for ln in spacing.splitlines() if "First item Y" in ln)
    step = next(ln for ln in spacing.splitlines() if "Vertical spacing" in ln)
    assert num(first) == c["first_row_y"] and num(step) == c["row_step"]


# ---------------------------------------------------------------- charts


def test_chart_style_table_quotes_the_chart_tokens():
    c = tok("charts")
    heading = "Chart Style"
    line = row("charts.md", heading, "Line")["Spec"]
    want = [c["line"][k] for k in ("width_pt", "marker_size", "marker_line_pt")]
    assert nums(line)[:3] == want, line
    assert "no smoothing" in line and not c["line"]["smooth"]
    area = row("charts.md", heading, "Area-line")["Spec"]
    assert num(area) == pytest.approx(c["area_line"]["fill_alpha"] * 100)
    labels = row("charts.md", heading, "Data labels")["Spec"]
    assert num(labels) == c["data_labels"]["size"] and hexes(labels) == [
        hex_of(c["data_labels"]["color"])
    ]
    axis = row("charts.md", heading, "Category axis")["Spec"]
    assert nums(axis) == [c["category_axis"]["size"], c["category_axis"]["line_pt"]]
    assert hexes(axis) == [hex_of(c["category_axis"]["color"]), hex_of(c["category_axis"]["line"])]
    value = row("charts.md", heading, "Value axis")["Spec"]
    assert num(value) == c["value_axis"]["size"] and hexes(value) == [
        hex_of(c["value_axis"]["muted_color"])
    ]
    legend = row("charts.md", heading, "Legend")["Spec"]
    assert num(legend) == c["legend"]["size"] and c["legend"]["position"].capitalize() in legend
    bars = row("charts.md", heading, "Bar and column")["Spec"]
    assert nums(bars) == [c["bar"]["gap_width"], c["bar"]["overlap_stacked"]]
    assert num(row("charts.md", heading, "Doughnut")["Spec"]) == c["doughnut"]["hole_size"]
    waterfall = row("charts.md", heading, "Waterfall")["Spec"]
    assert num(waterfall) == c["waterfall"]["gap_width"]
    assert hexes(waterfall) == [
        hex_of(c["waterfall"][k]) for k in ("total_color", "increase_color", "decrease_color")
    ]
    gridlines = row("charts.md", heading, "Gridlines")["Spec"]
    assert gridlines == "None" and not c["gridlines"]


def test_marker_ring_quotes_the_token_everywhere():
    """c21af1e thinned the marker ring to 2pt so a 6pt marker keeps its white centre;
    Standard #5, charts.md and the README kept saying it matched the 3.5pt line."""
    ring = tok("charts.line.marker_line_pt")
    spec = section("charts.md", "Hollow")
    outline = next(ln for ln in spec.splitlines() if ln.startswith("- Marker outline"))
    assert nums(outline)[0] == ring, outline
    assert f"line.width = Pt({ring:g})" in spec
    assert f"{ring:g}pt ring" in row("README.md", "Critical Rules", "Line charts")["Enforcement"]
    assert f'<a:ln w="{round(ring * 12700)}">' in standard(5)
    assert f"{ring:g}pt" in standard(5)


def test_doughnut_slice_order_quotes_the_tokens():
    order = [str(h).upper() for h in tok("charts.doughnut.slice_palette")]
    quoted = hexes(row("charts.md", "Chart Style", "Doughnut")["Spec"])
    assert quoted == order, f"Chart Style › Doughnut quotes {quoted}; tokens say {order}"
    quoted = hexes(section("charts.md", "Doughnut Charts"))[: len(order)]
    assert quoted == order, f"Doughnut Charts quotes {quoted}; tokens say {order}"
    # What the docs claim for the order: teal never beside grey, around the whole ring.
    teal, grey = hex_of("teal"), hex_of("muted_grey")
    ring = order + order[:1]
    touching = [(a, b) for a, b in zip(ring, ring[1:], strict=False) if {a, b} == {teal, grey}]
    assert not touching, f"slice_palette puts teal beside grey: {touching}"


def test_fill_band_and_sparse_growth_quote_the_tokens():
    """Standard #2 item 7 names the band the builder grows a sparse slide into."""
    item = next(ln for ln in standard(2).splitlines() if ln.startswith("7. "))
    band = tok("geometry.fill")
    assert f"{band['min'] * 100:g}-{band['max'] * 100:g}%" in item, item
    assert f"toward {tok('type.body.max_size'):g}pt" in item, item
    assert f'toward {tok("components.table.row_h_max"):g}"' in item, item
    tables = section("layouts.md", "Table Styling")
    bullet = tables[tables.index("**Body rows") :].split("\n- ")[0]
    heights = nums(bullet)
    assert heights[0] == tok("components.table.row_h"), bullet
    assert heights[-1] == tok("components.table.row_h_max"), bullet


def test_svg_text_floor_quotes_the_tokens():
    text = " ".join(standard(11).split())
    svg = tok("components.image.svg_label_min_pt")
    floor = tok("accessibility.min_font_pt")
    want = f"under {svg:g}pt it warns, under the {floor:g}pt floor it errors"
    assert want in text, f"Standard #11 does not say {want!r}"
