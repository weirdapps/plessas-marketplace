"""Tests for nbg_tokens.py and the integrity of shared/brand-system/tokens.yaml."""

from __future__ import annotations

import re

import pytest

yaml = pytest.importorskip("yaml")

import nbg_tokens  # noqa: E402  (sits next to this file)

HEX = re.compile(r"^[0-9A-F]{6}$")


def test_loads_version_1():
    assert nbg_tokens.load()["version"] == 1


def test_core_brand_values():
    assert nbg_tokens.color("dark_teal") == "003841"
    assert nbg_tokens.color("teal") == "007B85"
    assert nbg_tokens.get("geometry.gutter") == 0.374
    assert nbg_tokens.get("fonts.primary") == "Aptos"


def test_color_accepts_hex_and_rejects_unknown_names():
    assert nbg_tokens.color("#00adbf") == "00ADBF"
    with pytest.raises(KeyError):
        nbg_tokens.color("not_a_colour")


def test_get_names_the_missing_segment():
    with pytest.raises(KeyError, match="missing 'nope'"):
        nbg_tokens.get("geometry.nope")


def test_every_type_role_resolves_to_a_hex_colour():
    for role in nbg_tokens.load()["type"]:
        style = nbg_tokens.type_style(role)
        assert HEX.match(style["color"]), role
        assert style["size"] >= nbg_tokens.get("accessibility.pill_font_pt"), role


def test_every_named_colour_reference_resolves():
    """Component and chart entries name colours by token; each name must exist."""
    colors = nbg_tokens.load()["colors"]
    names: list[str] = []

    def walk(node, key=""):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, k)
        elif isinstance(node, str) and (
            key in ("fill", "color", "border", "text_color", "glyph_color", "muted_color")
            or key.endswith("_color")
            or key.endswith("_fill")
        ):
            names.append(node)

    walk(nbg_tokens.load()["components"])
    walk(nbg_tokens.load()["charts"])
    for n in names:
        # "auto" = pick black or white by contrast against the fill (data labels).
        assert n == "auto" or n in colors or HEX.match(n.upper()), n


def test_chart_palette_is_six_documented_colours():
    palette = nbg_tokens.chart_palette()
    assert len(palette) == nbg_tokens.get("charts.max_series") == 6
    assert set(palette) <= nbg_tokens.allowed_colors()


def test_retired_colours_are_never_allowed():
    allowed = nbg_tokens.allowed_colors()
    retired = nbg_tokens.retired_colors()
    assert "595959" in retired and "4F81BD" in retired
    assert not (allowed & set(retired))


def test_content_width_is_derived_from_slide_and_gutter():
    g = nbg_tokens.load()["geometry"]
    assert g["content_w"] == pytest.approx(g["slide"]["w"] - 2 * g["gutter"], abs=0.002)
    assert g["right_boundary"] == pytest.approx(g["slide"]["w"] - g["gutter"], abs=0.002)
    assert g["slide"]["w_emu"] == 12192000 and g["slide"]["h_emu"] == 6858000
