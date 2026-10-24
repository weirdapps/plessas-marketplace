#!/usr/bin/env python3
"""NBG HTML decks: build, check and export an editable, self-contained HTML deck.

    decks-py html-build <deck.src.html> <deck.html>
    decks-py html-check <deck.html> [--static] [--format json]
    decks-py html-pdf   <deck.html> [-o deck.pdf] [--png <dir>] [--dpi 80]

The deck is HTML a person or an agent writes with the classes of runtime/deck.css:
one <main class="deck"> holding one <section class="slide"> per slide, each a
1920 x 1080 artboard (the 13.333 x 7.5 in PowerPoint slide at 144 px per inch).

build   inlines the design system (its :root block generated from tokens.yaml, so
        the HTML and PowerPoint decks share one brand), the editing runtime and
        every local picture as a data URI. The result is one file that opens
        anywhere, edits in place and prints one page per slide. Building a built
        deck again (an edited copy included) swaps in the current runtime and keeps
        the slides, which is how an old deck gets a newer editor.
check   static: one deck, self-contained, NBG colours and fonts only, no shadows,
        no em dashes. Then, unless --static, opens the deck in headless Chrome and
        reports per slide: pictures that failed, text under the 10pt floor, content
        off the slide, across the gutter, into the footer or past the body area.
pdf     prints with headless Chrome at the artboard size and verifies one page per
        slide at 1920 x 1080 px, then (--png) draws each page for visual QA.

Exit codes: 0 ok; 1 the check or the verification failed; 2 bad input or another
error; 3 no Chrome, Edge or Chromium found (the HTML stays the deliverable);
4 the PDF was written but Aptos was not embedded (another font stood in).
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nbg_tokens  # noqa: E402

HERE = Path(__file__).resolve().parent
RUNTIME_CSS = HERE / "runtime" / "deck.css"
RUNTIME_JS = HERE / "runtime" / "editor.js"
ASSETS = HERE.parent.parent / "assets"
LOGO_WORDMARK = ASSETS / "nbg-logo-gr.svg"  # Standard #10: the Greek wordmark, always
LOGO_EMBLEM = ASSETS / "nbg-back-cover-logo.png"

PX_PER_IN = 144  # 1920 px / 13.333 in
PX_PER_PT = 2  # 144 px per inch / 72 pt per inch
SLIDE_W, SLIDE_H = 1920, 1080
RUNTIME_VERSION = "1"

NO_BROWSER = 3
FONT_FALLBACK = 4

# Our own blocks carry this attribute, so a rebuild finds and replaces them.
RUNTIME_BLOCK_RE = re.compile(
    r"<(style|script|meta)\b[^>]*\bdata-nbg-runtime\b[^>]*>(?:.*?</\1>)?\s*", re.S | re.I
)
IMG_SRC_RE = re.compile(
    r"""(<(?:img|image|source)\b[^>]*?\s(?:src|href|xlink:href)\s*=\s*)(["'])(.*?)\2""", re.S | re.I
)
CSS_URL_RE = re.compile(r"""url\(\s*(["']?)(.*?)\1\s*\)""", re.I)
DATA_URI_RE = re.compile(r"data:[^\"')\s]+", re.I)
HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
SHADOW_RE = re.compile(r"(box-shadow|text-shadow)\s*:\s*(?!none\b)[^;\"']+|drop-shadow\(", re.I)
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;\"'}]+(?:\"[^\"]*\"[^;\"'}]*)*)", re.I)
GENERIC_FONTS = {"sans-serif", "serif", "monospace", "inherit", "initial", "unset", "system-ui"}
# Written as a code point: a repository hook refuses literal em dashes in any file.
EM_DASH = chr(0x2014)


class DeckError(Exception):
    """Bad input: reported with exit 2."""


# --------------------------------------------------------------------- tokens
def _px_in(v: float) -> str:
    return f"{round(float(v) * PX_PER_IN, 2):g}px"


