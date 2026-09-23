#!/usr/bin/env python3
"""Read, normalise and check a deck spec before anything is drawn.

`decks-py check` and the first stage of `decks-py build` both run this, in order:

1. Load the YAML as UTF-8 (a Greek spec read with the Windows code page is noise),
   and turn a syntax error into a line and column rather than a traceback.
2. Normalise legacy names (toc, bar_chart, charts/pie_single, hyper_title, items,
   waterfall_items, recommended_visual, ...) to the canonical ones, each with a
   warning naming the replacement, and coerce the unquoted numbers and dates YAML
   hands back where the spec meant text.
3. Validate against deck.schema.json (JSON Schema 2020-12).
4. Check what the schema cannot say: sources on exhibits inside columns and custom
   elements, one value per category, images that exist, custom elements inside the
   safe zones, colour names that exist in tokens.yaml, a deck that ends on its
   back cover.

nbg_build.py then lays every slide out in a dry run, which is where text that
cannot fit is caught. Every issue names the slide (number, id and type), the path
in the spec and the fix, because the reader is an agent in a fix loop or a
colleague, and neither can act on "KeyError: 'values'".
"""

from __future__ import annotations

import copy
import datetime as _dt
import difflib
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent.parent
ASSETS_DIR = PLUGIN_ROOT / "assets"
SCHEMA_PATH = HERE / "deck.schema.json"
CATALOG_PATH = ASSETS_DIR / "slide-catalog.yaml"

sys.path.insert(0, str(HERE.parent))
import nbg_tokens  # noqa: E402

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg"}
EM_DASH = chr(0x2014)  # the dash Standard #7 bans from slide text


class CannotRun(Exception):
    """The check could not run at all (missing file, unreadable environment): exit 2."""


# ---------------------------------------------------------------- issues


@dataclass
class Issue:
    level: str  # "error" or "warning"
    message: str
    fix: str = ""
    path: str = ""
    slide: int | None = None  # 1-based position in the deck
    slide_id: str | None = None
    slide_type: str | None = None

    def where(self) -> str:
        if self.slide is None:
            return "deck"
        named = ", ".join(x for x in (self.slide_id, self.slide_type) if x)
        return f"slide {self.slide}" + (f" ({named})" if named else "")

    def format(self) -> str:
        label = "ERROR" if self.level == "error" else "WARNING"
        path = f" {self.path}" if self.path else ""
        message = self.message.rstrip(".")
        text = f"{label} {self.where()}{path}: {message}."
        if self.fix:
            text += f" Fix: {self.fix.rstrip('.')}."
        return text

    def as_dict(self) -> dict[str, Any]:
        return {
            "slide": self.slide,
            "id": self.slide_id,
            "type": self.slide_type,
            "path": self.path,
            "message": self.message,
            "fix": self.fix,
        }


@dataclass
class Report:
    spec_path: Path
    spec: dict[str, Any] | None = None
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def error_slides(self) -> set[int]:
        return {i.slide for i in self.errors if i.slide is not None}

    def as_dict(self) -> dict[str, Any]:
        return {
            "spec": str(self.spec_path),
            "ok": self.ok,
            "errors": [i.as_dict() for i in self.errors],
            "warnings": [i.as_dict() for i in self.warnings],
        }

    def format_text(self) -> str:
        lines = [i.format() for i in self.errors + self.warnings]
        verdict = "OK" if self.ok else "FAILED"
        lines.append(
            f"{verdict}: {len(self.errors)} error(s), {len(self.warnings)} warning(s) "
            f"in {self.spec_path}"
        )
        return "\n".join(lines)


class Issues:
    """Collects issues, attributing each to the slide its path points into."""

    def __init__(self, spec: Any = None) -> None:
        self.items: list[Issue] = []
        self.spec = spec

    def add(self, level: str, path: str, message: str, fix: str = "") -> None:
        slide, slide_id, slide_type = slide_of(self.spec, path)
        self.items.append(Issue(level, message, fix, path, slide, slide_id, slide_type))

    def error(self, path: str, message: str, fix: str = "") -> None:
        self.add("error", path, message, fix)

    def warning(self, path: str, message: str, fix: str = "") -> None:
        self.add("warning", path, message, fix)


_SLIDE_PATH = re.compile(r"^(?:presentation\.)?slides\[(\d+)\]")


def slide_of(spec: Any, path: str) -> tuple[int | None, str | None, str | None]:
    """(1-based slide number, id, type) for a spec path that points into a slide."""
    m = _SLIDE_PATH.match(path or "")
    if not m:
        return None, None, None
    index = int(m.group(1))
    slides = slide_list(spec)
    slide = slides[index] if 0 <= index < len(slides) else None
    if not isinstance(slide, dict):
        return index + 1, None, None
    sid = slide.get("id")
    stype = slide.get("type")
    return (
        index + 1,
        str(sid) if isinstance(sid, str | int) and not isinstance(sid, bool) else None,
        stype if isinstance(stype, str) else None,
    )


def slide_list(spec: Any) -> list[Any]:
    """The slides, wherever the spec keeps them (top level or inside `presentation`)."""
    if not isinstance(spec, dict):
        return []
    slides = spec.get("slides")
    if slides is None and isinstance(spec.get("presentation"), dict):
        slides = spec["presentation"].get("slides")
    return slides if isinstance(slides, list) else []


def slides_path(spec: Any) -> str:
    if (
        isinstance(spec, dict)
        and "slides" not in spec
        and isinstance(spec.get("presentation"), dict)
    ):
        return "presentation.slides"
    return "slides"


def language(spec: Any) -> str:
    pres = spec.get("presentation") if isinstance(spec, dict) else None
    lang = pres.get("language") if isinstance(pres, dict) else None
    return "el" if lang == "el" else "en"


# ---------------------------------------------------------------- catalog


@lru_cache(maxsize=1)
def catalog() -> dict[str, Any]:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or data.get("version") != 2:
        raise CannotRun(f"{CATALOG_PATH}: expected a version 2 slide catalog")
    return data


def slide_types() -> list[str]:
    return list(catalog()["slide_types"])


def chart_types() -> list[str]:
    return list(catalog()["chart_types"])


