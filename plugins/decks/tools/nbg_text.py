#!/usr/bin/env python3
"""Text helpers shared by the decks Python tools: Greek capitals, fonts, text measurement.

nbg_build.py sizes the section pill to its text, keeps a cover title on one line,
wraps titles and refuses content that cannot fit, and all of that needs to know how
wide a string is in Aptos before PowerPoint draws it. nbg_keynote.py needs the same
fonts and the same Greek capitals. Both used to carry their own copy; this is the
single one.

Measurement uses the real Aptos files when they are installed (Pillow reads them),
and otherwise a width table taken from Aptos itself: the wider of Regular and Bold
for every character, plus 3%. The table can only overestimate, so a fit decision
made without the fonts errs towards wrapping, never towards clipping.

Pillow is imported lazily: greek_upper and the table need only the standard library.
"""

from __future__ import annotations

import os
import unicodedata
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------- Greek capitals

TONOS = "\u0301"  # combining acute, which is what NFD turns the Greek tonos into
DIALYTIKA = "\u0308"  # combining diaeresis: the Greek dialytika
# The vowel pairs Greek reads as one sound. A tonos on the first letter is what says
# they are two (the alpha and iota of the month May); once capitals drop it, the
# second letter takes a dialytika instead.
_DIGRAPHS = {
    ("\u0391", "\u0399"),  # alpha iota
    ("\u0395", "\u0399"),  # epsilon iota
    ("\u039f", "\u0399"),  # omicron iota
    ("\u03a5", "\u0399"),  # upsilon iota
    ("\u0391", "\u03a5"),  # alpha upsilon
    ("\u0395", "\u03a5"),  # epsilon upsilon
    ("\u039f", "\u03a5"),  # omicron upsilon
    ("\u0397", "\u03a5"),  # eta upsilon
}


def _is_greek(ch: str) -> bool:
    return "\u0370" <= ch <= "\u03ff" or "\u1f00" <= ch <= "\u1fff"


def greek_upper(text: str) -> str:
    """ALL CAPS the way Greek writes them: the tonos goes, the dialytika stays, and a
    dialytika appears where dropping a tonos would join two vowels into one sound.

    Python's str.upper() keeps both, so upper-casing "η συναίνεση" leaves the accent
    on the capital iota, a visible spelling error in every Greek pill or kicker. Only
    a tonos that sits on a Greek letter is dropped, so a Latin "é" in a Greek deck
    keeps its accent. The month May, with its tonos on the alpha, would read as the
    diphthong alpha-iota without it, so its capitals put a dialytika on the iota.
    """
    clusters: list[list[str]] = []  # a base letter and the marks that follow it
    for ch in unicodedata.normalize("NFD", text.upper()):
        if unicodedata.combining(ch) and clusters:
            clusters[-1].append(ch)
        else:
            clusters.append([ch])
    for i, cluster in enumerate(clusters):
        base = cluster[0]
        if not _is_greek(base) or TONOS not in cluster[1:]:
            continue
        cluster[1:] = [mark for mark in cluster[1:] if mark != TONOS]
        following = clusters[i + 1] if i + 1 < len(clusters) else None
        if following and (base, following[0]) in _DIGRAPHS and DIALYTIKA not in following[1:]:
            following.append(DIALYTIKA)
    return unicodedata.normalize("NFC", "".join("".join(c) for c in clusters))


def caps(text: str, language: str = "en") -> str:
    """Upper-case for display in the deck's language (Greek drops the tonos)."""
    return greek_upper(text) if language == "el" else text.upper()


_GREEK_SEPARATORS = str.maketrans(",.", ".,")


def localise_number(text: str, language: str = "en") -> str:
    """A number written the English way (1,234.5) in the deck's language: Greek puts a
    point between thousands and a comma before decimals (1.234,5)."""
    return text.translate(_GREEK_SEPARATORS) if language == "el" else text


def format_number(value: float, decimals: int, language: str = "en", *, group: bool = True) -> str:
    """value with `decimals` places, in the deck's language, grouped in thousands
    unless group is False. It rounds as PowerPoint does: to 15 significant digits
    first, then half away from zero (Python's own format rounds 12.5 to 12)."""
    exact = Decimal(f"{float(value):.15g}").quantize(
        Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP
    )
    if exact == 0:
        exact = abs(exact)  # no "-0.00"
    return localise_number(f"{exact:{',' if group else ''}.{decimals}f}", language)


# ---------------------------------------------------------------- font discovery