def _px_pt(v: float) -> str:
    return f"{round(float(v) * PX_PER_PT, 2):g}px"


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def root_block() -> str:
    """The :root custom properties deck.css draws with, all from tokens.yaml."""
    t = nbg_tokens.load()
    g, c, ty = t["geometry"], t["components"], t["type"]
    v: dict[str, str] = {}
    for name, hexv in t["colors"].items():
        v[f"c-{name.replace('_', '-')}"] = f"#{hexv}"
    for i, hexv in enumerate(t["charts"]["palette"], 1):
        v[f"chart-{i}"] = f"#{hexv}"
    for role, spec in ty.items():
        v[f"fs-{role.replace('_', '-')}"] = _px_pt(spec["size"])
    v["fs-body-max"] = _px_pt(ty["body"]["max_size"])
    v["fs-min"] = _px_pt(t["accessibility"]["min_font_pt"])
    v["fs-takeaway"] = _px_pt(c["takeaway_strip"]["size"])
    fonts = t["fonts"]
    stack = [fonts["primary"], *fonts["fallback"]]
    v["font-stack"] = ", ".join(f'"{f}"' for f in stack) + ", sans-serif"
    v["bullet-font"] = f'"{fonts["bullet_glyph"]}", sans-serif'
    v["lh-title"] = str(t["line_spacing"]["title"])
    # CSS line-height is not PowerPoint's line spacing: 1.1 sets visibly tighter in a browser.
    v["lh-body"] = f"{t['line_spacing']['body'] + 0.12:g}"

    v["gutter"] = _px_in(g["gutter"])
    v["content-w"] = _px_in(g["content_w"])
    v["title-y"] = _px_in(g["title"]["y"])
    v["title-y-pill"] = _px_in(g["title"]["y_with_pill"])
    v["title-h"] = _px_in(g["title"]["h"])
    v["body-top"] = _px_in(g["body_top"])
    v["body-bottom"] = _px_in(g["body_bottom"])
    v["footer-top"] = _px_in(g["footer_top"])
    v["grid-gap"] = _px_in(g["grid_gap"])
    v["source-h"] = _px_in(g["source_line"]["h"])
    v["caption-gap"] = _px_in(g["caption"]["gap_below"])
    for key in ("logo_small", "logo_large", "logo_back", "page_number"):
        for dim in ("x", "y", "w", "h"):
            if dim in g[key]:
                v[f"{key.replace('_', '-')}-{dim}"] = _px_in(g[key][dim])

    pill = c["pill"]
    v["pill-y"] = _px_in(pill["y"])
    v["pill-h"] = _px_in(pill["h"])
    v["pill-min-w"] = _px_in(pill["min_w"])
    v["pill-pad-x"] = _px_in(pill["pad_x"])
    v["pill-radius"] = _px_in(pill["radius_in"])
    b = c["bullets"]
    v["bullet-indent"] = _px_in(b["indent_emu"] / 914400)
    v["bullet-space"] = _px_pt(b["space_before_pt"])
    v["bullet-space-l2"] = _px_pt(b["space_before_l2_pt"])
    card = c["card"]
    v["card-radius"] = _px_in(card["radius_in"])
    v["card-pad"] = _px_in(card["pad"])
    v["card-gap"] = _px_in(card["gap"])
    v["card-min-h"] = _px_in(card["min_h"])
    v["icon-size"] = _px_in(card["icon"])
    v["recommended-border"] = _px_pt(card["recommended"]["border_pt"])
    v["recommended-tab-h"] = _px_in(card["recommended_tab"]["h"])
    v["recommended-tab-pad-x"] = _px_in(card["recommended_tab"]["pad_x"])
    v["badge-size"] = _px_in(c["badge"]["size_in"])
    ts = c["takeaway_strip"]
    v["takeaway-h"] = _px_in(ts["h"])
    v["takeaway-pad-x"] = _px_in(ts["pad_x"])
    kpi = c["kpi"]
    v["kpi-radius"] = _px_in(kpi["radius_in"])
    v["kpi-pad"] = _px_in(kpi["pad"])
    # A tile takes its content's height, never less than half the PowerPoint card.
    v["kpi-min-h"] = _px_in(kpi["h"] / 2)
    tb = c["table"]
    v["table-header-h"] = _px_in(tb["header_h"])
    v["table-row-h"] = _px_in(tb["row_h"])
    v["table-inset"] = _px_in(tb["cell_inset"])
    pr = c["process"]
    v["process-tile"] = _px_in(pr["tile"]["size"])
    v["process-arrow-w"] = _px_in(pr["arrow"]["w"])
    v["process-arrow-h"] = _px_in(pr["arrow"]["h"])
    v["process-gap"] = _px_in(pr["gap"])
    v["process-label-gap"] = _px_in(pr["label_gap"])
    v["two-col-heading-gap"] = _px_in(c["two_column"]["heading_gap"])
    v["image-caption-gap"] = _px_in(c["image"]["caption_gap"])
    v["bar-gap"] = _px_in(g["grid_gap"])
    v["axis-line"] = _px_pt(t["charts"]["category_axis"]["line_pt"])
    cov = c["cover"]
    v["cover-title-x"] = _px_in(cov["title"]["x"])
    v["cover-title-y"] = _px_in(cov["title"]["y"])
    v["cover-title-w"] = _px_in(cov["title"]["w"])
    v["cover-subtitle-gap"] = _px_in(cov["subtitle"]["gap_below_title"])
    v["cover-location-x"] = _px_in(cov["location"]["x"])
    v["cover-location-y"] = _px_in(cov["location"]["y"])
    v["cover-date-y"] = _px_in(cov["date"]["y"])
    dv = c["divider"]
    v["divider-y"] = _px_in(dv["number"]["y"])
    v["divider-number-x"] = _px_in(dv["number"]["x"])
    v["divider-title-x"] = _px_in(dv["title"]["x"])
    v["divider-title-w"] = _px_in(dv["title"]["w"])
    ct = c["contents"]
    v["contents-header-y"] = _px_in(ct["header"]["y"])
    v["contents-first-row-y"] = _px_in(ct["first_row_y"])
    v["contents-number-w"] = _px_in(ct["number_w"])
    v["contents-row-step"] = _px_in(ct["row_step"])

    v["logo-wordmark"] = f'url("{_data_uri(LOGO_WORDMARK)}")'
    v["logo-emblem"] = f'url("{_data_uri(LOGO_EMBLEM)}")'
    v["logo-aspect"] = f"{g['logo_aspect']:g}"
    v.update(keynote_vars(t))
    body = "\n".join(f"  --{k}: {val};" for k, val in v.items())
    return ":root {\n" + body + "\n}\n"