def _alias_map(section: str) -> dict[str, str]:
    out = {}
    for name, entry in catalog()[section].items():
        for alias in entry.get("aliases") or []:
            out[str(alias)] = name
    return out


def _suggest(value: str, choices: list[str]) -> str:
    close = difflib.get_close_matches(str(value), choices, n=1, cutoff=0.6)
    return f"did you mean '{close[0]}'? " if close else ""


def resolve_chart_type(raw: Any) -> str | None:
    """Canonical chart type for a canonical name or an alias, None when unknown."""
    if not isinstance(raw, str):
        return None
    name = raw.strip().lower()
    if name in chart_types():
        return name
    return _alias_map("chart_types").get(name)


# ---------------------------------------------------------------- loading


_YAML_FIXES = (
    (
        "mapping values are not allowed",
        "quote a value that contains ': ' (a colon then a space), e.g. title: \"Q3: the year\"",
    ),
    ("found character '\\t'", "indent with spaces, not tabs"),
    ("could not find expected ':'", "check the indentation and that every key ends with ':'"),
    ("found undefined alias", "quote a value that starts with '*'"),
    ("expected <block end>", "check that items of one list or mapping share one indentation"),
)


def load_yaml(path: Path) -> tuple[Any, list[Issue]]:
    """(data, issues). Raises CannotRun when the file cannot be read at all."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise CannotRun(f"spec not found: {path}") from e
    except IsADirectoryError as e:
        raise CannotRun(f"spec is a directory, not a file: {path}") from e
    except UnicodeDecodeError as e:
        return None, [
            Issue(
                "error",
                f"{path.name} is not UTF-8 text (byte {e.start} cannot be decoded)",
                "save the file as UTF-8; every editor has the option",
            )
        ]
    try:
        return yaml.safe_load(text), []
    except yaml.MarkedYAMLError as e:
        mark = e.problem_mark or e.context_mark
        where = f"line {mark.line + 1}, column {mark.column + 1}" if mark else "somewhere"
        problem = str(e.problem or e.context or "invalid YAML")
        fix = next((f for key, f in _YAML_FIXES if key in problem), "")
        if not fix:
            fix = (
                "check the YAML at that line; quote any value that contains ': ' or ' #', "
                "or starts with one of * & ! | > ' \" % @ `"
            )
        return None, [Issue("error", f"{path.name} {where}: YAML syntax: {problem}", fix)]
    except yaml.YAMLError as e:
        return None, [Issue("error", f"{path.name}: YAML syntax: {e}", "check the YAML syntax")]


# ---------------------------------------------------------------- normalisation

# Keys whose values are text. YAML hands back 2026 as an int and 2026-09-23 as a
# date; both are coerced back to what the author typed (with a warning to quote
# them), because the author meant text. A boolean is not coerced: YES, no, on and
# off all come back as True/False and the original spelling is gone.
TEXT_KEYS = {
    "title",
    "subtitle",
    "audience",
    "purpose",
    "main_recommendation",
    "author",
    "date",
    "location",
    "key_message",
    "so_what",
    "notes",
    "bumper",
    "description",
    "takeaway",
    "name",
    "as_of",
    "basis",
    "label",
    "delta",
    "body",
    "heading",
    "text",
    "caption",
    "alt_text",
    "unit",
    "highlight_category",
    "number_format",
    "path",
    "icon",
    "id",
}
_NO_DASH_CHECK = {"path", "icon", "id", "number_format"}
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_NUMERIC_TEXT = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def _coerce_scalar(value: Any, path: str, issues: Issues, *, number: bool = False) -> Any:
    """Coerce a YAML scalar standing where text (default) or a number was meant."""
    if isinstance(value, bool):
        issues.error(
            path,
            f"YAML read this unquoted value as {str(value).lower()} (it does that to "
            "yes, no, on, off, true and false)",
            'quote it, e.g. bumper: "YES"' if not number else "write a number",
        )
        return value
    if number:
        if isinstance(value, str) and _NUMERIC_TEXT.match(value.strip()):
            issues.warning(path, f"the number {value!r} is written as text", "drop the quotes")
            n = float(value)
            return int(n) if n.is_integer() and "." not in value else n
        return value
    if isinstance(value, _dt.datetime | _dt.date):
        text = value.isoformat()
        issues.warning(
            path,
            f"YAML read the unquoted date {text} as a date",
            f'quote it as you want it shown, e.g. "{text}" or "September 2026"',
        )
        return text
    if isinstance(value, int | float):
        text = str(value)
        issues.warning(path, f"YAML read {text} as a number", f'quote it: "{text}"')
        return text
    return value


def _walk_text(node: Any, path: str, issues: Issues, key: str = "") -> Any:
    """Coerce text scalars and flag control characters and em dashes, recursively."""
    if isinstance(node, dict):
        for k in list(node):
            child = f"{path}.{k}" if path else str(k)
            node[k] = _walk_text(node[k], child, issues, str(k))
        return node
    if isinstance(node, list):
        for i, item in enumerate(node):
            node[i] = _walk_text(item, f"{path}[{i}]", issues, key)
        return node
    if key in TEXT_KEYS and not isinstance(node, str) and node is not None:
        # A kpi value is text and a waterfall value is a number; both are called
        # "value", which is not in TEXT_KEYS, so each is handled by its own pass.
        node = _coerce_scalar(node, path, issues)
    if isinstance(node, str):
        bad = _CONTROL.search(node)
        if bad:
            issues.error(
                path,
                f"contains the control character U+{ord(bad.group()):04X}, which PowerPoint "
                "cannot store",
                "delete it; it usually arrives with text pasted from a PDF",
            )
        if EM_DASH in node and key not in _NO_DASH_CHECK:
            issues.warning(
                path,
                "contains an em dash",
                "Standard #7: use a comma, a colon, a semicolon or a full stop",
            )
    return node


def _as_points(items: list[Any]) -> list[Any]:
    """Legacy `paragraphs` ({text, bullet}) and plain strings, as `points`."""
    points: list[Any] = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text")
            if text is None:
                text = ": ".join(str(item[k]) for k in ("title", "description") if item.get(k))
            level = item.get("level", 1)
            points.append({"text": text, "level": 2} if level == 2 else text)
        else:
            points.append(item)
    return points


def _items_as_cards(items: list[Any], numbered: bool) -> list[Any]:
    cards: list[Any] = []
    for i, item in enumerate(items):
        if isinstance(item, dict):
            card: dict[str, Any] = {"title": item.get("title") or item.get("text") or ""}
            body = item.get("description") or item.get("body")
            if body:
                card["body"] = body
            if item.get("icon"):
                card["icon"] = item["icon"]
        else:
            card = {"title": item}
        if numbered:
            card["number"] = i + 1
        cards.append(card)
    return cards


def _normalise_chart(chart: dict[str, Any], path: str, issues: Issues) -> None:
    raw = chart.get("type")
    if raw is None:
        return
    canonical = resolve_chart_type(raw)
    if canonical is None:
        issues.error(
            f"{path}.type",
            f"unknown chart type '{raw}'",
            f"{_suggest(str(raw), chart_types())}use one of: {', '.join(chart_types())}",
        )
        return
    if canonical != raw:
        issues.warning(
            f"{path}.type", f"'{raw}' is a legacy chart type", f"write type: {canonical}"
        )
        chart["type"] = canonical


def _move_chart_data(slide: dict[str, Any], path: str, issues: Issues) -> None:
    """Chart data where the builder used to look for it, moved to slide.chart.data."""
    content = slide.get("content")
    if isinstance(content, dict) and ("categories" in content or "series" in content):
        chart = slide.get("chart")
        if chart is None:
            chart = slide["chart"] = {}
        if isinstance(chart, dict):
            data = chart.setdefault("data", {})
            if isinstance(data, dict):
                data.setdefault("categories", content.pop("categories", []))
                data.setdefault("series", content.pop("series", []))
                issues.warning(
                    f"{path}.content.categories",
                    "chart data under content is a legacy shape",
                    "move categories and series to chart.data",
                )
    chart = slide.get("chart")
    if isinstance(chart, dict) and ("labels" in chart or "values" in chart):
        data = chart.setdefault("data", {})
        if isinstance(data, dict):
            data.setdefault("categories", chart.pop("labels", []))
            values = chart.pop("values", [])
            name = str(chart.pop("name", "") or "")
            data.setdefault("series", [{"name": name, "values": values}])
            issues.warning(
                f"{path}.chart.labels",
                "chart.labels + chart.values is a legacy single-series shape",
                "write chart.data: {categories: [...], series: [{name, values}]}",
            )


def _normalise_waterfall(slide: dict[str, Any], path: str, issues: Issues) -> None:
    content = slide.get("content")
    if isinstance(content, dict) and "waterfall_items" in content:
        items = content.pop("waterfall_items")
        chart = slide.get("chart")
        if not isinstance(chart, dict):
            chart = slide["chart"] = {}
        chart.setdefault("type", "waterfall")
        chart.setdefault("data", {}).setdefault("items", items)
        issues.warning(
            f"{path}.content.waterfall_items",
            "content.waterfall_items is a legacy shape",
            "move the items to chart.data.items",
        )
    chart = slide.get("chart")
    if not isinstance(chart, dict):
        return
    if chart.get("type") is None:
        chart["type"] = "waterfall"
    data = chart.get("data")
    if isinstance(data, dict) and "items" not in data and "series" in data:
        series = data.get("series")
        categories = data.get("categories") or []
        if isinstance(series, list) and len(series) == 1 and isinstance(series[0], dict):
            values = series[0].get("values") or []
            data["items"] = [
                {"label": str(c), "value": v} for c, v in zip(categories, values, strict=False)
            ]
            data.pop("series", None)
            data.pop("categories", None)
            issues.warning(
                f"{path}.chart.data",
                "a waterfall takes chart.data.items, not categories and series",
                "write items: [{label, value, total?}]",
            )
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        for i, item in enumerate(data["items"]):
            if isinstance(item, dict) and "value" in item:
                item["value"] = _coerce_scalar(
                    item["value"], f"{path}.chart.data.items[{i}].value", issues, number=True
                )


def _normalise_series_values(chart: Any, path: str, issues: Issues) -> None:
    if not isinstance(chart, dict) or not isinstance(chart.get("data"), dict):
        return
    series = chart["data"].get("series")
    if not isinstance(series, list):
        return
    for s, entry in enumerate(series):
        if not isinstance(entry, dict):
            continue
        values = entry.get("values")
        if not isinstance(values, list):
            continue
        for v, value in enumerate(values):
            if isinstance(value, str) and _NUMERIC_TEXT.match(value.strip()):
                values[v] = _coerce_scalar(
                    value, f"{path}.data.series[{s}].values[{v}]", issues, number=True
                )


def _normalise_table(table: Any, path: str, issues: Issues) -> None:
    """Rows written as mappings are re-ordered by the headers, when the keys match."""
    if not isinstance(table, dict):
        return
    headers = table.get("headers")
    rows = table.get("rows")
    if not isinstance(rows, list) or not isinstance(headers, list):
        return
    keys = {str(h).strip().casefold() for h in headers}
    for r, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        folded = {str(k).strip().casefold(): v for k, v in row.items()}
        if set(folded) <= keys:
            rows[r] = [folded.get(str(h).strip().casefold()) for h in headers]
            issues.warning(
                f"{path}.rows[{r}]",
                "a row written as a mapping was ordered by the headers",
                "write each row as a list, one cell per header",
            )


def _resolve_slide_type(slide: dict[str, Any], path: str, issues: Issues) -> bool:
    """Map a legacy type to its canonical name. Returns True for a numbered infographic."""
    raw = slide.get("type")
    if not isinstance(raw, str):
        return False
    aliases = _alias_map("slide_types")
    visuals = catalog()["visual_aliases"]
    prefixes = catalog()["path_prefixes"]
    name = raw.strip()
    new_type: str | None = None
    chart_type: str | None = None
    numbered = False
    if name in slide_types():
        new_type = name
    elif name in aliases:
        new_type = aliases[name]
        numbered = name == "numbered_infographic"
    elif name in visuals:
        chart_type = visuals[name]
        new_type = "waterfall" if chart_type == "waterfall" else "chart"
    elif "/" in name and name.split("/", 1)[0] in prefixes:
        prefix, suffix = name.split("/", 1)
        new_type = prefixes[prefix]
        if prefix == "charts":
            if suffix.startswith("waterfall"):
                new_type = "waterfall"
            else:
                chart_type = resolve_chart_type(suffix) or resolve_chart_type(
                    suffix.split("_", 1)[0]
                )
        elif prefix == "infographics":
            if aliases.get(suffix) == "process":
                new_type = "process"
            numbered = suffix.startswith("numbered")
    if new_type is None:
        known = slide_types() + sorted(aliases) + sorted(visuals)
        issues.error(
            f"{path}.type",
            f"unknown slide type '{name}'",
            f"{_suggest(name, known)}use one of: {', '.join(slide_types())}",
        )
        return False
    if new_type != name:
        issues.warning(
            f"{path}.type", f"'{name}' is a legacy slide type", f"write type: {new_type}"
        )
        slide["type"] = new_type
    if chart_type and new_type == "chart":
        chart = slide.setdefault("chart", {})
        if isinstance(chart, dict) and not chart.get("type"):
            chart["type"] = chart_type
    return numbered


def _normalise_content(slide: dict[str, Any], path: str, numbered: bool, issues: Issues) -> None:
    stype = slide.get("type")
    if "bumper" in slide:
        content = slide.setdefault("content", {})
        if isinstance(content, dict):
            content.setdefault("bumper", slide.pop("bumper"))
            issues.warning(
                f"{path}.bumper", "bumper belongs under content", "move it to content.bumper"
            )
    content = slide.get("content")
    if not isinstance(content, dict):
        return
    if "hyper_title" in content:
        content.setdefault("bumper", content.pop("hyper_title"))
        issues.warning(
            f"{path}.content.hyper_title", "hyper_title is a legacy key", "write content.bumper"
        )
    if "paragraphs" in content:
        paragraphs = content.pop("paragraphs")
        if isinstance(paragraphs, list):
            content.setdefault("points", _as_points(paragraphs))
        issues.warning(
            f"{path}.content.paragraphs", "paragraphs is a legacy key", "write content.points"
        )
    if "items" in content:
        items = content.pop("items")
        if isinstance(items, list):
            if stype == "cards":
                slide.setdefault("cards", _items_as_cards(items, numbered))
            elif stype == "process":
                steps = [
                    {k: v for k, v in card.items() if k in ("title", "body", "icon")}
                    for card in _items_as_cards(items, False)
                ]
                slide.setdefault("steps", steps)
            else:
                content.setdefault("points", _as_points(items))
        issues.warning(
            f"{path}.content.items",
            "content.items is a legacy key",
            "write cards (cards slide), steps (process slide) or content.points",
        )
    if isinstance(content.get("points"), list):
        content["points"] = _as_points(content["points"])


def _normalise_slide(slide: dict[str, Any], path: str, issues: Issues) -> None:
    numbered = _resolve_slide_type(slide, path, issues)
    visuals = catalog()["visual_aliases"]
    visual = slide.pop("recommended_visual", None)
    if visual is not None:
        mapped = visuals.get(str(visual))
        if slide.get("type") == "chart" and mapped == "waterfall":
            slide["type"] = "waterfall"
        elif slide.get("type") == "chart" and mapped:
            chart = slide.setdefault("chart", {})
            if isinstance(chart, dict) and not chart.get("type"):
                chart["type"] = mapped
        issues.warning(
            f"{path}.recommended_visual",
            "recommended_visual is a storyline hint the builder does not read",
            "set the slide's type (and chart.type) instead",
        )
    _normalise_content(slide, path, numbered, issues)
    stype = slide.get("type")
    _move_chart_data(slide, path, issues)
    if stype == "waterfall":
        _normalise_waterfall(slide, path, issues)
    elif isinstance(slide.get("chart"), dict):
        _normalise_chart(slide["chart"], f"{path}.chart", issues)
        _normalise_series_values(slide["chart"], f"{path}.chart", issues)
    if isinstance(slide.get("table"), dict):
        _normalise_table(slide["table"], f"{path}.table", issues)
    for side in ("left", "right"):
        column = slide.get(side)
        if not isinstance(column, dict):
            continue
        if isinstance(column.get("chart"), dict):
            _normalise_chart(column["chart"], f"{path}.{side}.chart", issues)
            _normalise_series_values(column["chart"], f"{path}.{side}.chart", issues)
        if isinstance(column.get("table"), dict):
            _normalise_table(column["table"], f"{path}.{side}.table", issues)
        if isinstance(column.get("points"), list):
            column["points"] = _as_points(column["points"])
    for e, element in enumerate(slide.get("elements") or []):
        if not isinstance(element, dict):
            continue
        if isinstance(element.get("chart"), dict):
            _normalise_chart(element["chart"], f"{path}.elements[{e}].chart", issues)
            _normalise_series_values(element["chart"], f"{path}.elements[{e}].chart", issues)
        if isinstance(element.get("table"), dict):
            _normalise_table(element["table"], f"{path}.elements[{e}].table", issues)
    for i, kpi in enumerate(slide.get("kpis") or []):
        if isinstance(kpi, dict) and "value" in kpi and not isinstance(kpi["value"], str):
            kpi["value"] = _coerce_scalar(kpi["value"], f"{path}.kpis[{i}].value", issues)


def normalise(data: Any) -> tuple[Any, list[Issue]]:
    """A normalised deep copy of the spec, and the warnings (and errors) raised."""
    issues = Issues()
    if data is None:
        issues.error(
            "",
            "the spec is empty",
            "write a mapping with a slides: list; deck.schema.json has the fields",
        )
        return data, issues.items
    if not isinstance(data, dict):
        issues.error(
            "",
            f"the top level must be a mapping with a slides: list, not a {type(data).__name__}",
            "put the slides under slides: (and deck metadata under presentation:)",
        )
        return data, issues.items
    spec = copy.deepcopy(data)
    issues.spec = spec
    if "template" in spec:
        spec.pop("template")
        issues.warning(
            "template",
            "template: has no effect (the builder draws every slide from scratch)",
            "delete the key",
        )
    _walk_text(spec, "", issues)
    base = slides_path(spec)
    for i, slide in enumerate(slide_list(spec)):
        if isinstance(slide, dict):
            _normalise_slide(slide, f"{base}[{i}]", issues)
    return spec, issues.items


# ---------------------------------------------------------------- schema


@lru_cache(maxsize=1)
def _validator() -> Any:
    try:
        import jsonschema
    except ImportError as e:  # requirements.txt carries it; this is the clear message
        raise CannotRun(
            "jsonschema is not installed; run through bin/decks-py, which installs "
            "tools/nbg-presentation/requirements.txt"
        ) from e
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    return jsonschema.Draft202012Validator(schema)


REQUIRED_FIX = {
    "source": "add source: {name: <where the figures come from>, as_of: <date or period>}",
    "as_of": "add as_of: the date or period the figures refer to",
    "name": "name it",
    "title": "add a title",
    "points": "add points: a list of bullets",
    "chart": "add chart: {type, data: {categories, series}}",
    "data": "add data",
    "categories": "add categories: one label per value",
    "series": "add series: [{name, values}]",
    "values": "add values: one number per category",
    "items": "add items: [{label, value}]",
    "sections": "add sections: [{title}]",
    "cards": "add cards: [{title, body}]",
    "steps": "add steps: [{title, body}]",
    "kpis": "add kpis: [{value, label}]",
    "table": "add table: {headers, rows}",
    "headers": "add headers: one per column",
    "rows": "add rows: each a list of cells",
    "image": "add image: {path, alt_text}",
    "path": "add the file path",
    "alt_text": "describe what the image shows, for screen-reader users",
    "left": "add the left column: {kind, ...}",
    "right": "add the right column: {kind, ...}",
    "elements": "add elements: [{kind, x, y, w, h}]",
    "kind": "add kind",
    "content": "add content: {title: ...}",
    "number": "add the section number, e.g. 1",
    "value": "add the value",
    "label": "add the label",
    "type": "add type: one of the slide types",
    "text": "add the text",
    "shape": "add shape: rect, rounded_rect, oval, chevron or arrow_right",
}

_JSON_TYPES = {
    "string": "text",
    "number": "a number",
    "integer": "a whole number",
    "array": "a list",
    "object": "a mapping",
    "boolean": "true or false",
    "null": "empty",
}


def format_path(parts: Any) -> str:
    out = ""
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}" if out else str(part)
    return out


def _deepest(error: Any) -> Any:
    """For anyOf/oneOf failures, the branch error that says the most."""
    if not error.context:
        return error
    import jsonschema.exceptions

    return _deepest(jsonschema.exceptions.best_match(error.context))


def _allowed_keys(schema: dict[str, Any]) -> list[str]:
    keys = list((schema.get("properties") or {}).keys())
    for branch in schema.get("allOf") or []:
        then = branch.get("then") or {}
        keys += list((then.get("properties") or {}).keys())
    return sorted(set(keys))


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _type_fix(wants: list[str], inst: Any, wanted: str) -> str:
    if "string" in wants and isinstance(inst, int | float) and not isinstance(inst, bool):
        return f'quote it: "{inst}"'
    if "number" in wants and isinstance(inst, str):
        return (
            "write a plain number (no %, currency or thousands separator) and set "
            "chart.number_format for the display"
        )
    if "array" in wants and not isinstance(inst, list):
        return "write it as a list, e.g. [a, b, c]"
    if "object" in wants and isinstance(inst, list):
        return "write it as a mapping of named fields, e.g. {name: ..., as_of: ...}"
    if inst is None:
        return "fill it in, or delete the key"
    return f"make it {wanted}"


def _describe(error: Any) -> tuple[str, str, str]:
    """(path, message, fix) for one jsonschema error."""
    v = error.validator
    path = format_path(error.absolute_path)
    inst = error.instance
    if v == "required":
        key = re.findall(r"'([^']+)'", error.message)
        name = key[0] if key else "a field"
        return (
            f"{path}.{name}" if path else name,
            f"missing {name}",
            REQUIRED_FIX.get(name, f"add {name}"),
        )
    if v in ("additionalProperties", "unevaluatedProperties"):
        names = re.findall(r"'([^']+)'", error.message.split("(")[-1]) or ["?"]
        allowed = _allowed_keys(error.schema) if isinstance(error.schema, dict) else []
        where = f"{path}.{names[0]}" if path else names[0]
        more = f" (and {len(names) - 1} more)" if len(names) > 1 else ""
        fix = f"{_suggest(names[0], allowed)}remove it or fix the spelling"
        if allowed:
            fix += f"; allowed here: {', '.join(allowed)}"
        return where, f"unknown key '{names[0]}'{more}", fix
    if v == "enum":
        choices = [str(c) for c in error.validator_value]
        return (
            path,
            f"'{inst}' is not allowed here",
            f"{_suggest(str(inst), choices)}use one of: {', '.join(choices)}",
        )
    if v == "const":
        return path, f"'{inst}' is not allowed here", f"write {error.validator_value}"
    if v == "type":
        want = error.validator_value
        wants = [want] if isinstance(want, str) else list(want)
        wanted = " or ".join(_JSON_TYPES.get(w, w) for w in wants)
        got = _JSON_TYPES.get(_json_type(inst), _json_type(inst))
        return path, f"expected {wanted}, got {got}", _type_fix(wants, inst, wanted)
    if v == "maxLength":
        return (
            path,
            f"{len(inst)} characters, the limit here is {error.validator_value}",
            f"shorten it to {error.validator_value} characters or fewer",
        )
    if v == "minLength":
        return path, "is empty", "fill it in, or delete the key"
    if v == "minItems":
        return (
            path,
            f"needs at least {error.validator_value} item(s), has {len(inst)}",
            "add the missing items",
        )
    if v == "maxItems":
        fix = "split it across two slides"
        if path.endswith("series"):
            fix = "Standard #22: past six series use small multiples or group the tail into 'Other'"
        return path, f"at most {error.validator_value} items allowed, has {len(inst)}", fix
    if v == "pattern":
        return (
            path,
            f"'{inst}' is not a valid id",
            "use letters, digits, '-' and '_' only, e.g. S03",
        )
    if v in ("minimum", "exclusiveMinimum"):
        return (
            path,
            f"{inst} is too small (minimum {error.validator_value})",
            f"use a value above {error.validator_value}",
        )
    if v == "maxProperties":
        return path, "a back cover carries nothing (Standard #19)", "delete the content block"
    return path, error.message, "see deck.schema.json for the shapes accepted here"


def schema_issues(spec: Any) -> list[Issue]:
    issues = Issues(spec)
    described = []
    for top in sorted(
        _validator().iter_errors(spec), key=lambda e: list(map(str, e.absolute_path))
    ):
        error = _deepest(top)
        path, message, fix = _describe(error)
        if path == "slides" and isinstance(error.instance, dict):
            message = "slides must be a list"
            fix = "write each slide as a list item starting with '- type:'"
        described.append((error.validator, path, message, fix))
    seen: set[tuple[str, str]] = set()
    for validator, path, message, fix in described:
        # A key whose own subschema failed counts as unevaluated too, so the same
        # mistake also surfaces as "unknown key 'content'". Report the real one.
        if validator == "unevaluatedProperties" and any(
            other.startswith(path + ".") or other.startswith(path + "[")
            for _, other, _, _ in described
        ):
            continue
        if (path, message) in seen:
            continue
        seen.add((path, message))
        issues.error(path, message, fix)
    return issues.items


# ---------------------------------------------------------------- semantic checks


def resolve_asset(raw: str, spec_dir: Path) -> Path | None:
    """An image path: absolute, else relative to the spec file, else to assets/."""
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate if candidate.is_file() else None
    for base in (spec_dir, ASSETS_DIR):
        p = (base / candidate).resolve()
        if p.is_file():
            return p
    return None


def svg_supported() -> bool:
    try:
        import resvg_py  # noqa: F401
    except ImportError:
        return False
    return True


def undecodable(file: Path) -> str | None:
    """Why an existing image file cannot be drawn, or None when it decodes: a renamed
    HEIC or a malformed SVG exists, has the right suffix, and still cannot be placed."""
    try:
        if file.suffix.lower() == ".svg":
            import resvg_py

            resvg_py.svg_to_bytes(svg_path=str(file), width=16)
        else:
            from PIL import Image

            with Image.open(file) as img:
                img.verify()
    except Exception as e:  # noqa: BLE001 - whatever the decoder raises, the file is unusable
        return f"{type(e).__name__}: {e}"
    return None


def _check_image(raw: Any, path: str, spec_dir: Path, issues: Issues) -> None:
    if not isinstance(raw, str) or not raw.strip():
        return
    suffix = Path(raw).suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        issues.error(path, f"'{Path(raw).name}' is not a PNG, JPEG or SVG", "convert it to PNG")
        return
    found = resolve_asset(raw, spec_dir)
    if found is None:
        issues.error(
            path,
            f"image not found: {raw}",
            f"give an absolute path, or one relative to {spec_dir} or to the plugin's "
            "assets/ folder",
        )
    elif suffix == ".svg" and not svg_supported():
        issues.error(
            path,
            "SVG needs resvg-py, which is not installed",
            "run through bin/decks-py (it installs requirements.txt), or convert the SVG to PNG",
        )
    elif (why := undecodable(found)) is not None:
        issues.error(
            path,
            f"'{found.name}' exists but cannot be read as {suffix.lstrip('.').upper()} ({why})",
            "re-export it as a PNG, JPEG or valid SVG; a photo saved as HEIC needs converting",
        )


def _is_number(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def _series_issues(series: list[Any], categories: list[Any], path: str, issues: Issues) -> None:
    for s, entry in enumerate(series):
        if not isinstance(entry, dict) or not isinstance(entry.get("values"), list):
            continue
        values = entry["values"]
        where = f"{path}.data.series[{s}].values"
        if len(values) != len(categories):
            plural = "category" if len(categories) == 1 else "categories"
            issues.error(
                where,
                f"{len(values)} value(s) for {len(categories)} {plural}",
                "give one value per category (null for a gap)",
            )
        bad = [v for v in values if not (v is None or _is_number(v))]
        if bad:
            issues.error(
                where,
                f"{bad[0]!r} is not a number",
                "write plain numbers (12, not '12%') and set chart.number_format, e.g. '0%'",
            )
        elif values and all(v is None for v in values):
            issues.error(where, "every value is empty", "fill in the data")
        elif any(isinstance(v, float) and not math.isfinite(v) for v in values):
            issues.error(where, "contains inf or nan", "use a real number or null")


# ---------------------------------------------------------------- peer banks


def fold(text: Any) -> str:
    """Lower case with the accents removed (final sigma folds to sigma): how names match."""
    decomposed = unicodedata.normalize("NFD", str(text))
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).casefold()


@lru_cache(maxsize=1)
def _bank_patterns() -> dict[str, re.Pattern[str]]:
    """Per bank, its full names and its label-only short forms: a chart label is a
    label, so both count here."""
    patterns = {}
    for key, bank in nbg_tokens.get("banks").items():
        aliases = list(bank["names"]) + list(bank["label_aliases"])
        names = sorted((fold(a) for a in aliases), key=len, reverse=True)
        patterns[key] = re.compile("|".join(rf"\b{re.escape(n)}\b" for n in names))
    return patterns


def bank_of(label: Any) -> str | None:
    """The tokens.yaml bank a chart label names, or None. A label naming two banks is
    None too: it is a comparison written in words, not one bank's bar."""
    folded = fold(label)
    hits = [key for key, pattern in _bank_patterns().items() if pattern.search(folded)]
    return hits[0] if len(hits) == 1 else None


