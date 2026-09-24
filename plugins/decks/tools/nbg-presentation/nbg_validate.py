#!/usr/bin/env python3
"""NBG brand validator: the gate every .pptx passes before the decks plugin ships it.

Usage:
    nbg_validate.py <deck.pptx> [--format text|json] [--strict]
    nbg_validate.py --list-checks [--format text|json]

Normally run through the launcher, which owns the Python environment:
    bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" validate <deck.pptx> --format json

Exit codes (a contract with nbg_build.py and presentation-qa):
    0  no check failed; warnings and skipped checks may be present
    1  at least one check failed (with --strict, also a skipped universal check or a
       SmartArt diagram with no drawing part to read)
    2  the validator could not run: missing file, not a pptx, missing dependency

Every brand value comes from shared/brand-system/tokens.yaml through nbg_tokens.py;
this file holds rules, never a second copy of the brand. VALIDATOR.md, next to this
file, is the check inventory: rule, source Standard, severity, and what each check
counts as a candidate. `--list-checks` prints the same table from the registry at
the bottom of this file, which is the one place a check is declared.

Two properties hold for every check, because the failure they prevent recurred:
  - "examined" counts the candidates the check actually inspected, on failure as
    well as on success. A check that passes having examined nothing reports
    "skipped", never "pass": a gate that cannot tell "found nothing" from "did not
    look" is worse than no gate, because a human stops looking.
  - Slides are numbered by their position in the deck (p:sldIdLst), not by the
    slideN.xml file name, which a reordered deck no longer matches.
"""

from __future__ import annotations

import argparse
import colorsys
import copy
import hashlib
import io
import json
import math
import os
import posixpath
import re
import struct
import sys
import unicodedata
import zipfile
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import defusedxml.ElementTree as ET  # noqa: N817

    # nbg_tokens, nbg_color and nbg_package sit one level up, shared with nbg_build and
    # nbg-keynote.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import nbg_package
    import nbg_tokens
    from nbg_color import contrast_ratio, min_ratio
    from nbg_package import MAX_XML_PART_BYTES, MAX_XML_RATIO, MAX_XML_TOTAL_BYTES
except ImportError as exc:  # exit 2, not 1: a missing module is not a brand violation
    if __name__ != "__main__":
        raise
    print(
        f"nbg_validate: cannot run, a dependency is missing: {exc}.\n"
        'Run it through the launcher, which builds its environment: bash "${CLAUDE_PLUGIN_ROOT}'
        '/bin/decks-py" validate <deck.pptx>',
        file=sys.stderr,
    )
    sys.exit(2)

# ------------------------------------------------------------------ namespaces

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "dsp": "http://schemas.microsoft.com/office/drawing/2008/diagram",
}
A = "{" + NS["a"] + "}"
P = "{" + NS["p"] + "}"
R = "{" + NS["r"] + "}"
C = "{" + NS["c"] + "}"
MC = "{" + NS["mc"] + "}"
REL = "{" + NS["rel"] + "}"
DGM = "{" + NS["dgm"] + "}"
DSP = "{" + NS["dsp"] + "}"

EMU = 914400
POS_TOL = 0.05  # inches: placement tolerance for geometry matches
GUTTER_TOL = 0.01  # inches: Standard #15 says the gutter is exactly 0.374
INSET_TOL = 0.02  # inches: a text box margin below this is zero
HEADER_BAND = 1.2  # inches: a content title starts above this (title zone plus slack)
STATEMENT_MIN_PT = 40  # cover titles run 44-48pt and divider titles 48pt; content titles 24pt
TITLE_MIN_PT = 20  # a header-band title is at least this size
SUBTITLE_MAX_H = 0.5
SUBTITLE_MAX_GAP = 0.35
MIN_TITLE_GAP = 0.15  # inches between a title's bottom and the first body element
CLOSING_MAX_WORDS = 12

# Written as code points: a repository hook refuses literal em dashes in any file.
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)
DOUBLE_HYPHEN = " -- "  # typed for an em dash, so held to the same rule
_APOSTROPHES = str.maketrans({chr(0x2019): "'", chr(0x02BC): "'", chr(0x00B4): "'"})


def _local(tag: Any) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def fold(text: str) -> str:
    """Accent- and case-folded text: 'Ευχαριστούμε' -> 'ευχαριστουμε', 'ΠΗΓΗ:' -> 'πηγη:'.

    casefold() also turns the Greek final sigma into σ, so every pattern matched
    against folded text spells sigma as σ.
    """
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", kept).casefold().translate(_APOSTROPHES)


def _snippet(text: str, n: int = 50) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 3] + "..."


def _words(text: str) -> int:
    return len(re.findall(r"\w+", text))


# ----------------------------------------------------------------- the brand


@dataclass(frozen=True)
class Brand:
    """Everything the checks read from tokens.yaml, resolved once per process."""

    slide_w_emu: int
    slide_h_emu: int
    slide_w: float
    slide_h: float
    gutter: float
    right: float
    footer_top: float
    body_top: float
    body_bottom: float
    title_zone_bottom: float
    logo_small: tuple[float, float, float, float]
    logo_large: tuple[float, float, float, float]
    logo_back: tuple[float, float, float, float]
    logo_aspect: float
    page_number: tuple[float, float, float, float]
    min_font: float
    pill_font: float
    source_font: float
    title_max_chars: int
    max_series: int
    max_series_absolute: int
    muted: str
    fonts_allowed: tuple[str, ...]
    theme_fonts: tuple[str, ...]
    forbidden_weights: tuple[str, ...]
    peer_banks: dict[str, str]
    marker_symbol: str
    marker_fill: str


def _box4(node: dict[str, Any]) -> tuple[float, float, float, float]:
    return float(node["x"]), float(node["y"]), float(node["w"]), float(node["h"])


@lru_cache(maxsize=1)
def brand() -> Brand:
    g = nbg_tokens.get("geometry")
    return Brand(
        slide_w_emu=int(g["slide"]["w_emu"]),
        slide_h_emu=int(g["slide"]["h_emu"]),
        slide_w=float(g["slide"]["w"]),
        slide_h=float(g["slide"]["h"]),
        gutter=float(g["gutter"]),
        right=float(g["right_boundary"]),
        footer_top=float(g["footer_top"]),
        body_top=float(g["body_top"]),
        body_bottom=float(g["body_bottom"]),
        title_zone_bottom=float(g["title_zone_bottom"]),
        logo_small=_box4(g["logo_small"]),
        logo_large=_box4(g["logo_large"]),
        logo_back=_box4(g["logo_back"]),
        logo_aspect=float(g["logo_aspect"]),
        page_number=_box4(g["page_number"]),
        min_font=float(nbg_tokens.get("accessibility.min_font_pt")),
        pill_font=float(nbg_tokens.get("accessibility.pill_font_pt")),
        source_font=float(
            max(nbg_tokens.get("type.source.size"), nbg_tokens.get("type.footnote.size"))
        ),
        title_max_chars=int(nbg_tokens.get("type.title.max_chars")),
        max_series=int(nbg_tokens.get("charts.max_series")),
        max_series_absolute=int(nbg_tokens.get("charts.max_series_absolute")),
        muted=nbg_tokens.color("muted_grey"),
        fonts_allowed=tuple(nbg_tokens.get("fonts.allowed")),
        theme_fonts=(nbg_tokens.get("fonts.primary"), nbg_tokens.get("fonts.display")),
        forbidden_weights=tuple(nbg_tokens.get("fonts.forbidden_weights")),
        peer_banks={
            k: str(v).upper() for k, v in nbg_tokens.get("extended_palettes.peer_banks").items()
        },
        marker_symbol=str(nbg_tokens.get("charts.line.marker")),
        marker_fill=nbg_tokens.color(str(nbg_tokens.get("charts.line.marker_fill"))),
    )


@lru_cache(maxsize=1)
def allowed_colors() -> frozenset[str]:
    """Every hex tokens.yaml documents, retired colours excluded (nbg_tokens decides)."""
    return frozenset(nbg_tokens.allowed_colors())


@lru_cache(maxsize=1)
def retired_colors() -> dict[str, str]:
    return {str(k): str(v) for k, v in nbg_tokens.retired_colors().items()}


def _color_verdict(hex_: str) -> str | None:
    """Why a colour is off-brand, or None when it is allowed."""
    if hex_ in retired_colors():
        return f"is retired: {retired_colors()[hex_]}"
    if hex_ not in allowed_colors():
        return "is not in the NBG palette (tokens.yaml)"
    return None


ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"


@lru_cache(maxsize=16)
def _asset_hash(name: str) -> str | None:
    path = ASSETS_DIR / name
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


# ------------------------------------------------------------------ results


@dataclass(frozen=True)
class Finding:
    """One thing to fix. `slide` is the position in the deck, None for deck-level."""

    slide: int | None
    message: str
    severity: str = "error"

    def text(self) -> str:
        return f"Slide {self.slide}: {self.message}" if self.slide is not None else self.message


class ValidationResult:
    """One check's outcome.

    `examined` is how many candidates the check inspected, set on failure too. A
    result that passed with `examined == 0` is "skipped": honest, but evidence of
    nothing. `severity` is the check's declared severity; a result carrying any
    error finding is an error, one carrying only warning findings is a warning, and
    a warning reports without blocking. `details` renders the findings as
    "Slide N: ..." lines, ordered by slide.
    """

    def __init__(
        self,
        name: str,
        passed: bool,
        message: str,
        details: list[str] | None = None,
        examined: int | None = None,
        severity: str = "error",
        findings: list[Finding] | None = None,
        not_examined: dict[str, int] | None = None,
    ):
        self.name = name
        self.passed = passed
        self.message = message
        self.examined = examined
        self.declared_severity = severity
        if findings is None:
            findings = [Finding(None, d, severity) for d in details or []]
        # Stable: findings on one slide keep the order the check found them in.
        self.findings = sorted(findings, key=lambda f: (f.slide is None, f.slide or 0))
        self.not_examined = dict(not_examined or {})

    @property
    def details(self) -> list[str]:
        return [f.text() for f in self.findings]

    @property
    def severity(self) -> str:
        if self.findings:
            return "error" if any(f.severity == "error" for f in self.findings) else "warning"
        return self.declared_severity

    @property
    def skipped(self) -> bool:
        return self.passed and self.examined == 0

    @property
    def warned(self) -> bool:
        return not self.passed and self.severity == "warning"

    @property
    def status(self) -> str:
        if self.passed:
            return "skipped" if self.examined == 0 else "pass"
        return "warn" if self.severity == "warning" else "fail"


class Collector:
    """What a check fills in; run_check turns it into a ValidationResult."""

    def __init__(self, severity: str):
        self.severity = severity
        self.findings: list[Finding] = []
        self.examined = 0
        self.not_examined: Counter[str] = Counter()
        self._seen: set[tuple[Any, ...]] = set()

    def add(self, slide: int | None, message: str, severity: str | None = None) -> None:
        key = (slide, message, severity)
        if key in self._seen:
            return
        self._seen.add(key)
        self.findings.append(Finding(slide, message, severity or self.severity))

    def count(self, n: int = 1) -> None:
        self.examined += n

    def skip(self, reason: str, n: int = 1) -> None:
        self.not_examined[reason] += n


# ------------------------------------------------------------------ package

# Content the validator cannot see at all; --strict fails a deck that has any.
SMARTART_UNREAD = "SmartArt diagram with no drawing part"

# The package limits live in tools/nbg_package.py, shared with extract and render.
# The validator also hashes every picture it checks, so it caps the whole package too.
MAX_TOTAL_BYTES = 1024 * 1024 * 1024


class DeckError(Exception):
    """The file cannot be validated at all (exit 2)."""


class Package:
    """Reads members straight from the zip, with size limits, never extracting.

    /redesign-deck and /polish-slides open decks somebody else made, so the input is
    untrusted: the shared pre-flight (nbg_package.check_package) bounds every member
    before anything is inflated, every part parsed as XML is checked again whatever
    its name, and XML is parsed with defusedxml.
    """

    def __init__(self, path: Path):
        try:
            nbg_package.check_package(path)
        except nbg_package.PackageError as e:
            raise DeckError(f"{path}: {e}") from e
        try:
            self._zip = zipfile.ZipFile(path)
        except (zipfile.BadZipFile, OSError) as e:
            raise DeckError(f"{path}: not a .pptx ({e})") from e
        infos = self._zip.infolist()
        if sum(i.file_size for i in infos) > MAX_TOTAL_BYTES:
            raise DeckError(f"{path}: over {MAX_TOTAL_BYTES // 2**20} MiB uncompressed")
        self._info = {i.filename: i for i in infos}
        self._xml: dict[str, Any] = {}
        self._xml_bytes = 0
        self._rels: dict[str, dict[str, tuple[str, str | None]]] = {}

    def close(self) -> None:
        self._zip.close()

    def has(self, name: str | None) -> bool:
        return bool(name) and name in self._info

    def read(self, name: str) -> bytes:
        return self._zip.read(name)  # the pre-flight bounded every member's size

    def xml(self, name: str | None) -> Any:
        """The parsed part. The pre-flight skips members named as media, so every part
        parsed as XML, whatever its name or size, is held to the XML caps and the
        compression-ratio test again before it is inflated."""
        if not name or not self.has(name):
            return None
        if name not in self._xml:
            info = self._info[name]
            if info.file_size > MAX_XML_PART_BYTES:
                raise DeckError(
                    f"{name} is {info.file_size} bytes of XML, over {MAX_XML_PART_BYTES // 2**20} MiB for one part"
                )
            if info.compress_size and info.file_size / info.compress_size > MAX_XML_RATIO:
                raise DeckError(f"{name}: compression ratio suggests a zip bomb")
            self._xml_bytes += info.file_size
            if self._xml_bytes > MAX_XML_TOTAL_BYTES:
                raise DeckError(
                    f"{name}: over {MAX_XML_TOTAL_BYTES // 2**20} MiB of XML in the package"
                )
            try:
                self._xml[name] = ET.fromstring(self.read(name))
            except ET.ParseError as e:
                raise DeckError(f"{name}: malformed XML ({e})") from e
        return self._xml[name]

    def rels(self, part: str | None) -> dict[str, tuple[str, str | None]]:
        """rId -> (relationship type, resolved part name or None when external)."""
        if not part:
            return {}
        if part in self._rels:
            return self._rels[part]
        folder, base = posixpath.split(part)
        root = self.xml(posixpath.join(folder, "_rels", base + ".rels"))
        out: dict[str, tuple[str, str | None]] = {}
        if root is not None:
            for rel in root.findall(f"{REL}Relationship"):
                target = rel.get("Target", "")
                rtype = rel.get("Type", "").rsplit("/", 1)[-1]
                if rel.get("TargetMode") == "External":
                    out[rel.get("Id", "")] = (rtype, None)
                elif target.startswith("/"):
                    out[rel.get("Id", "")] = (rtype, target.lstrip("/"))
                else:
                    out[rel.get("Id", "")] = (
                        rtype,
                        posixpath.normpath(posixpath.join(folder, target)),
                    )
        self._rels[part] = out
        return out

    def related(self, part: str | None, rtype: str) -> str | None:
        for kind, target in self.rels(part).values():
            if kind == rtype and target:
                return target
        return None


# ------------------------------------------------------------------ colours

_FILL_TAGS = ("noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill")
_CLR_TAGS = ("srgbClr", "schemeClr", "sysClr", "prstClr", "scrgbClr", "hslClr")
_PRESET_COLORS = {
    "black": "000000",
    "white": "FFFFFF",
    "red": "FF0000",
    "green": "008000",
    "blue": "0000FF",
    "yellow": "FFFF00",
    "gray": "808080",
    "grey": "808080",
    "orange": "FFA500",
    "navy": "000080",
    "cyan": "00FFFF",
    "magenta": "FF00FF",
}
_PRESET_SHORT = (("dk", "dark"), ("lt", "light"), ("med", "medium"))


@lru_cache(maxsize=256)
def _preset_color(name: str) -> str | None:
    """An a:prstClr name: the CSS colour names, with the dk, lt and med short forms
    DrawingML adds ("dkGreen" is CSS darkgreen)."""
    if name in _PRESET_COLORS:
        return _PRESET_COLORS[name]
    try:
        from PIL import ImageColor
    except ImportError:
        return None
    key = name.lower()
    for short, full in _PRESET_SHORT:
        if key not in ImageColor.colormap and key.startswith(short):
            key = full + key[len(short) :]
    if key not in ImageColor.colormap:
        return None
    return "".join(f"{v:02X}" for v in ImageColor.getrgb(key)[:3])


_DEFAULT_CLR_MAP = {
    "bg1": "lt1",
    "tx1": "dk1",
    "bg2": "lt2",
    "tx2": "dk2",
    **{f"accent{i}": f"accent{i}" for i in range(1, 7)},
    "hlink": "hlink",
    "folHlink": "folHlink",
}
_THEME_SLOTS = (
    "dk1",
    "lt1",
    "dk2",
    "lt2",
    *(f"accent{i}" for i in range(1, 7)),
    "hlink",
    "folHlink",
)


def _linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gamma(c: float) -> float:
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _apply_modifiers(hex_: str, el: Any) -> str:
    """Apply lumMod/lumOff/tint/shade in document order. Alpha changes no hex. PowerPoint
    mixes tint and shade in linear light, so a 40% tint of 4F81BD is D0D8E8, not the
    B9CDE5 an sRGB mix gives."""
    r, g, b = (int(hex_[i : i + 2], 16) / 255 for i in (0, 2, 4))
    for mod in el:
        tag = _local(mod.tag)
        try:
            val = int(mod.get("val", "100000")) / 100000
        except ValueError:
            continue
        if tag in ("lumMod", "lumOff"):
            h, lum, s = colorsys.rgb_to_hls(r, g, b)
            lum = lum * val if tag == "lumMod" else lum + val
            r, g, b = colorsys.hls_to_rgb(h, min(1.0, max(0.0, lum)), s)
        elif tag == "tint":
            r, g, b = (_gamma(_linear(c) * val + 1 - val) for c in (r, g, b))
        elif tag == "shade":
            r, g, b = (_gamma(_linear(c) * val) for c in (r, g, b))
    return "".join(f"{round(min(1.0, max(0.0, c)) * 255):02X}" for c in (r, g, b))


@dataclass
class Theme:
    part: str | None = None
    colors: dict[str, str] = field(default_factory=dict)
    major: str | None = None
    minor: str | None = None
    effect_styles: list[Any] = field(default_factory=list)
    bg_fill_styles: list[Any] = field(default_factory=list)


def _parse_theme(root: Any, part: str | None) -> Theme:
    theme = Theme(part=part)
    if root is None:
        return theme
    scheme = root.find(f".//{A}clrScheme")
    if scheme is not None:
        for slot in scheme:
            name = _local(slot.tag)
            for clr in slot:
                tag = _local(clr.tag)
                if tag == "srgbClr":
                    theme.colors[name] = clr.get("val", "").upper()
                elif tag == "sysClr":
                    theme.colors[name] = (clr.get("lastClr") or "").upper()
    fonts = root.find(f".//{A}fontScheme")
    if fonts is not None:
        major = fonts.find(f"{A}majorFont/{A}latin")
        minor = fonts.find(f"{A}minorFont/{A}latin")
        theme.major = major.get("typeface") if major is not None else None
        theme.minor = minor.get("typeface") if minor is not None else None
    effects = root.find(f".//{A}effectStyleLst")
    theme.effect_styles = list(effects) if effects is not None else []
    bg = root.find(f".//{A}bgFillStyleLst")
    theme.bg_fill_styles = list(bg) if bg is not None else []
    return theme


@dataclass
class ColorContext:
    theme: Theme
    clr_map: dict[str, str]

    def resolve(self, el: Any, ph_color: str | None = None) -> str | None:
        """Hex for one colour-choice element, through the theme and clrMap."""
        tag = _local(el.tag)
        base: str | None = None
        if tag == "srgbClr":
            base = (el.get("val") or "").upper()
        elif tag == "sysClr":
            base = (
                el.get("lastClr")
                or {"windowText": "000000", "window": "FFFFFF"}.get(el.get("val", ""), "")
            ).upper()
        elif tag == "schemeClr":
            val = el.get("val", "")
            if val == "phClr":
                base = ph_color
            else:
                base = self.theme.colors.get(self.clr_map.get(val, val))
        elif tag == "prstClr":
            base = _preset_color(el.get("val", ""))
        elif tag == "hslClr":
            try:  # hue in 60000ths of a degree; saturation and luminance in 1000ths of a percent
                hls = (
                    int(el.get("hue", "0")) / 21600000 % 1.0,
                    min(1.0, max(0.0, int(el.get("lum", "0")) / 100000)),
                    min(1.0, max(0.0, int(el.get("sat", "0")) / 100000)),
                )
            except ValueError:
                base = None
            else:
                base = "".join(f"{round(c * 255):02X}" for c in colorsys.hls_to_rgb(*hls))
        elif tag == "scrgbClr":
            try:
                base = "".join(
                    f"{round(min(100000, max(0, int(el.get(k, '0')))) / 100000 * 255):02X}"
                    for k in ("r", "g", "b")
                )
            except ValueError:
                base = None
        if not base or not re.fullmatch(r"[0-9A-F]{6}", base):
            return None
        return _apply_modifiers(base, el) if len(el) else base

    def first(self, parent: Any, ph_color: str | None = None) -> str | None:
        """The resolved colour of the first colour child of `parent`."""
        if parent is None:
            return None
        for child in parent:
            if _local(child.tag) in _CLR_TAGS:
                return self.resolve(child, ph_color)
        return None

    def describe(self, el: Any) -> str:
        tag = _local(el.tag)
        if tag == "schemeClr":
            return f"theme colour {el.get('val')}"
        return ""


def _fill_child(parent: Any) -> Any:
    if parent is None:
        return None
    for child in parent:
        if _local(child.tag) in _FILL_TAGS:
            return child
    return None


# ------------------------------------------------------------------ the deck

_SHAPE_TAGS = ("sp", "pic", "graphicFrame", "cxnSp", "grpSp")