# Keynote chassis in its own 2560 px space (shared/brand-system/keynote.md, the
# values nbg_keynote.py draws with). The HTML artboard is 1920 wide, so each is
# x 0.75. Colours and the gutter come from tokens.yaml.
KEYNOTE_PX = {
    "logo-y": 1300,
    "logo-h": 46,
    "cover-logo-y": 1195,
    "cover-logo-h": 60,
    "closing-logo-y": 1290,
    "closing-logo-h": 52,
    "back-logo-h": 150,
    "kicker-y": 150,
    "kicker-indent": 44,
    "kicker-square": 22,
    "kicker-track": 6,
    "title-y": 250,
    "cover-title-y": 300,
    "cover-subtitle-y": 500,
    "speaker-y": 1140,
    "statement-y": 470,
    "statement-w": 2260,
    "statement-w-photo": 1500,
    "coda-y": 980,
    "closing-y": 330,
    "closing-coda-y": 1130,
    "hero-y": 270,
    "hero-w": 2100,
    "hero-w-photo": 1700,
    "hero-w-right": 1250,
    "duo-y": 420,
    "duo-right-x": 1360,
    "bars-base": 1170,
    "bar-w": 380,
    "axis-label-y": 1235,
    "points-y": 500,
    "points-square": 18,
    "takeaway-y": 1100,
    "divider-x": 1290,
    "divider-y": 560,
    "source-y": 1312,
    "footer-top": 1280,
    "fs-kicker": 30,
    "fs-title": 56,
    "fs-cover-title": 150,
    "fs-caption": 54,
    "fs-role": 27,
    "fs-source": 24,
    "fs-body": 36,
    "fs-statement": 80,
    "fs-hero": 420,
    "fs-duo": 280,
    "fs-divider": 96,
    "fs-bar-value": 60,
    "fs-bar-cat": 34,
    "fs-bar-value-many": 46,
    "fs-bar-cat-many": 30,
    "fs-min": 24,
    "fs-coda": 44,
    "fs-closing-coda": 40,
}
KEYNOTE_SCALE = SLIDE_W / 2560