def bank_plan(chart: Any) -> tuple[str, list[str | None]] | None:
    """("series", the bank per series) or ("categories", the bank per category) when a
    chart compares two or more banks, else None. Series win: a chart whose series are
    banks is a comparison whatever its categories are."""
    if not isinstance(chart, dict) or not isinstance(chart.get("data"), dict):
        return None
    series = chart["data"].get("series") or []
    by_series = [bank_of(s.get("name", "")) if isinstance(s, dict) else None for s in series]
    if len({b for b in by_series if b}) >= 2:
        return "series", by_series
    by_category = [bank_of(c) for c in chart["data"].get("categories") or []]
    if len({b for b in by_category if b}) >= 2:
        return "categories", by_category
    return None


BANK_CATEGORY_TYPES = ("bar", "bar_horizontal", "doughnut")


def _bank_issues(chart: dict[str, Any], path: str, issues: Issues) -> None:
    plan = bank_plan(chart)
    if plan is None:
        return
    mode, _ = plan
    series = chart["data"].get("series") or []
    if mode == "categories" and len(series) > 1:
        issues.error(
            f"{path}.data.series",
            f"banks as categories take one series, not {len(series)}: each bank is one colour",
            "keep one series, or make the banks the series and the periods the categories",
        )
    elif mode == "categories" and chart.get("type") not in BANK_CATEGORY_TYPES:
        issues.error(
            f"{path}.type",
            f"a {chart.get('type')} chart cannot compare banks across its categories",
            "use bar or bar_horizontal (or doughnut for shares), or make the banks the series",
        )
    if chart.get("bank_logos") is False:
        issues.error(
            f"{path}.bank_logos",
            "bank_logos is false on a peer comparison, and the Bank Branding gate requires "
            "each plotted bank's logo",
            "remove bank_logos: false; the builder places the logos itself",
        )
    if chart.get("highlight_category") is not None:
        issues.warning(
            f"{path}.highlight_category",
            "ignored on a bank comparison: each bank takes its brand colour",
            "remove highlight_category",
        )