@dataclass
class _Xform:
    ox: float = 0.0
    oy: float = 0.0
    sx: float = 1.0
    sy: float = 1.0

    def apply(self, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
        return self.ox + x * self.sx, self.oy + y * self.sy, w * self.sx, h * self.sy

    def child(self, xfrm: Any) -> _Xform:
        """The transform for a group's children, from the group's a:xfrm."""
        off, ext = xfrm.find(f"{A}off"), xfrm.find(f"{A}ext")
        ch_off, ch_ext = xfrm.find(f"{A}chOff"), xfrm.find(f"{A}chExt")
        if off is None or ext is None or ch_off is None or ch_ext is None:
            return self
        gx, gy = int(off.get("x", 0)), int(off.get("y", 0))
        gw, gh = int(ext.get("cx", 0)), int(ext.get("cy", 0))
        cx, cy = int(ch_off.get("x", 0)), int(ch_off.get("y", 0))
        cw, chh = int(ch_ext.get("cx", 0)), int(ch_ext.get("cy", 0))
        sx = gw / cw if cw else 1.0
        sy = gh / chh if chh else 1.0
        return _Xform(
            ox=self.ox + (gx - cx * sx) * self.sx,
            oy=self.oy + (gy - cy * sy) * self.sy,
            sx=self.sx * sx,
            sy=self.sy * sy,
        )


@dataclass(eq=False)
class Shape:
    kind: str
    el: Any
    z: int
    x: float | None
    y: float | None
    w: float | None
    h: float | None
    rot: float
    name: str
    ph_type: str | None
    ph_idx: str | None
    depth: int
    layout_ph: Any = None
    master_ph: Any = None
    part: str | None = None  # the layout or master that owns an inherited shape
    parent: Shape | None = None  # the group a shape sits in

    @property
    def has_box(self) -> bool:
        return None not in (self.x, self.y, self.w, self.h)

    @property
    def right(self) -> float:
        return (self.x or 0.0) + (self.w or 0.0)

    @property
    def bottom(self) -> float:
        return (self.y or 0.0) + (self.h or 0.0)

    @property
    def is_placeholder(self) -> bool:
        return self.ph_type is not None or self.ph_idx is not None

    @property
    def sp_pr(self) -> Any:
        return self.el.find(f"{P}grpSpPr" if self.kind == "grpSp" else f"{P}spPr")

    @property
    def tx_body(self) -> Any:
        return self.el.find(f"{P}txBody")

    @property
    def c_nv_pr(self) -> Any:
        for child in self.el:
            if _local(child.tag).startswith("nv"):
                return child.find(f"{P}cNvPr")
        return None

    @property
    def prst(self) -> str | None:
        sp_pr = self.sp_pr
        geom = sp_pr.find(f"{A}prstGeom") if sp_pr is not None else None
        return geom.get("prst") if geom is not None else None

    @property
    def is_table(self) -> bool:
        return self.kind == "graphicFrame" and self.el.find(f".//{A}tbl") is not None

    @property
    def chart_rid(self) -> str | None:
        ref = self.el.find(f".//{C}chart")
        return ref.get(f"{R}id") if ref is not None else None

    def contains(self, px: float, py: float) -> bool:
        return self.has_box and self.x <= px <= self.right and self.y <= py <= self.bottom  # type: ignore[operator]


def _xfrm_of(el: Any, kind: str) -> Any:
    if kind == "graphicFrame":
        return el.find(f"{P}xfrm")
    holder = el.find(f"{P}grpSpPr" if kind == "grpSp" else f"{P}spPr")
    return holder.find(f"{A}xfrm") if holder is not None else None


def _nv_parts(el: Any) -> tuple[str, str | None, str | None]:
    name, ph_type, ph_idx = "", None, None
    for child in el:
        if _local(child.tag).startswith("nv"):
            c_nv = child.find(f"{P}cNvPr")
            if c_nv is not None:
                name = c_nv.get("name", "")
            ph = child.find(f"{P}nvPr/{P}ph")
            if ph is not None:
                ph_type = ph.get("type", "obj")
                ph_idx = ph.get("idx")
    return name, ph_type, ph_idx


def _flatten(
    tree: Any, xf: _Xform, depth: int, out: list[Shape], parent: Shape | None = None
) -> list[Shape]:
    for child in tree:
        tag = _local(child.tag)
        if tag == "AlternateContent":
            branch = child.find(f"{MC}Fallback")
            if branch is None:
                branch = child.find(f"{MC}Choice")
            if branch is not None:
                _flatten(branch, xf, depth, out, parent)
            continue
        if tag not in _SHAPE_TAGS:
            continue
        xfrm = _xfrm_of(child, tag)
        x = y = w = h = None
        rot = 0.0
        if xfrm is not None:
            off, ext = xfrm.find(f"{A}off"), xfrm.find(f"{A}ext")
            if off is not None and ext is not None:
                ex, ey, ew, eh = xf.apply(
                    int(off.get("x", 0)),
                    int(off.get("y", 0)),
                    int(ext.get("cx", 0)),
                    int(ext.get("cy", 0)),
                )
                x, y, w, h = ex / EMU, ey / EMU, ew / EMU, eh / EMU
            rot = int(xfrm.get("rot", "0") or 0) / 60000
        name, ph_type, ph_idx = _nv_parts(child)
        shape = Shape(tag, child, len(out), x, y, w, h, rot, name, ph_type, ph_idx, depth)
        shape.parent = parent
        out.append(shape)
        if tag == "grpSp":
            _flatten(child, xf.child(xfrm) if xfrm is not None else xf, depth + 1, out, shape)
    return out


def _group_fill(shape: Shape) -> Any:
    """The fill an a:grpFill stands for: the nearest enclosing group's own fill (a group
    whose fill is itself grpFill defers to its parent). None when no group sets one."""
    group = shape.parent
    while group is not None:
        fill = _fill_child(group.el.find(f"{P}grpSpPr"))
        if fill is not None and _local(fill.tag) != "grpFill":
            return fill
        group = group.parent
    return None


_TITLE_TYPES = ("title", "ctrTitle")


def _ph_family(ph_type: str | None) -> str:
    if ph_type in _TITLE_TYPES:
        return "title"
    if ph_type in ("dt", "ftr", "sldNum", "sldImg", "hdr"):
        return ph_type or "obj"
    return "body"


def _find_ph(root: Any, ph_type: str | None, ph_idx: str | None, *, by_idx: bool) -> Any:
    if root is None:
        return None
    tree = root.find(f"{P}cSld/{P}spTree")
    if tree is None:
        return None
    candidates = []
    for sp in tree.iter(f"{P}sp"):
        _, t, i = _nv_parts(sp)
        if t is not None or i is not None:
            candidates.append((t, i, sp))
    if by_idx and ph_idx is not None:
        for _t, i, sp in candidates:
            if i == ph_idx:
                return sp
    family = _ph_family(ph_type)
    for t, _i, sp in candidates:
        if _ph_family(t) == family:
            return sp
    return None


def _as_presentationml(tree: Any) -> Any:
    """A copy of a SmartArt drawing's shape tree with dsp: renamed to p:. dsp:sp, dsp:spPr,
    dsp:style and dsp:txBody mirror their p: counterparts, so the slide code reads them."""
    tree = copy.deepcopy(tree)
    for el in tree.iter():
        if isinstance(el.tag, str) and el.tag.startswith(DSP):
            el.tag = P + el.tag[len(DSP) :]
    return tree


def _shows_master_shapes(root: Any) -> bool:
    return root is not None and root.get("showMasterSp", "1") not in ("0", "false")


@dataclass
class Chart:
    part: str
    root: Any
    slide: Slide
    frame: Shape

    @property
    def stem(self) -> str:
        return posixpath.splitext(posixpath.basename(self.part))[0]


class Slide:
    def __init__(self, deck: Deck, position: int, part: str):
        pkg = deck.pkg
        self.deck = deck
        self.position = position
        self.part = part
        self.root = pkg.xml(part)
        self.layout_part = pkg.related(part, "slideLayout")
        self.layout = pkg.xml(self.layout_part)
        self.master_part = pkg.related(self.layout_part, "slideMaster")
        self.master = pkg.xml(self.master_part)
        self.theme = deck.theme(pkg.related(self.master_part, "theme"))
        clr_map = dict(_DEFAULT_CLR_MAP)
        master_map = self.master.find(f"{P}clrMap") if self.master is not None else None
        if master_map is not None:
            clr_map.update(master_map.attrib)
        for holder in (self.layout, self.root):
            override = (
                holder.find(f"{P}clrMapOvr/{A}overrideClrMapping") if holder is not None else None
            )
            if override is not None:
                clr_map.update(override.attrib)
        self.ctx = ColorContext(self.theme, clr_map)
        tree = self.root.find(f"{P}cSld/{P}spTree") if self.root is not None else None
        self.shapes: list[Shape] = _flatten(tree, _Xform(), 0, []) if tree is not None else []
        for shape in self.shapes:
            if shape.is_placeholder:
                self._inherit_placeholder(shape)
        self.inherited = self._background_graphics()
        self.diagram_shapes, self.unread_diagrams = self._diagrams()
        self._frames: dict[int, Frame | None] = {}

    def _diagrams(self) -> tuple[list[Shape], int]:
        """The shapes of each SmartArt diagram's drawing part (what PowerPoint shows),
        placed at the diagram's frame, and how many diagrams have no drawing part. The
        drawing is found through the data part's dsp:dataModelExt, whose relId is a
        relationship of the slide."""
        pkg = self.deck.pkg
        rels = pkg.rels(self.part)
        shapes: list[Shape] = []
        unread = 0
        for frame in self.shapes:
            ids = frame.el.find(f".//{DGM}relIds") if frame.kind == "graphicFrame" else None
            if ids is None:
                continue
            data = pkg.xml(rels.get(ids.get(f"{R}dm", ""), ("", None))[1])
            ext = data.find(f".//{DSP}dataModelExt") if data is not None else None
            part = rels.get(ext.get("relId", ""), ("", None))[1] if ext is not None else None
            drawing = pkg.xml(part)
            tree = drawing.find(f"{DSP}spTree") if drawing is not None else None
            if tree is None:
                unread += 1
                continue
            origin = _Xform(ox=(frame.x or 0.0) * EMU, oy=(frame.y or 0.0) * EMU)
            for shape in _flatten(_as_presentationml(tree), origin, 0, []):
                shape.part = part
                shape.name = shape.name or f"{frame.name} (SmartArt)"
                shapes.append(shape)
        return shapes, unread

    def _background_graphics(self) -> list[Shape]:
        """The layout's and master's non-placeholder shapes this slide renders, master
        first. showMasterSp="0" on the slide (Hide Background Graphics) hides both; on
        the layout it hides the master's."""
        if not _shows_master_shapes(self.root):
            return []
        owners = [(self.layout, self.layout_part)]
        if _shows_master_shapes(self.layout):
            owners.insert(0, (self.master, self.master_part))
        out: list[Shape] = []
        for root, part in owners:
            tree = root.find(f"{P}cSld/{P}spTree") if root is not None else None
            if tree is None:
                continue
            for shape in _flatten(tree, _Xform(), 0, []):
                if not shape.is_placeholder:
                    shape.part = part
                    out.append(shape)
        return out

    def _inherit_placeholder(self, shape: Shape) -> None:
        shape.layout_ph = _find_ph(self.layout, shape.ph_type, shape.ph_idx, by_idx=True)
        shape.master_ph = _find_ph(self.master, shape.ph_type, shape.ph_idx, by_idx=False)
        if shape.has_box:
            return
        for inherited in (shape.layout_ph, shape.master_ph):
            if inherited is None:
                continue
            xfrm = _xfrm_of(inherited, "sp")
            if xfrm is None:
                continue
            off, ext = xfrm.find(f"{A}off"), xfrm.find(f"{A}ext")
            if off is None or ext is None:
                continue
            shape.x, shape.y = int(off.get("x", 0)) / EMU, int(off.get("y", 0)) / EMU
            shape.w, shape.h = int(ext.get("cx", 0)) / EMU, int(ext.get("cy", 0)) / EMU
            return

    def frame(self, shape: Shape) -> Frame | None:
        key = id(shape.el)
        if key not in self._frames:
            self._frames[key] = _shape_frame(self, shape)
        return self._frames[key]

    def text_shapes(self) -> Iterator[tuple[Shape, Frame]]:
        for shape in self.shapes:
            if shape.kind != "sp":
                continue
            frame = self.frame(shape)
            if frame is not None and frame.text.strip():
                yield shape, frame

    def all_text(self) -> str:
        return " ".join(t for t in _slide_texts(self))

    def image_part(self, shape: Shape) -> str | None:
        blip = shape.el.find(f".//{A}blip")
        rid = blip.get(f"{R}embed") if blip is not None else None
        if not rid:
            return None
        return self.deck.pkg.rels(shape.part or self.part).get(rid, ("", None))[1]

    def chart_part(self, shape: Shape) -> str | None:
        rid = shape.chart_rid
        owner = shape.part or self.part
        return self.deck.pkg.rels(owner).get(rid, ("", None))[1] if rid else None


class Deck:
    """A parsed presentation: slides in presentation order, themes, charts, media."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        if not self.path.exists():
            raise DeckError(f"presentation not found: {self.path}")
        self.pkg = Package(self.path)
        self.presentation = self.pkg.xml("ppt/presentation.xml")
        if self.presentation is None:
            raise DeckError(f"{self.path}: no ppt/presentation.xml, so not a PowerPoint deck")
        self.default_text_style = self.presentation.find(f"{P}defaultTextStyle")
        self._themes: dict[str | None, Theme] = {}
        self._charts: list[Chart] | None = None
        self._media: dict[str, tuple[str, tuple[int, int] | None]] = {}
        self._table_styles: dict[str, Any] = {}
        self.missing_slides: list[str] = []
        self.measurer = TextMeasurer()
        self.slides = self._load_slides()

    def close(self) -> None:
        self.pkg.close()

    def _load_slides(self) -> list[Slide]:
        rels = self.pkg.rels("ppt/presentation.xml")
        lst = self.presentation.find(f"{P}sldIdLst")
        slides: list[Slide] = []
        for sld_id in lst if lst is not None else []:
            rid = sld_id.get(f"{R}id", "")
            part = rels.get(rid, ("", None))[1]
            if not part or not self.pkg.has(part):
                self.missing_slides.append(rid)
                continue
            slides.append(Slide(self, len(slides) + 1, part))
        return slides

    def table_style(self, style_id: str | None) -> Any:
        """The a:tblStyle a table names: the deck's own definition in ppt/tableStyles.xml,
        else a built-in style known by its GUID. No id means the list's default style
        (tblStyleLst/@def). None when the style cannot be found."""
        styles = self.pkg.xml(self.pkg.related("ppt/presentation.xml", "tableStyles"))
        key = (style_id or (styles.get("def", "") if styles is not None else "")).strip().upper()
        if key not in self._table_styles:
            found = next(
                (
                    style
                    for style in (styles.findall(f"{A}tblStyle") if styles is not None else [])
                    if (style.get("styleId") or "").strip().upper() == key
                ),
                None,
            )
            if found is None and key in _BUILTIN_TABLE_STYLES:
                found = ET.fromstring(
                    f'<a:tblStyle xmlns:a="{NS["a"]}">{_BUILTIN_TABLE_STYLES[key]}</a:tblStyle>'
                )
            self._table_styles[key] = found
        return self._table_styles[key]

    def theme(self, part: str | None) -> Theme:
        if part not in self._themes:
            self._themes[part] = _parse_theme(self.pkg.xml(part), part)
        return self._themes[part]

    def themes(self) -> list[Theme]:
        """Every theme a slide master uses, whether or not a slide uses the master."""
        out: dict[str | None, Theme] = {}
        rels = self.pkg.rels("ppt/presentation.xml")
        masters = self.presentation.find(f"{P}sldMasterIdLst")
        for entry in masters if masters is not None else []:
            master = rels.get(entry.get(f"{R}id", ""), ("", None))[1]
            part = self.pkg.related(master, "theme")
            if part and part not in out:
                out[part] = self.theme(part)
        for s in self.slides:
            if s.theme.part and s.theme.part not in out:
                out[s.theme.part] = s.theme
        return list(out.values())

    def charts(self) -> list[Chart]:
        if self._charts is None:
            seen: dict[str, Chart] = {}
            for s in self.slides:
                for shape in s.shapes:
                    part = s.chart_part(shape) if shape.kind == "graphicFrame" else None
                    if part and part not in seen and self.pkg.has(part):
                        seen[part] = Chart(part, self.pkg.xml(part), s, shape)
            self._charts = list(seen.values())
        return self._charts

    def media(self, part: str) -> tuple[str, tuple[int, int] | None]:
        """(sha256, pixel size) of an image part."""
        if part not in self._media:
            data = self.pkg.read(part) if self.pkg.has(part) else b""
            self._media[part] = (hashlib.sha256(data).hexdigest(), _image_size(data))
        return self._media[part]


@contextmanager
def load_deck(path: str | Path) -> Iterator[Deck]:
    deck = Deck(path)
    try:
        yield deck
    finally:
        deck.close()


def _image_size(data: bytes) -> tuple[int, int] | None:
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return int(width), int(height)
    try:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as image:
            return int(image.size[0]), int(image.size[1])
    except Exception:
        return None


# ------------------------------------------------------------------ text model


@dataclass
class Run:
    text: str
    size: float | None  # points, after any autofit scaling
    bold: bool
    color: str | None
    color_explicit: bool
    typeface: str | None


@dataclass
class Para:
    runs: list[Run]
    level: int = 1
    mar_l: float = 0.0
    indent: float = 0.0
    align: str = "l"
    line_pct: float | None = None
    line_pts: float | None = None
    space_before: tuple[str, float] | None = None
    space_after: tuple[str, float] | None = None
    end_size: float | None = None

    @property
    def text(self) -> str:
        return "".join(r.text for r in self.runs)

    @property
    def size(self) -> float | None:
        sizes = [r.size for r in self.runs if r.size and r.text.strip()]
        return max(sizes) if sizes else self.end_size


@dataclass
class Frame:
    paragraphs: list[Para]
    l_ins: float = 0.1
    t_ins: float = 0.05
    r_ins: float = 0.1
    b_ins: float = 0.05
    wrap: bool = True
    anchor: str = "t"
    autofit: str = "none"
    vertical: bool = False

    @property
    def text(self) -> str:
        return "\n".join(p.text for p in self.paragraphs)

    def runs(self) -> Iterator[Run]:
        for p in self.paragraphs:
            yield from p.runs

    def max_size(self) -> float | None:
        sizes = [r.size for r in self.runs() if r.size and r.text.strip()]
        return max(sizes) if sizes else None

    def bold(self) -> bool:
        return any(r.bold for r in self.runs() if r.text.strip())


class _Props:
    """One level of run properties: an a:rPr/a:defRPr, or a p:style fontRef."""

    __slots__ = ("bold", "fill", "latin", "size")

    size: str | None
    bold: str | None
    fill: Any
    latin: str | None

    def __init__(self, el: Any, *, font_ref: bool = False):
        if font_ref:
            self.size = None
            self.bold = None
            self.fill = el  # the fontRef itself holds the colour child
            idx = el.get("idx", "minor")
            self.latin = "+mj-lt" if idx == "major" else "+mn-lt"
            return
        self.size = el.get("sz")
        self.bold = el.get("b")
        self.fill = _fill_child(el)
        latin = el.find(f"{A}latin")
        self.latin = latin.get("typeface") if latin is not None and latin.get("typeface") else None


def _lvl(container: Any, level: int) -> Any:
    return container.find(f"{A}lvl{level}pPr") if container is not None else None


def _typeface(name: str | None, theme: Theme) -> str | None:
    if not name:
        return None
    if name.startswith("+mn"):
        return theme.minor
    if name.startswith("+mj"):
        return theme.major
    return name


def _spacing(el: Any) -> tuple[str, float] | None:
    if el is None:
        return None
    pct, pts = el.find(f"{A}spcPct"), el.find(f"{A}spcPts")
    try:
        if pts is not None:
            return "pts", int(pts.get("val", "0")) / 100
        if pct is not None:
            return "pct", int(pct.get("val", "0")) / 100000
    except ValueError:
        return None
    return None


def _build_frame(
    tx_body: Any,
    ctx: ColorContext,
    level_sources: Callable[[int], list[Any]],
    body_chain: list[Any],
    font_ref: Any = None,
    insets_default: tuple[int, int, int, int] = (91440, 45720, 91440, 45720),
) -> Frame:
    """Resolve every paragraph and run of a txBody through its inheritance chain."""
    theme = ctx.theme

    def body_attr(name: str) -> str | None:
        for body in body_chain:
            if body is not None and body.get(name) is not None:
                return str(body.get(name))
        return None

    autofit, font_scale, spacing_cut = "none", 1.0, 0.0
    for body in body_chain:
        if body is None:
            continue
        found = False
        for tag in ("noAutofit", "normAutofit", "spAutoFit"):
            node = body.find(f"{A}{tag}")
            if node is not None:
                autofit = {"noAutofit": "none", "normAutofit": "norm", "spAutoFit": "shape"}[tag]
                if tag == "normAutofit":
                    font_scale = int(node.get("fontScale", "100000")) / 100000
                    spacing_cut = int(node.get("lnSpcReduction", "0")) / 100000
                found = True
                break
        if found:
            break

    def inset(name: str, default: int) -> float:
        value = body_attr(name)
        try:
            return (int(value) if value is not None else default) / EMU
        except ValueError:
            return default / EMU

    frame = Frame(
        paragraphs=[],
        l_ins=inset("lIns", insets_default[0]),
        t_ins=inset("tIns", insets_default[1]),
        r_ins=inset("rIns", insets_default[2]),
        b_ins=inset("bIns", insets_default[3]),
        wrap=body_attr("wrap") != "none",
        anchor=body_attr("anchor") or "t",
        autofit=autofit,
        vertical=(body_attr("vert") or "horz") not in ("horz", ""),
    )
    lst_style = tx_body.find(f"{A}lstStyle")
    for p in tx_body.findall(f"{A}p"):
        p_pr = p.find(f"{A}pPr")
        level = (
            int(p_pr.get("lvl", "0")) + 1
            if p_pr is not None and p_pr.get("lvl", "0").isdigit()
            else 1
        )
        ppr_chain = [p_pr, _lvl(lst_style, level), *level_sources(level)]
        ppr_chain = [x for x in ppr_chain if x is not None]

        def ppr_attr(name: str, chain: list[Any] = ppr_chain) -> str | None:
            for node in chain:
                if node.get(name) is not None:
                    return str(node.get(name))
            return None

        def ppr_child(name: str, chain: list[Any] = ppr_chain) -> Any:
            for node in chain:
                child = node.find(f"{A}{name}")
                if child is not None:
                    return child
            return None

        run_defaults = [
            _Props(node.find(f"{A}defRPr"))
            for node in ppr_chain
            if node.find(f"{A}defRPr") is not None
        ]
        if font_ref is not None:
            # A shape's p:style fontRef outranks everything the shape inherits and yields
            # only to its own paragraph and list-style defaults, however many of those
            # exist (none, typically, for text typed into a PowerPoint shape).
            own = sum(
                1
                for node in (p_pr, _lvl(lst_style, level))
                if node is not None and node.find(f"{A}defRPr") is not None
            )
            run_defaults.insert(own, _Props(font_ref, font_ref=True))
        para = Para(runs=[], level=level)
        try:
            para.mar_l = int(ppr_attr("marL") or 0) / EMU
            para.indent = int(ppr_attr("indent") or 0) / EMU
        except ValueError:
            pass
        para.align = ppr_attr("algn") or "l"
        line = _spacing(ppr_child("lnSpc"))
        if line is not None:
            if line[0] == "pct":
                para.line_pct = line[1] * (1 - spacing_cut)
            else:
                para.line_pts = line[1]
        elif spacing_cut:
            para.line_pct = 1 - spacing_cut
        para.space_before = _spacing(ppr_child("spcBef"))
        para.space_after = _spacing(ppr_child("spcAft"))

        def resolve(
            props: list[_Props], explicit: _Props | None
        ) -> tuple[float | None, bool, str | None, bool, str | None]:
            chain = ([explicit] if explicit is not None else []) + props
            size = next((pr.size for pr in chain if pr.size), None)
            bold = next((pr.bold for pr in chain if pr.bold is not None), None)
            color, color_explicit = None, False
            for i, pr in enumerate(chain):
                if pr.fill is None:
                    continue
                tag = _local(pr.fill.tag)
                if tag in ("solidFill", "fontRef"):
                    color = ctx.first(pr.fill)
                color_explicit = explicit is not None and i == 0
                break
            latin = next((pr.latin for pr in chain if pr.latin), None)
            pt = int(size) / 100 * font_scale if size and str(size).isdigit() else None
            return pt, bold in ("1", "true"), color, color_explicit, _typeface(latin, theme)

        for child in p:
            tag = _local(child.tag)
            if tag in ("r", "fld"):
                t = child.find(f"{A}t")
                r_pr = child.find(f"{A}rPr")
                size, bold, color, explicit, face = resolve(
                    run_defaults, _Props(r_pr) if r_pr is not None else None
                )
                para.runs.append(
                    Run(t.text or "" if t is not None else "", size, bold, color, explicit, face)
                )
            elif tag == "br":
                para.runs.append(Run("\n", None, False, None, False, None))
        end = p.find(f"{A}endParaRPr")
        para.end_size = resolve(run_defaults, _Props(end) if end is not None else None)[0]
        frame.paragraphs.append(para)
    return frame


def _txstyle(master: Any, name: str) -> Any:
    return master.find(f"{P}txStyles/{P}{name}") if master is not None else None


def _shape_frame(slide: Slide, shape: Shape) -> Frame | None:
    tx = shape.tx_body
    if tx is None:
        return None
    deck = slide.deck
    ph = shape.is_placeholder
    layout_tx = shape.layout_ph.find(f"{P}txBody") if shape.layout_ph is not None else None
    master_tx = shape.master_ph.find(f"{P}txBody") if shape.master_ph is not None else None
    style = None
    if ph:
        style = _txstyle(
            slide.master, "titleStyle" if shape.ph_type in _TITLE_TYPES else "bodyStyle"
        )
    default = deck.default_text_style

    def sources(level: int) -> list[Any]:
        found = []
        if ph:
            found += [
                _lvl(layout_tx.find(f"{A}lstStyle") if layout_tx is not None else None, level),
                _lvl(master_tx.find(f"{A}lstStyle") if master_tx is not None else None, level),
                _lvl(style, level),
            ]
        found += [_lvl(default, level), default.find(f"{A}defPPr") if default is not None else None]
        return [x for x in found if x is not None]

    body_chain = [tx.find(f"{A}bodyPr")]
    if ph:
        body_chain += [
            layout_tx.find(f"{A}bodyPr") if layout_tx is not None else None,
            master_tx.find(f"{A}bodyPr") if master_tx is not None else None,
        ]
    font_ref = None if ph else shape.el.find(f"{P}style/{A}fontRef")
    return _build_frame(tx, slide.ctx, sources, body_chain, font_ref)


def _cell_frame(slide: Slide, tc: Any, look: _CellLook | None = None) -> Frame | None:
    tx = tc.find(f"{A}txBody")
    if tx is None:
        return None
    default = slide.deck.default_text_style
    styled = _style_run_defaults(look)

    def sources(level: int) -> list[Any]:
        found = [
            styled,
            _lvl(default, level),
            default.find(f"{A}defPPr") if default is not None else None,
        ]
        return [x for x in found if x is not None]

    tc_pr = tc.find(f"{A}tcPr")
    margins = [91440, 45720, 91440, 45720]
    if tc_pr is not None:
        for i, name in enumerate(("marL", "marT", "marR", "marB")):
            value = tc_pr.get(name)
            if value is not None and value.lstrip("-").isdigit():
                margins[i] = int(value)
    frame = _build_frame(
        tx, slide.ctx, sources, [None], None, (margins[0], margins[1], margins[2], margins[3])
    )
    frame.anchor = (tc_pr.get("anchor") if tc_pr is not None else None) or "t"
    return frame


def _slide_texts(slide: Slide) -> Iterator[str]:
    """The text of each shape and each table cell, separately."""
    for shape in slide.shapes:
        if shape.kind == "sp":
            frame = slide.frame(shape)
            if frame is not None and frame.text.strip():
                yield " ".join(frame.text.split())
        elif shape.is_table:
            for tc in shape.el.iter(f"{A}tc"):
                text = " ".join((t.text or "") for t in tc.iter(f"{A}t"))
                if text.strip():
                    yield " ".join(text.split())


def _slide_paragraphs(slide: Slide) -> Iterator[str]:
    """Each paragraph and each table cell on its own: a year closing one bullet must
    not read as the amount of a currency marker opening the next."""
    for shape in slide.shapes:
        if shape.kind == "sp":
            frame = slide.frame(shape)
            for para in frame.paragraphs if frame is not None else []:
                if para.text.strip():
                    yield para.text
        elif shape.is_table:
            for tc in shape.el.iter(f"{A}tc"):
                for p in tc.iter(f"{A}p"):
                    text = "".join((t.text or "") for t in p.iter(f"{A}t"))
                    if text.strip():
                        yield text


def _cells(shape: Shape) -> Iterator[Any]:
    yield from shape.el.iter(f"{A}tc")


# A cell takes its fill and text colour from the table's style unless it sets its own.
# PowerPoint writes each style a deck uses into ppt/tableStyles.xml; python-pptx names a
# built-in style by GUID alone, so those styles are spelled out here, copied from
# PowerPoint's own definitions (borders left out: no check reads them).
TABLE_STYLE_UNREAD = "table cell coloured by a table style the validator does not know"
_TABLE_FLAGS = ("firstRow", "lastRow", "firstCol", "lastCol", "bandRow", "bandCol")
_PLAIN_TABLE = (
    '<a:wholeTbl><a:tcTxStyle><a:schemeClr val="tx1"/></a:tcTxStyle>'
    "<a:tcStyle><a:fill><a:noFill/></a:fill></a:tcStyle></a:wholeTbl>"
)
_ACCENT_1 = '<a:solidFill><a:schemeClr val="accent1"/></a:solidFill>'
_MEDIUM_2_ACCENT_1 = (
    '<a:wholeTbl><a:tcTxStyle><a:schemeClr val="dk1"/></a:tcTxStyle><a:tcStyle><a:fill>'
    '<a:solidFill><a:schemeClr val="accent1"><a:tint val="20000"/></a:schemeClr></a:solidFill>'
    "</a:fill></a:tcStyle></a:wholeTbl>"
    + "".join(
        f"<a:{band}><a:tcStyle><a:fill><a:solidFill>"
        '<a:schemeClr val="accent1"><a:tint val="40000"/></a:schemeClr>'
        f"</a:solidFill></a:fill></a:tcStyle></a:{band}>"
        for band in ("band1H", "band1V")
    )
    + "".join(
        f'<a:{part}><a:tcTxStyle b="on"><a:schemeClr val="lt1"/></a:tcTxStyle>'
        f"<a:tcStyle><a:fill>{_ACCENT_1}</a:fill></a:tcStyle></a:{part}>"
        for part in ("lastCol", "firstCol", "lastRow", "firstRow")
    )
)
_BUILTIN_TABLE_STYLES = {
    "{2D5ABB26-0587-4C30-8999-92F81FD0307C}": _PLAIN_TABLE,  # No Style, No Grid
    "{5940675A-B579-460E-94D1-54222C63F5DA}": _PLAIN_TABLE,  # No Style, Table Grid
    "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}": _MEDIUM_2_ACCENT_1,  # the default table
}


def _style_parts(flags: set[str], r: int, c: int, *, rows: int, cols: int) -> list[str]:
    """The table-style parts that reach cell (r, c), in the order PowerPoint layers them:
    whole table, banded rows, banded columns, first and last column, first and last row,
    corner cells. Banding skips a header or total row and restarts after the header."""
    first_row = "firstRow" in flags and r == 0
    last_row = "lastRow" in flags and r == rows - 1
    first_col = "firstCol" in flags and c == 0
    last_col = "lastCol" in flags and c == cols - 1
    parts = ["wholeTbl"]
    if "bandRow" in flags and not (first_row or last_row):
        row = r - (1 if "firstRow" in flags else 0)
        parts.append("band1H" if row % 2 == 0 else "band2H")
    if "bandCol" in flags and not (first_col or last_col):
        col = c - (1 if "firstCol" in flags else 0)
        parts.append("band1V" if col % 2 == 0 else "band2V")
    edges = (
        ("firstCol", first_col),
        ("lastCol", last_col),
        ("firstRow", first_row),
        ("lastRow", last_row),
        ("seCell", last_row and last_col),
        ("swCell", last_row and first_col),
        ("neCell", first_row and last_col),
        ("nwCell", first_row and first_col),
    )
    return parts + [name for name, applies in edges if applies]


@dataclass(frozen=True)
class _CellLook:
    """What a table style gives one cell. fill: ("solid", hex), ("none", None) or
    ("other", None), or None when no part sets one; text colour and weight likewise."""

    fill: tuple[str, str | None] | None = None
    text: str | None = None
    bold: bool | None = None


def _cell_look(ctx: ColorContext, style: Any, parts: list[str]) -> _CellLook:
    fill: tuple[str, str | None] | None = None
    text: str | None = None
    bold: bool | None = None
    for name in parts:
        part = style.find(f"{A}{name}")
        if part is None:
            continue
        tc_style = part.find(f"{A}tcStyle")
        node = _fill_child(tc_style.find(f"{A}fill")) if tc_style is not None else None
        ref = tc_style.find(f"{A}fillRef") if tc_style is not None else None
        if node is not None:
            kind = _local(node.tag)
            fill = (
                ("solid", ctx.first(node))
                if kind == "solidFill"
                else ("none", None)
                if kind == "noFill"
                else ("other", None)
            )
        elif ref is not None:
            fill = ("solid", ctx.first(ref))
        tx = part.find(f"{A}tcTxStyle")
        if tx is not None:
            font_ref = tx.find(f"{A}fontRef")
            text = ctx.first(tx) or (ctx.first(font_ref) if font_ref is not None else None) or text
            if tx.get("b") in ("on", "off"):
                bold = tx.get("b") == "on"
    return _CellLook(fill, text, bold)


def _cell_looks(s: Slide, shape: Shape) -> Iterator[tuple[Any, _CellLook | None]]:
    """Each a:tc a table draws (merged-away cells skipped), with what the table's style
    gives it: None when the table names a style the validator does not know."""
    tbl = shape.el.find(f".//{A}tbl")
    if tbl is None:
        return
    tbl_pr = tbl.find(f"{A}tblPr")
    inline = tbl_pr.find(f"{A}tableStyle") if tbl_pr is not None else None
    id_el = tbl_pr.find(f"{A}tableStyleId") if tbl_pr is not None else None
    style = (
        inline
        if inline is not None
        else s.deck.table_style(id_el.text if id_el is not None else None)
    )
    flags = {f for f in _TABLE_FLAGS if tbl_pr is not None and tbl_pr.get(f) in ("1", "true")}
    rows = tbl.findall(f"{A}tr")
    cols = len(tbl.findall(f"{A}tblGrid/{A}gridCol"))
    for r, tr in enumerate(rows):
        for c, tc in enumerate(tr.findall(f"{A}tc")):
            if tc.get("hMerge") in ("1", "true") or tc.get("vMerge") in ("1", "true"):
                continue
            if style is None:
                yield tc, None
                continue
            parts = _style_parts(flags, r, c, rows=len(rows), cols=cols or len(tr))
            yield tc, _cell_look(s.ctx, style, parts)


def _style_run_defaults(look: _CellLook | None) -> Any:
    """A table style's text colour and weight as a list-style level, so they slot into
    the text chain between the cell's own text and the deck default."""
    if look is None or (look.text is None and look.bold is None):
        return None
    bold = "" if look.bold is None else f' b="{int(look.bold)}"'
    fill = f'<a:solidFill><a:srgbClr val="{look.text}"/></a:solidFill>' if look.text else ""
    return ET.fromstring(
        f'<a:lvl1pPr xmlns:a="{NS["a"]}"><a:defRPr{bold}>{fill}</a:defRPr></a:lvl1pPr>'
    )


def _table_style_colors(s: Slide, shape: Shape) -> Iterator[tuple[str, str | None] | None]:
    """(role, hex) for each colour a table's style actually paints: a fill where the cell
    sets none, a text colour where a run sets none. None for a cell whose colours would
    come from a style the validator does not know."""
    for tc, look in _cell_looks(s, shape):
        own_fill = _fill_child(tc.find(f"{A}tcPr")) is not None
        cell = _cell_frame(s, tc, look)
        plain = [
            r for r in (cell.runs() if cell else []) if r.text.strip() and not r.color_explicit
        ]
        if look is None:
            if not own_fill or plain:
                yield None
            continue
        if not own_fill and look.fill is not None and look.fill[0] == "solid":
            yield "fill from its table style", look.fill[1]
        if look.text and any(r.color == look.text for r in plain):
            yield "text colour from its table style", look.text


# ------------------------------------------------------------ measuring text

# Aptos advance widths in font units per 1000 em, regular and bold, read from
# Aptos.ttf / Aptos-Bold.ttf with Pillow's basic layout (no kerning, which only
# narrows text, so the table errs wide). Order: printable ASCII 0x20-0x7E, Greek
# 0x0386-0x03CE without the three unassigned code points, then _WIDTH_EXTRA.
_WIDTH_EXTRA = (
    0x20AC, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026,
    0x00AB, 0x00BB, 0x00B0, 0x00B7, 0x00D7, 0x00B1, 0x2264, 0x2265, 0x2192,
)  # fmt: skip
_WIDTH_CHARS = (
    "".join(chr(c) for c in range(0x20, 0x7F))
    + "".join(chr(c) for c in range(0x0386, 0x03CF) if c not in (0x038B, 0x038D, 0x03A2))
    + "".join(chr(c) for c in _WIDTH_EXTRA)
)
_APTOS_REGULAR = (
    "203,293,370,537,534,826,643,210,293,293,457,534,286,340,286,339,534,534,534,534,534,534,534,"
    "534,534,534,286,286,534,534,534,501,895,589,604,692,686,556,524,709,707,260,331,568,500,790,"
    "706,732,577,732,606,566,479,681,585,892,553,540,516,294,339,294,534,460,552,531,561,525,561,"
    "527,301,484,551,239,239,487,260,853,551,552,561,561,334,486,323,559,452,721,442,452,438,294,"
    "270,294,534,589,287,556,707,260,732,540,734,261,589,604,464,590,556,516,707,732,260,568,585,"
    "790,706,563,732,697,577,500,479,540,734,553,767,734,260,540,564,496,551,261,565,564,546,452,"
    "552,496,416,551,549,261,487,452,563,452,415,552,584,561,428,580,425,565,671,460,702,800,261,"
    "565,552,565,800,534,460,920,270,270,452,453,470,818,416,416,365,286,534,534,534,534,600"
)
_APTOS_BOLD = (
    "203,293,420,537,534,841,677,232,293,293,457,534,300,340,300,387,534,534,534,534,534,534,534,"
    "534,534,534,300,300,534,534,534,518,900,620,619,707,707,573,537,718,729,294,367,623,512,821,"
    "723,737,605,737,634,598,505,696,617,940,599,586,547,337,387,337,534,460,552,552,586,549,586,"
    "556,335,511,579,268,268,534,296,889,579,573,586,586,369,516,355,582,494,761,495,494,466,337,"
    "270,337,534,620,300,573,729,294,737,586,744,296,620,619,485,626,573,547,729,737,294,623,617,"
    "821,723,586,737,719,605,528,505,586,795,599,835,744,294,586,595,523,579,296,586,595,570,494,"
    "573,523,455,579,582,296,534,494,585,494,450,573,603,586,465,599,443,586,731,509,770,851,296,"
    "586,573,586,851,534,460,920,298,298,519,520,488,850,445,445,378,300,534,534,534,534,600"
)
_TABLE = {
    False: dict(zip(_WIDTH_CHARS, (int(v) for v in _APTOS_REGULAR.split(",")), strict=True)),
    True: dict(zip(_WIDTH_CHARS, (int(v) for v in _APTOS_BOLD.split(",")), strict=True)),
}
_UNKNOWN_WIDTH = {False: 560, True: 590}  # wider than the average letter, on purpose
APTOS_LINE = 1.221  # (ascender 939 + descender 282) / 1000, from the Aptos hhea table
PILLOW_SCALE = 20  # Pillow measures at 20 pixels per point

_FONT_FILES = {
    ("aptos", False): ("aptos.ttf",),
    ("aptos", True): ("aptos-bold.ttf", "aptosbold.ttf", "aptos_bold.ttf"),
    ("aptos display", False): ("aptos-display.ttf", "aptosdisplay.ttf", "aptos display.ttf"),
    ("aptos display", True): ("aptos-display-bold.ttf", "aptosdisplay-bold.ttf"),
    ("calibri", False): ("calibri.ttf",),
    ("calibri", True): ("calibrib.ttf", "calibri bold.ttf"),
    ("arial", False): ("arial.ttf",),
    ("arial", True): ("arialbd.ttf", "arial bold.ttf"),
    ("tahoma", False): ("tahoma.ttf",),
    ("tahoma", True): ("tahomabd.ttf", "tahoma bold.ttf"),
}
FONT_DIRS_ENV = "DECKS_FONT_DIRS"


def font_search_dirs() -> list[Path]:
    """Where Aptos is looked for. DECKS_FONT_DIRS (os.pathsep-separated) replaces the list.

    Office for Mac keeps its fonts inside each app bundle (Contents/Resources/DFonts)
    and in a cloud-font cache with hashed file names; Windows keeps per-user fonts
    under LOCALAPPDATA. A colleague rarely has Aptos in ~/Library/Fonts.
    """
    override = os.environ.get(FONT_DIRS_ENV)
    if override is not None:
        return [Path(p) for p in override.split(os.pathsep) if p]
    home = Path.home()
    dirs = [home / "Library" / "Fonts", Path("/Library/Fonts")]
    for app in ("Microsoft PowerPoint", "Microsoft Word", "Microsoft Excel", "Microsoft Outlook"):
        dirs.append(Path("/Applications") / f"{app}.app" / "Contents" / "Resources" / "DFonts")
    dirs.append(
        home
        / "Library"
        / "Group Containers"
        / "UBF8T346G9.Office"
        / "FontCache"
        / "4"
        / "CloudFonts"
    )
    windir = os.environ.get("WINDIR") or "C:\\Windows"
    dirs.append(Path(windir) / "Fonts")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
        dirs.append(Path(local) / "Microsoft" / "FontCache" / "4" / "CloudFonts")
    dirs += [home / ".fonts", home / ".local" / "share" / "fonts", Path("/usr/share/fonts")]
    return dirs


@lru_cache(maxsize=32)
def _find_font(family: str, bold: bool, dirs: tuple[str, ...]) -> str | None:
    wanted = _FONT_FILES.get((family.lower(), bold))
    if not wanted:
        return None
    for folder in dirs:
        base = Path(folder)
        try:
            if not base.is_dir():
                continue
            names = {p.name.lower(): p for p in base.iterdir() if p.is_file()}
        except OSError:
            continue
        for name in wanted:
            if name in names:
                return str(names[name])
        if base.name == "CloudFonts":  # hashed names: match on the name table
            hit = _cloud_font(base, family, bold)
            if hit:
                return hit
    return None


def _cloud_font(base: Path, family: str, bold: bool) -> str | None:
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    style = "bold" if bold else "regular"
    for i, path in enumerate(base.rglob("*.tt[fc]")):
        if i > 400:
            break
        try:
            name, sub = ImageFont.truetype(str(path), 10).getname()
        except Exception:
            continue
        if (name or "").lower() == family.lower() and (sub or "").lower() == style:
            return str(path)
    return None


@lru_cache(maxsize=16)
def _font_bytes(path: str) -> bytes:
    return Path(path).read_bytes()


@lru_cache(maxsize=64)
def _pillow_font(path: str, px: int) -> Any:
    from PIL import ImageFont

    # From bytes, not the path: given a path it cannot load, Pillow quietly searches
    # the system font folders for a file of the same name and measures with that.
    return ImageFont.truetype(
        io.BytesIO(_font_bytes(path)), px, layout_engine=ImageFont.Layout.BASIC
    )


def reset_font_cache() -> None:
    """Forget discovered fonts, e.g. after DECKS_FONT_DIRS changes (tests)."""
    _find_font.cache_clear()
    _font_bytes.cache_clear()
    _pillow_font.cache_clear()


class TextMeasurer:
    """Widths and line heights in points: Pillow with Aptos when found, else the table."""

    def __init__(self) -> None:
        self._dirs = tuple(str(d) for d in font_search_dirs())
        self._broken: set[str] = set()
        self.font_path = self._path("Aptos", False)
        if self.font_path and self._font(self.font_path, 10) is None:
            self.font_path = None
        if self.font_path:
            self.source = f"Aptos ({self.font_path})"
        else:
            self.source = (
                "the Aptos width table (no loadable Aptos font found; widths are Aptos advances)"
            )

    def _path(self, family: str, bold: bool) -> str | None:
        path = _find_font(family, bold, self._dirs)
        return None if path in self._broken else path

    def _font(self, path: str, size_pt: float) -> Any:
        try:
            return _pillow_font(path, max(1, int(round(size_pt * PILLOW_SCALE))))
        except Exception:
            self._broken.add(path)
            return None

    def width(
        self, text: str, size_pt: float, *, bold: bool = False, family: str | None = "Aptos"
    ) -> float:
        if not text:
            return 0.0
        fam = (family or "Aptos").strip()
        path = self._path(fam, bold) or (
            self._path("Aptos", bold) if fam.lower().startswith("aptos") else None
        )
        if path and self.font_path:
            font = self._font(path, size_pt)
            if font is not None:
                return float(font.getlength(text)) / PILLOW_SCALE
        table = _TABLE[bold]
        unknown = _UNKNOWN_WIDTH[bold]
        return sum(table.get(ch, unknown) for ch in text) * size_pt / 1000

    def line_height(self, size_pt: float, family: str | None = "Aptos") -> float:
        return size_pt * APTOS_LINE


@dataclass
class TextLayout:
    height: float  # inches, insets included
    width: float  # widest line, inches, insets excluded
    lines: list[int]
    top_line: float  # height of the first line, inches


def _paragraph_lines(para: Para, avail: float, wrap: bool, m: TextMeasurer) -> tuple[int, float]:
    """(lines, widest line in points) for one paragraph laid out in `avail` points."""
    default = para.size or 18.0
    segments: list[list[tuple[float, float]]] = [[]]  # per hard line: [(word, space after)]
    current = 0.0
    has_word = False
    for run in para.runs:
        if run.text == "\n":
            if has_word:
                segments[-1].append((current, 0.0))
            current, has_word = 0.0, False
            segments.append([])
            continue
        size = run.size or default
        for piece in re.split(r"(\s+)", run.text):
            if not piece:
                continue
            if piece.isspace():
                if has_word:
                    segments[-1].append((current, 0.0))
                    current, has_word = 0.0, False
                if segments[-1]:
                    w, s = segments[-1][-1]
                    segments[-1][-1] = (
                        w,
                        s
                        + m.width(
                            piece.replace("\t", "    "), size, bold=run.bold, family=run.typeface
                        ),
                    )
            else:
                current += m.width(piece, size, bold=run.bold, family=run.typeface)
                has_word = True
    if has_word:
        segments[-1].append((current, 0.0))
    lines = 0
    widest = 0.0
    for words in segments:
        if not words:
            lines += 1
            continue
        if not wrap or avail <= 0:
            total = sum(w + s for w, s in words) - words[-1][1]
            lines += 1
            widest = max(widest, total)
            continue
        line_w, pending, count = 0.0, 0.0, 1
        for w, s in words:
            if line_w <= 0.0:  # nothing on this line yet
                if w > avail:
                    extra = math.ceil(w / avail) - 1
                    count += extra
                    line_w = w - extra * avail
                    widest = max(widest, avail)
                else:
                    line_w = w
            elif line_w + pending + w <= avail + 0.01:
                line_w += pending + w
            else:
                widest = max(widest, line_w)
                count += 1
                if w > avail:
                    extra = math.ceil(w / avail) - 1
                    count += extra
                    line_w = w - extra * avail
                else:
                    line_w = w
            pending = s
        widest = max(widest, line_w)
        lines += count
    return lines, widest


def layout_text(frame: Frame, box_w: float, m: TextMeasurer) -> TextLayout:
    """Height and width a frame's text needs when wrapped at `box_w` inches."""
    total = frame.t_ins + frame.b_ins
    widest = 0.0
    counts: list[int] = []
    top_line = 0.0
    for i, para in enumerate(frame.paragraphs):
        size = para.size or 18.0
        family = next((r.typeface for r in para.runs if r.typeface), "Aptos")
        single = m.line_height(size, family)
        if para.line_pts is not None:
            line_h = para.line_pts
        else:
            line_h = single * (para.line_pct if para.line_pct is not None else 1.0)
        avail_in = box_w - frame.l_ins - frame.r_ins - para.mar_l
        lines, width = _paragraph_lines(para, avail_in * 72, frame.wrap, m)
        counts.append(lines)
        widest = max(widest, width / 72 + para.mar_l)
        height = lines * line_h
        if i > 0 and para.space_before:
            kind, value = para.space_before
            height += value if kind == "pts" else value * single
        if i < len(frame.paragraphs) - 1 and para.space_after:
            kind, value = para.space_after
            height += value if kind == "pts" else value * single
        total += height / 72
        if i == 0:
            top_line = line_h / 72
    return TextLayout(total, widest, counts, top_line)


# ------------------------------------------------------------------ titles

_SECTION_NUMBER = re.compile(r"^\d{1,3}\.?$")


@dataclass
class Title:
    shape: Shape
    frame: Frame
    text: str
    size: float
    kind: str  # "placeholder", "header" or "statement"
    is_content: bool  # an action title on a body slide, not a cover or divider title

    @property
    def text_left(self) -> float:
        return (self.shape.x or 0.0) + self.frame.l_ins


# Layout types whose title placeholder is a cover or section title, not an action title.
_STATEMENT_LAYOUTS = ("title", "secHead")


def _explicit_size(tx_body: Any) -> bool:
    """True when the slide's own text body sets a font size anywhere."""
    if tx_body is None:
        return False
    return any(el.get("sz") for el in tx_body.iter() if _local(el.tag) in ("rPr", "defRPr"))


def find_title(slide: Slide) -> Title | None:
    """The one title definition every title check uses.

    1. A title placeholder (p:ph type title or ctrTitle), resolved through its layout.
    2. Otherwise the largest text of 20pt or more whose top sits in the header band
       (y < 1.2"): content titles, the contents header, the 22pt Key Figures title.
    3. Otherwise the largest text of 40pt or more in the top 3.5": cover and divider
       titles. A bare section number ("01") is a marker, never a title (Standard #3).
    """
    layout_type = slide.layout.get("type") if slide.layout is not None else None
    for shape in slide.shapes:
        if shape.ph_type in _TITLE_TYPES:
            frame = slide.frame(shape)
            if frame is not None and frame.text.strip():
                ph_size = frame.max_size() or 44.0
                # A size written on the slide says what the title is: 24pt is an
                # action title, 48pt a cover or divider title (nbg_build puts a title
                # placeholder on every slide). A size inherited from the template
                # (44pt in the default one) says nothing, so the role is then read
                # from the placeholder type and the layout.
                if _explicit_size(shape.tx_body):
                    content = ph_size < STATEMENT_MIN_PT
                else:
                    content = shape.ph_type == "title" and layout_type not in _STATEMENT_LAYOUTS
                text = " ".join(frame.text.split())
                return Title(shape, frame, text, ph_size, "placeholder", content)
    header: list[tuple[float, float, float, Shape, Frame]] = []
    statement: list[tuple[float, float, float, Shape, Frame]] = []
    for shape, frame in slide.text_shapes():
        text = " ".join(frame.text.split())
        size = frame.max_size()
        if not shape.has_box or size is None or _SECTION_NUMBER.match(text):
            continue
        key = (-size, shape.y or 0.0, shape.x or 0.0, shape, frame)
        if (shape.y or 0.0) < HEADER_BAND and size >= TITLE_MIN_PT:
            header.append(key)
        elif (shape.y or 0.0) <= 3.5 and size >= STATEMENT_MIN_PT:
            statement.append(key)
    for group, kind in ((header, "header"), (statement, "statement")):
        if group:
            group.sort(key=lambda k: (k[0], k[1], k[2]))
            _, _, _, shape, frame = group[0]
            size = frame.max_size() or 0.0
            text = " ".join(frame.text.split())
            return Title(shape, frame, text, size, kind, size < STATEMENT_MIN_PT)
    return None


def _is_cover(deck: Deck, slide: Slide) -> bool:
    """Slide 1 of a multi-slide deck, unless it opens on a content slide: a one-slide
    view (/create-infographic) or a deck without a cover gets no cover rules."""
    if slide.position != 1 or len(deck.slides) < 2:
        return False
    title = find_title(slide)
    return title is None or not title.is_content


# ------------------------------------------------------------- shape helpers


def _spot_match(
    shape: Shape, spot: tuple[float, float, float, float], *, size: bool = True
) -> bool:
    x, y, w, h = spot
    if not shape.has_box:
        return False
    close = abs((shape.x or 0) - x) <= POS_TOL and abs((shape.y or 0) - y) <= POS_TOL
    if not size:
        return close
    return close and abs((shape.w or 0) - w) <= POS_TOL and abs((shape.h or 0) - h) <= POS_TOL


def _is_logo_footprint(shape: Shape) -> bool:
    b = brand()
    return shape.kind == "pic" and any(
        _spot_match(shape, s) for s in (b.logo_small, b.logo_large, b.logo_back)
    )


def _is_page_number(shape: Shape) -> bool:
    x, y, _w, _h = brand().page_number
    return (
        shape.kind == "sp"
        and shape.has_box
        and abs((shape.x or 0) - x) <= 0.1
        and abs((shape.y or 0) - y) <= 0.1
    )


def _is_chrome(shape: Shape) -> bool:
    return _is_logo_footprint(shape) or _is_page_number(shape)


def _fill(slide: Slide, shape: Shape) -> tuple[str, str | None]:
    """("solid", hex) | ("none", None) | ("other", None) for a shape's own fill."""
    if shape.kind not in ("sp", "cxnSp"):
        return ("other", None) if shape.kind == "pic" else ("none", None)
    for holder in (
        shape.sp_pr,
        *(ph.find(f"{P}spPr") for ph in (shape.layout_ph, shape.master_ph) if ph is not None),
    ):
        fill = _fill_child(holder)
        if fill is None:
            continue
        if _local(fill.tag) == "grpFill":
            fill = _group_fill(shape)
            if fill is None:
                return "none", None
        tag = _local(fill.tag)
        if tag == "solidFill":
            return "solid", slide.ctx.first(fill)
        if tag == "noFill":
            return "none", None
        return "other", None
    ref = shape.el.find(f"{P}style/{A}fillRef")
    if ref is not None and ref.get("idx", "0") not in ("0", "1000"):
        return "solid", slide.ctx.first(ref)
    return "none", None


SOURCE_PREFIX = re.compile(r"^\s*(?:sources?|πηγ(?:η|εσ))\s*[:\-" + EN_DASH + "]")
NOTE_PREFIX = re.compile(r"^\s*(?:notes?|σημειωσ(?:η|εισ)|σημ\.|\*|[¹²³])")
# What dates a source: a four-digit year, a slashed or dotted date, or a reporting
# period with a two- or four-digit year, as board packs write them (FY25, FY2025, 1Q26,
# Q2'26, 9M25, 1H2025, H1 '26). A period without a year ("H1", "latest") dates nothing.
# Public: nbg_spec's `check` applies it to source.as_of, so check and this gate agree.
_PERIOD_YEAR = r"\s?['" + chr(0x2019) + r"]?(?:(?:19|20)\d{2}|\d{2})\b"
SOURCE_AS_OF = re.compile(
    r"\b(?:19|20)\d{2}\b"
    r"|\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b"
    rf"|\b(?:FY|CY){_PERIOD_YEAR}"
    rf"|\b[1-4]Q{_PERIOD_YEAR}|\bQ[1-4]{_PERIOD_YEAR}"
    rf"|\b(?:[1-9]|1[0-2])M{_PERIOD_YEAR}"
    rf"|\b[12]H{_PERIOD_YEAR}|\bH[12]{_PERIOD_YEAR}",
    re.IGNORECASE,
)


def _is_source(text: str) -> bool:
    folded = fold(text)
    return bool(SOURCE_PREFIX.match(folded) or NOTE_PREFIX.match(folded))


def _is_pill(slide: Slide, shape: Shape, title: Title | None) -> bool:
    """The header pill: a filled rounded rectangle lying wholly above the title."""
    if shape.prst != "roundRect" or not shape.has_box:
        return False
    kind, _ = _fill(slide, shape)
    if kind != "solid":
        return False
    ceiling = (
        title.shape.y
        if title is not None and title.shape.y is not None
        else brand().title_zone_bottom
    )
    return shape.bottom <= ceiling + 0.02


def _pill_label(slide: Slide, shape: Shape, title: Title | None) -> bool:
    """A text box above the title laid over a pill drawn as a separate shape (VALIDATOR-7)."""
    if not shape.has_box or _is_pill(slide, shape, title):
        return _is_pill(slide, shape, title)
    ceiling = (
        title.shape.y
        if title is not None and title.shape.y is not None
        else brand().title_zone_bottom
    )
    if shape.bottom > ceiling + 0.02:
        return False
    cx, cy = (shape.x or 0) + (shape.w or 0) / 2, (shape.y or 0) + (shape.h or 0) / 2
    return any(
        other.z < shape.z and _is_pill(slide, other, title) and other.contains(cx, cy)
        for other in slide.shapes
    )


def _slide_background(slide: Slide) -> tuple[str, str | None, str]:
    """(kind, hex, where) of the effective background: slide, then layout, then master."""
    for holder, where in (
        (slide.root, "slide"),
        (slide.layout, "layout"),
        (slide.master, "master"),
    ):
        bg = holder.find(f"{P}cSld/{P}bg") if holder is not None else None
        if bg is None:
            continue
        bg_pr = bg.find(f"{P}bgPr")
        if bg_pr is not None:
            fill = _fill_child(bg_pr)
            if fill is None or _local(fill.tag) == "noFill":
                return "solid", "FFFFFF", where
            if _local(fill.tag) == "solidFill":
                return "solid", slide.ctx.first(fill), where
            return _local(fill.tag), None, where
        ref = bg.find(f"{P}bgRef")
        if ref is not None:
            color = slide.ctx.first(ref)
            try:
                idx = int(ref.get("idx", "0"))
            except ValueError:
                idx = 0
            styles = slide.theme.bg_fill_styles
            style = styles[idx - 1001] if idx >= 1001 and idx - 1001 < len(styles) else None
            if style is None or _local(style.tag) == "solidFill":
                inner = slide.ctx.first(style, ph_color=color) if style is not None else None
                return "solid", inner or color, where
            return _local(style.tag), None, where
    return "solid", "FFFFFF", "default"


# ------------------------------------------------------------------ chart helpers

_PLOT_TAGS = (
    "barChart", "bar3DChart", "lineChart", "line3DChart", "areaChart", "area3DChart",
    "pieChart", "pie3DChart", "ofPieChart", "doughnutChart", "radarChart", "scatterChart",
    "bubbleChart", "stockChart", "surfaceChart", "surface3DChart",
)  # fmt: skip
PIE_TAGS = ("pieChart", "pie3DChart", "ofPieChart")
BAR_CHART_TAGS = ("barChart", "bar3DChart")


def _plots(chart: Chart) -> list[Any]:
    area = chart.root.find(f".//{C}plotArea")
    return [p for p in area if _local(p.tag) in _PLOT_TAGS] if area is not None else []


def _series_name(ser: Any) -> str:
    return " ".join(v.text or "" for v in ser.findall(f"{C}tx//{C}v")).strip() or "(unnamed)"


def _categories(ser: Any) -> list[str]:
    cat = ser.find(f"{C}cat")
    if cat is None:
        return []
    points = cat.findall(f".//{C}pt")
    if points:
        ordered = sorted(points, key=lambda pt: int(pt.get("idx", "0")))
        return [(pt.findtext(f"{C}v") or "") for pt in ordered]
    count = cat.find(f".//{C}ptCount")
    return [""] * int(count.get("val", "0")) if count is not None else []


def _chart_texts(chart: Chart) -> Iterator[str]:
    for t in chart.root.iter(f"{A}t"):
        if t.text and t.text.strip():
            yield t.text
    for v in chart.root.iter(f"{C}v"):
        parent_cache = v.text or ""
        if parent_cache.strip() and not re.fullmatch(r"-?[\d.eE+]+", parent_cache.strip()):
            yield parent_cache


# ======================================================================
# Checks. Each fills a Collector and returns its one-line summary.
# ======================================================================


def check_slides(deck: Deck, out: Collector) -> str:
    out.count(len(deck.slides))
    for rid in deck.missing_slides:
        out.add(None, f"slide list entry {rid} points at a part that does not exist")
    if not deck.slides:
        out.add(None, "the deck has no slides")
        return "no slides in the slide list"
    return f"{len(deck.slides)} slide(s) in presentation order"


def check_dimensions(deck: Deck, out: Collector) -> str:
    b = brand()
    size = deck.presentation.find(f"{P}sldSz")
    if size is None:
        out.add(None, "presentation.xml carries no slide size (p:sldSz)")
        return "slide size missing"
    out.count()
    cx, cy = int(size.get("cx", 0)), int(size.get("cy", 0))
    actual = f'{cx / EMU:.3f}" x {cy / EMU:.3f}" ({cx} x {cy} EMU)'
    if abs(cx - b.slide_w_emu) > 635 or abs(cy - b.slide_h_emu) > 635:
        out.add(
            None,
            f'slide size is {actual}; the brand is {b.slide_w}" x {b.slide_h}" '
            f"({b.slide_w_emu} x {b.slide_h_emu} EMU, PowerPoint Widescreen)",
        )
        return f"slide size {actual} is not the brand size"
    return f"{actual}, PowerPoint Widescreen"


def check_theme(deck: Deck, out: Collector) -> str:
    b = brand()
    themes = [t for t in deck.themes() if t.part]
    for theme in themes:
        where = posixpath.basename(theme.part or "theme")
        for slot in _THEME_SLOTS:
            value = theme.colors.get(slot)
            if not value:
                continue
            out.count()
            verdict = _color_verdict(value)
            if verdict:
                out.add(
                    None,
                    f"{where} {slot} #{value} {verdict}; new shapes and automatic chart colours use it",
                )
        for role, face in (("major (headings)", theme.major), ("minor (body)", theme.minor)):
            out.count()
            if face not in b.theme_fonts:
                out.add(
                    None, f"{where} {role} font is {face or 'unset'}; the brand theme font is Aptos"
                )
    if not themes:
        return "no theme part"
    if out.findings:
        return f"{len(out.findings)} theme value(s) are not NBG in {len(themes)} theme(s)"
    return f"{len(themes)} theme(s): NBG colours and Aptos fonts"


def check_background(deck: Deck, out: Collector) -> str:
    for s in deck.slides:
        out.count()
        kind, color, where = _slide_background(s)
        source = {
            "slide": "set on the slide",
            "layout": "inherited from its layout",
            "master": "inherited from its master",
            "default": "default",
        }[where]
        if kind != "solid":
            out.add(
                s.position,
                f"background is a {kind} ({source}); slides are always white (Standard #2)",
            )
        elif color != "FFFFFF":
            out.add(
                s.position,
                f"background is #{color} ({source}); slides are always white (Standard #2)",
            )
    if out.findings:
        return f"{len(out.findings)} of {out.examined} slide(s) not white"
    return f"{out.examined} slide(s), all white"


def _style_ref_colors(slide: Slide, shape: Shape) -> Iterator[tuple[str, str | None]]:
    """Colours a shape takes from its p:style because spPr does not override them."""
    style = shape.el.find(f"{P}style")
    if style is None or shape.kind not in ("sp", "cxnSp"):
        return
    sp_pr = shape.sp_pr
    ln = sp_pr.find(f"{A}ln") if sp_pr is not None else None
    ln_ref = style.find(f"{A}lnRef")
    if ln_ref is not None and ln_ref.get("idx", "0") != "0" and _fill_child(ln) is None:
        yield "outline from its shape style", slide.ctx.first(ln_ref)
    fill_ref = style.find(f"{A}fillRef")
    if (
        shape.kind == "sp"
        and fill_ref is not None
        and fill_ref.get("idx", "0") not in ("0", "1000")
        and _fill_child(sp_pr) is None
    ):
        yield "fill from its shape style", slide.ctx.first(fill_ref)


def _color_elements(root: Any) -> Iterator[Any]:
    """Colour elements outside effects (shadow colours are the Shadows check's job)."""
    stack = [root]
    while stack:
        node = stack.pop()
        for child in node:
            tag = _local(child.tag)
            if tag in ("effectLst", "effectDag", "extLst", "style"):
                continue
            if tag in _CLR_TAGS:
                yield child
                continue
            stack.append(child)


def _judged_shapes(deck: Deck, out: Collector) -> Iterator[tuple[Slide, Shape]]:
    """Each slide's shapes, the shapes of its SmartArt drawings, then the layout and
    master shapes it renders. An inherited shape comes once, with the first slide that
    shows it: a band on the master is one finding, not one per slide. A diagram with no
    drawing part to read is recorded as not examined."""
    seen: set[int] = set()
    for s in deck.slides:
        if s.unread_diagrams:
            out.skip(SMARTART_UNREAD, s.unread_diagrams)
        yield from ((s, shape) for shape in s.shapes)
        yield from ((s, shape) for shape in s.diagram_shapes)
        for shape in s.inherited:
            if id(shape.el) not in seen:
                seen.add(id(shape.el))
                yield s, shape


def _where(shape: Shape) -> str:
    name = f'"{shape.name}"' if shape.name else shape.kind
    return f"{name} on {posixpath.basename(shape.part)}" if shape.part else name


def check_colors(deck: Deck, out: Collector) -> str:
    for s, shape in _judged_shapes(deck, out):
        if shape.kind == "grpSp":
            continue
        where = _where(shape)
        own_fill = _fill_child(shape.sp_pr)
        group_fill = (
            _group_fill(shape)
            if own_fill is not None and _local(own_fill.tag) == "grpFill"
            else None
        )
        for source, role in ((shape.el, ""), (group_fill, "group fill, ")):
            for el in _color_elements(source) if source is not None else ():
                hex_ = s.ctx.resolve(el)
                if hex_ is None:
                    out.skip("unresolvable colour reference")
                    continue
                out.count()
                verdict = _color_verdict(hex_)
                if verdict:
                    via = f" ({s.ctx.describe(el)})" if s.ctx.describe(el) else ""
                    out.add(s.position, f"#{hex_}{via} {verdict} ({role}in {where})")
        for role, hex_ in _style_ref_colors(s, shape):
            if hex_ is None:
                out.skip("unresolvable style colour")
                continue
            out.count()
            verdict = _color_verdict(hex_)
            if verdict:
                out.add(s.position, f"#{hex_} {verdict} ({role}, in {where}); set it explicitly")
        if shape.is_table:
            for painted in _table_style_colors(s, shape):
                if painted is None:
                    out.skip(TABLE_STYLE_UNREAD)
                    continue
                role, hex_ = painted
                if hex_ is None:
                    out.skip("unresolvable table style colour")
                    continue
                out.count()
                verdict = _color_verdict(hex_)
                if verdict:
                    out.add(s.position, f"#{hex_} {verdict} ({role}, in {where})")
    for chart in deck.charts():
        for el in _color_elements(chart.root):
            hex_ = chart.slide.ctx.resolve(el)
            if hex_ is None:
                out.skip("unresolvable chart colour")
                continue
            out.count()
            verdict = _color_verdict(hex_)
            if verdict:
                out.add(chart.slide.position, f"#{hex_} {verdict} (in chart {chart.stem})")
    if out.findings:
        return f"{len(out.findings)} off-palette colour use(s) among {out.examined} colour reference(s)"
    return f"{out.examined} colour reference(s) in slides and charts, all NBG colours"


_FACE_ROLES = {"latin": "text", "sym": "symbol", "buFont": "bullet"}


def _typefaces(root: Any, tags: Iterable[str] = tuple(_FACE_ROLES)) -> Iterator[tuple[str, str]]:
    for tag in tags:
        for el in root.iter(f"{A}{tag}"):
            face = el.get("typeface")
            if face:
                yield face, _FACE_ROLES[tag]


def _shape_runs(s: Slide, shape: Shape) -> Iterator[Run]:
    """The text runs a shape draws: its own text, or each table cell's."""
    if shape.kind == "sp":
        frames = [s.frame(shape)]
    elif shape.is_table:
        frames = [_cell_frame(s, tc, look) for tc, look in _cell_looks(s, shape)]
    else:
        frames = []
    for frame in frames:
        for run in frame.runs() if frame is not None else []:
            if run.text.strip():
                yield run


def check_fonts(deck: Deck, out: Collector) -> str:
    b = brand()
    used: Counter[str] = Counter()

    def judge(position: int | None, face: str, role: str, theme: Theme, where: str) -> None:
        resolved = _typeface(face, theme)
        if not resolved:
            out.skip("theme font reference with no theme font")
            return
        out.count()
        used[resolved] += 1
        if resolved in b.forbidden_weights:
            out.add(
                position,
                f'"{resolved}" is a forbidden weight: NBG text is Aptos Regular or Bold, never SemiBold ({role} in {where})',
            )
        elif resolved not in b.fonts_allowed:
            out.add(
                position,
                f'"{resolved}" is not an NBG font; use {", ".join(b.fonts_allowed)} ({role} in {where})',
            )

    # A run's typeface is its own, else what it inherits (list styles, placeholders, the
    # deck default), else the theme's minor font: the font it is drawn in. Symbol and
    # bullet fonts are read where they are written.
    for s, shape in _judged_shapes(deck, out):
        if shape.kind == "grpSp":
            continue
        where = _where(shape)
        for face, role in _typefaces(shape.el, ("sym", "buFont")):
            judge(s.position, face, role, s.theme, where)
        for run in _shape_runs(s, shape):
            judge(s.position, run.typeface or "+mn-lt", "text", s.theme, where)
    for chart in deck.charts():
        where = f"chart {chart.stem}"
        for face, role in _typefaces(chart.root):
            judge(chart.slide.position, face, role, chart.slide.theme, where)
        top = chart.root.find(f"{C}txPr")
        if top is None or top.find(f".//{A}latin") is None:  # chart text in the theme font
            judge(chart.slide.position, "+mn-lt", "text", chart.slide.theme, f"{where}, theme font")
    if out.findings:
        return f"{len(out.findings)} non-NBG font use(s) among {out.examined} typeface reference(s)"
    return f"{out.examined} typeface reference(s): {', '.join(sorted(used)) or 'no text'}"


def _size_floor(slide: Slide, shape: Shape, frame: Frame, title: Title | None) -> tuple[float, str]:
    """(minimum size, what the text is) for the runs of one shape (Standard #11)."""
    b = brand()
    if _pill_label(slide, shape, title):
        return b.pill_font, "header pill"
    if _is_page_number(shape):
        return b.min_font, "page number"
    text = frame.text.strip()
    if _is_source(text):
        return b.source_font, "source or footnote"
    return b.min_font, "text"


def check_font_sizes(deck: Deck, out: Collector) -> str:
    b = brand()
    sizes: set[float] = set()
    titles: dict[int, Title | None] = {}
    for s, shape in _judged_shapes(deck, out):
        if shape.is_table:
            for tc in _cells(shape):
                cell = _cell_frame(s, tc)
                if cell is None:
                    continue
                for run in cell.runs():
                    if not run.text.strip():
                        continue
                    if run.size is None:
                        out.skip("table text size inherited from a default")
                        continue
                    out.count()
                    sizes.add(run.size)
                    if run.size + 1e-6 < b.min_font:
                        out.add(
                            s.position,
                            f'{run.size:g}pt table text "{_snippet(run.text)}" is below the {b.min_font:g}pt floor (Standard #11)',
                        )
            continue
        frame = s.frame(shape) if shape.kind == "sp" else None
        if frame is None or not frame.text.strip():
            continue
        if s.position not in titles:
            titles[s.position] = find_title(s)
        floor, role = _size_floor(s, shape, frame, titles[s.position])
        for run in frame.runs():
            if not run.text.strip():
                continue
            if run.size is None:
                out.skip("size inherited from a default the validator cannot read")
                continue
            out.count()
            sizes.add(run.size)
            if run.size + 1e-6 < floor:
                if role == "source or footnote":
                    out.add(
                        s.position,
                        f'{run.size:g}pt source or footnote "{_snippet(run.text)}"; sources and footnotes are at least {floor:g}pt (Standard #11)',
                    )
                else:
                    out.add(
                        s.position,
                        f'{run.size:g}pt {role} "{_snippet(run.text)}" is below the {floor:g}pt floor (Standard #11)',
                    )
    for chart in deck.charts():
        for el in list(chart.root.iter(f"{A}defRPr")) + list(chart.root.iter(f"{A}rPr")):
            sz = el.get("sz")
            if not sz or not sz.isdigit():
                continue
            out.count()
            size = int(sz) / 100
            sizes.add(size)
            if size + 1e-6 < b.min_font:
                out.add(
                    chart.slide.position,
                    f"{size:g}pt text in chart {chart.stem} is below the {b.min_font:g}pt floor (Standard #11)",
                )
    used = ", ".join(f"{v:.1f}pt" for v in sorted(sizes))
    if out.findings:
        return f"{len(out.findings)} run(s) below their floor among {out.examined} sized run(s). Sizes used: {used}"
    return f"{out.examined} sized run(s) meet the floors (10pt, 11pt sources, 9pt pill). Sizes used: {used}"


_INSIDE_CHART_TAGS = ("doughnutChart", "pieChart", "pie3DChart", "ofPieChart")
_INSIDE_LABEL_POS = ("ctr", "inEnd", "inBase")


def _background_under(slide: Slide, shape: Shape, slide_bg: str | None) -> tuple[str | None, str]:
    """(hex, where) of what sits behind a text shape: its own fill, then the topmost
    filled shape below it in z-order that contains its centre, then the slide."""
    kind, color = _fill(slide, shape)
    if kind == "solid":
        return color, "own fill"
    if kind == "other":
        return None, "gradient or picture fill"
    if not shape.has_box:
        return slide_bg, "slide"
    cx, cy = (shape.x or 0) + (shape.w or 0) / 2, (shape.y or 0) + (shape.h or 0) / 2
    for other in reversed(slide.shapes[: shape.z]):
        if other.kind not in ("sp", "pic", "graphicFrame") or not other.contains(cx, cy):
            continue
        if other.kind == "pic":
            return None, "text over a picture"
        if other.kind == "graphicFrame":
            continue
        k, c = _fill(slide, other)
        if k == "solid":
            return c, f'"{other.name}"'
        if k == "other":
            return None, "gradient or picture fill underneath"
    return slide_bg, "slide"


def _muted_waived(
    color: str, background: str | None, shape: Shape | None, size: float | None, axis: bool = False
) -> bool:
    """Muted grey on white (2.96:1) is sanctioned for page numbers and muted axis labels
    only (Standard #22). The cover date is caption grey, so it gets no waiver."""
    if color != brand().muted or background != "FFFFFF":
        return False
    if axis:
        return True
    return shape is not None and _is_page_number(shape) and (size or 10) <= 10


def check_contrast(deck: Deck, out: Collector) -> str:
    waived: list[str] = []

    def measure(
        position: int,
        color: str | None,
        background: str | None,
        size: float | None,
        bold: bool,
        what: str,
        shape: Shape | None,
        axis: bool = False,
    ) -> None:
        if not color or not background:
            out.skip("no resolvable colour or background")
            return
        out.count()
        need = min_ratio(size if size is not None else 12, bold)
        ratio = contrast_ratio(color, background)
        if ratio + 1e-9 >= need:
            return
        line = f"#{color} on #{background} is {ratio:.2f}:1 (needs {need}:1 at {size or 12:g}pt{' bold' if bold else ''}): {what}"
        if _muted_waived(color, background, shape, size, axis):
            waived.append(f"Slide {position}: {line}")
            return
        out.add(position, line)

    for s in deck.slides:
        kind, slide_bg, _ = _slide_background(s)
        slide_bg = slide_bg if kind == "solid" else None
        for shape, frame in s.text_shapes():
            background, _where = _background_under(s, shape, slide_bg)
            for run in frame.runs():
                if run.text.strip():
                    measure(
                        s.position,
                        run.color,
                        background,
                        run.size,
                        run.bold,
                        f'"{_snippet(run.text, 40)}"',
                        shape,
                    )
        for shape in s.shapes:
            if not shape.is_table:
                continue
            for tc, look in _cell_looks(s, shape):
                cell = _cell_frame(s, tc, look)
                if cell is None:
                    continue
                own = _fill_child(tc.find(f"{A}tcPr"))
                if own is not None:  # the cell's own fill outranks its table style
                    kind, hex_ = _local(own.tag), s.ctx.first(own)
                elif look is not None and look.fill is not None:
                    kind = {"solid": "solidFill", "none": "noFill"}.get(look.fill[0], "other")
                    hex_ = look.fill[1]
                else:
                    kind, hex_ = "noFill", None
                cell_bg = hex_ if kind == "solidFill" else slide_bg if kind == "noFill" else None
                for run in cell.runs():
                    if not run.text.strip():
                        continue
                    if look is None and (own is None or not run.color_explicit):
                        out.skip(TABLE_STYLE_UNREAD)
                        continue
                    measure(
                        s.position,
                        run.color,
                        cell_bg,
                        run.size,
                        run.bold,
                        f'table cell "{_snippet(run.text, 40)}"',
                        None,
                    )
    for chart in deck.charts():
        kind, slide_bg, _ = _slide_background(chart.slide)
        outside = slide_bg if kind == "solid" else None
        space_fill = _fill_child(chart.root.find(f"{C}spPr"))
        if space_fill is not None and _local(space_fill.tag) == "solidFill":
            outside = chart.slide.ctx.first(space_fill)
        for style, background, what, axis in _chart_text_rows(chart, outside):
            color, size, bold = style
            measure(
                chart.slide.position,
                color,
                background,
                size,
                bold,
                f"chart {chart.stem} {what}",
                None,
                axis,
            )
    note = f"; {len(waived)} muted-grey page number or axis label run(s) waived" if waived else ""
    if out.findings:
        return f"{len(out.findings)} run(s) below WCAG AA among {out.examined} measured{note}"
    return f"{out.examined} run(s) measured, all clear WCAG AA{note}"


def _txpr_style(
    ctx: ColorContext, tx_pr: Any, inherited: tuple[str | None, float | None, bool]
) -> tuple[str | None, float | None, bool]:
    """(colour, size, bold) of a chart c:txPr or c:rich over `inherited`: paragraph
    defaults first, then a run's own properties (a rich-text label's colour sits there)."""
    if tx_pr is None:
        return inherited
    color, size, bold = inherited
    for props in list(tx_pr.iter(f"{A}defRPr")) + list(tx_pr.iter(f"{A}rPr")):
        fill = _fill_child(props)
        if fill is not None and _local(fill.tag) == "solidFill":
            color = ctx.first(fill)
        if props.get("sz", "").isdigit():
            size = int(props.get("sz")) / 100
        if props.get("b") is not None:
            bold = props.get("b") in ("1", "true")
    return color, size, bold


def _chart_text_rows(
    chart: Chart, outside: str | None
) -> list[tuple[tuple[str | None, float | None, bool], str | None, str, bool]]:
    """(style, background, what, is_axis) for data labels, axis labels and legends."""
    ctx = chart.slide.ctx
    base = _txpr_style(ctx, chart.root.find(f"{C}txPr"), (None, None, False))
    rows = []
    for plot in _plots(chart):
        tag = _local(plot.tag)
        grouping = plot.find(f"{C}grouping")
        inside_default = tag in _INSIDE_CHART_TAGS or (
            grouping is not None and grouping.get("val") in ("stacked", "percentStacked")
        )

        def inside(holder: Any, default: bool = inside_default) -> bool:
            pos = holder.find(f"{C}dLblPos")
            return pos.get("val") in _INSIDE_LABEL_POS if pos is not None else default

        plot_labels = plot.find(f"{C}dLbls")
        for ser in plot.findall(f"{C}ser"):
            # A series or point with a:noFill draws nothing, so a label "inside" it sits
            # on whatever is behind the chart (nbg_build's waterfall step labels ride an
            # invisible carrier series).
            ser_fill = _fill_child(ser.find(f"{C}spPr"))
            if ser_fill is not None and _local(ser_fill.tag) == "noFill":
                ser_color = outside
            elif ser_fill is not None and _local(ser_fill.tag) == "solidFill":
                ser_color = ctx.first(ser_fill)
            else:
                ser_color = None
            points: dict[str | None, str | None] = {}
            for dpt in ser.findall(f"{C}dPt"):
                idx = dpt.find(f"{C}idx")
                fill = _fill_child(dpt.find(f"{C}spPr"))
                if idx is None or fill is None:
                    continue
                if _local(fill.tag) == "solidFill":
                    points[idx.get("val")] = ctx.first(fill)
                elif _local(fill.tag) == "noFill":
                    points[idx.get("val")] = outside
            labels = ser.find(f"{C}dLbls")
            if labels is None:
                labels = plot_labels
            if labels is None or _flag(labels, "delete"):
                continue
            name = _series_name(ser)
            count = len(_categories(ser)) or len(ser.findall(f"{C}val//{C}pt"))
            style = _txpr_style(ctx, labels.find(f"{C}txPr"), base)
            overridden: set[str] = set()
            # A per-point c:dLbl overrides the series labels for that point: its own
            # text colour, its own position, or its deletion.
            for dlbl in labels.findall(f"{C}dLbl"):
                idx_el = dlbl.find(f"{C}idx")
                if idx_el is None:
                    continue
                idx = idx_el.get("val", "0")
                overridden.add(idx)
                rich = dlbl.find(f"{C}tx/{C}rich")  # custom label text, e.g. a signed delta
                if _flag(dlbl, "delete") or not (
                    _shown(dlbl) or _shown(labels) or rich is not None
                ):
                    continue
                holder = dlbl.find(f"{C}txPr")
                point_style = _txpr_style(ctx, holder if holder is not None else rich, style)
                bg = (points.get(idx) or ser_color) if inside(dlbl, inside(labels)) else outside
                rows.append((point_style, bg, f"series {name!r} label {int(idx) + 1}", False))
            if not _shown(labels):
                continue
            backgrounds: set[str | None] = set()
            for i in range(count):
                if str(i) in overridden:
                    continue
                backgrounds.add((points.get(str(i)) or ser_color) if inside(labels) else outside)
            for bg in backgrounds:
                rows.append((style, bg, f"series {name!r} labels", False))
    for axis in (
        list(chart.root.iter(f"{C}catAx"))
        + list(chart.root.iter(f"{C}valAx"))
        + list(chart.root.iter(f"{C}dateAx"))
    ):
        if _flag(axis, "delete"):
            continue
        if (
            axis.find(f"{C}tickLblPos") is not None
            and axis.find(f"{C}tickLblPos").get("val") == "none"
        ):
            continue
        rows.append(
            (
                _txpr_style(ctx, axis.find(f"{C}txPr"), base),
                outside,
                f"{_local(axis.tag)} labels",
                True,
            )
        )
    legend = chart.root.find(f".//{C}legend")
    if legend is not None:
        rows.append((_txpr_style(ctx, legend.find(f"{C}txPr"), base), outside, "legend", False))
    return rows


def _flag(parent: Any, name: str) -> bool:
    """A chart CT_Boolean child: present with no val means true, per the schema."""
    node = parent.find(f"{C}{name}") if parent is not None else None
    return node is not None and node.get("val", "true") in ("1", "true")


def _shown(labels: Any) -> bool:
    for flag in ("showVal", "showCatName", "showSerName", "showPercent"):
        if _flag(labels, flag):
            return True
    return False


def _content_shapes(slide: Slide) -> Iterator[Shape]:
    for shape in slide.shapes:
        if shape.kind == "grpSp" or not shape.has_box or _is_chrome(shape):
            continue
        yield shape


def check_boundaries(deck: Deck, out: Collector) -> str:
    b = brand()
    for s in deck.slides:
        for shape in s.shapes:
            if shape.kind == "grpSp" or not shape.has_box:
                continue
            out.count()
            label = f'"{shape.name}"' if shape.name else shape.kind
            if shape.right > b.slide_w + POS_TOL:
                out.add(
                    s.position,
                    f'{label} extends {shape.right - b.slide_w:.2f}" past the right edge',
                )
            if shape.bottom > b.slide_h + POS_TOL:
                out.add(
                    s.position,
                    f'{label} extends {shape.bottom - b.slide_h:.2f}" past the bottom edge',
                )
            if (shape.x or 0) < -POS_TOL:
                out.add(s.position, f'{label} starts {-(shape.x or 0):.2f}" past the left edge')
            if (shape.y or 0) < -POS_TOL:
                out.add(s.position, f'{label} starts {-(shape.y or 0):.2f}" past the top edge')
    if out.findings:
        return f"{len(out.findings)} element(s) outside the slide among {out.examined} positioned"
    return f"{out.examined} positioned element(s) (shapes, pictures, charts, tables, connectors), all on the slide"


def check_safe_zones(deck: Deck, out: Collector) -> str:
    b = brand()
    for s in deck.slides:
        for shape in _content_shapes(s):
            out.count()
            label = f'"{shape.name}"' if shape.name else shape.kind
            if (shape.x or 0) < b.gutter - POS_TOL:
                out.add(
                    s.position,
                    f'{label} starts at {shape.x:.2f}", left of the {b.gutter}" gutter (dimensions.md)',
                )
            if shape.right > b.right + POS_TOL:
                out.add(
                    s.position,
                    f'{label} ends at {shape.right:.2f}", right of the {b.right}" boundary (dimensions.md)',
                )
            if shape.bottom > b.footer_top + POS_TOL:
                out.add(
                    s.position,
                    f'{label} bottom edge at {shape.bottom:.2f}" runs into the footer zone; content ends by {b.footer_top}"',
                )
            elif shape.kind == "sp":
                frame = s.frame(shape)
                if (
                    frame is not None
                    and frame.text.strip()
                    and _is_source(frame.text)
                    and shape.bottom > b.body_bottom + POS_TOL
                ):
                    out.add(
                        s.position,
                        f'source or footnote ends at {shape.bottom:.2f}"; sources and footnotes end by {b.body_bottom}" (dimensions.md)',
                    )
    if out.findings:
        return f"{len(out.findings)} safe-zone violation(s) among {out.examined} content element(s)"
    return f"{out.examined} content element(s) inside the gutter, right boundary and footer line"


def _title_bottom(slide: Slide, title: Title) -> float:
    shape = title.shape
    lay = layout_text(title.frame, shape.w or 0.0, slide.deck.measurer)
    text_bottom = (shape.y or 0.0) + lay.height
    return min(shape.bottom, text_bottom) if shape.has_box else text_bottom


def _is_subtitle(slide: Slide, shape: Shape, title_bottom: float) -> bool:
    if shape.kind != "sp" or not shape.has_box or (shape.h or 0) > SUBTITLE_MAX_H:
        return False
    if _fill(slide, shape)[0] != "none":
        return False
    frame = slide.frame(shape)
    if frame is None or not frame.text.strip():
        return False
    return title_bottom - 0.05 <= (shape.y or 0) <= title_bottom + SUBTITLE_MAX_GAP


def check_content_spacing(deck: Deck, out: Collector) -> str:
    b = brand()
    for s in deck.slides:
        title = find_title(s)
        if title is None:
            if s.all_text().strip():
                out.skip("slide without a title")
            continue
        if not title.is_content:
            continue
        bottom = _title_bottom(s, title)
        body = []
        subtitle_taken = False
        for shape in _content_shapes(s):
            if shape is title.shape or (shape.y or 0) < bottom - 0.02:
                continue  # the title, and header chrome that starts above its bottom
            if (shape.y or 0) >= b.footer_top - POS_TOL:
                continue
            if not subtitle_taken and _is_subtitle(s, shape, bottom):
                subtitle_taken = True
                continue
            body.append(shape)
        if not body:
            continue
        out.count()
        first = min(body, key=lambda sh: sh.y or 0)
        need = max(b.body_top, bottom + MIN_TITLE_GAP)
        if (first.y or 0) < need - 0.02:
            label = f'"{first.name}"' if first.name else first.kind
            out.add(
                s.position,
                f'first body element {label} starts at {first.y:.2f}"; body starts at {need:.2f}" or lower (title ends at {bottom:.2f}", Standard #11)',
            )
    if out.findings:
        return f"{len(out.findings)} of {out.examined} slide(s) crowd the title"
    return f'{out.examined} titled slide(s), body at {b.body_top}" or lower and clear of the title'


def _extent(shape: Shape, frame: Frame, lay: TextLayout) -> tuple[float, float, float, float]:
    """The rectangle the text itself occupies (x0, y0, x1, y1), in inches."""
    x, y, w, h = shape.x or 0.0, shape.y or 0.0, shape.w or 0.0, shape.h or 0.0
    inner_w = w - frame.l_ins - frame.r_ins
    width = min(lay.width, inner_w) if frame.wrap else lay.width
    align = frame.paragraphs[0].align if frame.paragraphs else "l"
    if align == "ctr":
        x0 = x + frame.l_ins + (inner_w - width) / 2
    elif align == "r":
        x0 = x + w - frame.r_ins - width
    else:
        x0 = x + frame.l_ins
    text_h = lay.height - frame.t_ins - frame.b_ins
    inner_h = h - frame.t_ins - frame.b_ins
    if frame.anchor == "ctr":
        y0 = y + frame.t_ins + (inner_h - text_h) / 2
    elif frame.anchor == "b":
        y0 = y + h - frame.b_ins - text_h
    else:
        y0 = y + frame.t_ins
    return x0, y0, x0 + width, y0 + text_h


def _opaque(slide: Slide, shape: Shape) -> bool:
    """A shape whose solid fill hides what lies under it: no alpha below 100%."""
    if _fill(slide, shape)[0] != "solid":
        return False
    fill = _fill_child(shape.sp_pr)
    if fill is None or _local(fill.tag) != "solidFill":
        return True  # a fill from the shape's style or its placeholder
    color = next((c for c in fill if _local(c.tag) in _CLR_TAGS), None)
    alpha = color.find(f"{A}alpha") if color is not None else None
    try:
        return alpha is None or int(alpha.get("val", "100000")) >= 100000
    except ValueError:
        return True


def check_text_fit(deck: Deck, out: Collector) -> str:
    b = brand()
    m = deck.measurer
    for s in deck.slides:
        cover = _is_cover(deck, s)
        extents: list[tuple[Shape, tuple[float, float, float, float]]] = []
        for shape, frame in s.text_shapes():
            if not shape.has_box:
                out.skip("text with no position")
                continue
            if shape.rot or frame.vertical:
                out.skip("rotated or vertical text")
                continue
            out.count()
            lay = layout_text(frame, shape.w or 0.0, m)
            filled = _fill(s, shape)[0] != "none"
            label = f'"{shape.name}"' if shape.name else "text"
            snippet = _snippet(frame.text)
            if frame.autofit == "shape":
                # "Resize shape to fit text": the box grows downward instead of
                # overflowing, so what matters is where it grows to.
                grown = (shape.y or 0.0) + max(shape.h or 0.0, lay.height)
                if grown > b.footer_top + POS_TOL and not _is_chrome(shape):
                    out.add(
                        s.position,
                        f'{label} grows to fit its text and ends at {grown:.2f}", into the footer zone past {b.footer_top}": "{snippet}"',
                    )
            else:
                slack = 0.02 if filled else max(0.03, 0.5 * lay.top_line)
                if lay.height > (shape.h or 0.0) + slack:
                    lines = sum(lay.lines)
                    out.add(
                        s.position,
                        f'{label} needs {lay.height:.2f}" for {lines} line(s) but is {shape.h:.2f}" tall: "{snippet}"',
                    )
            inner = (shape.w or 0.0) - frame.l_ins - frame.r_ins
            if not frame.wrap and lay.width > inner + 0.02:
                if filled:
                    out.add(
                        s.position,
                        f'{label} text is {lay.width + frame.l_ins + frame.r_ins:.2f}" wide, wider than its {shape.w:.2f}" shape: "{snippet}"',
                    )
                elif (shape.x or 0) + frame.l_ins + lay.width > b.right + POS_TOL:
                    out.add(
                        s.position,
                        f'{label} unwrapped text runs past the {b.right}" boundary: "{snippet}"',
                    )
            if cover and (frame.max_size() or 0) >= TITLE_MIN_PT:
                wrapped = [n for n in lay.lines if n > 1]
                if wrapped:
                    out.add(
                        s.position,
                        f'cover text {label} wraps to {max(wrapped)} lines; cover title and subtitle stay on one line (Standard #13): "{snippet}"',
                    )
            extents.append((shape, _extent(shape, frame, lay)))
        for i, (first, a) in enumerate(extents):
            for second, c in extents[i + 1 :]:
                dx = min(a[2], c[2]) - max(a[0], c[0])
                dy = min(a[3], c[3]) - max(a[1], c[1])
                if dx > 0.04 and dy > 0.04:
                    out.add(
                        s.position,
                        f'text of "{first.name}" and "{second.name}" overlap by {dy:.2f}" vertically',
                    )
        for shape, (x0, y0, x1, y1) in extents:
            for other in s.shapes[shape.z + 1 :]:  # drawn later, so on top
                if other.kind != "sp" or not other.has_box or not _opaque(s, other):
                    continue
                dx = min(x1, other.right) - max(x0, other.x or 0.0)
                dy = min(y1, other.bottom) - max(y0, other.y or 0.0)
                if dx > 0.04 and dy > 0.04:
                    out.add(
                        s.position,
                        f'text of "{shape.name}" is hidden under "{other.name}", an opaque shape drawn on top of it',
                    )
                    break
        for shape in s.shapes:
            if not shape.is_table or not shape.has_box:
                continue
            out.count()
            height = _table_height(s, shape, m)
            if (shape.y or 0) + height > b.footer_top + POS_TOL:
                out.add(
                    s.position,
                    f'table "{shape.name}" grows to {(shape.y or 0) + height:.2f}" (rows grow to fit their text: row heights are minimums), into the footer zone past {b.footer_top}"',
                )
    summary = f"measured with {m.source}"
    if out.findings:
        return f"{len(out.findings)} fit problem(s) among {out.examined} text frame(s); {summary}"
    return f"{out.examined} text frame(s) and table(s) fit their boxes without overlap; {summary}"


def _table_height(slide: Slide, shape: Shape, m: TextMeasurer) -> float:
    tbl = shape.el.find(f".//{A}tbl")
    if tbl is None:
        return shape.h or 0.0
    widths = [int(col.get("w", "0")) / EMU for col in tbl.findall(f"{A}tblGrid/{A}gridCol")]
    total = 0.0
    for tr in tbl.findall(f"{A}tr"):
        row_h = int(tr.get("h", "0")) / EMU
        col = 0
        for tc in tr.findall(f"{A}tc"):
            span = int(tc.get("gridSpan", "1") or 1)
            width = sum(widths[col : col + span]) or (shape.w or 0.0) / max(1, len(widths))
            col += span
            if tc.get("hMerge") in ("1", "true") or tc.get("vMerge") in ("1", "true"):
                continue
            frame = _cell_frame(slide, tc)
            if frame is not None and frame.text.strip():
                row_h = max(row_h, layout_text(frame, width, m).height)
        total += row_h
    return total


def check_text_margins(deck: Deck, out: Collector) -> str:
    for s in deck.slides:
        for shape, frame in s.text_shapes():
            if _fill(s, shape)[0] != "none":
                continue  # a filled shape pads its text on purpose (pills, cards, badges)
            out.count()
            insets = (frame.l_ins, frame.t_ins, frame.r_ins, frame.b_ins)
            if max(insets) > INSET_TOL:
                l_, t_, r_, b_ = insets
                out.add(
                    s.position,
                    f'"{shape.name}" has margins l={l_:.2f}" t={t_:.2f}" r={r_:.2f}" b={b_:.2f}"; text boxes use zero margins (dimensions.md)',
                )
    if out.findings:
        return f"{len(out.findings)} of {out.examined} unfilled text box(es) have margins"
    return f"{out.examined} unfilled text box(es), all with zero margins"


def _logo_kind(deck: Deck, slide: Slide, shape: Shape) -> tuple[str, tuple[int, int] | None]:
    """("greek" | "english" | "emblem" | "other", pixel size) for a picture."""
    part = slide.image_part(shape)
    if not part:
        return "other", None
    digest, size = deck.media(part)
    if digest == _asset_hash("nbg-logo-gr.png"):
        return "greek", size
    if digest == _asset_hash("nbg-logo-fallback.png"):
        return "english", size
    if digest == _asset_hash("nbg-back-cover-logo.png"):
        return "emblem", size
    if size and size[1]:
        aspect = size[0] / size[1]
        if abs(aspect - brand().logo_aspect) / brand().logo_aspect <= 0.05:
            return "greek", size
        if abs(aspect - 4.74) / 4.74 <= 0.05:
            return "english", size
        back = brand().logo_back
        if abs(aspect - back[2] / back[3]) / (back[2] / back[3]) <= 0.05:
            return "emblem", size
    return "other", size


def _stretch(shape: Shape, size: tuple[int, int] | None) -> float | None:
    if not size or not size[1] or not shape.h:
        return None
    image, shown = size[0] / size[1], (shape.w or 0) / shape.h
    return abs(shown - image) / image


def check_logo(deck: Deck, out: Collector) -> str:
    b = brand()
    slides = deck.slides[:-1] if len(deck.slides) > 1 else deck.slides
    for s in slides:
        out.count()
        spots = [
            (shape, spot_name)
            for shape in s.shapes + s.inherited
            if shape.kind == "pic"
            for spot_name, spot in (("small", b.logo_small), ("large", b.logo_large))
            if _spot_match(shape, spot, size=False)
        ]
        if not spots:
            out.add(
                s.position,
                f"no NBG logo at the small ({b.logo_small[0]}, {b.logo_small[1]}) or large ({b.logo_large[0]}, {b.logo_large[1]}) position (Standard #17)",
            )
            continue
        shape, spot_name = spots[0]
        kind, size = _logo_kind(deck, s, shape)
        if kind == "english":
            out.add(
                s.position,
                "the logo is the English fallback; use the Greek wordmark nbg-logo-gr.png (Standard #10)",
            )
        elif kind != "greek":
            out.add(
                s.position,
                "the picture at the logo position is not the NBG Greek wordmark (Standard #17)",
            )
            continue
        stretch = _stretch(shape, size)
        if stretch is not None and stretch > 0.03 and size:
            shown = (shape.w or 0.0) / (shape.h or 1.0)
            out.add(
                s.position,
                f"the logo is stretched: shown at {shown:.2f}:1, the image is {size[0] / size[1]:.2f}:1 (Standard #4)",
            )
        spot = b.logo_small if spot_name == "small" else b.logo_large
        if not _spot_match(shape, spot):
            out.add(
                s.position,
                f'the logo is {shape.w:.3f}" x {shape.h:.3f}"; the {spot_name} logo is {spot[2]}" x {spot[3]}" (Standard #17)',
            )
        if _is_cover(deck, s) and spot_name != "large":
            out.add(
                s.position,
                "slide 1 is the cover and carries the small logo; covers and dividers use the large logo (Standard #17)",
            )
    if out.findings:
        return f"{len(out.findings)} logo problem(s) on {out.examined} slide(s)"
    return f"{out.examined} slide(s) carry the Greek wordmark at the brand position and aspect"


def check_back_cover(deck: Deck, out: Collector) -> str:
    b = brand()
    if len(deck.slides) < 2:
        return "a one-slide deck has no back cover to check"
    s = deck.slides[-1]
    out.count()
    shown = s.shapes + s.inherited
    pictures = [sh for sh in shown if sh.kind == "pic"]
    others = [sh for sh in shown if sh.kind in ("graphicFrame", "cxnSp")]
    texts = [sh for sh in shown if sh.kind == "sp"]
    for shape in texts:
        frame = s.frame(shape)
        body = frame.text.strip() if frame is not None else ""
        if _is_page_number(shape):
            out.add(
                s.position,
                f'the back cover carries a page number "{_snippet(body)}" (Standard #19)',
            )
        elif body:
            out.add(
                s.position,
                f'the back cover carries text "{_snippet(body)}"; it holds only the emblem (Standard #19)',
            )
        else:
            out.add(
                s.position,
                f'the back cover carries a shape "{shape.name}"; it holds only the emblem (Standard #19)',
            )
    for shape in others:
        out.add(
            s.position,
            f"the back cover carries a {'chart or table' if shape.kind == 'graphicFrame' else 'line'} (Standard #19)",
        )
    emblems = [
        p for p in pictures if _spot_match(p, b.logo_back) and _logo_kind(deck, s, p)[0] == "emblem"
    ]
    if not emblems:
        out.add(
            s.position,
            f"no NBG oval emblem at the centred back-cover position {b.logo_back[:2]} (Standard #19)",
        )
    extra = len(pictures) - len(emblems[:1])
    if extra > 0:
        out.add(
            s.position,
            f"the back cover carries {extra} picture(s) besides the emblem; no corner logo (Standard #19)",
        )
    if out.findings:
        return f"slide {s.position} is not the plain back cover"
    return f"slide {s.position} is the plain back cover: the emblem alone"


# Greek thanks are the verb forms only (ευχαριστώ, ευχαριστούμε, folded): the same stem
# gives ευχάριστη (pleasant), ευχαριστημένοι (satisfied) and ευχαρίστηση (satisfaction).
_STRONG_CLOSING = re.compile(
    r"\bthank\s*-?\s*you\b|\bthanks\b(?!\s+to\b)|\bany\s+questions\b|\bmerci\b|\bgrazie\b"
    r"|\bdanke\b|\bευχαριστ(?:ω|ουμε)\b"
)
_WEAK_CLOSING = re.compile(r"^(?:q\s*&\s*a|questions|ερωτησεισ|ερωτησεισ\s*&\s*απαντησεισ)$")


def check_thank_you(deck: Deck, out: Collector) -> str:
    n = len(deck.slides)
    for s in deck.slides:
        texts = list(_slide_texts(s))
        words = sum(_words(t) for t in texts)
        if not (s.position > n - 2 or words <= CLOSING_MAX_WORDS):
            continue
        if not texts:
            out.count()
            continue
        out.count()
        # Matched folded, reported as written: "Ευχαριστούμε", not "ευχαριστουμε".
        hit = next((_snippet(t) for t in texts if _STRONG_CLOSING.search(fold(t))), None)
        title = find_title(s)
        largest = max(s.text_shapes(), key=lambda sf: sf[1].max_size() or 0, default=None)
        weak = None
        for candidate in (
            title.text if title else None,
            " ".join(largest[1].text.split()) if largest else None,
        ):
            if candidate:
                cleaned = re.sub(r"[^\w&\s]", "", fold(candidate)).strip()
                if _WEAK_CLOSING.match(cleaned):
                    weak = candidate
        if hit or weak:
            found = weak or hit
            out.add(
                s.position,
                f'closing text "{found}"; decks end on the plain back cover, not a thank-you or Q&A slide (Standard #19)',
            )
    if out.findings:
        return f"{len(out.findings)} closing slide(s) with thank-you or Q&A text"
    return f"{out.examined} closing candidate(s) (last two slides, short slides), none with closing text"


_DECORATIVE = re.compile(
    r"^(?:star\d+|heart|moon|cloud|cloudCallout|sun|lightningBolt|irregularSeal\d|smileyFace|noSmoking|wave|doubleWave)$"
)


def check_decorative(deck: Deck, out: Collector) -> str:
    for s in deck.slides:
        for shape in s.shapes:
            prst = shape.prst
            if prst is None:
                continue
            out.count()
            where = f'"{shape.name}" at ({shape.x or 0:.2f}, {shape.y or 0:.2f}), {shape.w or 0:.2f}" x {shape.h or 0:.2f}"'
            if _DECORATIVE.match(prst):
                out.add(s.position, f"{prst} shape {where} is decorative (Standards #3 and #19)")
            elif prst == "ellipse":
                frame = s.frame(shape)
                has_text = frame is not None and frame.text.strip()
                big = max(shape.w or 0, shape.h or 0) > 0.5
                carries_picture = any(
                    o.kind == "pic"
                    and o.z > shape.z
                    and shape.contains((o.x or 0) + (o.w or 0) / 2, (o.y or 0) + (o.h or 0) / 2)
                    for o in s.shapes
                )
                if not has_text and big and not carries_picture:
                    out.add(
                        s.position,
                        f"ellipse {where} carries no text and no icon: a decorative blob, not a numbered badge (Standard #3)",
                    )
    if out.findings:
        return f"{len(out.findings)} decorative shape(s) among {out.examined} preset shape(s)"
    return f"{out.examined} preset shape(s): badges, pills, cards and arrows, none decorative"


_SHADOW_TAGS = ("outerShdw", "innerShdw", "prstShdw")


def _has_shadow(effects: Any) -> bool:
    return effects is not None and any(effects.find(f".//{A}{t}") is not None for t in _SHADOW_TAGS)


def check_shadows(deck: Deck, out: Collector) -> str:
    for s in deck.slides:
        for shape in s.shapes:
            if shape.kind == "graphicFrame":
                continue
            out.count()
            sp_pr = shape.sp_pr
            label = f'"{shape.name}"' if shape.name else shape.kind
            effects = sp_pr.find(f"{A}effectLst") if sp_pr is not None else None
            dag = sp_pr.find(f"{A}effectDag") if sp_pr is not None else None
            if _has_shadow(effects) or _has_shadow(dag):
                out.add(
                    s.position, f"{label} has a shadow; no shape carries one (brand-system README)"
                )
                continue
            if effects is not None or dag is not None:
                continue
            ref = shape.el.find(f"{P}style/{A}effectRef")
            if ref is None:
                continue
            try:
                idx = int(ref.get("idx", "0"))
            except ValueError:
                continue
            styles = s.theme.effect_styles
            if 1 <= idx <= len(styles) and _has_shadow(styles[idx - 1]):
                out.add(
                    s.position,
                    f"{label} inherits a shadow from theme effect style {idx}; set an empty effect list (python-pptx: shadow.inherit = False)",
                )
    for chart in deck.charts():
        out.count()
        if any(_has_shadow(sp) for sp in chart.root.iter(f"{C}spPr")):
            out.add(
                chart.slide.position, f"chart {chart.stem} draws a shadow (brand-system README)"
            )
    if out.findings:
        return f"{len(out.findings)} shadow(s) among {out.examined} shape(s) and chart(s)"
    return f"{out.examined} shape(s) and chart(s), no shadows"


def dash_problem(text: str) -> tuple[str, str] | None:
    """(severity, reason) when `text` breaks Standard #7, else None.

    Public: nbg_spec's `check` applies the same rule to a deck spec, so a spec that
    passes check is not failed by this gate for a dash. An em dash or " -- " is an
    error; a spaced en dash used as a dash is a warning; "2024-2025" with an en dash
    is a range and fine.
    """
    if EM_DASH in text or DOUBLE_HYPHEN in text:
        return "error", "em dash"
    if f" {EN_DASH} " in text:
        return "warning", "spaced en dash used as a dash"
    return None


def check_em_dashes(deck: Deck, out: Collector) -> str:
    def judge(position: int, text: str, where: str) -> None:
        out.count()
        problem = dash_problem(text)
        if problem is None:
            return
        severity, reason = problem
        out.add(
            position,
            f'{reason} in {where}: "{_snippet(text)}"; use a comma, colon or full stop (Standard #7)',
            severity,
        )

    for s in deck.slides:
        for text in _slide_texts(s):
            judge(s.position, text, "slide text")
    for chart in deck.charts():
        for text in _chart_texts(chart):
            judge(chart.slide.position, text, f"chart {chart.stem}")
    if out.findings:
        return f"{len(out.findings)} dash problem(s) among {out.examined} text item(s)"
    return f"{out.examined} text item(s) in slides and charts, no em dashes"


# Words that end in a period without ending a sentence: Greek number and list
# abbreviations, and company suffixes. Folded, so "δισ." matches "ΔΙΣ.".
_ABBREVIATIONS = frozenset(
    fold(a)
    for a in (
        "χιλ.",
        "εκ.",
        "εκατ.",
        "δισ.",
        "τρισ.",
        "κ.λπ.",
        "π.χ.",
        "Α.Ε.",
        "etc.",
        "Inc.",
        "Ltd.",
        "S.A.",
    )
)


def _closing_period(title: str) -> bool:
    text = title.rstrip()
    if not text.endswith(".") or text.endswith("..."):
        return False
    return fold(text.rsplit(None, 1)[-1]) not in _ABBREVIATIONS


def check_title_style(deck: Deck, out: Collector) -> str:
    b = brand()
    for s in deck.slides:
        title = find_title(s)
        if title is None:
            continue
        out.count()
        if title.frame.bold():
            out.add(
                s.position,
                f'title "{_snippet(title.text)}" is bold; titles are Regular weight (Standard #16)',
            )
        left = title.text_left
        if abs(left - b.gutter) > GUTTER_TOL:
            ty0, ty1 = title.shape.y or 0, title.shape.bottom
            leader = any(
                o is not title.shape
                and o.has_box
                and abs((o.x or 0) - b.gutter) <= GUTTER_TOL + 0.01
                and o.right <= (title.shape.x or 0) + 0.05
                and (o.y or 0) < ty1
                and o.bottom > ty0
                for o in s.shapes
            )
            if not leader:
                out.add(
                    s.position,
                    f'title starts at {left:.3f}", not the {b.gutter}" gutter (Standard #15)',
                )
        if _closing_period(title.text):
            out.add(
                s.position,
                f'title "{_snippet(title.text)}" ends with a period (brand-system README)',
                "warning",
            )
    if out.findings:
        return f"{len(out.findings)} title style problem(s) among {out.examined} title(s)"
    return f"{out.examined} title(s): Regular weight, on the gutter, no closing period"


def check_title_length(deck: Deck, out: Collector) -> str:
    limit = brand().title_max_chars
    for s in deck.slides:
        title = find_title(s)
        if title is None or not title.is_content:
            continue
        out.count()
        if len(title.text) > limit:
            out.add(
                s.position,
                f'title is {len(title.text)} characters, over the {limit} that fit one line at 24pt: "{_snippet(title.text, 60)}"',
            )
    if out.findings:
        return f"{len(out.findings)} of {out.examined} content title(s) over {limit} characters"
    return f"{out.examined} content title(s) within {limit} characters"


def check_slide_titles(deck: Deck, out: Collector) -> str:
    seen: dict[str, int] = {}
    textless = 0
    for s in deck.slides:
        if not s.all_text().strip():
            textless += 1
            continue
        out.count()
        title = find_title(s)
        if title is None:
            out.add(
                s.position,
                'no title: no title placeholder, no text of 20pt or more above 1.2", no 40pt statement title',
            )
            continue
        key = fold(title.text)
        if key in seen:
            out.add(
                s.position,
                f'title "{title.text}" duplicates slide {seen[key]}; disambiguate it (add the segment, period or part number)',
            )
        else:
            seen[key] = s.position
    exempt = f", {textless} text-free slide(s) exempt" if textless else ""
    if out.findings:
        return f"{len(out.findings)} title problem(s) across {out.examined} titled slide(s){exempt}"
    return f"{out.examined} slide(s) titled, all present and unique{exempt}"


TOPIC_LABEL_TITLES = frozenset(
    {
        "agenda", "appendix", "background", "conclusion", "conclusions", "context",
        "executive summary", "financials", "introduction", "key takeaways", "next steps",
        "objectives", "our approach", "overview", "recommendations", "results", "summary",
        "takeaways", "the ask", "timeline",
    }
)  # fmt: skip
# The year carries its own trailing whitespace: two \s* either side of an optional group
# backtrack quadratically on a long run of spaces after "q1" that then fails to match.
TOPIC_LABEL_PATTERN = re.compile(
    r"^(?:q[1-4]|h[12]|fy)\s*(?:20\d{2}\s*)?(?:results|performance|review|update|summary|numbers|highlights)$"
)
ACTION_TITLE_MAX_WORDS = 15


def check_action_titles(deck: Deck, out: Collector) -> str:
    """Warning by design: a noun-phrase title is sometimes a deliberate choice (a
    product name, a programme name), so this reports and never blocks."""
    for s in deck.slides:
        title = find_title(s)
        if title is None or not title.is_content:
            continue
        out.count()
        stripped = fold(title.text.rstrip(".:").strip())
        words = len(title.text.split())
        if stripped in TOPIC_LABEL_TITLES or TOPIC_LABEL_PATTERN.match(stripped):
            out.add(
                s.position,
                f'"{title.text}" is a topic label, not an assertion; say what the slide found',
            )
        elif words > ACTION_TITLE_MAX_WORDS:
            out.add(
                s.position,
                f'title runs {words} words (max {ACTION_TITLE_MAX_WORDS}): "{_snippet(title.text, 70)}"',
            )
    if out.findings:
        return (
            f"{len(out.findings)} of {out.examined} content title(s) are topic labels or overlong"
        )
    return f"{out.examined} content title(s), all assertions within {ACTION_TITLE_MAX_WORDS} words"


def check_chart_types(deck: Deck, out: Collector) -> str:
    for chart in deck.charts():
        out.count()
        for plot in _plots(chart):
            tag = _local(plot.tag)
            if tag in PIE_TAGS:
                out.add(
                    chart.slide.position,
                    f"chart {chart.stem} is a {tag}; part-to-whole is a doughnut (charts.md)",
                )
    if out.findings:
        return f"{len(out.findings)} pie chart(s) among {out.examined} chart(s)"
    return f"{out.examined} chart(s), no pie charts"


def check_chart_data(deck: Deck, out: Collector) -> str:
    b = brand()
    for chart in deck.charts():
        out.count()
        series = [ser for plot in _plots(chart) for ser in plot.findall(f"{C}ser")]
        pos = chart.slide.position
        if not series:
            out.add(pos, f"chart {chart.stem} has no series: the plot area is blank")
            continue
        categorical = any(
            _local(p.tag) not in ("scatterChart", "bubbleChart") for p in _plots(chart)
        )
        cats = max((len(_categories(ser)) for ser in series), default=0)
        if categorical and cats == 0:
            out.add(pos, f"chart {chart.stem} has no categories")
        pie_like = all(_local(p.tag) in (*PIE_TAGS, "doughnutChart") for p in _plots(chart))
        # Distinct names: an area-line chart draws each series twice (an areaChart fill
        # and a lineChart stroke of the same name), which is one series to the reader.
        names = {
            name if name != "(unnamed)" else f"#{i}"
            for i, name in enumerate(_series_name(ser) for ser in series)
        }
        count, what = (cats, "slices") if pie_like else (len(names), "series")
        if count > b.max_series_absolute:
            out.add(
                pos,
                f"chart {chart.stem} has {count} {what}; the ceiling is {b.max_series_absolute}, use small multiples (Standard #22)",
            )
        elif count > b.max_series:
            out.add(
                pos,
                f"chart {chart.stem} has {count} {what}; past {b.max_series} use small multiples or group the tail (Standard #22)",
                "warning",
            )
    if out.findings:
        return f"{len(out.findings)} data problem(s) among {out.examined} chart(s)"
    return f"{out.examined} chart(s) with data, within {b.max_series} series"


def _automatic_color(chart: Chart, index: int) -> str | None:
    slot = f"accent{index % 6 + 1}"
    return chart.slide.ctx.theme.colors.get(chart.slide.ctx.clr_map.get(slot, slot))


def check_chart_styling(deck: Deck, out: Collector) -> str:
    b = brand()
    for chart in deck.charts():
        pos = chart.slide.position
        ctx = chart.slide.ctx
        for plot in _plots(chart):
            tag = _local(plot.tag)
            plot_marker = plot.find(f"{C}marker")
            varies = _flag(plot, "varyColors")
            for n, ser in enumerate(plot.findall(f"{C}ser")):
                out.count()
                name = _series_name(ser)
                idx_el = ser.find(f"{C}idx")
                index = int(idx_el.get("val", n)) if idx_el is not None else n
                sp_pr = ser.find(f"{C}spPr")
                fill = _fill_child(sp_pr)
                line = sp_pr.find(f"{A}ln") if sp_pr is not None else None
                line_fill = _fill_child(line)
                if tag in ("lineChart", "line3DChart", "areaChart", "area3DChart"):
                    if line_fill is None:
                        auto = _automatic_color(chart, index)
                        out.add(
                            pos,
                            f"series {name!r} in chart {chart.stem} has no explicit line colour (c:spPr/a:ln); it falls back to the theme accent #{auto or '?'}",
                        )
                    if tag.startswith("area") and fill is None:
                        out.add(
                            pos,
                            f"area series {name!r} in chart {chart.stem} has no explicit fill; it takes the theme accent",
                        )
                elif (
                    tag in ("barChart", "bar3DChart", "radarChart") and fill is None and not varies
                ):
                    auto = _automatic_color(chart, index)
                    verdict = _color_verdict(auto) if auto else "cannot be resolved"
                    if verdict:
                        out.add(
                            pos,
                            f"series {name!r} in chart {chart.stem} has no explicit colour and takes theme accent #{auto or '?'}, which {verdict}",
                        )
                if tag in (*PIE_TAGS, "doughnutChart") or varies:
                    explicit = {
                        dpt.find(f"{C}idx").get("val")
                        for dpt in ser.findall(f"{C}dPt")
                        if dpt.find(f"{C}idx") is not None
                        and _fill_child(dpt.find(f"{C}spPr")) is not None
                    }
                    for i in range(len(_categories(ser))):
                        if str(i) in explicit:
                            continue
                        auto = _automatic_color(chart, i)
                        verdict = _color_verdict(auto) if auto else "cannot be resolved"
                        if verdict:
                            out.add(
                                pos,
                                f"point {i + 1} of {name!r} in chart {chart.stem} takes theme accent #{auto or '?'}, which {verdict}",
                            )
                            break
                if tag in ("lineChart", "line3DChart") or (
                    tag == "scatterChart" and line_fill is not None
                ):
                    marker = ser.find(f"{C}marker")
                    symbol_el = marker.find(f"{C}symbol") if marker is not None else None
                    symbol = symbol_el.get("val") if symbol_el is not None else None
                    marker_fill = (
                        ctx.first(_fill_child(marker.find(f"{C}spPr")))
                        if marker is not None and marker.find(f"{C}spPr") is not None
                        else None
                    )
                    if symbol is None:
                        shown = plot_marker is None or _flag(plot, "marker")
                        symbol = "automatic" if shown else "none"
                    if symbol != b.marker_symbol or marker_fill != b.marker_fill:
                        out.add(
                            pos,
                            f"series {name!r} in chart {chart.stem} has {symbol} markers; line charts use hollow circle markers, white fill with a series-colour ring (Standard #5)",
                            "warning",
                        )
    if out.findings:
        return f"{len(out.findings)} styling problem(s) among {out.examined} series"
    return f"{out.examined} series with explicit brand colours and hollow circle markers"


def _bar_values(chart: Chart) -> list[float]:
    """What a bar chart's value axis must span: each bar, or each stack's positive and
    negative totals. Empty for percent-stacked bars, whose axis is fixed at 0-100%."""
    values: list[float] = []
    for plot in _plots(chart):
        if _local(plot.tag) not in BAR_CHART_TAGS:
            continue
        grouping = plot.find(f"{C}grouping")
        kind = grouping.get("val", "clustered") if grouping is not None else "clustered"
        if kind == "percentStacked":
            continue
        stacks: dict[str, list[float]] = {}
        for ser in plot.findall(f"{C}ser"):
            for pt in ser.findall(f"{C}val//{C}pt"):
                try:
                    v = float(pt.findtext(f"{C}v") or "")
                except ValueError:
                    continue
                if kind == "stacked":
                    stacks.setdefault(pt.get("idx", "0"), []).append(v)
                else:
                    values.append(v)
        for stack in stacks.values():
            values += [sum(v for v in stack if v > 0), sum(v for v in stack if v < 0)]
    return values


def _axis_bound(scaling: Any, name: str) -> tuple[float | None, str | None]:
    """(value, raw text) of an explicit c:min or c:max; (None, raw) when unparseable."""
    node = scaling.find(f"{C}{name}") if scaling is not None else None
    if node is None:
        return None, None
    raw = node.get("val", "0")
    try:
        return float(raw), raw
    except ValueError:
        return None, raw


def check_zero_baseline(deck: Deck, out: Collector) -> str:
    """Bar and column value axes include zero. Read by parsing: 'c:min' also occurs
    inside c:minorTickMark on every chart, so a text search finds minimums that are
    not there.

    An explicit minimum above zero (or maximum below it) truncates the bars. So does an
    automatic axis on close values: PowerPoint, like Excel, leaves zero off an automatic
    axis when the lowest bar is over five sixths of the highest, so 2.9 to 3.3 draws from
    about 2.7 and a 14% rise looks like a tripling (E2E-OUTPUT-01). A hidden axis hides
    the truncation, it does not remove it.
    """
    non_bar = 0
    for chart in deck.charts():
        tags = {_local(p.tag) for p in _plots(chart)}
        bars = tags & set(BAR_CHART_TAGS)
        if not bars:
            non_bar += 1
            continue
        kinds = "/".join(sorted(bars))
        values = _bar_values(chart)
        lo, hi = (min(values), max(values)) if values else (0.0, 0.0)
        for val_ax in chart.root.iter(f"{C}valAx"):
            out.count()
            scaling = val_ax.find(f"{C}scaling")
            minimum, raw_min = _axis_bound(scaling, "min")
            maximum, raw_max = _axis_bound(scaling, "max")
            for raw, value in ((raw_min, minimum), (raw_max, maximum)):
                if raw is not None and value is None:
                    out.add(
                        chart.slide.position,
                        f"chart {chart.stem} value axis bound is not a number ({raw!r})",
                    )
            if minimum is not None and minimum > 0:
                out.add(
                    chart.slide.position,
                    f"chart {chart.stem} {kinds} value axis starts at {minimum:g}, not zero; a truncated bar misstates every ratio",
                )
            elif maximum is not None and maximum < 0:
                out.add(
                    chart.slide.position,
                    f"chart {chart.stem} {kinds} value axis ends at {maximum:g}, below zero; the negative bars are truncated",
                )
            elif raw_min is None and lo >= 0 and hi > 0 and lo > hi * 5 / 6:
                out.add(
                    chart.slide.position,
                    f"chart {chart.stem} {kinds} value axis is automatic and the bars run {lo:g} to {hi:g}: PowerPoint starts that axis above zero and truncates every bar; set its minimum to 0",
                )
            elif raw_max is None and hi <= 0 and lo < 0 and hi < lo * 5 / 6:
                out.add(
                    chart.slide.position,
                    f"chart {chart.stem} {kinds} value axis is automatic and the bars run {lo:g} to {hi:g}: PowerPoint ends that axis below zero and truncates every bar; set its maximum to 0",
                )
    note = f", {non_bar} non-bar chart(s) not subject to the rule" if non_bar else ""
    if out.findings:
        return f"{len(out.findings)} truncated value axis/axes of {out.examined}{note}"
    return f"{out.examined} bar/column value axis/axes, all based at zero{note}"


def check_exhibit_sources(deck: Deck, out: Collector) -> str:
    for s in deck.slides:
        kinds = []
        if any(sh.chart_rid for sh in s.shapes if sh.kind == "graphicFrame"):
            kinds.append("chart")
        if any(sh.is_table for sh in s.shapes):
            kinds.append("table")
        if not kinds:
            continue
        out.count()
        sources = [t for t in _slide_texts(s) if SOURCE_PREFIX.match(fold(t))]
        what = " and ".join(kinds)
        if not sources:
            out.add(
                s.position, f'carries a {what} and no source line ("Source: <name>, <as-of date>")'
            )
        elif not any(SOURCE_AS_OF.search(t) for t in sources):
            out.add(s.position, f'source line "{_snippet(sources[0], 60)}" carries no as-of date')
    if out.findings:
        return f"{len(out.findings)} of {out.examined} exhibit slide(s) unsourced or undated"
    return f"{out.examined} exhibit slide(s), all carrying a dated source line"


ALT_TEXT_LEAD_IN = re.compile(
    r"^\s*(?:image|picture|graphic|photo|screenshot)\s+of\b", re.IGNORECASE
)
ALT_TEXT_PLACEHOLDER = re.compile(
    r"^\s*(?:[\w .\-]+\.(?:png|jpe?g|gif|svg|bmp|tiff?|emf|wmf)"
    r"|(?:image|picture|chart|table|group|object|diagram|graphic|shape)\s*\d*)\s*$",
    re.IGNORECASE,
)


def alt_text_problem(alt: str, captions: Iterable[str] = ()) -> str | None:
    """Why `alt` describes nothing, or None when it is usable alt text.

    Public: nbg_spec's `check` runs it on a spec's alt_text so check and this gate
    agree. `captions` is the slide's other text; alt text identical to one of them is
    read out twice by a screen reader.
    """
    text = " ".join(alt.split())
    if not text:
        return "no alt text"
    if ALT_TEXT_PLACEHOLDER.match(text):
        return f'alt text "{text}" is a filename or an autoname, not a description'
    if ALT_TEXT_LEAD_IN.match(text):
        return f'alt text "{_snippet(text)}" opens with "image of"; describe the content'
    if fold(text) in {fold(c) for c in captions}:
        return f'alt text "{_snippet(text)}" repeats a caption already on the slide'
    return None


_DECORATIVE_EXT = "{C183D7F6-B498-43B3-948B-1728B52AA6E4}"


def _marked_decorative(shape: Shape) -> bool:
    """PowerPoint's "Mark as decorative" (Office 2019+): a:ext with an adec:decorative child."""
    nv = shape.c_nv_pr
    if nv is None:
        return False
    for ext in nv.iter(f"{A}ext"):
        if ext.get("uri", "").upper() == _DECORATIVE_EXT:
            for child in ext:
                if _local(child.tag) == "decorative" and child.get("val", "1") in ("1", "true"):
                    return True
    return False


def check_alt_text(deck: Deck, out: Collector) -> str:
    decorative = marked = 0
    for s in deck.slides:
        captions = list(_slide_texts(s))
        for shape in s.shapes:
            if shape.kind not in ("pic", "graphicFrame", "grpSp") or shape.depth > 0:
                continue
            if shape.kind == "pic" and _is_logo_footprint(shape):
                decorative += 1
                continue
            if shape.kind == "pic" and _marked_decorative(shape):
                marked += 1
                continue
            out.count()
            nv = shape.c_nv_pr
            problem = alt_text_problem(nv.get("descr", "") if nv is not None else "", captions)
            if problem is not None:
                name = shape.name or shape.kind
                out.add(
                    s.position,
                    f"{name} has no alt text" if problem == "no alt text" else f"{name} {problem}",
                )
    chrome = f", {decorative} brand logo(s) exempt as decorative" if decorative else ""
    if marked:
        chrome += f", {marked} picture(s) marked decorative in PowerPoint"
    if out.findings:
        return f"{len(out.findings)} of {out.examined} object(s) without usable alt text{chrome}"
    return f"{out.examined} object(s) carry descriptive alt text{chrome}"


# Bank names and logos come from tokens.yaml `banks`, colours from
# extended_palettes.peer_banks. `names` count anywhere; `label_aliases` only in a chart
# label, where a short name is unambiguous ("Alpha" beside "Eurobank"), so "alpha
# release" and "Piraeus port" in running text name no bank (VALIDATOR-9).
@dataclass(frozen=True)
class _Bank:
    name: str
    logo: str
    text: re.Pattern[str]
    label: re.Pattern[str]
    alias: re.Pattern[str] | None  # a short form, matched only as a whole chart label


# What may follow a short form and still leave it the bank: "Piraeus Group", "Alpha S.A.".
_ALIAS_TAIL = r"(?:\s+(?:bank|group|s\.?\s?a\.?|α\.?\s?ε\.?))?"


def _names_pattern(names: Iterable[str]) -> re.Pattern[str]:
    words = [fold(str(n)).split() for n in names]
    alternatives = [r"(?<!\w)" + r"\s+".join(map(re.escape, w)) + r"(?!\w)" for w in words if w]
    return re.compile("|".join(alternatives) or r"(?!)")


@lru_cache(maxsize=1)
def _bank_table() -> dict[str, _Bank]:
    table = {}
    for key, bank in nbg_tokens.get("banks").items():
        names = list(bank.get("names") or [bank["name"]])
        aliases = list(bank.get("label_aliases") or [])
        forms = sorted((fold(str(a)) for a in aliases), key=len, reverse=True)
        table[key] = _Bank(
            str(bank["name"]),
            str(bank["logo"]),
            _names_pattern(names),
            _names_pattern(names + aliases),
            re.compile(f"(?:{'|'.join(map(re.escape, forms))}){_ALIAS_TAIL}") if forms else None,
        )
    return table


def chart_label_bank(label: str) -> str | None:
    """The bank a chart label (a category or a series name) names, or None.

    Public: nbg_spec's bank_of calls it, so the builder brands exactly the charts this
    gate checks. A full name (tokens `names`) counts anywhere in the label ("Eurobank
    Cyprus"); a short form (`label_aliases`: Alpha, Piraeus, ΕΤΕ) only as the whole
    label, optionally followed by Bank, Group, S.A. or Α.Ε. So "Piraeus Port Authority"
    names no bank: a short form anywhere gave it Piraeus Bank's colour and logo
    (BUILDER-CODE-04). A label naming two banks names none."""
    folded = " ".join(fold(str(label)).split())
    hits = [
        key
        for key, bank in _bank_table().items()
        if bank.text.search(folded) or (bank.alias is not None and bank.alias.fullmatch(folded))
    ]
    return hits[0] if len(hits) == 1 else None


def _banks_in(text: str, *, label: bool) -> set[str]:
    folded = fold(text)
    return {
        key
        for key, bank in _bank_table().items()
        if (bank.label if label else bank.text).search(folded)
    }


@lru_cache(maxsize=8)
def _asset_size(name: str) -> tuple[int, int] | None:
    try:
        return _image_size((ASSETS_DIR / name).read_bytes())
    except OSError:
        return None


def _bank_logo(deck: Deck, s: Slide, pic: Shape) -> tuple[str | None, tuple[int, int] | None]:
    """The bank whose logo `pic` shows, and the image's pixel size. A picture is a
    bank's logo when it is that bank's shipped asset, or when it names the bank in its
    alt text or name and keeps the asset's aspect ratio (a redrawn copy)."""
    part = s.image_part(pic)
    if not part:
        return None, None
    digest, size = deck.media(part)
    table = _bank_table()
    for key, bank in table.items():
        if digest == _asset_hash(bank.logo):
            return key, size
    nv = pic.c_nv_pr
    named = _banks_in(f"{pic.name} {nv.get('descr', '') if nv is not None else ''}", label=True)
    if len(named) == 1 and size and size[1]:
        key = named.pop()
        asset = _asset_size(table[key].logo)
        if asset and asset[1]:
            aspect = asset[0] / asset[1]
            if abs(size[0] / size[1] - aspect) / aspect <= 0.05:
                return key, size
    return None, size


def check_bank_branding(deck: Deck, out: Collector) -> str:
    b = brand()
    table = _bank_table()
    mentioned: set[str] = set()
    for s in deck.slides:
        for text in _slide_texts(s):
            if not _is_source(text):
                mentioned |= _banks_in(text, label=False)
        comparisons: list[tuple[Chart, set[str]]] = []
        for chart in (c for c in deck.charts() if c.slide is s):
            plotted: dict[str, str] = {}
            for plot in _plots(chart):
                for ser in plot.findall(f"{C}ser"):
                    ser_fill = _fill_child(ser.find(f"{C}spPr"))
                    ser_color = (
                        s.ctx.first(ser_fill)
                        if ser_fill is not None and _local(ser_fill.tag) == "solidFill"
                        else None
                    )
                    line = ser.find(f"{C}spPr/{A}ln")
                    line_fill = _fill_child(line)
                    ser_color = ser_color or (
                        s.ctx.first(line_fill) if line_fill is not None else None
                    )
                    named = chart_label_bank(_series_name(ser))
                    if named:
                        plotted[named] = ser_color or ""
                    points = {}
                    for dpt in ser.findall(f"{C}dPt"):
                        idx = dpt.find(f"{C}idx")
                        fill = _fill_child(dpt.find(f"{C}spPr"))
                        if idx is not None and fill is not None:
                            points[idx.get("val")] = s.ctx.first(fill)
                    for i, label in enumerate(_categories(ser)):
                        bank = chart_label_bank(label)
                        if bank:
                            color = points.get(str(i)) or ser_color or ""
                            if plotted.get(bank) != b.peer_banks[bank]:
                                plotted[bank] = color
            mentioned |= set(plotted)
            if len(plotted) >= 2:
                comparisons.append((chart, set(plotted)))
                out.count()
                for bank, color in sorted(plotted.items()):
                    if color != b.peer_banks[bank]:
                        shown = f"#{color}" if color else "an automatic colour"
                        out.add(
                            s.position,
                            f"chart {chart.stem} plots {table[bank].name} in {shown}, not its brand colour #{b.peer_banks[bank]} (presentation-qa 2H)",
                        )
        if comparisons:
            banks = set().union(*(c[1] for c in comparisons))
            shown_logos: set[str] = set()
            for pic in (sh for sh in s.shapes if sh.kind == "pic" and not _is_logo_footprint(sh)):
                key, size = _bank_logo(deck, s, pic)
                if key is None:
                    continue
                shown_logos.add(key)
                stretch = _stretch(pic, size)
                if stretch is not None and stretch > 0.03:
                    out.add(
                        s.position,
                        f"the {table[key].name} logo is stretched; keep its native aspect ratio (Standard #4)",
                    )
            missing = [table[key].name for key in table if key in banks - shown_logos]
            if missing:
                out.add(
                    s.position,
                    f"the slide plots {len(banks)} banks but carries no logo for {', '.join(missing)}; each plotted bank needs its own logo from assets/bank-logos (presentation-qa 2H)",
                )
    if not out.examined:
        return f"no chart compares two or more banks ({len(mentioned)} bank name(s) found)"
    if out.findings:
        return f"{len(out.findings)} branding problem(s) in {out.examined} bank comparison chart(s)"
    return f"{out.examined} bank comparison chart(s): brand colours and logos in place"


# A currency marker before or after the amount is required, which keeps years,
# page numbers, headcounts and percentages out of the sample.
_CURRENCY = r"(?:eur|usd|gbp|chf|€|\$|£)"
_AMOUNT = r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)"
_SUFFIX = r"(bn|mn|b|m|k|εκ\.?|εκατ\.?|δισ\.?|χιλ\.?)"
CURRENCY_AMOUNT = re.compile(
    rf"{_CURRENCY}\s?{_AMOUNT}\s?{_SUFFIX}?(?![\w%])"
    rf"|{_AMOUNT}\s?{_SUFFIX}?\s?(?:€|eur\b|ευρω)"
)
_SUFFIX_CANON = {
    "k": "K",
    "χιλ": "K",
    "m": "M",
    "mn": "M",
    "εκ": "M",
    "εκατ": "M",
    "b": "B",
    "bn": "B",
    "δισ": "B",
}
RAW_AMOUNT_MIN_DIGITS = 4