def _rgba(hexv: str, alpha: float) -> str:
    r, g, b = (int(hexv[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha:g})"


def white_wordmark() -> str:
    """The Greek wordmark recoloured white for dark grounds, as nbg_keynote.py does."""
    svg = LOGO_WORDMARK.read_text(encoding="utf-8")
    svg = re.sub(r'fill="#[0-9A-Fa-f]{3,6}"', 'fill="#FFFFFF"', svg)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def keynote_vars(t: dict[str, Any]) -> dict[str, str]:
    k = t["keynote"]
    v = {f"k-{name}": f"{round(px * KEYNOTE_SCALE, 2):g}px" for name, px in KEYNOTE_PX.items()}
    v["k-gutter"] = f"{round(k['gutter_px'] * KEYNOTE_SCALE, 2):g}px"
    for name, hexv in k["dark"].items():
        v[f"k-{name.replace('_', '-')}"] = f"#{hexv}"
    ground = k["dark"]["ground_from"]
    # nbg_keynote.py adds a faint cyan bloom (0, 40, 46) to the ground, lower left.
    r, g, b = (int(ground[i : i + 2], 16) for i in (0, 2, 4))
    v["k-bloom"] = f"rgb({r}, {min(255, g + 40)}, {min(255, b + 46)})"
    v["k-scrim-strong"] = _rgba(ground, 0.9)
    v["k-scrim-full"] = _rgba(ground, 0.55)
    v["k-band"] = _rgba(ground, 0.5)
    v["k-vignette"] = "rgba(0, 0, 0, 0.45)"
    # Film grain, which also stops the dark gradient from banding.
    noise = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>"
        "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/>"
        "<feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0'/></filter>"
        "<rect width='240' height='240' filter='url(%23n)'/></svg>"
    )
    v["k-grain"] = 'url("data:image/svg+xml;utf8,' + noise.replace('"', "'") + '")'
    v["logo-wordmark-white"] = f'url("{white_wordmark()}")'
    return v


def design_css() -> str:
    return root_block() + RUNTIME_CSS.read_text(encoding="utf-8")


def runtime_js() -> str:
    js = RUNTIME_JS.read_text(encoding="utf-8")
    if "</script" in js.lower():
        raise DeckError("runtime/editor.js contains '</script', which would end the inline block")
    return js


# ---------------------------------------------------------------------- build
def strip_runtime(text: str) -> str:
    return RUNTIME_BLOCK_RE.sub("", text)


def embed_images(text: str, base: Path) -> tuple[str, list[str]]:
    """Inline every local picture as a data URI. Returns the text and the problems."""
    problems: list[str] = []

    def resolve(ref: str) -> str | None:
        ref = html.unescape(ref.strip())
        if not ref or ref.startswith(("data:", "#")):
            return None
        if re.match(r"^[a-z][a-z0-9+.-]*://", ref, re.I) and not ref.lower().startswith("file://"):
            problems.append(
                f"external picture {ref[:80]}: download it and reference the local file"
            )
            return None
        path = Path(ref[7:] if ref.lower().startswith("file://") else ref).expanduser()
        if not path.is_absolute():
            path = base / path
        if not path.is_file():
            problems.append(f"picture not found: {ref}")
            return None
        if path.stat().st_size > 4 * 1024 * 1024:
            problems.append(f"picture over 4 MB: {ref}; shrink it first (decks-py measure image)")
            return None
        return _data_uri(path)

    def img(m: re.Match[str]) -> str:
        uri = resolve(m.group(3))
        return m.group(0) if uri is None else f"{m.group(1)}{m.group(2)}{uri}{m.group(2)}"

    def css(m: re.Match[str]) -> str:
        uri = resolve(m.group(2))
        return m.group(0) if uri is None else f'url("{uri}")'

    def markup(part: str) -> str:
        part = IMG_SRC_RE.sub(img, part)
        part = re.sub(
            r'(style\s*=\s*")([^"]*)(")',
            lambda m: m.group(1) + CSS_URL_RE.sub(css, m.group(2)).replace('"', "'") + m.group(3),
            part,
        )
        return re.sub(
            r"(<style\b[^>]*>)(.*?)(</style>)",
            lambda m: m.group(1) + CSS_URL_RE.sub(css, m.group(2)) + m.group(3),
            part,
            flags=re.S | re.I,
        )

    # A picture named inside an HTML comment is documentation, not content.
    parts = re.split(r"(<!--.*?-->)", text, flags=re.S)
    text = "".join(p if p.startswith("<!--") else markup(p) for p in parts)
    return text, problems


