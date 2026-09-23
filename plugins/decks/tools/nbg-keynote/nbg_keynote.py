#!/usr/bin/env python3
"""NBG Keynote compositor: build a cinematic dark keynote from a YAML spec.

Renders 2560x1440 slides with Pillow (full-bleed imagery, directional teal scrims,
Aptos typography, film grain) and assembles them into a 13.333x7.5in PPTX plus a
matching PDF, with per-slide speaker notes.

Keynote mode is Standard #21 in shared/presentation-style-guide.md. It is the ONLY
sanctioned exception to the light-mode NBG deck format, and only for talks delivered
live to an external or bank-wide audience. Everything else uses nbg_build.py.

Spec: shared/brand-system/keynote.md. Dark tokens: shared/brand-system/tokens.yaml.

Usage (through the plugin launcher, which provides the Python environment):
    decks-py keynote deck.yaml
    decks-py keynote deck.yaml --out ~/Downloads/202608061821_my_talk
    decks-py keynote deck.yaml --validate              # check spec and layout, render nothing
    decks-py keynote deck.yaml --slides 1,4,7          # re-render a subset
    decks-py keynote deck.yaml --placeholder-images    # lay out before the photographs exist
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import unicodedata
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# nbg_color and nbg_tokens sit one level up, shared with nbg-presentation. These
# are scripts in hyphenated directories rather than a package, so add the path by hand.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nbg_tokens  # noqa: E402
from nbg_color import contrast_ratio  # noqa: E402
from nbg_color import relative_luminance as luminance  # noqa: E402,F401  (re-export)

# ============================================================ canvas constants

W, H = 2560, 1440  # render resolution (2x of 1280x720)
EMU_W, EMU_H = 12192000, 6858000  # 13.333in x 7.5in
DPI = 192  # 2560 / 13.333in

M = int(nbg_tokens.get("keynote.gutter_px"))  # side gutter, both sides (155 = 0.807in)
X_RIGHT = W - M  # 2405
SAFE = 100  # nothing critical within 100px of an edge
CONTENT_BOTTOM = 1280  # slide text ends above the footer row (logo at y 1300)

Y_KICKER = 150
Y_TITLE = 250
Y_COVER_TITLE = 300
Y_COVER_SUB = 500
Y_FOOTER_LOGO = 1300
Y_SOURCE = 1312  # the ascender line of the source note (Pillow's default anchor)
LOGO_H_CONTENT = 46
LOGO_H_COVER = 60
LOGO_H_BACK = 150

GRAIN_SIGMA = 4
DUO_X_RIGHT = 1360  # left edge of the right-hand stat in duo-stat

# ============================================================ palette (dark)
# shared/brand-system/tokens.yaml (keynote.dark) is the machine source; keynote.md
# explains the mapping from the light-mode colours in colors.md.

_DARK = nbg_tokens.get("keynote.dark")


def _rgb(token: str) -> tuple[int, int, int]:
    h = str(_DARK[token]).lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


INK = _rgb("ink")  # #FFFFFF   <- 003841  primary text, hero numbers
INK_2 = _rgb("ink_2")  # #DFE6E6   <- 202020  body and support text
INK_3 = _rgb("ink_3")  # #96A6A8   <- 5A5F5A  source notes, metadata
ACCENT = _rgb("accent")  # #00DFF8   <- 007B85  kicker, emphasis, highlight
ACCENT_BAR = _rgb("accent_bar")  # #00BED2   <- 00ADBF  default bar fill
ACCENT_MUTE = _rgb("accent_mute")  # #008292   <- BEC1BE  non-highlighted bars
GROUND_TOP = _rgb("ground_from")  # #00161B   <- FFFFFF  gradient top, scrim base
GROUND_BOT = _rgb("ground_to")  # #003841   <- F5F8F6  gradient bottom (brand Dark Teal)
NEGATIVE = _rgb("negative")  # #FF5263   <- AA0028  negative statistic
RULE = _rgb("rule")  # #788C8E   <- BEC1BE  chart baseline

GLOW = np.array([0, 40, 46])  # faint cyan bloom, lower-left of the gradient
PLACEHOLDER = (38, 58, 64)  # stands in for a missing photograph with --placeholder-images

NAMED_COLORS = {
    "ink": INK,
    "white": INK,
    "ink-2": INK_2,
    "ink-3": INK_3,
    "accent": ACCENT,
    "cyan": ACCENT,
    "negative": NEGATIVE,
    "red": NEGATIVE,
}

# ============================================================ typography

# Aptos is the NBG brand font. Fall back rather than crash on a machine without it.


def default_font_dirs() -> list[Path]:
    """Every folder a colleague's machine keeps Aptos or Calibri in.

    Office for Mac installs neither into a font folder: each app bundle carries its
    own copy under Contents/Resources/DFonts. Windows keeps system fonts in
    %WINDIR%\\Fonts and per-user fonts in %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts.
    Searching only ~/Library/Fonts meant a stock Mac with Office aborted before
    slide 1, asking for fonts it already had.
    """
    home = Path.home()
    dirs = [
        home / "Library/Fonts",
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts/Supplemental"),
    ]
    dirs += [
        Path(f"/Applications/Microsoft {app}.app/Contents/Resources/DFonts")
        for app in ("PowerPoint", "Word", "Excel", "Outlook")
    ]
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if windir:
        dirs.append(Path(windir) / "Fonts")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
    dirs += [
        home / ".local/share/fonts",
        home / ".fonts",
        Path("/usr/share/fonts/truetype"),
        Path("/usr/share/fonts"),
    ]
    return dirs


FONT_DIRS = default_font_dirs()
# Matched case-insensitively. Office ships Calibri as Calibri.ttf / Calibrib.ttf
# (Windows: calibri.ttf / calibrib.ttf); no Office has a "Calibri Bold.ttf".
FONT_FILES = {
    "x": ["Aptos-ExtraBold.ttf", "Aptos-Bold.ttf", "calibrib.ttf", "DejaVuSans-Bold.ttf"],
    "s": ["Aptos-SemiBold.ttf", "Aptos-Bold.ttf", "calibrib.ttf", "DejaVuSans-Bold.ttf"],
    "l": ["Aptos-Light.ttf", "Aptos.ttf", "calibril.ttf", "calibri.ttf", "DejaVuSans.ttf"],
    "r": ["Aptos.ttf", "calibri.ttf", "DejaVuSans.ttf"],
}
WEIGHT_NAMES = {"x": "ExtraBold", "s": "SemiBold", "l": "Light", "r": "Regular"}
_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
_font_warned: set[str] = set()
_index_cache: dict[tuple[Path, ...], list[tuple[dict[str, Path], dict[str, Path]]]] = {}


def _index(d: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    """Lower-cased file name -> path, for `d` itself and for one level below it.

    The macOS dirs and the Office bundles hold their fonts flat. Linux does not:
    Debian and Ubuntu file fonts by family, so DejaVu lives at
    /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf, one level below the listed
    directory. Without the second level CI had no way to find its only font.
    """
    flat: dict[str, Path] = {}
    nested: dict[str, Path] = {}
    try:
        entries = sorted(d.iterdir())
    except OSError:
        return flat, nested
    for p in entries:
        if p.is_dir():
            try:
                for q in sorted(p.iterdir()):
                    if q.is_file():
                        nested.setdefault(q.name.lower(), q)
            except OSError:
                continue
        else:
            flat.setdefault(p.name.lower(), p)
    return flat, nested


def _find_font_file(name: str) -> Path | None:
    """Locate a font file by name, ignoring case. A file directly inside a listed
    folder wins over one a level below it, so Aptos still beats a stray copy."""
    key = tuple(FONT_DIRS)
    if key not in _index_cache:
        _index_cache[key] = [_index(d) for d in FONT_DIRS]
    wanted = name.lower()
    for level in (0, 1):
        for idx in _index_cache[key]:
            if wanted in idx[level]:
                return idx[level][wanted]
    return None


def font_path(kind: str) -> Path:
    """The file weight `kind` renders with: Aptos when present, else the first fallback."""
    for i, name in enumerate(FONT_FILES[kind]):
        p = _find_font_file(name)
        if p is not None:
            if i > 0 and kind not in _font_warned:
                _font_warned.add(kind)
                warn(f"Aptos {WEIGHT_NAMES[kind]} missing, falling back to {p.name}")
            return p
    raise SystemExit(
        f"No usable font for weight '{kind}' ({WEIGHT_NAMES[kind]}). Looked for "
        f"{', '.join(FONT_FILES[kind])} in: {'; '.join(str(d) for d in FONT_DIRS)}. "
        f"Install Aptos (Light, Regular, SemiBold, ExtraBold) or Calibri; Office for Mac "
        f"and Windows already ship both. `decks-py doctor` lists the fonts it can see."
    )


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    p = font_path(kind)
    key = (str(p), size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(p), size)
    return _font_cache[key]


# Greek all-caps drops the tonos but keeps the dialytika. Python's str.upper()
# keeps both, so 'η συναίνεση'.upper() renders as 'Η ΣΥΝΑΊΝΕΣΗ', a visible typo.
TONOS = "́"
DIALYTIKA = "̈"


def greek_upper(text: str) -> str:
    out = []
    for ch in unicodedata.normalize("NFD", text.upper()):
        if ch == TONOS:
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def wrap(text: str, fnt: ImageFont.FreeTypeFont, maxw: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if fnt.getlength(trial) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ============================================================ background


def cover_fit(img: Image.Image) -> Image.Image:
    """Scale to cover the canvas, then centre-crop."""
    iw, ih = img.size
    s = max(W / iw, H / ih)
    img = img.resize((int(iw * s + 1), int(ih * s + 1)), Image.Resampling.LANCZOS)
    iw, ih = img.size
    x, y = (iw - W) // 2, (ih - H) // 2
    return img.crop((x, y, x + W, y + H))


def gradient_bg() -> Image.Image:
    top, bot = np.array(GROUND_TOP), np.array(GROUND_BOT)
    col = np.linspace(0, 1, H)[:, None]
    grad = (top[None, :] * (1 - col) + bot[None, :] * col).astype(np.uint8)
    im = np.repeat(grad[:, None, :], W, axis=1).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - 300) / 1500) ** 2 + ((yy - 1250) / 900) ** 2)
    im += np.clip(1 - d, 0, 1)[:, :, None] * GLOW
    return Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


SCRIM_SIDES = ("left", "right", "upperleft", "bottom", "full")


def scrim(base: Image.Image, side: str = "left", strength: float = 1.0) -> Image.Image:
    """Darken and lay a directional teal scrim so text stays legible over imagery."""
    if side not in SCRIM_SIDES:
        raise SystemExit(f"Unknown scrim '{side}'. Use one of {SCRIM_SIDES}.")
    im = np.array(base.convert("RGB")).astype(np.float32) * 0.82
    yy, xx = np.mgrid[0:H, 0:W]
    if side == "left":
        a = np.clip(1 - xx / (W * 0.72), 0, 1) ** 1.4
    elif side == "right":
        a = np.clip((xx - W * 0.28) / (W * 0.72), 0, 1) ** 1.4
    elif side == "upperleft":
        a = np.clip(1 - (xx / (W * 0.8) + yy / (H * 1.1)), 0, 1) ** 1.2
    elif side == "bottom":
        a = np.clip((yy - H * 0.35) / (H * 0.65), 0, 1) ** 1.3
    else:
        a = np.full((H, W), 0.55)
    a = np.clip(a * 0.9 * strength, 0, 1)[:, :, None]
    im = im * (1 - a) + np.array(GROUND_TOP) * a
    # bottom band so the footer always reads over imagery
    ba = np.clip((yy - H * 0.80) / (H * 0.20), 0, 1)[:, :, None] * 0.5
    im = im * (1 - ba) + np.array(GROUND_TOP) * ba
    # vignette
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    im = im * (1 - np.clip(d - 0.7, 0, 1)[:, :, None] * 0.45)
    return Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def grain(im: Image.Image, seed: int, amt: int = GRAIN_SIGMA) -> Image.Image:
    """Film grain. Also the thing that stops the dark gradient from banding."""
    rng = np.random.default_rng(seed)
    a = np.array(im.convert("RGB")).astype(np.float32) + rng.normal(0, amt, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# ============================================================ contrast guard


# luminance() and contrast_ratio() come from ../nbg_color.py, the single copy
# shared with nbg_build.py and nbg_validate.py. _bg_luminance below keeps its
# own vectorised form because it samples a whole image patch, not one colour.


def _bg_luminance(canvas: Image.Image, box) -> float:
    """90th-percentile luminance under a text box, the brightest realistic patch,
    not the average, because text fails where the photograph is lightest."""
    x0, y0, x1, y1 = (max(0, int(v)) for v in box)
    x1, y1 = min(W, max(x1, x0 + 1)), min(H, max(y1, y0 + 1))
    a = np.array(canvas.convert("RGB").crop((x0, y0, x1, y1))).astype(np.float32) / 255.0
    lin = np.where(a <= 0.03928, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    lum = 0.2126 * lin[:, :, 0] + 0.7152 * lin[:, :, 1] + 0.0722 * lin[:, :, 2]
    return float(np.percentile(lum, 90))


def ensure_contrast(canvas: Image.Image, box, fg, min_ratio: float, label: str = "") -> None:
    """Deepen a feathered patch of scrim under `box` until `fg` clears `min_ratio`.

    The patch is Gaussian-blurred at a large radius so its edge is invisible against
    photography and grain. Mutates `canvas` in place.
    """
    if contrast_ratio(fg, _bg_luminance(canvas, box)) >= min_ratio:
        return
    # A wide feather keeps the patch from reading as a rectangle, but the blur must
    # stay well inside the padding or it dilutes the alpha over the text itself.
    pad, blur = 240, 150
    x0, y0, x1, y1 = box
    for alpha in (0.20, 0.35, 0.50, 0.65, 0.80, 0.92, 1.0):
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).rectangle(
            [x0 - pad, y0 - pad, x1 + pad, y1 + pad], fill=int(255 * alpha)
        )
        patch = Image.new("RGBA", (W, H), GROUND_TOP + (255,))
        patch.putalpha(mask.filter(ImageFilter.GaussianBlur(blur)))
        trial = Image.alpha_composite(canvas.convert("RGBA"), patch)
        if contrast_ratio(fg, _bg_luminance(trial, box)) >= min_ratio:
            canvas.paste(trial, (0, 0))
            return
    canvas.paste(trial, (0, 0))
    warn(
        f"contrast below {min_ratio}:1 even at maximum scrim{', ' + label if label else ''}. "
        f"Use a darker photograph or move the text."
    )


def _min_ratio(size: int) -> float:
    """WCAG: 3:1 for large text (>=18pt), 4.5:1 otherwise.

    2560px spans 13.333in = 960pt, so 1px = 0.375pt and 18pt = 48px.
    """
    return 3.0 if size >= 48 else 4.5


# ============================================================ layout plan

Box = tuple[float, float, float, float]


class _Plan:
    """What a renderer would draw, recorded instead of drawn.

    Every slide is rendered twice. The first pass lays it out: each text block
    records its ink box and the contrast it needs, and nothing is painted. The
    scrim patches then go down, and the second pass draws. Guarding while drawing
    let a later block's patch settle over text already on the canvas (a title's
    patch dimmed the kicker above it); guarding first cannot. validate() reuses the
    first pass, so it measures every block with the renderer's own fonts and wrap.
    """

    def __init__(self) -> None:
        # (label, ink box, is footer chrome, block id): lines of one paragraph share a block
        self.texts: list[tuple[str, Box, bool, int]] = []
        self.guards: list[tuple[Box, tuple, float, str]] = []

    def add(
        self,
        label: str,
        boxes: list[Box],
        fill,
        size: int,
        guard: Box | None = None,
        footer: bool = False,
    ) -> None:
        block = len(self.texts)
        for b in boxes:
            self.texts.append((label, b, footer, block))
        if boxes:
            self.guards.append((guard or _union(boxes), fill, _min_ratio(size), label))


_PLAN: _Plan | None = None


def _union(boxes: list[Box]) -> Box:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def text_box(xy, text: str, fnt: ImageFont.FreeTypeFont, anchor: str | None = None) -> Box:
    """The ink box of `text` drawn at `xy`: the pixels Pillow will actually paint."""
    x0, y0, x1, y1 = fnt.getbbox(text, anchor=anchor)
    return (xy[0] + x0, xy[1] + y0, xy[0] + x1, xy[1] + y1)


def _two_phase(draw):
    """Wrap an archetype renderer: lay out, guard every text box, then draw."""

    def render(canvas, s, ctx, on_image) -> None:
        global _PLAN
        _PLAN = plan = _Plan()
        try:
            draw(canvas, s, ctx, on_image)
        finally:
            _PLAN = None
        for box, fill, ratio, label in plan.guards:
            ensure_contrast(canvas, box, fill, ratio, label)
        draw(canvas, s, ctx, on_image)

    render.layout = draw  # type: ignore[attr-defined]
    return render


# ============================================================ drawing helpers


def shadow_text(canvas, xy, text, fnt, fill, shadow=True, anchor=None) -> None:
    if shadow:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).text(
            (xy[0] + 3, xy[1] + 5), text, font=fnt, fill=(0, 0, 0, 170), anchor=anchor
        )
        canvas.alpha_composite(lay.filter(ImageFilter.GaussianBlur(7)))
    ImageDraw.Draw(canvas).text(xy, text, font=fnt, fill=fill, anchor=anchor)


def para(
    canvas,
    x: int,
    y: int,
    text,
    fnt,
    fill,
    maxw: int,
    lh: int,
    shadow=False,
    size: int = 0,
    guard=True,
    label="",
) -> int:
    """Draw a wrapped paragraph. Returns the y just past the last line."""
    if not text:
        return y
    lines = wrap(text, fnt, maxw)
    if not lines:
        # Whitespace-only text clears `if not text` but wraps to no lines, which
        # used to reach max() on an empty sequence and abort the whole build
        # with a raw traceback. There is nothing to draw, so draw nothing.
        return y
    if _PLAN is not None:
        width = max(fnt.getlength(ln) for ln in lines)
        _PLAN.add(
            label or text[:40],
            [text_box((x, y + i * lh), ln, fnt) for i, ln in enumerate(lines)],
            fill,
            size or fnt.size,
            guard=(x, y, x + width, y + lh * len(lines)) if guard else None,
        )
        return y + lh * len(lines)
    for ln in lines:
        shadow_text(canvas, (x, y), ln, fnt, fill, shadow)
        y += lh
    return y


def line(canvas, xy, text, fnt, fill, shadow=False, guard=True, label="") -> None:
    if not text:
        return
    if _PLAN is not None:
        _PLAN.add(
            label or text[:40],
            [text_box(xy, text, fnt)],
            fill,
            fnt.size,
            guard=(xy[0], xy[1], xy[0] + fnt.getlength(text), xy[1] + fnt.size * 1.3)
            if guard
            else None,
        )
        return
    shadow_text(canvas, xy, text, fnt, fill, shadow)


def kicker(canvas, text, greek=False, color=ACCENT, y=Y_KICKER) -> None:
    """The keynote's section marker: a small square plus tracked-out caps.
    Same job as the filled section pill in light mode."""
    if not text:
        return
    f = font("s", 30)
    caps = greek_upper(text) if greek else text.upper()
    if _PLAN is not None:
        x_end = M + 44 + sum(f.getlength(ch) + 6 for ch in caps) - 6
        _PLAN.add("kicker", [(M, y, x_end, y + f.size * 1.3)], color, f.size)
        return
    d = ImageDraw.Draw(canvas)
    d.rectangle([M, y + 6, M + 22, y + 28], fill=color)
    x = float(M + 44)
    for ch in caps:
        d.text((x, y), ch, font=f, fill=color)
        x += f.getlength(ch) + 6


def mark(canvas, box, fill) -> None:
    """A filled square or rule: drawn only in the draw pass."""
    if _PLAN is None:
        ImageDraw.Draw(canvas).rectangle(box, fill=fill)


def place_logo(canvas, logo: Image.Image, height: int, xy) -> int:
    w = int(height * logo.width / logo.height)
    if _PLAN is None:
        canvas.alpha_composite(logo.resize((w, height), Image.Resampling.LANCZOS), xy)
    return w


def footer(canvas, logo, source=None) -> None:
    w = place_logo(canvas, logo, LOGO_H_CONTENT, (M, Y_FOOTER_LOGO))
    if not source:
        return
    f = font("r", 24)
    xy = (M + w + 40, Y_SOURCE)
    if _PLAN is not None:
        _PLAN.add("source", [text_box(xy, source, f)], INK_3, f.size, footer=True)
        return
    ImageDraw.Draw(canvas).text(xy, source, font=f, fill=INK_3)


MAX_BARS = 7
MAX_CHARTS = 2  # the exemplar keynote uses two in 16 slides; more is a business deck
BAR_W_CAP = 380  # a few bars otherwise yield 500-1000px bars: a wall, not a comparison


def draw_bars(canvas, cats, vals, highlight=None, unit="") -> None:
    if len(vals) != len(cats):
        raise SystemExit("bars: 'cats' and 'vals' must be the same length")
    if len(vals) > MAX_BARS:
        raise SystemExit(f"bars: at most {MAX_BARS} bars in keynote mode (got {len(vals)})")
    if any(v < 0 for v in vals):
        # Pillow refuses a rectangle drawn upwards from the baseline, and the deck
        # died on a raw traceback. validate() rejects this first; this is the belt.
        raise SystemExit(
            "bars: negative values cannot stand on a true zero baseline; "
            "state a decline as a hero-stat (color: negative) or a statement"
        )
    base, top = 1170, 545
    n = len(vals)
    gap = 46 if n > 3 else 150
    span = X_RIGHT - M
    # The cap holds for every bar count; the group is centred in the content band.
    bw = min((span - gap * (n - 1)) / n, float(BAR_W_CAP))
    x0 = M + (span - (bw * n + gap * (n - 1))) / 2
    mx = max(vals)
    # An all-zero series has no scale. The bars collapse onto the baseline instead
    # of dividing by zero; validate() rejects such a spec before it ever reaches
    # here, so this is the belt to that pair of braces.
    scale = (base - top - 90) / mx if mx > 0 else 0.0
    vfont = font("x", 60 if n <= 3 else 46)
    cfont = font("r", 34 if n <= 3 else 30)
    if _PLAN is None:
        ImageDraw.Draw(canvas).line([M, base, X_RIGHT, base], fill=RULE, width=2)
    for i, (c, v) in enumerate(zip(cats, vals, strict=True)):
        bx = x0 + i * (bw + gap)
        bh = v * scale  # true zero baseline
        if highlight == i:
            col = ACCENT
        elif highlight is None:
            col = ACCENT_BAR
        else:
            col = ACCENT_MUTE
        value_xy, value = (bx + bw / 2, base - bh - 20), f"{v}{unit}"
        cat_xy, cat = (bx + bw / 2, base + 22), str(c)
        cat_fill = INK if highlight == i else INK_2
        if _PLAN is not None:
            _PLAN.add("bar value", [text_box(value_xy, value, vfont, "mb")], INK, vfont.size)
            _PLAN.add("bar label", [text_box(cat_xy, cat, cfont, "ma")], cat_fill, cfont.size)
            continue
        d = ImageDraw.Draw(canvas)
        d.rectangle([bx, base - bh, bx + bw, base], fill=col)
        d.text(value_xy, value, font=vfont, fill=INK, anchor="mb")
        d.text(cat_xy, cat, font=cfont, fill=cat_fill, anchor="ma")


# ============================================================ archetypes


def _image_path(img, assets: Path) -> Path:
    p = Path(img).expanduser()
    return p if p.is_absolute() else assets / img


def _ground(spec, assets: Path, placeholder: bool = False):
    """Photo plus scrim, or the house gradient.

    With `placeholder`, a missing photograph becomes a flat dark stand-in under the
    same scrim, so the slide lays out exactly as it will over the real picture.
    """
    img = spec.get("image")
    if not img:
        return gradient_bg(), False
    p = _image_path(img, assets)
    if p.exists():
        photo = cover_fit(Image.open(p))
    elif placeholder:
        warn(f"image not found: {p}; laid out over a placeholder")
        photo = Image.new("RGB", (W, H), PLACEHOLDER)
    else:
        raise SystemExit(f"image not found: {p}")
    return scrim(photo, spec.get("scrim", "left"), float(spec.get("scrim_strength", 1.0))), True


def is_color(v) -> bool:
    """True for a NAMED_COLORS key or a #RRGGBB hex string.

    Split out of _color so validate() can reject a bad colour before a render
    aborts on it. The hex branch also checks the digits: 'chartreuse!' is six
    characters after stripping nothing, and used to reach int(..., 16).
    """
    if not isinstance(v, str):
        return False
    if v in NAMED_COLORS:
        return True
    h = v.lstrip("#")
    return len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h)


def _color(spec, key, default):
    v = spec.get(key)
    if v is None:
        return default
    if not is_color(v):
        raise SystemExit(f"unknown colour '{v}' for '{key}'")
    if v in NAMED_COLORS:
        return NAMED_COLORS[v]
    h = v.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def render_cover(c, s, ctx, on_image):
    size = s.get("size", 150)
    lh = int(size * 1.1)
    # Wrapped inside the gutters: drawn as one line it ran off the canvas edge.
    y = para(
        c,
        M,
        Y_COVER_TITLE,
        s["title"],
        font("x", size),
        INK,
        X_RIGHT - M,
        lh,
        shadow=True,
        size=size,
        label="cover title",
    )
    # A second title line pushes the subtitle down by exactly one line.
    sub_y = Y_COVER_SUB + max(0, y - (Y_COVER_TITLE + lh))
    para(
        c,
        M,
        sub_y,
        s.get("subtitle", ""),
        font("l", 50),
        INK_2,
        1450,
        68,
        shadow=True,
        label="cover subtitle",
    )
    sp = s.get("speaker") or {}
    y = 1140
    line(c, (M, y), sp.get("name", ""), font("s", 30), ACCENT, label="speaker name")
    line(c, (M, y + 45), sp.get("role", ""), font("r", 27), INK_2, label="speaker role")
    line(c, (M, y + 92), s.get("venue", ""), font("r", 24), INK_3, label="venue")
    lg = ctx["logo"]
    w = int(LOGO_H_COVER * lg.width / lg.height)
    place_logo(c, lg, LOGO_H_COVER, (X_RIGHT - w, 1195))


def render_statement(c, s, ctx, on_image):
    kicker(c, s.get("kicker"), ctx["greek"])
    size = s.get("size", 84 if on_image else 86)
    maxw = s.get("maxw", 1500 if on_image else 2260)
    lh = int(size * 1.25)
    y = para(
        c,
        M,
        s.get("y", 470),
        s["text"],
        font("l", size),
        INK,
        maxw,
        lh,
        shadow=on_image,
        size=size,
        label="statement",
    )
    if s.get("emphasis"):
        para(
            c,
            M,
            y + int(lh * 0.35),
            s["emphasis"],
            font("l", size),
            ACCENT,
            maxw,
            lh,
            shadow=on_image,
            size=size,
            label="emphasis",
        )
    if s.get("coda"):
        line(
            c,
            (M, s.get("coda_y", 980)),
            s["coda"],
            font("l", 44),
            ACCENT,
            shadow=on_image,
            label="coda",
        )
    footer(c, ctx["logo"], s.get("source"))


def render_hero_stat(c, s, ctx, on_image):
    kicker(c, s.get("kicker"), ctx["greek"])
    # A stat can sit on the open side of a photograph rather than the gutter.
    right = s.get("align", "left") == "right"
    x = int(s.get("x", 1150 if right else M))
    # Narrow the text column over a photograph: a 'left' scrim has faded by ~x1840,
    # so a full-width line runs out of its own background and onto the image.
    if right:
        maxw_cap, maxw_sup = 1250, 1250
    elif on_image:
        maxw_cap, maxw_sup = 1700, 1750
    else:
        maxw_cap, maxw_sup = 2100, 1950
    maxw_cap = int(s.get("maxw", maxw_cap))
    maxw_sup = int(s.get("maxw", maxw_sup))
    vsize = s.get("size", 400 if on_image else 440)
    vy = s.get("y", 250 if on_image else 300)
    vcolor = _color(s, "color", INK)
    line(c, (x, vy), str(s["value"]), font("x", vsize), vcolor, shadow=on_image, label="hero value")
    cy = s.get("caption_y", vy + int(vsize * 1.18))
    csize = s.get("caption_size", 48 if right else (58 if on_image else 60))
    # The caption is normally accent cyan. When the number is red it goes white:
    # cyan against negative red is two loud colours fighting for the same eye.
    y = para(
        c,
        x + (6 if right else 0),
        cy,
        s.get("caption", ""),
        font("l", csize),
        _color(s, "caption_color", INK if vcolor == NEGATIVE else ACCENT),
        maxw_cap,
        int(csize * 1.25),
        shadow=on_image,
        size=csize,
        label="stat caption",
    )
    para(
        c,
        x + (6 if right else 0),
        y + 76,
        s.get("support", ""),
        font("r", 34 if right else (37 if on_image else 38)),
        INK_2,
        maxw_sup,
        47 if right else 52,
        shadow=on_image,
        label="stat support",
    )
    footer(c, ctx["logo"], s.get("source"))


def render_duo_stat(c, s, ctx, on_image):
    kicker(c, s.get("kicker"), ctx["greek"])
    para(
        c,
        M,
        Y_TITLE,
        s.get("title", ""),
        font("l", 52),
        INK,
        2250,
        64,
        shadow=on_image,
        size=52,
        label="duo title",
    )
    left, right = s["left"], s["right"]
    vsize = s.get("size", 300)
    for spec, x, default_col in ((left, M, INK), (right, DUO_X_RIGHT, ACCENT)):
        line(
            c,
            (x, 470),
            str(spec["value"]),
            font("x", vsize),
            _color(spec, "color", default_col),
            shadow=on_image,
            label="duo value",
        )
        para(
            c,
            x + 6,
            820,
            spec.get("caption", ""),
            font("r", 34),
            INK_2,
            1000,
            46,
            shadow=on_image,
            label="duo caption",
        )
    footer(c, ctx["logo"], s.get("source"))


def render_bars(c, s, ctx, on_image):
    kicker(c, s.get("kicker"), ctx["greek"])
    para(
        c,
        M,
        Y_TITLE,
        s.get("title", ""),
        font("l", 54),
        INK,
        2250,
        66,
        shadow=on_image,
        size=54,
        label="bars title",
    )
    draw_bars(c, s["cats"], s["vals"], s.get("highlight"), s.get("unit", ""))
    if s.get("axis_label"):
        line(c, (M, 1235), s["axis_label"], font("r", 28), INK_2, label="axis label")
    footer(c, ctx["logo"], s.get("source"))


def render_points(c, s, ctx, on_image):
    kicker(c, s.get("kicker"), ctx["greek"])
    para(
        c,
        M,
        Y_TITLE,
        s.get("title", ""),
        font("l", 56),
        INK,
        2250,
        68,
        shadow=on_image,
        size=56,
        label="points title",
    )
    y = s.get("y", 500)
    for p in s["points"]:
        mark(c, [M, y + 12, M + 18, y + 30], ACCENT)
        y = (
            para(c, M + 42, y, p, font("r", 37), INK_2, 2050, 50, shadow=on_image, label="point")
            + 34
        )
    if s.get("takeaway"):
        line(c, (M, y + 6), s["takeaway"], font("s", 44), ACCENT, shadow=on_image, label="takeaway")
    footer(c, ctx["logo"], s.get("source"))


def render_divider(c, s, ctx, on_image):
    kicker(c, s.get("kicker"), ctx["greek"])
    x = M if s.get("align", "right") == "left" else 1290
    # The right-hand column ends at the gutter; it used to run 15px past it.
    maxw = X_RIGHT - x
    size = s.get("size", 96)
    para(
        c,
        x,
        s.get("y", 560),
        s["title"],
        font("x", size),
        INK,
        maxw,
        int(size * 1.17),
        shadow=on_image,
        size=size,
        label="divider title",
    )
    place_logo(c, ctx["logo"], LOGO_H_CONTENT, (M, Y_FOOTER_LOGO))


def render_closing(c, s, ctx, on_image):
    kicker(c, s.get("kicker"), ctx["greek"])
    size = s.get("size", 72)
    para(
        c,
        M,
        s.get("y", 330),
        s["text"],
        font("l", size),
        INK,
        2050,
        92,
        shadow=on_image,
        size=size,
        label="closing",
    )
    if s.get("coda"):
        line(
            c,
            (M, s.get("coda_y", 1130)),
            s["coda"],
            font("l", 40),
            ACCENT,
            shadow=on_image,
            label="closing coda",
        )
    place_logo(c, ctx["logo"], s.get("logo_h", 52), (M, 1290))


def render_back(c, s, ctx, on_image):
    lg = ctx["logo"]
    w = int(LOGO_H_BACK * lg.width / lg.height)
    place_logo(c, lg, LOGO_H_BACK, ((W - w) // 2, (H - LOGO_H_BACK) // 2))


RENDERERS = {
    "cover": _two_phase(render_cover),
    "statement": _two_phase(render_statement),
    "hero-stat": _two_phase(render_hero_stat),
    "duo-stat": _two_phase(render_duo_stat),
    "bars": _two_phase(render_bars),
    "points": _two_phase(render_points),
    "divider": _two_phase(render_divider),
    "closing": _two_phase(render_closing),
    "back": _two_phase(render_back),
}
REQUIRED_KEYS = {
    "cover": ["title"],
    "statement": ["text"],
    "hero-stat": ["value"],
    "duo-stat": ["left", "right"],
    "bars": ["cats", "vals"],
    "points": ["points"],
    "divider": ["title"],
    "closing": ["text"],
    "back": [],
}

# ============================================================ text for assistive technology


def _brand_name(greek: bool) -> str:
    return "Εθνική Τράπεζα" if greek else "National Bank of Greece"


def slide_title(s: dict, greek: bool = False) -> str:
    """The one line a screen reader and PowerPoint's outline announce for the slide."""
    t = s.get("type")
    if t == "hero-stat":
        return f"{s.get('value', '')} {s.get('caption', '')}".strip()
    if t == "duo-stat" and not s.get("title"):
        return f"{(s.get('left') or {}).get('value', '')} {(s.get('right') or {}).get('value', '')}".strip()
    if t == "back":
        return _brand_name(greek)
    return str(s.get("title") or s.get("text") or "").strip()