def _chart_issues(chart: Any, path: str, issues: Issues) -> None:
    if not isinstance(chart, dict) or not isinstance(chart.get("data"), dict):
        return
    data = chart["data"]
    categories = data.get("categories")
    series = data.get("series")
    if not isinstance(categories, list) or not isinstance(series, list):
        return
    _series_issues(series, categories, path, issues)
    max_series = int(nbg_tokens.get("charts.max_series"))
    if len(series) > max_series:
        issues.warning(
            f"{path}.data.series",
            f"{len(series)} series; six is the practical ceiling",
            "Standard #22: past six series use small multiples or group the tail into 'Other'",
        )
    if chart.get("type") == "doughnut":
        values = series[0].get("values") if series and isinstance(series[0], dict) else None
        if len(series) != 1:
            issues.error(
                f"{path}.data.series",
                f"a doughnut takes one series, has {len(series)}",
                "keep one series, or use a stacked bar",
            )
        elif isinstance(values, list) and any(_is_number(v) and v < 0 for v in values):
            issues.error(
                f"{path}.data.series[0].values",
                "a doughnut cannot show a negative share",
                "use a bar chart",
            )
        if len(categories) > max_series:
            issues.warning(
                f"{path}.data.categories",
                f"{len(categories)} slices; six is the practical ceiling",
                "group the smallest slices into 'Other'",
            )
    highlight = chart.get("highlight_category")
    if highlight is not None and str(highlight) not in [str(c) for c in categories]:
        issues.error(
            f"{path}.highlight_category",
            f"'{highlight}' is not one of the categories",
            f"use one of: {', '.join(str(c) for c in categories)}",
        )
    _bank_issues(chart, path, issues)