def build(src: Path, out: Path) -> dict[str, Any]:
    text = src.read_text(encoding="utf-8")
    text = strip_runtime(text)
    low = text.lower()
    if "<html" not in low or "<head" not in low or "<body" not in low:
        raise DeckError("the source needs <html>, <head> and <body>")
    if len(re.findall(r'<main\b[^>]*class\s*=\s*"[^"]*\bdeck\b', text, re.I)) != 1:
        raise DeckError('the source needs exactly one <main class="deck">')
    text, problems = embed_images(text, src.resolve().parent)
    if problems:
        raise DeckError("; ".join(problems))
    # The charset must sit in the first 1024 bytes or a browser may guess the
    # encoding and garble Greek, so it is re-emitted first on every build, ahead
    # of the 100 KB design system. Ours then goes first in <head>, so a <style>
    # the author adds after it wins. Every block we add ends in the whitespace a
    # rebuild strips with it, so building a built deck changes nothing.
    head_block = (
        '\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'\n<meta name="generator" content="nbg-html-deck {RUNTIME_VERSION}" data-nbg-runtime>'
        f'\n<style id="nbg-deck-css" data-nbg-runtime>\n{design_css()}</style>\n'
    )
    text = re.sub(
        r"<meta\b[^>]*(?:\bcharset\b|name\s*=\s*[\"']viewport[\"'])[^>]*>\s*", "", text, flags=re.I
    )
    m = re.search(r"<head\b[^>]*>\s*", text, re.I)
    if not m:
        raise DeckError("no <head> start tag")
    text = text[: m.end()].rstrip() + head_block + text[m.end() :]
    js = f'<script id="nbg-deck-runtime" data-nbg-runtime>\n{runtime_js()}</script>\n'
    idx = text.lower().rfind("</body>")
    text = text[:idx] + js + text[idx:]
    if not text.lstrip().lower().startswith("<!doctype"):
        text = "<!doctype html>\n" + text
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return {"out": str(out), "slides": count_slides(text), "bytes": out.stat().st_size}


