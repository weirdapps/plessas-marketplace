#!/usr/bin/env python3
"""Brand tokens shared by the decks Python tools.

shared/brand-system/tokens.yaml is the one machine-readable copy of the NBG brand:
colours, type scale, geometry, component and chart styling. nbg_build.py renders
with it, nbg_validate.py checks decks against it, nbg_keynote.py reads its dark
keynote tokens, and the tests assert that the brand-system prose quotes it.
Before this file existed the same values were restated in more than ten places
and had drifted into three different brands.

Only PyYAML is needed, which every tool that imports this already depends on.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

TOKENS_PATH = Path(__file__).resolve().parent.parent / "shared" / "brand-system" / "tokens.yaml"


@lru_cache(maxsize=1)
def load() -> dict[str, Any]:
    """The parsed tokens file. Cached: the file is read once per process."""
    with open(TOKENS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError(f"{TOKENS_PATH}: expected a version 1 tokens mapping")
    return data


def get(path: str) -> Any:
    """A token by dotted path, e.g. get("geometry.gutter") or get("type.title.size")."""
    node: Any = load()
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"no brand token {path!r} (missing {part!r})")
        node = node[part]
    return node


def color(name_or_hex: str) -> str:
    """Resolve a colour token name ("teal") or pass a 6-digit hex through, uppercased.

    Type-scale and component entries name colours by token ("color: dark_teal"), so
    one call turns either form into the hex python-pptx and Pillow want.
    """
    colors = load()["colors"]
    if name_or_hex in colors:
        return str(colors[name_or_hex]).upper()
    h = name_or_hex.lstrip("#").upper()
    if len(h) == 6 and all(c in "0123456789ABCDEF" for c in h):
        return h
    raise KeyError(f"unknown colour token {name_or_hex!r}")


def type_style(role: str) -> dict[str, Any]:
    """A type-scale role with its colour resolved to hex: size, bold, color, and extras."""
    style = dict(get(f"type.{role}"))
    style["color"] = color(style["color"])
    return style


def allowed_colors() -> set[str]:
    """Every hex the brand documents: core colours, status palettes, extended palettes,
    the chart palette and the keynote dark tokens. The validator's allow-list."""
    t = load()
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            h = node.upper()
            if len(h) == 6 and all(c in "0123456789ABCDEF" for c in h):
                found.add(h)

    for section in ("colors", "status", "extended_palettes", "charts", "keynote"):
        walk(t.get(section, {}))
    return found - set(retired_colors())


def retired_colors() -> dict[str, str]:
    """Hex -> reason for every colour a deck must not contain."""
    return {str(k).upper(): str(v) for k, v in load().get("retired_colors", {}).items()}


def chart_palette() -> list[str]:
    return [str(c).upper() for c in get("charts.palette")]