def _table_issues(table: Any, path: str, issues: Issues) -> None:
    if not isinstance(table, dict):
        return
    headers = table.get("headers") or []
    rows = table.get("rows") or []
    width = len(headers) if isinstance(headers, list) else 0
    for r, row in enumerate(rows if isinstance(rows, list) else []):
        if not isinstance(row, list):
            continue
        if width and len(row) > width:
            issues.error(
                f"{path}.rows[{r}]",
                f"{len(row)} cells for {width} header(s)",
                "add the missing header or remove the extra cell",
            )
        elif width and len(row) < width:
            issues.warning(
                f"{path}.rows[{r}]",
                f"{len(row)} cells for {width} header(s)",
                "the row is padded with blank cells; fill them in if they carry data",
            )
        for c, cell in enumerate(row):
            if isinstance(cell, bool):
                issues.error(
                    f"{path}.rows[{r}][{c}]",
                    f"YAML read this unquoted cell as {str(cell).lower()}",
                    'quote it, e.g. "Yes"',
                )
    highlight = table.get("highlight_column")
    if isinstance(highlight, int) and width and highlight >= width:
        issues.error(
            f"{path}.highlight_column",
            f"column {highlight} does not exist (0 to {width - 1})",
            "count columns from 0",
        )
    align = table.get("column_align")
    if isinstance(align, list) and width and len(align) > width:
        issues.error(
            f"{path}.column_align",
            f"{len(align)} alignments for {width} columns",
            "give one per column",
        )


