#!/usr/bin/env python3
"""House-style illustrations for NBG decks, drawn by Gemini's image model.

    decks-py illustrate --probe
    decks-py illustrate --brief "<scene>" --out <file.png> [--ref <anchor.png>]
                        [--size-in W H | --aspect 4:3] [--candidates N]

One style for every deck. The prompt is the house style below with the palette from
tokens.yaml (`illustration.palette`), and every illustration after a deck's first is
drawn with that first one as a style reference, so a set reads as one hand. A picture
carries no words or numbers: the slide's own text boxes say those, so they stay
editable, spelled right and translatable.

The brief leaves this machine: it goes to Google's Gemini API under the user's own
GEMINI_API_KEY. So a brief describes a generic scene, and one holding a digit, a
currency or percent sign, or the bank's name is refused before anything is sent.
The key is read from the environment, else on a Mac from the login Keychain item
named GEMINI_API_KEY: a profile that exports it from the Keychain reaches login
shells only, not a Claude Code session started some other way.

Every picture written is cleaned the same way: trimmed to its subject, at most
`illustration.max_px` on the long side, and its white background, the near-white
region joined to the border, made transparent. It is saved as RGBA: a palette PNG
with one transparent index renders as a white box on a tinted card in LibreOffice.

Exit codes: 0 written; 1 the model returned no image; 2 bad input, or the API or the
network failed (the message says which); 3 no GEMINI_API_KEY, so the deck uses the
library instead (this is not an error).
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import nbg_tokens  # noqa: E402

MODEL = os.environ.get("DECKS_IMAGE_MODEL", "gemini-3-pro-image-preview")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT_S = 240
ASPECTS = ("1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9")

STYLE = (
    "Premium isometric vector illustration for a bank's strategy presentation, in the style "
    "of a top consulting firm's digital report. Clean geometric shapes, flat colour with subtle "
    "two-tone shading on the isometric faces, crisp edges, no outlines. Strict palette only: "
    "{palette}. Pure white background, no ground shadow, no drop shadows, no gradients, no glow. "
    "No text, no letters, no numbers, no logos, no writing anywhere; screens show only simple "
    "abstract bars, lines and blocks, never a pie chart. People are simple, stylised and "
    "faceless, in teal and "
    "deep-teal clothing. AI agents, when the scene has any, are small friendly floating "
    "rounded-hexagon orbs in cyan with a white four-point sparkle inside. Generous white space "
    "around the subject; the subject is centred and fully inside the frame."
)
REFERENCE = (
    "Match the reference image exactly in drawing style, palette, proportions, shading and the "
    "way people and agents are drawn. Draw only the scene described next, not the reference's "
    "content."
)

# What must not leave the machine, and what an illustration must never carry.
_REFUSED = (
    (re.compile(r"\d"), "a digit"),
    (re.compile(r"[€$£%]"), "a currency or percent sign"),
    (
        re.compile(r"\bNBG\b|national\s+bank|εθνικ\w*\s+τρ[αά]πεζ", re.IGNORECASE),
        "the bank's name",
    ),
)

NEAR_WHITE = 240  # every channel at or above this is background, if joined to the border
CONTENT = 245  # trimming keeps everything darker than this
PAD = 0.03  # trimmed margin, a share of the subject's longer side


class Failure(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def api_key() -> str:
    """GEMINI_API_KEY from the environment, else from the macOS login Keychain."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key or sys.platform != "darwin" or os.environ.get("DECKS_NO_KEYCHAIN"):
        return key
    try:
        found = subprocess.run(
            ["security", "find-generic-password", "-s", "GEMINI_API_KEY", "-w"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return found.stdout.strip() if found.returncode == 0 else ""


def refused(brief: str) -> str | None:
    """Why the brief may not be sent, or None."""
    for pattern, what in _REFUSED:
        if pattern.search(brief):
            return what
    return None


def prompt(brief: str, *, with_reference: bool) -> str:
    colours = nbg_tokens.get("illustration.palette").items()
    palette = ", ".join(f"{name.replace('_', ' ')} #{hexa}" for name, hexa in colours)
    parts = [STYLE.format(palette=palette)]
    if with_reference:
        parts.append(REFERENCE)
    parts.append(f"Scene: {brief.strip()}")
    return " ".join(parts)


def nearest_aspect(w: float, h: float) -> str:
    target = w / h

    def ratio(a: str) -> float:
        x, y = a.split(":")
        return int(x) / int(y)

    return min(ASPECTS, key=lambda a: abs(ratio(a) / target - 1))


def request_body(text: str, refs: list[Path], aspect: str) -> dict[str, Any]:
    parts: list[dict[str, Any]] = []
    for ref in refs:
        mime = "image/jpeg" if ref.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        data = base64.b64encode(ref.read_bytes()).decode("ascii")
        parts.append({"inlineData": {"mimeType": mime, "data": data}})
    parts.append({"text": text})
    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect, "imageSize": "2K"},
        },
    }


