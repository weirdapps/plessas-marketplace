#!/usr/bin/env python3
"""Size `custom` slide elements with the builder's own measurements, before a build.

    decks-py measure text "<text>" --w 4.5 [--size 16] [--bold] [--role card_body]
    decks-py measure image <path> --box X Y W H [--deck deck.yaml]
                           [--halign left|center|right] [--valign top|center|bottom]
    decks-py measure batch <requests.json> [--deck deck.yaml]

text: the lines the text wraps to in a box `--w` inches wide, and the `h` to give the
element. It wraps a little narrower than the builder does and adds 0.03 in, the
margin the validator's Text Fit needs, so a box sized from it passes both. Pass the
role, size and bold the element will carry: the role sets the line spacing.

image: the x, y, w and h that keep the picture's shape inside the box, aligned as
asked, and a warning when a PNG or JPEG is too small for it at the builder's minimum
DPI. A relative path resolves like the builder's: against the deck's folder, then
the plugin's assets.

batch: a JSON list of requests, each {"text", "w", "size"?, "bold"?, "role"?} or
{"image", "box", "halign"?, "valign"?}; prints the answers as a JSON list.

Exit codes: 0 measured; 2 bad input (a missing image, an unknown role).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import nbg_build  # noqa: E402
import nbg_spec  # noqa: E402
import nbg_tokens  # noqa: E402
from nbg_text import metrics  # noqa: E402

SAFETY = 0.985  # wrap width beyond the builder's FIT, for the validator's measurer
MARGIN_IN = 0.03


class BadInput(Exception):
    pass


def measure_text(
    text: str,
    w: float,
    *,
    size: float | None = None,
    bold: bool | None = None,
    role: str = "card_body",
) -> dict[str, Any]:
    try:
        base = nbg_tokens.type_style(role)
    except KeyError as e:
        raise BadInput(f"unknown role {role!r}") from e
    s = nbg_build.Style(
        float(size if size is not None else base["size"]),
        bool(base["bold"] if bold is None else bold),
        str(base["color"]),
    )
    spacing = nbg_build.BODY_SPACING if role in ("body", "body_dense", "card_body") else 1.0
    lines = list(metrics().wrap(str(text), w * nbg_build.FIT * SAFETY, s.size, s.bold))
    h = nbg_build.text_height(len(lines), s, spacing) + MARGIN_IN
    return {"lines": len(lines), "h": round(h, 3), "wrapped": lines}


def _pixels(path: Path) -> tuple[int, int, bool]:
    from PIL import Image

    vector = path.suffix.lower() == ".svg"
    if vector:
        import io

        import resvg_py

        data = bytes(resvg_py.svg_to_bytes(svg_path=str(path), width=600))
        with Image.open(io.BytesIO(data)) as im:
            return im.width, im.height, True
    with Image.open(path) as im:
        return im.width, im.height, False


def fit_image(
    raw: str,
    box: list[float],
    *,
    spec_dir: Path,
    halign: str = "center",
    valign: str = "center",
) -> dict[str, Any]:
    path = nbg_spec.resolve_asset(raw, spec_dir)
    if path is None:
        raise BadInput(f"image not found: {raw}")
    bx, by, bw, bh = (float(v) for v in box)
    px_w, px_h, vector = _pixels(path)
    aspect = px_w / px_h
    w, h = (bw, bw / aspect) if bw / aspect <= bh else (bh * aspect, bh)
    x = bx + {"left": 0.0, "center": (bw - w) / 2, "right": bw - w}[halign]
    y = by + {"top": 0.0, "center": (bh - h) / 2, "bottom": bh - h}[valign]
    out: dict[str, Any] = {
        "x": round(x, 3),
        "y": round(y, 3),
        "w": round(w, 3),
        "h": round(h, 3),
        "px": [px_w, px_h],
    }
    dpi = float(nbg_tokens.get("components.image.min_dpi"))
    if not vector and w * dpi > px_w + 0.5:
        out["warning"] = (
            f"{px_w} px wide is under {dpi:g} DPI at {w:.2f} in; the builder draws it at "
            f"{px_w / dpi:.2f} in"
        )
    return out


def answer(req: dict[str, Any], spec_dir: Path) -> dict[str, Any]:
    if "text" in req:
        return measure_text(
            req["text"],
            float(req["w"]),
            size=req.get("size"),
            bold=req.get("bold"),
            role=req.get("role", "card_body"),
        )
    if "image" in req:
        return fit_image(
            req["image"],
            req["box"],
            spec_dir=spec_dir,
            halign=req.get("halign", "center"),
            valign=req.get("valign", "center"),
        )
    raise BadInput(f"a request needs 'text' or 'image': {req}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="what", required=True)
    t = sub.add_parser("text")
    t.add_argument("text")
    t.add_argument("--w", type=float, required=True)
    t.add_argument("--size", type=float)
    t.add_argument("--bold", action="store_true", default=None)
    t.add_argument("--role", default="card_body")
    i = sub.add_parser("image")
    i.add_argument("path")
    i.add_argument("--box", type=float, nargs=4, required=True, metavar=("X", "Y", "W", "H"))
    i.add_argument("--deck", type=Path)
    i.add_argument("--halign", choices=("left", "center", "right"), default="center")
    i.add_argument("--valign", choices=("top", "center", "bottom"), default="center")
    b = sub.add_parser("batch")
    b.add_argument("requests", type=Path)
    b.add_argument("--deck", type=Path)
    args = ap.parse_args(argv)

    try:
        if args.what == "text":
            result: Any = measure_text(
                args.text, args.w, size=args.size, bold=args.bold, role=args.role
            )
        else:
            spec_dir = args.deck.resolve().parent if args.deck else Path.cwd()
            if args.what == "image":
                result = fit_image(
                    args.path, args.box, spec_dir=spec_dir, halign=args.halign, valign=args.valign
                )
            else:
                requests = json.loads(args.requests.read_text(encoding="utf-8"))
                result = [answer(r, spec_dir) for r in requests]
    except (BadInput, OSError, ValueError, KeyError) as e:
        print(f"measure: {e}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