def _colour_issue(value: Any, path: str, issues: Issues) -> None:
    if not isinstance(value, str):
        return
    colours = list(nbg_tokens.load()["colors"])
    if value not in colours:
        issues.error(
            path,
            f"'{value}' is not a colour in tokens.yaml",
            f"{_suggest(value, colours)}use a colour name such as teal, dark_teal or off_white",
        )


def body_bottom(has_source: bool) -> float:
    """Where the body area ends: the 6.5" floor, or above the source line."""
    g = nbg_tokens.load()["geometry"]
    if has_source:
        src = g["source_line"]
        return float(src["bottom"]) - float(src["h"]) - 0.1
    return float(g["body_bottom"])


def _element_issues(element: dict[str, Any], path: str, has_source: bool, issues: Issues) -> None:
    g = nbg_tokens.load()["geometry"]
    tol = 0.005
    try:
        x, y, w, h = (float(element[k]) for k in ("x", "y", "w", "h"))
    except (KeyError, TypeError, ValueError):
        return
    left, right = float(g["gutter"]), float(g["right_boundary"])
    top, bottom = float(g["body_top"]), body_bottom(has_source)
    area = f"x {left:g} to {right:g}, y {top:g} to {bottom:.2f}"
    if x < left - tol or x + w > right + tol:
        issues.error(
            path,
            f"runs from x {x:g} to {x + w:.3f}, outside the gutters",
            f"keep it inside the body area ({area})",
        )
    if y < top - tol or y + h > bottom + tol:
        issues.error(
            path,
            f"runs from y {y:g} to {y + h:.3f}, outside the body area",
            f"keep it inside the body area ({area}); the title zone and the footer are chrome",
        )
    for key in ("fill", "border", "text_color"):
        if key in element:
            _colour_issue(element[key], f"{path}.{key}", issues)