# ---------------------------------------------------------------------- check
class _Scan(HTMLParser):
    """Collects what the static check needs from the author's part of a deck."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.slides = 0
        self.mains = 0
        self.styles: list[str] = []
        self.attrs_colour: list[str] = []
        self.text: list[str] = []
        self.external: list[str] = []
        self.scripts = 0
        self.handlers: set[str] = set()
        self.lang = False
        self.title = ""
        self.keynote = False
        # Per slide, for the keynote rules: its classes, whether it has notes, its bars.
        self.per_slide: list[dict[str, Any]] = []
        self._in_title = False
        self._in_style = False
        self._in_notes = False
        self._skip = 0  # inside a script or our runtime style

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        runtime = "data-nbg-runtime" in a
        classes = a.get("class", "").split()
        if tag == "html" and a.get("lang"):
            self.lang = True
        if tag == "title":
            self._in_title = True
        if tag == "main" and "deck" in classes:
            self.mains += 1
            self.keynote = "keynote" in classes
        if tag == "section" and "slide" in classes:
            self.slides += 1
            self.per_slide.append(
                {"classes": classes, "notes": False, "bars": 0, "charts": 0, "photo": False}
            )
        if self.per_slide:
            cur = self.per_slide[-1]
            if "notes" in classes:
                self._in_notes = True
            if "kbar" in classes:
                cur["bars"] += 1
            if "kbars" in classes:
                cur["charts"] += 1
            if "bg" in classes:
                cur["photo"] = True
        if tag == "script":
            self._skip += 1
            if not runtime and a.get("type") != "application/json":
                self.scripts += 1
            if a.get("src"):
                self.external.append(f"<script src={a['src'][:60]}>")
        if tag == "style":
            if runtime:
                self._skip += 1
            else:
                self._in_style = True
        if tag == "link" and re.search(r"stylesheet|preload|import|icon", a.get("rel", ""), re.I):
            self.external.append(f"<link href={a.get('href', '')[:60]}>")
        if tag in ("iframe", "object", "embed"):
            self.external.append(f"<{tag}>")
        for k, val in a.items():
            if k.startswith("on"):
                self.handlers.add(k)
            if k == "style":
                self.styles.append(val)
            if k in ("fill", "stroke", "stop-color", "color", "bgcolor"):
                self.attrs_colour.append(val)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "aside":
            self._in_notes = False
        if tag == "script" or (tag == "style" and not self._in_style):
            self._skip = max(0, self._skip - 1)
        if tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._in_style:
            self.styles.append(data)
        elif not self._skip:
            self.text.append(data)
            if self._in_notes and data.strip() and self.per_slide:
                self.per_slide[-1]["notes"] = True


def palette(keynote: bool = False) -> tuple[set[str], dict[str, str]]:
    """Every colour tokens.yaml documents for slides, and the retired ones with their fix.
    A keynote also takes its dark palette (tokens.yaml keynote.dark)."""
    t = nbg_tokens.load()
    allowed: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for x in node.values():
                walk(x)
        elif isinstance(node, list):
            for x in node:
                walk(x)
        elif isinstance(node, str) and re.fullmatch(r"[0-9A-Fa-f]{6}", node):
            allowed.add(node.upper())

    for key in ("colors", "status", "extended_palettes", "charts"):
        walk(t[key])
    retired = {k.upper(): v for k, v in t["retired_colors"].items()}
    if keynote:
        walk(t["keynote"]["dark"])
        # A keynote's dark ground is the point; only the light deck retires dark grounds.
        retired = {k: v for k, v in retired.items() if "dark background" not in v}
    return allowed, retired


def _norm_hex(h: str) -> str:
    h = h.upper()
    return "".join(ch * 2 for ch in h) if len(h) == 3 else h


def _scan(text: str) -> _Scan:
    scan = _Scan()
    scan.feed(DATA_URI_RE.sub("data:", text))
    scan.close()
    return scan


def static_check(text: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    def add(level: str, what: str) -> None:
        issues.append({"level": level, "what": what})

    scan = _scan(text)
    if scan.mains != 1:
        add("error", f'{scan.mains} <main class="deck"> elements; a deck has exactly one')
    if not scan.slides:
        add("error", 'no <section class="slide"> found')
    if "data-nbg-runtime" not in text:
        add(
            "error", "not built: run decks-py html-build first (no design system or editor inlined)"
        )
    if not scan.lang:
        add(
            "warning",
            "<html> has no lang attribute (el or en): screen readers and hyphenation need it",
        )
    if not scan.title.strip():
        add("warning", "no <title>: the browser tab and the saved file have no name")
    for ext in scan.external:
        add("error", f"external resource {ext}: a deck must open offline, inline it")
    if scan.scripts:
        add(
            "error",
            f"{scan.scripts} author <script> block(s): only the NBG runtime may run in a deck",
        )
    for h in sorted(scan.handlers):
        add("error", f"inline event handler {h}=: remove it, the runtime handles interaction")
    css = "\n".join(scan.styles)
    if re.search(r"@import|url\(\s*[\"']?https?:", css, re.I):
        add("error", "CSS loads something from the network (@import or url(http...)); inline it")
    if scan.keynote:
        # keynote.md hard rules 1 and 3
        for i, s in enumerate(scan.per_slide, 1):
            if "k-back" not in s["classes"] and not s["notes"]:
                add(
                    "error",
                    f"slide {i}: no speaker note; every keynote slide but the back cover carries one",
                )
            if s["bars"] > 7:
                add("error", f"slide {i}: {s['bars']} bars; a keynote chart has at most 7")
            # A keynote is a photographic format: the cover, every divider and the
            # closing stand on a full-bleed photograph (keynote.md "Archetypes").
            needs = {"k-cover", "k-divider", "k-closing"} & set(s["classes"])
            if needs and not s["photo"]:
                add(
                    "error",
                    f"slide {i}: a {sorted(needs)[0][2:]} slide needs a photograph "
                    '(<div class="bg scrim-left"><img src="..."></div>)',
                )
        photos = sum(1 for s in scan.per_slide if s["photo"])
        if scan.per_slide and photos < len(scan.per_slide) / 3:
            add(
                "warning",
                f"{photos} of {len(scan.per_slide)} slides carry a photograph; a keynote "
                "is a photographic format, aim for a third or more",
            )
        charts = sum(1 for s in scan.per_slide if s["charts"])
        if charts > 2:
            add(
                "error",
                f"{charts} chart slides; a keynote has at most 2 (a slide needing a real chart is not a keynote slide)",
            )
    allowed, retired = palette(scan.keynote)
    seen: set[str] = set()
    for src in [css, *scan.attrs_colour]:
        for m in HEX_RE.finditer(src):
            h = _norm_hex(m.group(1))
            if h in seen:
                continue
            seen.add(h)
            if h in retired:
                add("error", f"colour #{h}: {retired[h]}")
            elif h not in allowed:
                add(
                    "error",
                    f"colour #{h} is not an NBG colour (tokens.yaml); use the var(--c-...) names",
                )
    shadow = SHADOW_RE.search(css)
    if shadow:
        add(
            "error",
            f"shadow ({shadow.group(0)[:40]}): the brand has none, and PDF viewers draw them as grey blocks",
        )
    fonts_ok = {f.lower() for f in nbg_tokens.load()["fonts"]["allowed"]} | GENERIC_FONTS
    for fm in FONT_FAMILY_RE.finditer(css):
        for fam in fm.group(1).split(","):
            name = fam.strip().strip("\"'").strip()
            if name and not name.startswith("var(") and name.lower() not in fonts_ok:
                add("error", f"font {name!r}: NBG decks use Aptos (Calibri, Tahoma as fallbacks)")
    body = "".join(scan.text)
    if EM_DASH in body or " -- " in body:
        add("error", "em dash in the text: use a comma, colon or parentheses")
    return issues


def count_slides(text: str) -> int:
    return _scan(text).slides


# -------------------------------------------------------------------- browser
def find_browser(explicit: str | None = None) -> str | None:
    """Chrome, Edge, Chromium or Brave: an explicit path, the environment, then this platform's usual places."""
    if explicit:
        if os.access(explicit, os.X_OK):
            return explicit
        raise DeckError(f"--browser is not an executable: {explicit}")
    for env in ("NBG_BROWSER", "CHROME_BIN", "CHROME_PATH"):
        p = os.environ.get(env)
        if p and os.access(p, os.X_OK):
            return p
    if sys.platform == "darwin":
        cands = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ]
    elif os.name == "nt":
        roots = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
        rels = [
            ("Google", "Chrome", "Application", "chrome.exe"),
            ("Microsoft", "Edge", "Application", "msedge.exe"),
            ("Chromium", "Application", "chrome.exe"),
        ]
        cands = [str(Path(r, *rel)) for rel in rels for r in roots if r]
    else:
        cands = []
    for c in cands:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    for name in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "chrome",
        "microsoft-edge",
        "msedge",
    ):
        p = shutil.which(name)
        if p:
            return p
    return None


