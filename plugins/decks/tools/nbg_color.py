#!/usr/bin/env python3
"""WCAG colour maths shared by the decks Python tools.

nbg_build.py, nbg_validate.py and nbg-keynote/nbg_keynote.py all need the same
gamma-corrected relative luminance. They each used to carry their own copy; this
is the single one. No dependencies beyond the standard library, so the light
tools can import it without pulling in Pillow or python-pptx.
"""

from __future__ import annotations

# WCAG 2.1 contrast floors. "Large" is >=18pt regular or >=14pt bold.
AA_NORMAL = 4.5
AA_LARGE = 3.0


def _channel(v: float) -> float:
    """Linearise one 0-255 channel (WCAG 2.1 sRGB transfer function)."""
    v /= 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def relative_luminance(color) -> float:
    """WCAG relative luminance of 'RRGGBB', '#RRGGBB' or an (r, g, b) sequence."""
    if isinstance(color, str):
        h = color.lstrip("#")
        if len(h) != 6:
            raise ValueError(f"expected a 6-digit hex colour, got {color!r}")
        rgb: tuple[float, ...] = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    else:
        rgb = tuple(color)[:3]
    r, g, b = (_channel(float(c)) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b) -> float:
    """WCAG contrast ratio. Each argument is a colour or an already-computed
    luminance (a float), so a caller that sampled a photograph can pass its
    measurement straight in."""
    la = a if isinstance(a, float) else relative_luminance(a)
    lb = b if isinstance(b, float) else relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def min_ratio(size_pt: float, bold: bool = False) -> float:
    """The AA floor for text at `size_pt`. 18pt regular and 14pt bold are 'large'."""
    return AA_LARGE if (size_pt >= 18 or (bold and size_pt >= 14)) else AA_NORMAL