def _column_issues(slide: dict[str, Any], p: str, spec_dir: Path, issues: Issues) -> bool:
    """Checks a two_column slide's columns; True when one holds an exhibit."""
    exhibit = False
    for side in ("left", "right"):
        column = slide.get(side)
        if not isinstance(column, dict):
            continue
        exhibit = exhibit or column.get("kind") in ("chart", "table", "kpis")
        if isinstance(column.get("chart"), dict):
            _chart_issues(column["chart"], f"{p}.{side}.chart", issues)
        if isinstance(column.get("table"), dict):
            _table_issues(column["table"], f"{p}.{side}.table", issues)
        if isinstance(column.get("image"), dict):
            _check_image(column["image"].get("path"), f"{p}.{side}.image.path", spec_dir, issues)
    return exhibit


def _custom_issues(
    slide: dict[str, Any], p: str, spec_dir: Path, has_source: bool, issues: Issues
) -> bool:
    """Checks a custom slide's elements; True when one is an exhibit."""
    exhibit = False
    for e, element in enumerate(slide.get("elements") or []):
        if not isinstance(element, dict):
            continue
        ep = f"{p}.elements[{e}]"
        exhibit = exhibit or element.get("kind") in ("chart", "table")
        _element_issues(element, ep, has_source, issues)
        if isinstance(element.get("chart"), dict):
            _chart_issues(element["chart"], f"{ep}.chart", issues)
        if isinstance(element.get("table"), dict):
            _table_issues(element["table"], f"{ep}.table", issues)
        if element.get("kind") == "image":
            _check_image(element.get("path"), f"{ep}.path", spec_dir, issues)
    return exhibit