def _parse_amount(number: str, suffixed: bool) -> tuple[int, int]:
    """(integer digits, decimal places), reading Greek and English separators."""
    seps = [c for c in number if c in ".,"]
    if not seps:
        return len(number), 0
    if len(set(seps)) == 2:
        decimal = number.rfind(".") if number.rfind(".") > number.rfind(",") else number.rfind(",")
        integer, fraction = number[:decimal], number[decimal + 1 :]
        return len(re.sub(r"\D", "", integer)), len(fraction)
    groups = re.split(r"[.,]", number)
    thousands = all(len(g) == 3 for g in groups[1:]) and (len(groups) > 2 or not suffixed)
    if thousands:
        return len("".join(groups)), 0
    return len("".join(groups[:-1])), len(groups[-1])


def _currency_forms(text: str) -> list[tuple[str, int, str]]:
    found = []
    for match in CURRENCY_AMOUNT.finditer(fold(text)):
        number = match.group(1) or match.group(3)
        suffix = (match.group(2) or match.group(4) or "").rstrip(".")
        unit = _SUFFIX_CANON.get(suffix, "")
        digits, decimals = _parse_amount(number, bool(unit))
        if not unit and digits < RAW_AMOUNT_MIN_DIGITS:
            continue
        found.append((unit or "raw", decimals, " ".join(match.group(0).split())))
    return found