def _chrome(browser: str, args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    # A throwaway profile: never the user's own, so a running Chrome or a stale
    # lock cannot interfere and nothing of theirs is read.
    with tempfile.TemporaryDirectory(prefix="nbg-html-") as prof:
        cmd = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--hide-scrollbars",
            f"--user-data-dir={prof}",
            "--virtual-time-budget=8000",
            *args,
        ]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def browser_check(deck: Path, browser: str, timeout: int = 120) -> dict[str, Any]:
    url = deck.resolve().as_uri() + "?nbg-check"
    r = _chrome(browser, ["--window-size=2000,1200", "--dump-dom", url], timeout)
    m = re.search(
        r'<script type="application/json" id="nbg-check-result">(.*?)</script>', r.stdout, re.S
    )
    if not m:
        raise DeckError(
            "the layout check produced no report: is this a built deck? " + r.stderr.strip()[-300:]
        )
    report: dict[str, Any] = json.loads(html.unescape(m.group(1)))
    return report


def check(deck: Path, static_only: bool, browser: str | None) -> dict[str, Any]:
    text = deck.read_text(encoding="utf-8")
    report: dict[str, Any] = {
        "deck": str(deck),
        "slides": count_slides(text),
        "static": static_check(text),
    }
    if not static_only:
        exe = find_browser(browser)
        if not exe:
            report["layout"] = None
            report["layout_skipped"] = "no Chrome, Edge or Chromium found"
        else:
            report["layout"] = browser_check(deck, exe)
    issues = report["static"] + [
        {"level": i["level"], "what": f"slide {s['index']}: {i['what']}"}
        for s in (report.get("layout") or {}).get("slides", [])
        for i in s["issues"]
    ]
    report["errors"] = sum(1 for i in issues if i["level"] == "error")
    report["warnings"] = sum(1 for i in issues if i["level"] == "warning")
    report["issues"] = issues
    return report