def slide_text(s: dict, greek: bool = False) -> str:
    """Everything the slide shows, in reading order: the picture's alt text.

    A keynote slide is one flattened image, so without this a screen reader
    announced every slide by its file name ('slide_01.jpg'). Standard #22 holds
    in keynote mode too.
    """
    t = s.get("type")
    parts: list[str] = [s.get("kicker", "")]
    if t == "cover":
        sp = s.get("speaker") or {}
        parts += [
            s.get("title", ""),
            s.get("subtitle", ""),
            sp.get("name", ""),
            sp.get("role", ""),
            s.get("venue", ""),
        ]
    elif t in ("statement", "closing"):
        parts += [s.get("text", ""), s.get("emphasis", ""), s.get("coda", "")]
    elif t == "hero-stat":
        parts += [str(s.get("value", "")), s.get("caption", ""), s.get("support", "")]
    elif t == "duo-stat":
        parts.append(s.get("title", ""))
        for side in ("left", "right"):
            half = s.get(side) or {}
            parts.append(f"{half.get('value', '')} {half.get('caption', '')}".strip())
    elif t == "bars":
        unit = s.get("unit", "")
        pairs = zip(s.get("cats") or [], s.get("vals") or [], strict=False)
        parts += [
            s.get("title", ""),
            ", ".join(f"{c} {v}{unit}" for c, v in pairs),
            s.get("axis_label", ""),
        ]
    elif t == "points":
        parts += [
            s.get("title", ""),
            *[str(p) for p in s.get("points") or []],
            s.get("takeaway", ""),
        ]
    elif t == "divider":
        parts.append(s.get("title", ""))
    elif t == "back":
        parts.append(_brand_name(greek))
    parts.append(s.get("source", ""))
    return "\n".join(str(p).strip() for p in parts if str(p).strip())