# Office for Mac keeps Aptos inside each app bundle, not in ~/Library/Fonts, so a
# lookup that only knows the user font folder reports a colleague's installed Aptos
# as missing. Windows keeps cloud fonts per user under LOCALAPPDATA.
_OFFICE_APPS = ("Microsoft PowerPoint", "Microsoft Word", "Microsoft Excel", "Microsoft Outlook")


def font_dirs() -> list[Path]:
    """Folders searched for font files, in order.

    DECKS_FONT_DIRS (os.pathsep-separated) replaces the whole list when set, which is
    how the tests force the fallback table and how a user points at a private folder.
    """
    override = os.environ.get("DECKS_FONT_DIRS")
    if override is not None:
        return [Path(p) for p in override.split(os.pathsep) if p]
    home = Path.home()
    dirs = [home / "Library" / "Fonts", Path("/Library/Fonts")]
    dirs += [
        Path("/Applications") / f"{app}.app" / "Contents/Resources/DFonts" for app in _OFFICE_APPS
    ]
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot") or "C:\\Windows"
    dirs.append(Path(windir) / "Fonts")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
    dirs += [
        home / ".local" / "share" / "fonts",
        home / ".fonts",
        Path("/usr/local/share/fonts"),
        Path("/usr/share/fonts"),
    ]
    return dirs


def _cloud_font_dirs(family: str) -> list[Path]:
    """Office's downloaded cloud fonts: one folder per family, files named by hash."""
    if os.environ.get("DECKS_FONT_DIRS") is not None:
        return []
    roots = [
        Path.home() / "Library/Group Containers/UBF8T346G9.Office/FontCache/4/CloudFonts",
    ]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots.append(Path(local) / "Microsoft" / "FontCache" / "4" / "CloudFonts")
    return [r / family for r in roots]


def _files_below(root: Path, depth: int) -> list[Path]:
    """The files exactly `depth` folder levels below root; nothing where unreadable."""
    level = [root]
    for _ in range(depth):
        below: list[Path] = []
        for d in level:
            try:
                below += sorted(s for s in d.iterdir() if s.is_dir())
            except OSError:
                continue
        level = below
    files: list[Path] = []
    for d in level:
        try:
            files += sorted(f for f in d.iterdir() if f.is_file())
        except OSError:
            continue
    return files


def find_font_file(name: str) -> Path | None:
    """A font file by name, ignoring case, in font_dirs() and two levels below them.

    Debian and Ubuntu file fonts by format and family (/usr/share/fonts/truetype/
    dejavu/), two levels down, and Windows and Office spell the same file aptos.ttf or
    Aptos.ttf, which a case-sensitive Linux file system tells apart. Every folder's
    flat files come first, so the macOS and Windows folders hit before any nesting.
    """
    want = name.casefold()
    dirs = font_dirs()
    for depth in range(3):
        for d in dirs:
            for p in _files_below(d, depth):
                if p.name.casefold() == want:
                    return p
    return None


_FILE_NAMES = {
    ("Aptos", False): ("Aptos.ttf", "aptos.ttf"),
    ("Aptos", True): ("Aptos-Bold.ttf", "aptosb.ttf", "Aptos Bold.ttf"),
}


def find_font(family: str = "Aptos", bold: bool = False) -> Path | None:
    """The file for a family and weight: known file names first, then the cloud cache."""
    for name in _FILE_NAMES.get((family, bold), ()):
        p = find_font_file(name)
        if p is not None:
            return p
    want = "Bold" if bold else "Regular"
    for d in _cloud_font_dirs(family):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.tt[fc]")):
            try:
                if _font_name(p) == (family, want):
                    return p
            except (ImportError, OSError):
                continue
    return None


def _font_name(path: Path) -> tuple[str, str]:
    from PIL import ImageFont

    family, style = ImageFont.truetype(str(path), 12).getname()
    return str(family), str(style)


# ---------------------------------------------------------------- measurement

# Aptos: hhea ascender 1923, descender 577, line gap 0, 2048 units per em. A line at
# 100% spacing is therefore 1.221 em tall, and the first baseline sits 0.939 em below
# the top of a zero-inset text box.
LINE_EM = (1923 + 577) / 2048
ASCENT_EM = 1923 / 2048
DESCENT_EM = 577 / 2048