def check_number_formats(deck: Deck, out: Collector) -> str:
    """Warning by design: mixed precision can be deliberate (a rate beside a total)."""
    forms: list[tuple[int, str, int, str]] = []
    for s in deck.slides:
        for text in _slide_paragraphs(s):
            for unit, decimals, literal in _currency_forms(text):
                forms.append((s.position, unit, decimals, literal))
    out.count(len(forms))
    units = {u for _, u, _, _ in forms}
    if "raw" in units and units - {"raw"}:
        raw = next((p, lit) for p, u, _, lit in forms if u == "raw")
        short = next((p, lit) for p, u, _, lit in forms if u != "raw")
        out.add(
            raw[0],
            f"deck mixes raw and abbreviated currency notation (slide {raw[0]}: {raw[1]}, slide {short[0]}: {short[1]}); pick one",
        )
    for unit in sorted(units - {"raw"}):
        widths = {d for _, u, d, _ in forms if u == unit}
        if len(widths) > 1:
            samples = sorted({lit for _, u, _, lit in forms if u == unit})[:4]
            first = min(p for p, u, _, _ in forms if u == unit)
            out.add(
                first,
                f"{unit} amounts use {len(widths)} decimal precisions ({', '.join(str(w) for w in sorted(widths))} places): {', '.join(samples)}",
            )
    if out.findings:
        return f"{len(out.findings)} formatting inconsistency/ies across {len(forms)} currency amount(s)"
    return f"{len(forms)} currency amount(s), consistent notation and precision"