# ------------------------------------------------------------------------ pdf
def export_pdf(
    deck: Path, out: Path, browser: str | None, png_dir: Path | None, dpi: int
) -> dict[str, Any]:
    import pypdf

    exe = find_browser(browser)
    if not exe:
        return {"no_browser": True}
    slides = count_slides(deck.read_text(encoding="utf-8"))
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    r = _chrome(
        exe, ["--no-pdf-header-footer", f"--print-to-pdf={out}", deck.resolve().as_uri()], 180
    )
    if not out.exists():
        raise DeckError(
            "Chrome wrote no PDF: " + (r.stderr.strip()[-400:] or f"exit {r.returncode}")
        )
    reader = pypdf.PdfReader(str(out))
    pages = len(reader.pages)
    problems: list[str] = []
    if pages != slides:
        problems.append(
            f"{pages} page(s) for {slides} slide(s): a slide spilled onto another page or was not printed"
        )
    box = reader.pages[0].mediabox
    w_px, h_px = round(float(box.width) * 96 / 72), round(float(box.height) * 96 / 72)
    if (w_px, h_px) != (SLIDE_W, SLIDE_H):
        problems.append(f"page is {w_px}x{h_px} px, not {SLIDE_W}x{SLIDE_H}")
    fonts: set[str] = set()
    for page in reader.pages:
        res = page.get("/Resources") or {}
        for f in (res.get("/Font") or {}).values():
            name = str(f.get_object().get("/BaseFont", ""))
            fonts.add(name.split("+", 1)[-1].lstrip("/"))
    aptos = any(f.lower().startswith("aptos") for f in fonts)
    pngs: list[str] = []
    if png_dir:
        import pypdfium2 as pdfium

        png_dir.mkdir(parents=True, exist_ok=True)
        for old in png_dir.glob("slide-*.png"):
            old.unlink()
        pdf = pdfium.PdfDocument(str(out))
        for i in range(len(pdf)):
            p = png_dir / f"slide-{i + 1:02d}.png"
            pdf[i].render(scale=dpi / 72).to_pil().save(p)
            pngs.append(str(p))
        pdf.close()
    return {
        "pdf": str(out),
        "slides": slides,
        "pages": pages,
        "page_px": [w_px, h_px],
        "fonts": sorted(fonts),
        "aptos_embedded": aptos,
        "pngs": pngs,
        "problems": problems,
    }


# ------------------------------------------------------------------------ cli
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="nbg_html", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="inline the design system, the runtime and the pictures")
    b.add_argument("src", type=Path)
    b.add_argument("out", type=Path)
    c = sub.add_parser("check", help="static check, then the headless layout check")
    c.add_argument("deck", type=Path)
    c.add_argument("--static", action="store_true", help="skip the browser layout check")
    c.add_argument("--format", choices=("text", "json"), default="text")
    c.add_argument("--browser")
    p = sub.add_parser("pdf", help="export a verified PDF, one page per slide")
    p.add_argument("deck", type=Path)
    p.add_argument("-o", "--out", type=Path)
    p.add_argument("--png", type=Path, help="also draw every page to <dir>/slide-NN.png")
    p.add_argument("--dpi", type=int, default=80, help="PNG resolution (80 = 1600x900)")
    p.add_argument("--browser")
    a = ap.parse_args(argv)

    try:
        if a.cmd == "build":
            if not a.src.is_file():
                raise DeckError(f"not found: {a.src}")
            r = build(a.src, a.out)
            print(
                f"built {r['out']}: {r['slides']} slide(s), {r['bytes'] // 1024} KB, self-contained"
            )
            return 0
        if a.cmd == "check":
            if not a.deck.is_file():
                raise DeckError(f"not found: {a.deck}")
            rep = check(a.deck, a.static, a.browser)
            if a.format == "json":
                print(json.dumps(rep, ensure_ascii=False, indent=2))
            else:
                print(f"{rep['deck']}: {rep['slides']} slide(s)")
                if rep.get("layout_skipped"):
                    print(f"  layout check skipped: {rep['layout_skipped']}")
                elif rep.get("layout") and not rep["layout"].get("aptos"):
                    print(
                        "  note: Aptos is not installed here, so layout was measured with a fallback font"
                    )
                for i in rep["issues"]:
                    print(f"  {i['level'].upper():7} {i['what']}")
                print(
                    f"RESULT: {'FAIL' if rep['errors'] else 'PASS'} ({rep['errors']} error(s), {rep['warnings']} warning(s))"
                )
            return 1 if rep["errors"] else 0
        if a.cmd == "pdf":
            if not a.deck.is_file():
                raise DeckError(f"not found: {a.deck}")
            out = a.out or a.deck.with_suffix(".pdf")
            res = export_pdf(a.deck, out, a.browser, a.png, a.dpi)
            if res.get("no_browser"):
                print(
                    "no Chrome, Edge or Chromium found: deliver the HTML; its PDF button prints the same pages",
                    file=sys.stderr,
                )
                return NO_BROWSER
            print(json.dumps(res, ensure_ascii=False, indent=2))
            if res["problems"]:
                return 1
            return 0 if res["aptos_embedded"] else FONT_FALLBACK
    except DeckError as e:
        print(f"nbg_html: {e}", file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired:
        print("nbg_html: the browser timed out", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