def _post(body: dict[str, Any], key: str) -> dict[str, Any]:
    """The API's JSON answer. The key goes in a header, never in the URL, so it
    cannot land in a log or an error message."""
    req = urllib.request.Request(
        ENDPOINT.format(model=MODEL),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return dict(json.loads(resp.read().decode("utf-8")))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            try:
                detail = json.loads(detail)["error"]["message"]
            except (ValueError, KeyError, TypeError):
                detail = detail[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt == 1:
                time.sleep(10)
                continue
            raise Failure(2, f"the Gemini API answered {e.code}: {detail}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 1:
                time.sleep(5)
                continue
            raise Failure(2, f"could not reach the Gemini API: {e}") from e
    raise Failure(2, "the Gemini API did not answer")  # pragma: no cover - loop always returns


def image_from(answer: dict[str, Any]) -> bytes:
    """The first picture in the answer, or Failure(1) saying why there is none."""
    candidates = answer.get("candidates") or []
    said: list[str] = []
    for cand in candidates:
        for part in (cand.get("content") or {}).get("parts") or []:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
            if part.get("text"):
                said.append(part["text"].strip()[:200])
    reason = candidates[0].get("finishReason") if candidates else None
    block = (answer.get("promptFeedback") or {}).get("blockReason")
    why = "; ".join(x for x in (block, reason, *said) if x) or "no reason given"
    raise Failure(1, f"the model returned no image ({why})")


def _border_background(mask: bytearray, w: int, h: int) -> bytearray:
    """Mark with 2 every near-white pixel (1 in `mask`) joined to the image border.

    A scanline fill over one flat buffer: each run of 1s is found and claimed by a
    C-speed regex, so a 1600 px picture takes a fraction of a second where Pillow's
    pixel-by-pixel floodfill takes many."""
    run = re.compile(rb"\x01+")
    st = mask
    stack = [(x, y) for y in (0, h - 1) for x in range(w)]
    stack += [(x, y) for x in (0, w - 1) for y in range(h)]
    while stack:
        x, y = stack.pop()
        row = y * w
        i = row + x
        if st[i] != 1:
            continue
        while i > row and st[i - 1] == 1:
            i -= 1
        found = run.match(st, i, row + w)
        if found is None:  # pragma: no cover - st[i] == 1 always starts a run
            continue
        start, end = found.span()
        st[start:end] = b"\x02" * (end - start)
        for ny in (y - 1, y + 1):
            if 0 <= ny < h:
                base = ny * w
                lo, hi = base + (start - row), base + (end - row)
                stack.extend((m.start() - base, ny) for m in run.finditer(st, lo, hi))
    return st


def _darkest_channel(rgb: Any) -> Any:
    """Per pixel, the lowest of R, G and B: near white only when all three are high."""
    from PIL import ImageChops

    r, g, b = rgb.split()
    return ImageChops.darker(ImageChops.darker(r, g), b)


def clean(data: bytes, max_px: int) -> Any:
    """Trimmed, sized, RGBA, with the white background joined to the border transparent.
    Whites inside the subject (a screen, a document, a speech bubble) stay white."""
    from PIL import Image

    with Image.open(io.BytesIO(data)) as raw:
        rgb = raw.convert("RGB")
    box = _darkest_channel(rgb).point(lambda v: 255 if v < CONTENT else 0).getbbox()
    if box is None:
        raise Failure(1, "the model returned a blank picture")
    x0, y0, x1, y1 = box
    pad = round(PAD * max(x1 - x0, y1 - y0))
    rgb = rgb.crop(
        (max(0, x0 - pad), max(0, y0 - pad), min(rgb.width, x1 + pad), min(rgb.height, y1 + pad))
    )
    scale = min(1.0, max_px / max(rgb.size))
    if scale < 1.0:
        rgb = rgb.resize(
            (round(rgb.width * scale), round(rgb.height * scale)), Image.Resampling.LANCZOS
        )
    mask = bytearray(_darkest_channel(rgb).point(lambda v: 1 if v >= NEAR_WHITE else 0).tobytes())
    st = _border_background(mask, rgb.width, rgb.height)
    alpha = bytes(st).translate(bytes(255 if v != 2 else 0 for v in range(256)))
    out = rgb.convert("RGBA")
    out.putalpha(Image.frombytes("L", rgb.size, alpha))
    return out


def generate(
    brief: str,
    out: Path,
    *,
    refs: list[Path],
    aspect: str,
    candidates: int,
    key: str,
) -> list[Path]:
    """Draw `candidates` pictures for the brief; one is written to `out`, more to
    `<stem>-c1.png` ... beside it, for the caller to look at and choose."""
    body = request_body(prompt(brief, with_reference=bool(refs)), refs, aspect)
    max_px = int(nbg_tokens.get("illustration.max_px"))
    targets = (
        [out]
        if candidates == 1
        else [out.with_name(f"{out.stem}-c{k}{out.suffix}") for k in range(1, candidates + 1)]
    )

    def one(target: Path) -> Path:
        picture = clean(image_from(_post(body, key)), max_px)
        picture.save(target, format="PNG", optimize=True)
        return target

    out.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=min(4, len(targets))) as pool:
        return list(pool.map(one, targets))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--probe", action="store_true", help="exit 0 if a key is set, 3 if not")
    ap.add_argument("--brief", help="the scene, in words: no digits, no money, no bank name")
    ap.add_argument("--out", type=Path, help="the .png to write")
    ap.add_argument("--ref", type=Path, action="append", default=[], help="style reference")
    ap.add_argument("--size-in", type=float, nargs=2, metavar=("W", "H"), help="the slot, inches")
    ap.add_argument("--aspect", choices=ASPECTS, help="aspect ratio, when no --size-in")
    ap.add_argument("--candidates", type=int, default=1, choices=range(1, 5))
    args = ap.parse_args(argv)

    key = api_key()
    if args.probe:
        if key:
            print(f"ready: {MODEL}")
            return 0
        print(
            "unavailable: no GEMINI_API_KEY (environment or Keychain); use the illustration library"
        )
        return 3
    if not args.brief or not args.out:
        ap.error("--brief and --out are required")
    if args.out.suffix.lower() != ".png":
        ap.error("--out must be a .png")
    why = refused(args.brief)
    if why:
        print(
            f"illustrate: the brief holds {why}. A picture carries no numbers or names, and the "
            "brief is sent to Google: describe the scene in words only.",
            file=sys.stderr,
        )
        return 2
    for ref in args.ref:
        if not ref.is_file():
            print(f"illustrate: reference not found: {ref}", file=sys.stderr)
            return 2
    if not key:
        print(
            "unavailable: no GEMINI_API_KEY (environment or Keychain); use the illustration library"
        )
        return 3
    aspect = nearest_aspect(*args.size_in) if args.size_in else (args.aspect or "4:3")
    try:
        written = generate(
            args.brief,
            args.out,
            refs=args.ref,
            aspect=aspect,
            candidates=args.candidates,
            key=key,
        )
    except Failure as e:
        print(f"illustrate: {e}", file=sys.stderr)
        return e.code
    from PIL import Image

    sizes = {}
    for p in written:
        with Image.open(p) as im:
            sizes[str(p)] = list(im.size)
    print(json.dumps({"model": MODEL, "aspect": aspect, "written": sizes}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