# Phrases, not single words: "leverage ratio" and "robust capital base" are Basel
# language, and "unlock" is a card feature. The verb uses are the register tell.
AI_SLOP_TERMS = (
    ("in today's fast-paced world", r"\bin today'?s fast[- ]paced world\b"),
    ("unprecedented change", r"\bunprecedented change\b"),
    ("in the era of digital transformation", r"\bin the era of digital transformation\b"),
    (
        "leverage",
        r"\b(?:we|they|to|will|can|could|must|should|and|by|us)\s+leverag(?:e|ing)\b|\bleverag(?:e|es|ing)\s+(?:our|the\s+power|synerg\w*)\b",
    ),
    ("seamless", r"\bseamless(?:ly)?\b"),
    ("robust", r"\brobust\s+(?:solutions?|platforms?|approach|ecosystem|offering)\b"),
    (
        "unlock",
        r"\bunlock(?:s|ing)?\s+(?:value|potential|growth|opportunit\w*|synerg\w*|the\s+(?:full\s+)?potential)\b",
    ),
    ("elevate", r"\belevat(?:e|es|ing)\b"),
    ("delve", r"\bdelv(?:e|es|ing)\b"),
    ("tapestry", r"\btapestry\b"),
    ("game-changer", r"\bgame[- ]chang(?:er|ing)\b"),
    ("studies show", r"\bstudies show\b"),
    ("research indicates", r"\bresearch (?:indicates|shows)\b"),
    ("experts agree", r"\bexperts agree\b"),
)
AI_SLOP_CLUSTER = 2
_AI_SLOP_PATTERNS = tuple((term, re.compile(pattern)) for term, pattern in AI_SLOP_TERMS)