# Width in thousandths of an em, the wider of Aptos Regular and Aptos Bold plus 3%,
# grouped by width. Generated from the font files; see the module docstring. Accented
# letters are measured through their base letter (NFD), so they need no entry.
_FALLBACK_WIDTHS_BY_MILLE_EM = {
    210: " ",
    239: "'",
    277: "ij",
    279: "|",
    302: "!()",
    303: "IΙ",
    305: "lι",
    307: "‘’",
    309: ",.:;··",
    346: "f",
    348: "[]{}",
    351: "-",
    366: "t",
    379: "J",
    381: "r",
    390: "°",
    399: "/\\",
    433: '"',
    457: "τ",
    459: "«»",
    464: "ξ",
    469: "ζ",
    471: "*",
    474: "_–",
    479: "ς",
    480: "z",
    483: "®",
    500: "Γ",
    503: "•",
    509: "vyγλν",
    510: "x",
    514: "§",
    521: "TΤ",
    525: "χ",
    527: "g",
    528: "L",
    532: "s",
    534: "?",
    535: "“",
    536: "”",
    539: "ε",
    544: "Σ",
    551: "$+0123456789<=>^k~κ€£±×÷¢¥",
    554: "#F",
    558: "™",
    564: "ZΖ",
    566: "c",
    569: "`a",
    573: "e",
    588: "β",
    591: "EoΕδο",
    597: "hnη",
    600: "uθ",
    603: "μ",
    604: "YbdpqΞΥρυ",
    613: "α",
    616: "S",
    617: "XΧσ",
    622: "π",
    624: "PΡ",
    636: "VΛ",
    638: "BΒ",
    639: "AΑ",
    642: "KΚ",
    645: "Δ",
    654: "R",
    698: "&",
    717: "U",
    729: "CD",
    740: "G",
    741: "Π",
    745: "NΝ",
    751: "HΗ",
    753: "φ",
    760: "OQΘΟ",
    767: "Ω",
    772: "©",
    784: "w",
    794: "ψ",
    819: "Φ",
    846: "MΜ",
    861: "Ψ",
    867: "%",
    876: "…",
    877: "ω",
    916: "m",
    927: "@",
    969: "W",
}
_FALLBACK = {ch: w for w, chars in _FALLBACK_WIDTHS_BY_MILLE_EM.items() for ch in chars}
_FALLBACK_DEFAULT = 700  # an unlisted Latin or symbol character: wider than any average
_FALLBACK_WIDE = 1000  # CJK and other full-width characters


def _fallback_width(ch: str) -> int:
    if ch in _FALLBACK:
        return _FALLBACK[ch]
    if unicodedata.combining(ch):
        return 0
    base = unicodedata.normalize("NFD", ch)[:1]
    if base in _FALLBACK:
        return _FALLBACK[base]
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return _FALLBACK_WIDE
    return _FALLBACK_DEFAULT


class TextMetrics:
    """Width and wrapping of text set in Aptos, in inches."""

    def __init__(self) -> None:
        self._fonts: dict[bool, Any] = {}
        for bold in (False, True):
            path = find_font("Aptos", bold)
            if path is None:
                continue
            try:
                from PIL import ImageFont

                self._fonts[bold] = ImageFont.truetype(str(path), 1000)
            except (ImportError, OSError):
                continue

    @property
    def uses_real_font(self) -> bool:
        return bool(self._fonts)

    @property
    def source(self) -> str:
        return "Aptos font files" if self.uses_real_font else "conservative width table"

    def width(self, text: str, size_pt: float, bold: bool = False) -> float:
        """Advance width of one line of `text` at `size_pt`, in inches."""
        font = self._fonts.get(bold, self._fonts.get(not bold))
        if font is not None:
            units = float(font.getlength(text))
        else:
            units = float(sum(_fallback_width(ch) for ch in text))
        return units / 1000.0 * size_pt / 72.0

    @staticmethod
    def line_height(size_pt: float, spacing: float = 1.0) -> float:
        """Height of one line at `size_pt` and a line-spacing multiple, in inches."""
        return size_pt * LINE_EM * spacing / 72.0

    def wrap(self, text: str, width_in: float, size_pt: float, bold: bool = False) -> list[str]:
        """Greedy word wrap the way PowerPoint does it; a newline starts a new line.

        A word wider than the whole line is broken between characters, as PowerPoint
        breaks it, so no returned line is ever wider than `width_in`.
        """
        lines: list[str] = []
        for paragraph in str(text).split("\n"):
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = ""
            for word in words:
                trial = f"{current} {word}" if current else word
                if self.width(trial, size_pt, bold) <= width_in:
                    current = trial
                    continue
                if current:
                    lines.append(current)
                while self.width(word, size_pt, bold) > width_in and len(word) > 1:
                    cut = len(word) - 1
                    while cut > 1 and self.width(word[:cut], size_pt, bold) > width_in:
                        cut -= 1
                    lines.append(word[:cut])
                    word = word[cut:]
                current = word
            lines.append(current)
        return lines


@lru_cache(maxsize=1)
def metrics() -> TextMetrics:
    """The process-wide TextMetrics. Cached: fonts are found and opened once."""
    return TextMetrics()