def _waterfall_issues(slide: dict[str, Any], p: str, issues: Issues) -> None:
    chart = slide.get("chart")
    data = chart.get("data") if isinstance(chart, dict) else None
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list) or len(items) < 2:
        return
    running = 0.0
    for i, item in enumerate(items):
        if not isinstance(item, dict) or not _is_number(item.get("value")):
            return
        value = float(item["value"])
        is_total = bool(item.get("total", i in (0, len(items) - 1)))
        if is_total:
            if i > 0 and abs(value - running) > max(0.005 * abs(running), 1e-9):
                issues.warning(
                    f"{p}.chart.data.items[{i}].value",
                    f"the total {value:g} differs from the running sum {running:g}",
                    "correct the total or a contribution; a bridge that does not add up is "
                    "challenged in the room",
                )
            running = value
        else:
            running += value


def _title_of(slide: dict[str, Any]) -> str | None:
    content = slide.get("content")
    if isinstance(content, dict) and isinstance(content.get("title"), str):
        return str(content["title"])
    return None


def semantic_issues(spec: Any, spec_dir: Path) -> list[Issue]:
    issues = Issues(spec)
    slides = slide_list(spec)
    base = slides_path(spec)
    ids: dict[str, int] = {}
    titles: dict[str, int] = {}
    for i, slide in enumerate(slides):
        if not isinstance(slide, dict):
            continue
        p = f"{base}[{i}]"
        stype = slide.get("type")
        raw_content = slide.get("content")
        content: dict[str, Any] = raw_content if isinstance(raw_content, dict) else {}
        has_source = bool(content.get("source"))

        sid = slide.get("id")
        if isinstance(sid, str):
            if sid in ids:
                issues.error(
                    f"{p}.id",
                    f"id '{sid}' is already used by slide {ids[sid] + 1}",
                    "give every slide its own id",
                )
            ids.setdefault(sid, i)

        title = _title_of(slide)
        if title and stype not in ("cover", "back_cover"):
            key = " ".join(title.split()).casefold()
            if key in titles:
                issues.error(
                    f"{p}.content.title",
                    f"the same title as slide {titles[key] + 1}",
                    "disambiguate it (add the segment, the period or 'part 2')",
                )
            titles.setdefault(key, i)

        if isinstance(slide.get("chart"), dict):
            _chart_issues(slide["chart"], f"{p}.chart", issues)
        if isinstance(slide.get("table"), dict):
            _table_issues(slide["table"], f"{p}.table", issues)
        if isinstance(slide.get("image"), dict):
            _check_image(slide["image"].get("path"), f"{p}.image.path", spec_dir, issues)
        for key in ("cards", "steps"):
            for c, item in enumerate(slide.get(key) or []):
                if isinstance(item, dict) and "icon" in item:
                    _check_image(item["icon"], f"{p}.{key}[{c}].icon", spec_dir, issues)

        exhibit = False
        if stype == "two_column":
            exhibit = _column_issues(slide, p, spec_dir, issues)
        elif stype == "custom":
            exhibit = _custom_issues(slide, p, spec_dir, has_source, issues)
        if exhibit and not has_source:
            issues.error(
                f"{p}.content.source",
                "the slide holds a chart, table or KPIs and has no source",
                REQUIRED_FIX["source"],
            )
        if stype == "waterfall":
            _waterfall_issues(slide, p, issues)
        if stype == "back_cover" and i != len(slides) - 1:
            issues.error(
                f"{p}.type",
                "the back cover is not the last slide",
                "move it to the end (Standard #19)",
            )

    if slides and isinstance(slides[-1], dict) and slides[-1].get("type") != "back_cover":
        issues.error(
            f"{base}[{len(slides) - 1}]",
            "the deck does not end with a back cover",
            "add '- type: back_cover' as the last slide (Standard #19)",
        )
    if slides and isinstance(slides[0], dict) and slides[0].get("type") != "cover":
        issues.warning(
            f"{base}[0].type", "the deck does not open with a cover", "add a cover first"
        )
    return issues.items


# ---------------------------------------------------------------- entry point


def check_file(spec_path: Path | str) -> Report:
    """Load, normalise, schema-check and semantically check a spec file."""
    path = Path(spec_path).expanduser().resolve()
    report = Report(path)
    data, load_issues = load_yaml(path)
    report.issues += load_issues
    if load_issues:
        return report
    spec, norm_issues = normalise(data)
    report.issues += norm_issues
    if not isinstance(spec, dict):
        return report
    report.spec = spec
    report.issues += schema_issues(spec)
    report.issues += semantic_issues(spec, path.parent)
    return report