def check_ai_slop(deck: Deck, out: Collector) -> str:
    for s in deck.slides:
        text = fold(s.all_text())
        if not text.strip():
            continue
        out.count()
        hits = [term for term, pattern in _AI_SLOP_PATTERNS if pattern.search(text)]
        if len(hits) >= AI_SLOP_CLUSTER:
            out.add(
                s.position,
                f"{len(hits)} AI-register phrases clustered ({', '.join(repr(h) for h in hits)})",
            )
    if out.findings:
        return f"{len(out.findings)} of {out.examined} slide(s) cluster {AI_SLOP_CLUSTER}+ AI-register phrases"
    return f"{out.examined} slide(s) scanned against {len(AI_SLOP_TERMS)} phrases, none clustering"


_OFFICIAL_NAME = re.compile(r"\bεθνικ\w*\s+τραπεζ\w*\s+τησ\s+ελλαδοσ\b")


def check_official_name(deck: Deck, out: Collector) -> str:
    for s in deck.slides:
        text = s.all_text()
        if not text.strip():
            continue
        out.count()
        if _OFFICIAL_NAME.search(fold(text)):
            out.add(
                s.position,
                'the bank\'s name is «Εθνική Τράπεζα», without "της Ελλάδος" (writing style)',
            )
    if out.findings:
        return f"{len(out.findings)} slide(s) use the old official name"
    return f"{out.examined} slide(s) use the current official name"