# ============================================================ assembly


def white_wordmark(path: Path) -> Image.Image:
    """The Greek wordmark, recoloured white. Greek logo on every deck, always."""
    lg = Image.open(path).convert("RGBA")
    a = np.array(lg)
    mask = a[:, :, 3] > 8
    a[:, :, 0][mask] = a[:, :, 1][mask] = a[:, :, 2][mask] = 255
    return Image.fromarray(a)


def build_pptx(
    images: list[Path],
    notes: list[str],
    out: Path,
    slides: list[dict] | None = None,
    greek: bool = False,
) -> None:
    from pptx import Presentation
    from pptx.util import Emu

    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(EMU_W), Emu(EMU_H)
    title_only = prs.slide_layouts[5]  # a real title placeholder, for assistive technology
    specs = slides if slides is not None else [{} for _ in images]
    for img, note, spec in zip(images, notes, specs, strict=True):
        s = prs.slides.add_slide(title_only)
        title = s.shapes.title
        if title is not None:
            title.text = slide_title(spec, greek) or img.stem
            # Covered by the full-bleed frame: announced by screen readers and shown
            # in the outline, never seen on screen.
            title.left, title.top, title.width, title.height = 0, 0, Emu(EMU_W), Emu(EMU_H // 6)
        pic = s.shapes.add_picture(str(img), Emu(0), Emu(0), width=Emu(EMU_W), height=Emu(EMU_H))
        # python-pptx seeds descr with the file name, which is what a screen reader
        # used to announce for every slide.
        pic._element.nvPicPr.cNvPr.set("descr", slide_text(spec, greek) or slide_title(spec, greek))
        if note:
            frame = s.notes_slide.notes_text_frame
            if frame is not None:
                frame.text = note
    prs.save(str(out))


def build_pdf(images: list[Path], out: Path) -> None:
    frames = [Image.open(p).convert("RGB") for p in images]
    # 4:4:4 like the frames (hard rule 7). Without subsampling=0 Pillow re-encoded
    # the PDF, the file that goes on the AV laptop, at 4:2:0.
    frames[0].save(
        out, save_all=True, append_images=frames[1:], resolution=DPI, quality=92, subsampling=0
    )


# ============================================================ validation


def warn(msg: str) -> None:
    print(f"  warning: {msg}", file=sys.stderr)


# Colour keys a renderer will push through _color(). Two live on the slide,
# two inside the duo-stat halves.
_COLOR_KEYS = ("color", "caption_color")
_COLOR_SUBKEYS = ("left", "right")
# Blocks with a line budget. Anything else is bounded by the gutter, the footer
# row and its neighbours.
LINE_BUDGET = {"cover title": 2}
_GUTTER_SLACK = 4  # px of glyph overhang tolerated past the gutter


def _blank(v) -> bool:
    """A string that renders to nothing. Numbers and lists are never blank."""
    return isinstance(v, str) and not v.strip()


def _logo_stub() -> Image.Image:
    """Stands in for the wordmark when laying out: same 1200x348 proportions."""
    return Image.new("RGBA", (1200, 348))


def _layout(slide: dict, greek: bool = False) -> _Plan:
    global _PLAN
    canvas = Image.new("RGBA", (W, H), GROUND_TOP + (255,))  # never painted in this pass
    ctx = {"logo": _logo_stub(), "greek": greek}
    _PLAN = plan = _Plan()
    try:
        RENDERERS[slide["type"]].layout(canvas, slide, ctx, bool(slide.get("image")))  # type: ignore[attr-defined]
    finally:
        _PLAN = None
    return plan


def text_boxes(slide: dict, greek: bool = False) -> list[tuple[str, Box]]:
    """Every text box `slide` would draw, as (label, (x0, y0, x1, y1)) ink boxes,
    measured with the renderer's own fonts and wrapping."""
    return [(label, box) for label, box, _, _ in _layout(slide, greek).texts]


def _fit_errors(i: int, t: str, plan: _Plan) -> list[str]:
    """Text that leaves its column, its line budget, the safe area or its neighbours."""
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    def once(label: str, kind: str, msg: str) -> None:
        if (label, kind) not in seen:
            seen.add((label, kind))
            errors.append(f"slide {i} ({t}): {label} {msg}")

    lines: dict[str, int] = {}
    for label, (x0, y0, x1, y1), footer_chrome, _ in plan.texts:
        lines[label] = lines.get(label, 0) + 1
        if x1 > X_RIGHT + _GUTTER_SLACK:
            once(
                label,
                "right",
                f"runs past the right gutter (ends at x={x1:.0f}, gutter x={X_RIGHT}); "
                f"shorten it or lower its size",
            )
        if x0 < SAFE:
            once(label, "left", f"starts outside the safe area (x={x0:.0f}, limit {SAFE})")
        if y0 < SAFE:
            once(label, "top", f"starts above the safe area (y={y0:.0f}, limit {SAFE})")
        if not footer_chrome and y1 > CONTENT_BOTTOM:
            once(
                label,
                "bottom",
                f"runs into the footer (ends at y={y1:.0f}, limit y={CONTENT_BOTTOM}); "
                f"shorten it or lower its size",
            )
    for label, budget in LINE_BUDGET.items():
        if lines.get(label, 0) > budget:
            once(
                label,
                "lines",
                f"needs {lines[label]} lines at this size, the budget is {budget}; "
                f"shorten it or lower `size`",
            )
    texts = plan.texts
    for a in range(len(texts)):
        la, ba, _, block_a = texts[a]
        for b in range(a + 1, len(texts)):
            lb, bb, _, block_b = texts[b]
            if block_a == block_b:
                continue
            if ba[0] < bb[2] and bb[0] < ba[2] and ba[1] < bb[3] and bb[1] < ba[3]:
                once(la, f"overlap:{lb}", f"overlaps {lb}")
    return errors


def validate(spec: dict, assets: Path, placeholder_images: bool = False) -> list[str]:
    """Check a spec well enough that `--validate` is worth trusting.

    README.md sells --validate as the gate before a render. Specs used to clear it
    and then fail the build or ship broken: whitespace-only text, mismatched cats
    and vals, an all-zero or partly negative bar series, an unknown colour name,
    and text that ran off the canvas or past the gutter. Every block is now laid
    out with the renderer's own fonts and wrapping and measured.
    """
    errors: list[str] = []
    slides = spec.get("slides") or []
    if not slides:
        errors.append("spec has no slides")
    greek = str((spec.get("meta") or {}).get("language", "en")).lower().startswith("el")
    charts = 0
    for i, s in enumerate(slides, 1):
        t = s.get("type")
        if t not in RENDERERS:
            errors.append(f"slide {i}: unknown type '{t}' (expected one of {sorted(RENDERERS)})")
            continue
        before = len(errors)
        for k in REQUIRED_KEYS[t]:
            if k not in s:
                errors.append(f"slide {i} ({t}): missing required key '{k}'")
            elif _blank(s[k]):
                errors.append(f"slide {i} ({t}): '{k}' is blank, so it would render nothing")
        # Standard #21: a keynote slide without a speaker note is half a slide.
        if t != "back" and not str(s.get("notes", "")).strip():
            errors.append(f"slide {i} ({t}): missing speaker notes")
        if t == "points":
            for j, p in enumerate(s.get("points") or [], 1):
                if not str(p).strip():
                    errors.append(f"slide {i} (points): point {j} is blank")
        if t == "bars":
            charts += 1
            cats = s.get("cats") or []
            vals = s.get("vals") or []
            if len(cats) != len(vals):
                errors.append(
                    f"slide {i} (bars): {len(cats)} cats and {len(vals)} vals; "
                    f"they must be the same length"
                )
            bad = [v for v in vals if isinstance(v, bool) or not isinstance(v, (int, float))]
            if bad:
                errors.append(f"slide {i} (bars): non-numeric value(s) {bad}")
            else:
                if vals and max(vals) <= 0:
                    errors.append(
                        f"slide {i} (bars): every value is {max(vals)} or less; a bar chart "
                        f"needs at least one positive value to set its scale"
                    )
                negative = [v for v in vals if v < 0]
                if negative:
                    errors.append(
                        f"slide {i} (bars): negative value(s) {negative}; keynote bars stand on "
                        f"a true zero baseline, so state a decline as a hero-stat "
                        f"(color: negative) or a statement"
                    )
            if len(vals) > MAX_BARS:
                errors.append(f"slide {i}: {len(vals)} bars exceeds the {MAX_BARS} limit")
        for key in _COLOR_KEYS:
            if key in s and not is_color(s[key]):
                errors.append(f"slide {i} ({t}): unknown colour '{s[key]}' for '{key}'")
        for side in _COLOR_SUBKEYS:
            half = s.get(side)
            if isinstance(half, dict) and "color" in half and not is_color(half["color"]):
                errors.append(
                    f"slide {i} ({t}): unknown colour '{half['color']}' for '{side}.color'"
                )
        if s.get("scrim") and s["scrim"] not in SCRIM_SIDES:
            errors.append(f"slide {i}: unknown scrim '{s['scrim']}'")
        if s.get("image"):
            p = _image_path(s["image"], assets)
            if not p.exists():
                if placeholder_images:
                    warn(f"slide {i}: image not found: {p}; it will be laid out over a placeholder")
                else:
                    errors.append(f"slide {i}: image not found: {p}")
        structural = any("image not found" not in e for e in errors[before:])
        if not structural:
            try:
                errors += _fit_errors(i, t, _layout(s, greek))
            except SystemExit as e:  # no usable font, or a value a renderer refuses
                errors.append(f"slide {i} ({t}): could not be laid out: {e}")
            except Exception as e:  # noqa: BLE001  a bad spec must never surface as a traceback
                errors.append(f"slide {i} ({t}): could not be laid out: {type(e).__name__}: {e}")
    if charts > MAX_CHARTS:
        errors.append(f"{charts} chart slides; keynote mode allows at most {MAX_CHARTS}")
    return errors


def font_report() -> list[str]:
    """The font file behind each weight, so a fallback is visible before a render."""
    lines = []
    for kind, weight in WEIGHT_NAMES.items():
        p = font_path(kind)
        note = (
            "" if p.name.lower() == FONT_FILES[kind][0].lower() else "  (fallback: Aptos not found)"
        )
        lines.append(f"  {weight:<9} {p}{note}")
    return lines


# ============================================================ frames


def _frame_key(
    s: dict,
    base_seed: int,
    assets: Path,
    logo_path: Path,
    greek: bool,
    placeholder: bool,
    source_digest: str,
) -> str:
    """What a frame depends on: the slide spec, the grain seed, the language, the
    photograph and wordmark on disk, and this compositor's own code."""
    h = hashlib.sha256()
    h.update(source_digest.encode())
    h.update(json.dumps(s, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8"))
    h.update(f"|{base_seed}|{greek}|{placeholder}".encode())
    paths = [logo_path]
    if s.get("image"):
        paths.append(_image_path(s["image"], assets))
    for p in paths:
        if p.exists():
            st = p.stat()
            h.update(f"|{p}|{st.st_size}|{st.st_mtime_ns}".encode())
    return h.hexdigest()[:20]


def _slide_seed(s: dict, base_seed: int) -> int:
    """Grain seed from the slide's own content, not its position, so a slide that
    moves keeps a byte-identical frame and a reused frame matches a fresh render."""
    digest = hashlib.sha256(
        json.dumps(s, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    )
    return base_seed + int(digest.hexdigest()[:8], 16)


def _publish(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


# ============================================================ main


def main() -> int:
    ap = argparse.ArgumentParser(description="Build an NBG keynote from a YAML spec.")
    ap.add_argument("spec", type=Path, help="YAML deck specification")
    ap.add_argument("--out", type=Path, help="output stem (overrides meta.output)")
    ap.add_argument("--assets", type=Path, help="base directory for relative image paths")
    ap.add_argument(
        "--validate", action="store_true", help="check the spec and its layout, render nothing"
    )
    ap.add_argument(
        "--slides",
        help="comma-separated 1-based indices to re-render; other slides reuse their frame "
        "only if nothing they depend on changed",
    )
    ap.add_argument(
        "--placeholder-images",
        action="store_true",
        help="lay out a slide whose photograph is missing over a placeholder instead of failing",
    )
    args = ap.parse_args()

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    meta = spec.get("meta") or {}
    assets = (args.assets or Path(meta.get("assets", args.spec.parent))).expanduser()

    errors = validate(spec, assets, placeholder_images=args.placeholder_images)
    slides = spec.get("slides") or []
    only = {int(n) for n in args.slides.split(",") if n.strip()} if args.slides else None
    if only:
        errors += [
            f"--slides: there is no slide {n}" for n in sorted(only) if not 1 <= n <= len(slides)
        ]
    if errors:
        print("Spec validation failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if args.validate:
        print(f"OK: {len(slides)} slides, spec and layout valid.")
        print("fonts:")
        for ln in font_report():
            print(ln)
        return 0

    if args.out:
        stem = args.out.expanduser()
    elif meta.get("output"):
        stem = Path(meta["output"]).expanduser()
    else:
        print("No output path: pass --out or set meta.output", file=sys.stderr)
        return 1
    stem.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = stem.parent / f"{stem.name}_frames"
    cache = frames_dir / ".cache"
    cache.mkdir(parents=True, exist_ok=True)

    logo_path = Path(
        meta.get("logo", Path(__file__).resolve().parents[2] / "assets/nbg-logo-gr.png")
    ).expanduser()
    if not logo_path.exists():
        print(f"NBG wordmark not found: {logo_path}", file=sys.stderr)
        return 1

    greek = str(meta.get("language", "en")).lower().startswith("el")
    ctx = {"logo": white_wordmark(logo_path), "greek": greek}
    base_seed = int((spec.get("theme") or {}).get("seed", 7))
    source_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    # Frames are stored by what they depend on, never by position: --slides used
    # to pair frame N with slide N, so an inserted slide shifted every later slide
    # onto a stale image and a slide went missing.
    images, notes, keys = [], [], []
    for i, s in enumerate(slides, 1):
        key = _frame_key(
            s, base_seed, assets, logo_path, greek, args.placeholder_images, source_digest
        )
        keys.append(key)
        cached = cache / f"{key}.jpg"
        out_img = frames_dir / f"slide_{i:02d}.jpg"
        if only is not None and i not in only and cached.exists():
            print(f"  slide {i:02d}  {s['type']}  (unchanged, frame reused)")
        else:
            ground, on_image = _ground(s, assets, placeholder=args.placeholder_images)
            canvas = grain(ground, _slide_seed(s, base_seed))  # deterministic per slide
            RENDERERS[s["type"]](canvas, s, ctx, on_image)
            # JPEG 4:4:4, 4:2:0 smears the grain and the fine type
            canvas.convert("RGB").save(cached, quality=92, subsampling=0)
            print(f"  slide {i:02d}  {s['type']}")
        _publish(cached, out_img)
        images.append(out_img)
        notes.append(str(s.get("notes", "")))

    # A deck that shrank leaves no stale slide_NN.jpg behind, and the store keeps
    # only the frames the current deck uses.
    current = {p.name for p in images}
    for p in frames_dir.glob("slide_*.jpg"):
        if p.name not in current:
            p.unlink()
    for p in cache.glob("*.jpg"):
        if p.stem not in keys:
            p.unlink()

    pptx_path, pdf_path = stem.with_suffix(".pptx"), stem.with_suffix(".pdf")
    build_pptx(images, notes, pptx_path, slides=slides, greek=greek)
    build_pdf(images, pdf_path)
    print(f"\n{pptx_path}  ({len(slides)} slides)")
    print(f"{pdf_path}")
    print(f"frames: {frames_dir}  (kept, so --slides can re-render one at a time)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