# Schema order of the children the builder and PowerPoint both write. A child out of
# order makes PowerPoint repair the file or refuse to open it.
_PPR_ORDER = [
    ("lnSpc",), ("spcBef",), ("spcAft",), ("buClrTx", "buClr"), ("buSzTx", "buSzPct", "buSzPts"),
    ("buFontTx", "buFont"), ("buNone", "buAutoNum", "buChar", "buBlip"), ("tabLst",), ("defRPr",), ("extLst",),
]  # fmt: skip
_RPR_ORDER = [
    ("ln",), _FILL_TAGS, ("effectLst", "effectDag"), ("highlight",), ("uLnTx", "uLn"), ("uFillTx", "uFill"),
    ("latin",), ("ea",), ("cs",), ("sym",), ("hlinkClick",), ("hlinkMouseOver",), ("rtl",), ("extLst",),
]  # fmt: skip
_SPPR_ORDER = [
    ("xfrm",), ("custGeom", "prstGeom"), _FILL_TAGS, ("ln",), ("effectLst", "effectDag"), ("scene3d",), ("sp3d",), ("extLst",),
]  # fmt: skip
_BODYPR_ORDER = [
    ("prstTxWarp",),
    ("noAutofit", "normAutofit", "spAutoFit"),
    ("scene3d",),
    ("sp3d",),
    ("flatTx",),
    ("extLst",),
]
_ORDERED = {
    f"{A}pPr": ("a:pPr", _PPR_ORDER),
    **{f"{A}lvl{i}pPr": (f"a:lvl{i}pPr", _PPR_ORDER) for i in range(1, 10)},
    f"{A}defPPr": ("a:defPPr", _PPR_ORDER),
    f"{A}rPr": ("a:rPr", _RPR_ORDER),
    f"{A}defRPr": ("a:defRPr", _RPR_ORDER),
    f"{A}endParaRPr": ("a:endParaRPr", _RPR_ORDER),
    f"{P}spPr": ("p:spPr", _SPPR_ORDER),
    f"{C}spPr": ("c:spPr", _SPPR_ORDER),
    f"{A}bodyPr": ("a:bodyPr", _BODYPR_ORDER),
}


def _order_problem(el: Any, order: list[tuple[str, ...]]) -> str | None:
    rank = {name: i for i, group in enumerate(order) for name in group}
    last, last_name = -1, ""
    for child in el:
        name = _local(child.tag)
        if name not in rank:
            continue
        if rank[name] < last:
            return f"a:{name} after a:{last_name}"
        last, last_name = rank[name], name
    return None


def check_ooxml_order(deck: Deck, out: Collector) -> str:
    def walk(root: Any, position: int, where: str) -> None:
        for el in root.iter():
            spec = _ORDERED.get(el.tag) if isinstance(el.tag, str) else None
            if spec is None:
                continue
            out.count()
            problem = _order_problem(el, spec[1])
            if problem:
                out.add(
                    position,
                    f"{spec[0]} children out of schema order in {where}: {problem}; PowerPoint may repair or refuse the file",
                )

    for s in deck.slides:
        for shape in s.shapes:
            if shape.depth == 0:
                walk(shape.el, s.position, f'"{shape.name}"' if shape.name else shape.kind)
    for chart in deck.charts():
        walk(chart.root, chart.slide.position, f"chart {chart.stem}")
    if out.findings:
        return f"{len(out.findings)} element(s) out of schema order among {out.examined}"
    return f"{out.examined} property element(s) in schema order"


# ======================================================================
# The registry: the one place a check is declared. VALIDATOR.md mirrors it.
# ======================================================================


@dataclass(frozen=True)
class CheckSpec:
    name: str
    func: Callable[[Deck, Collector], str]
    severity: str
    rule: str
    source: str
    candidates: str
    universal: bool = False


CHECKS: tuple[CheckSpec, ...] = (
    CheckSpec("Slides", check_slides, "error", "The deck has at least one slide and every slide-list entry resolves.", "implicit", "slide-list entries", True),
    CheckSpec("Dimensions", check_dimensions, "error", "Slide size is exactly 12192000 x 6858000 EMU (13.333 x 7.5 in, PowerPoint Widescreen).", "dimensions.md; tokens geometry.slide", "the p:sldSz element", True),
    CheckSpec("Theme", check_theme, "warning", "Theme colour slots are NBG colours and the major/minor fonts are Aptos.", "colors.md; tokens colors, fonts", "theme colour slots and font slots"),
    CheckSpec("Background", check_background, "error", "Every slide's effective background (slide, layout, master) is white.", "Standard #2", "slides", True),
    CheckSpec("Colors", check_colors, "error", "Every colour in slides (with the layout and master shapes they show) and charts, including theme references and shape-style colours, is in tokens.yaml; retired colours fail with their reason.", "colors.md; tokens colors, retired_colors", "colour references in slide, layout and master shapes and chart parts", True),
    CheckSpec("Fonts", check_fonts, "error", "Every font text is drawn in is allowed: each run's resolved typeface (theme font included), symbol and bullet fonts, chart fonts; Aptos SemiBold is forbidden.", "typography.md; tokens fonts", "text runs, symbol and bullet fonts, chart fonts", True),
    CheckSpec("Font Sizes", check_font_sizes, "error", "Text is 10pt or more; sources and footnotes 11pt or more; only the header pill may be 9pt.", "Standard #11; tokens accessibility, type.source", "sized text runs in slide, layout and master shapes, table cells and chart parts", True),
    CheckSpec("Contrast", check_contrast, "error", "Text meets WCAG AA against what is behind it; muted grey is waived only for page numbers and axis labels on white.", "Standard #22", "text runs with a resolvable colour and background", True),
    CheckSpec("Boundaries", check_boundaries, "error", "No element extends past a slide edge.", "dimensions.md", "positioned shapes, pictures, charts, tables and connectors", True),
    CheckSpec("Safe Zones", check_safe_zones, "error", "Content stays between the 0.374in gutter and the right boundary, above the 6.85in footer line; sources end by 6.5in.", "dimensions.md; tokens geometry", "content elements (logo footprints and the page number excluded)", True),
    CheckSpec("Content Spacing", check_content_spacing, "error", "The first body element starts at 1.3in or lower and 0.15in or more below the title.", "Standard #11; tokens geometry.body_top", "slides with a content title and body content"),
    CheckSpec("Text Fit", check_text_fit, "error", "Measured text fits its box, a pill is as wide as its text, cover titles stay on one line, text boxes do not overlap, no opaque shape on top hides text, tables do not grow into the footer.", "Standards #11, #13; dimensions.md", "text frames and tables", True),
    CheckSpec("Text Margins", check_text_margins, "error", "Unfilled text boxes have zero margins on all four sides.", "dimensions.md (Text Box Rules)", "unfilled text boxes carrying text"),
    CheckSpec("Logo", check_logo, "error", "Every slide but the back cover carries the Greek wordmark at the small or large position (on the slide, or its layout or master), unstretched; the cover uses the large logo.", "Standards #4, #10, #17", "slides other than the last", True),
    CheckSpec("Back Cover", check_back_cover, "error", "The last slide holds only the centred oval emblem: no text, no page number, no corner logo, counting the layout and master shapes it shows.", "Standard #19", "the last slide in presentation order", True),
    CheckSpec("Thank You Check", check_thank_you, "error", "No thank-you, closing or Q&A slide.", "Standard #19; layouts.md", "the last two slides and slides of 12 words or fewer"),
    CheckSpec("Decorative", check_decorative, "error", "No decorative presets (stars, hearts, clouds...); an ellipse is decorative only if textless, over 0.5in and carrying no icon.", "Standards #3, #19", "preset-geometry shapes"),
    CheckSpec("Shadows", check_shadows, "error", "No shape or chart draws a shadow, including one inherited from the theme's effect styles.", "brand-system README; tokens components.card.shadow", "shapes and charts", True),
    CheckSpec("Em Dashes", check_em_dashes, "error", "No em dash (or ' -- ') in slide or chart text; a spaced en dash is a warning.", "Standard #7", "text items in slides and charts", True),
    CheckSpec("Title Style", check_title_style, "error", "Titles are Regular weight and start on the 0.374in gutter (unless beside a gutter-anchored number or pill); a closing period is a warning.", "Standards #15, #16; brand-system README", "slides with a title", True),
    CheckSpec("Title Length", check_title_length, "error", "A content title fits one line: at most tokens type.title.max_chars characters.", "Standard #11; tokens type.title", "slides with a content title"),
    CheckSpec("Slide Titles", check_slide_titles, "error", "Every slide carrying text has a title, and no two titles are the same.", "presentation-qa (unique titles)", "slides carrying text", True),
    CheckSpec("Action Titles", check_action_titles, "warning", "A content title states a finding: not a topic label, at most 15 words.", "presentation-qa 2A", "slides with a content title"),
    CheckSpec("Chart Types", check_chart_types, "error", "No pie charts of any kind; part-to-whole is a doughnut.", "charts.md", "chart parts"),
    CheckSpec("Chart Data", check_chart_data, "error", "Every chart has series and categories; over 6 series warns, over 8 fails.", "Standard #22; tokens charts.max_series", "chart parts"),
    CheckSpec("Chart Styling", check_chart_styling, "error", "Line and area series carry an explicit line colour; automatic colours must resolve to NBG accents; line markers are hollow circles (warning).", "Standard #5; charts.md; tokens charts.line", "chart series"),
    CheckSpec("Zero Baseline", check_zero_baseline, "error", "Bar and column value axes include zero, including an automatic axis on close values, which PowerPoint draws without it.", "keynote.md; charts.md", "value axes of bar and column charts"),
    CheckSpec("Exhibit Sources", check_exhibit_sources, "error", "Every slide with a chart or table carries a dated source line.", "deck.schema.json content.source; presentation-qa", "slides carrying a chart or table"),
    CheckSpec("Alt Text", check_alt_text, "error", "Pictures, charts, tables and groups carry descriptive alt text; brand logos are decorative.", "Standard #22 (EN 301 549)", "top-level pictures, graphic frames and groups"),
    CheckSpec("Bank Branding", check_bank_branding, "error", "A chart plotting two or more banks colours each in its brand colour and the slide carries each plotted bank's own logo.", "presentation-qa 2H; tokens banks, extended_palettes.peer_banks", "charts plotting two or more banks"),
    CheckSpec("Number Formats", check_number_formats, "warning", "One currency notation per deck and one decimal precision per unit; Greek separators understood.", "typography.md", "currency amounts in slide text"),
    CheckSpec("AI Slop", check_ai_slop, "warning", "No slide clusters two or more AI-register phrases.", "presentation-qa (tone)", "slides carrying text"),
    CheckSpec("Official Name", check_official_name, "warning", "The bank is «Εθνική Τράπεζα», never «Εθνική Τράπεζα της Ελλάδος».", "writing style", "slides carrying text"),
    CheckSpec("OOXML Order", check_ooxml_order, "error", "Paragraph, run, shape and body property children follow the DrawingML schema order.", "ISO/IEC 29500 DrawingML", "property elements in slides and charts", True),
)  # fmt: skip
CHECK_NAMES: tuple[str, ...] = tuple(spec.name for spec in CHECKS)
CHECKS_BY_NAME: dict[str, CheckSpec] = {spec.name: spec for spec in CHECKS}


def run_check(spec: CheckSpec, deck: Deck) -> ValidationResult:
    out = Collector(spec.severity)
    message = spec.func(deck, out)
    return ValidationResult(
        spec.name,
        passed=not out.findings,
        message=message,
        examined=out.examined,
        severity=spec.severity,
        findings=out.findings,
        not_examined=dict(out.not_examined),
    )


def validate_presentation(
    pptx_path: str | Path, only: Iterable[str] | None = None
) -> list[ValidationResult]:
    """Run the checks (all, or the named ones) in registry order."""
    wanted = set(only) if only is not None else None
    unknown = (wanted or set()) - set(CHECK_NAMES)
    if unknown:
        raise ValueError(f"unknown check(s): {', '.join(sorted(unknown))}")
    with load_deck(pptx_path) as deck:
        return [run_check(spec, deck) for spec in CHECKS if wanted is None or spec.name in wanted]


def exit_code(results: list[ValidationResult], strict: bool = False) -> int:
    if any(r.status == "fail" for r in results):
        return 1
    if strict and any(
        r.status == "skipped" and CHECKS_BY_NAME.get(r.name, CHECKS[0]).universal for r in results
    ):
        return 1
    if strict and any(SMARTART_UNREAD in r.not_examined for r in results):
        return 1
    return 0


def summary(results: list[ValidationResult]) -> dict[str, int]:
    counts = Counter(r.status for r in results)
    return {
        "passed": counts["pass"],
        "failed": counts["fail"],
        "warnings": counts["warn"],
        "skipped": counts["skipped"],
        "checks": len(results),
    }


def report_json(
    path: str | Path, results: list[ValidationResult], strict: bool = False
) -> dict[str, Any]:
    return {
        "file": str(Path(path).expanduser().resolve()),
        "strict": strict,
        "summary": summary(results),
        "checks": [
            {
                "name": r.name,
                "status": r.status,
                "severity": r.severity,
                "examined": r.examined,
                "message": r.message,
                "details": [
                    {"slide": f.slide, "severity": f.severity, "message": f.message}
                    for f in r.findings
                ],
                "not_examined": r.not_examined,
            }
            for r in results
        ],
    }


def use_color(stream: Any, env: dict[str, str] | None = None) -> bool:
    env = dict(os.environ) if env is None else env
    try:
        tty = bool(stream.isatty())
    except (AttributeError, ValueError):
        tty = False
    return tty and "NO_COLOR" not in env and env.get("TERM") != "dumb"


_SYMBOLS = {"pass": ("✓", "92"), "fail": ("✗", "91"), "warn": ("!", "93"), "skipped": ("○", "93")}


def print_results(
    results: list[ValidationResult], pptx_path: str, color: bool | None = None, strict: bool = False
) -> bool:
    """Print the report; True when nothing failed (warnings and skips do not block)."""
    color = use_color(sys.stdout) if color is None else color

    def paint(text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if color else text

    print("\nNBG Brand Validation Report")
    print(f"File: {pptx_path}\n")
    for r in results:
        symbol, code = _SYMBOLS[r.status]
        examined = "examined nothing" if r.examined == 0 else f"examined {r.examined}"
        not_examined = ""
        if r.not_examined:
            not_examined = "; not examined: " + ", ".join(
                f"{n} {why}" for why, n in r.not_examined.items()
            )
        print(f"{paint(symbol, code)} {r.name}: {r.message} [{examined}{not_examined}]")
        for f in r.findings:
            tag = "" if f.severity == r.severity else f" ({f.severity})"
            print(f"    - {f.text()}{tag}")
        if r.findings:
            print()
    counts = summary(results)
    print(
        f"\nSummary: {counts['passed']} passed, {counts['failed']} failed, "
        f"{counts['warnings']} warning(s), {counts['skipped']} skipped"
        + (" (examined nothing)" if counts["skipped"] else "")
    )
    fixes = sorted(
        ((f, r.name) for r in results for f in r.findings),
        key=lambda item: (item[0].slide is None, item[0].slide or 0),
    )
    if fixes:
        print("\nFix list, by slide:")
        current: int | None | str = "start"
        for f, name in fixes:
            if f.slide != current:
                current = f.slide
                print(f"  {'Deck' if f.slide is None else f'Slide {f.slide}'}")
            print(f"    [{f.severity}] {name}: {f.message}")
    if exit_code(results, strict) == 0:
        notes = []
        if counts["warnings"]:
            notes.append("warnings do not block but are real findings")
        if counts["skipped"]:
            notes.append("a skipped check examined nothing and proves nothing")
        print(
            paint(
                "No blocking failures" + (f"; {'; '.join(notes)}." if notes else "."),
                "92" if not notes else "93",
            )
        )
    else:
        print(paint("Blocking failures: fix them before the deck ships.", "91"))
    return counts["failed"] == 0


def list_checks(fmt: str) -> None:
    rows = [
        {
            "name": s.name,
            "severity": s.severity,
            "rule": s.rule,
            "source": s.source,
            "candidates": s.candidates,
            "universal": s.universal,
        }
        for s in CHECKS
    ]
    if fmt == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    for row in rows:
        print(
            f"{row['name']} [{row['severity']}]: {row['rule']} (source: {row['source']}; candidates: {row['candidates']})"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a .pptx against the NBG brand (tokens.yaml)."
    )
    parser.add_argument("deck", nargs="?", help="the .pptx to validate")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="a skipped check that applies to every deck, or a SmartArt diagram with no drawing part, fails",
    )
    parser.add_argument(
        "--list-checks", action="store_true", help="print every check with its rule and source"
    )
    args = parser.parse_args(argv)
    _utf8_streams()
    if args.list_checks:
        list_checks(args.format)
        return 0
    if not args.deck:
        parser.print_usage(sys.stderr)
        return 2
    try:
        results = validate_presentation(args.deck)
        # Writing the report is part of running: a failure here leaves the deck
        # unvalidated, which is exit 2, never the "a check failed" exit 1.
        if args.format == "json":
            report = report_json(args.deck, results, args.strict)
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_results(results, args.deck, strict=args.strict)
    except DeckError as e:
        print(f"nbg_validate: cannot validate: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # a crash is "could not run", never a brand verdict
        print(
            f"nbg_validate: validator error, the deck is UNVALIDATED: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return 2
    return exit_code(results, args.strict)


def _utf8_streams() -> None:
    """UTF-8 on stdout and stderr whatever the console's code page: a Windows cp1252 or
    cp1253 console cannot encode the status marks or Greek slide text."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


if __name__ == "__main__":
    sys.exit(main())
