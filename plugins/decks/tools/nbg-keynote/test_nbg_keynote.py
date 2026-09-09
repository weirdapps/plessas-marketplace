#!/usr/bin/env python3
"""Tests for the NBG keynote compositor.

Runs in CI under `pytest plugins`. Locally, without the dependencies installed:
    uv run --with pytest --with pillow --with numpy --with pyyaml --with python-pptx \
        python -m pytest test_nbg_keynote.py -q
"""

import nbg_keynote as k
import pytest
import yaml
from PIL import Image

# ---------------------------------------------------------------- greek_upper


@pytest.mark.parametrize(
    "given,expected",
    [
        ("η συναίνεση", "Η ΣΥΝΑΙΝΕΣΗ"),  # tonos dropped
        ("το πρόβλημα", "ΤΟ ΠΡΟΒΛΗΜΑ"),
        ("Άγιος Ιωάννης", "ΑΓΙΟΣ ΙΩΑΝΝΗΣ"),
        ("ευθύνη", "ΕΥΘΥΝΗ"),
        ("the consensus", "THE CONSENSUS"),  # Latin untouched
        ("ΕΤΕ και NBG", "ΕΤΕ ΚΑΙ NBG"),  # acronyms survive
    ],
)
def test_greek_upper(given, expected):
    assert k.greek_upper(given) == expected


def test_greek_upper_keeps_dialytika():
    # The tonos goes, the dialytika stays: they mean different things.
    assert k.greek_upper("προϊόν") == "ΠΡΟΪΟΝ"


def test_plain_upper_would_have_been_wrong():
    """The bug this function exists to prevent."""
    assert "η συναίνεση".upper() == "Η ΣΥΝΑΊΝΕΣΗ"
    assert k.greek_upper("η συναίνεση") != "η συναίνεση".upper()


# ------------------------------------------------------------------ contrast


def test_luminance_endpoints():
    assert k.luminance((255, 255, 255)) == pytest.approx(1.0, abs=1e-6)
    assert k.luminance((0, 0, 0)) == pytest.approx(0.0, abs=1e-6)


def test_contrast_ratio_white_on_black():
    assert k.contrast_ratio((255, 255, 255), 0.0) == pytest.approx(21.0, abs=0.01)


def test_ground_gradient_clears_accent_text():
    """The house gradient must carry cyan body text without any scrim help."""
    assert k.contrast_ratio(k.ACCENT, k.luminance(k.GROUND_BOT)) >= 4.5


def test_min_ratio_threshold_is_18pt():
    # 2560px spans 960pt, so 18pt == 48px.
    assert k._min_ratio(47) == 4.5
    assert k._min_ratio(48) == 3.0


def test_ensure_contrast_darkens_a_bright_patch():
    canvas = Image.new("RGBA", (k.W, k.H), (235, 235, 235, 255))
    box = (400, 400, 1200, 500)
    before = k._bg_luminance(canvas, box)
    k.ensure_contrast(canvas, box, k.INK, 4.5, "test")
    after = k._bg_luminance(canvas, box)
    assert after < before
    assert k.contrast_ratio(k.INK, after) >= 4.5


def test_ensure_contrast_leaves_a_dark_ground_alone():
    canvas = k.gradient_bg()
    box = (400, 400, 1200, 500)
    before = k._bg_luminance(canvas, box)
    k.ensure_contrast(canvas, box, k.INK, 4.5, "test")
    assert k._bg_luminance(canvas, box) == pytest.approx(before, abs=1e-9)


# ---------------------------------------------------------------- bar geometry


def _bar_rects(cats, vals, **kw):
    canvas = k.gradient_bg()
    base = canvas.copy()
    k.draw_bars(canvas, cats, vals, **kw)
    # columns where the render differs from the clean ground = bar coverage
    import numpy as np

    diff = np.abs(
        np.array(canvas.convert("RGB"), dtype=int) - np.array(base.convert("RGB"), dtype=int)
    ).sum(axis=2)
    # Sample just above the baseline (1170) so even the shortest bar is crossed.
    cols = np.where(diff[1150, :] > 30)[0]
    runs, start = [], cols[0]
    for a, b in zip(cols, cols[1:]):
        if b - a > 1:
            runs.append((start, a))
            start = b
    runs.append((start, cols[-1]))
    return runs


def test_two_bars_are_capped_and_centred():
    runs = _bar_rects(["2008", "2024"], [186, 105])
    assert len(runs) == 2
    widths = [b - a for a, b in runs]
    assert all(w <= k.BAR_W_CAP + 2 for w in widths), widths
    # the group is centred in the content band
    left_pad, right_pad = runs[0][0] - k.M, k.X_RIGHT - runs[-1][1]
    assert abs(left_pad - right_pad) < 5


def test_seven_bars_span_the_content_band():
    runs = _bar_rects(["A", "B", "C", "D", "E", "F", "G"], [56, 49, 45, 43, 42, 30, 17], unit="%")
    assert len(runs) == 7
    assert runs[0][0] == pytest.approx(k.M, abs=3)
    assert runs[-1][1] == pytest.approx(k.X_RIGHT, abs=3)


def test_bar_heights_are_proportional_to_a_true_zero_baseline():
    canvas = k.gradient_bg()
    k.draw_bars(canvas, ["a", "b"], [100, 50])
    import numpy as np

    a = np.array(canvas.convert("RGB"), dtype=int)
    ground = np.array(k.gradient_bg().convert("RGB"), dtype=int)
    diff = np.abs(a - ground).sum(axis=2) > 30
    tall = np.where(diff[:, int(k.M + (k.X_RIGHT - k.M) * 0.30)])[0]
    short = np.where(diff[:, int(k.M + (k.X_RIGHT - k.M) * 0.70)])[0]
    # exclude the value label above each bar: measure from the shared baseline up
    h_tall = 1170 - tall.min()
    h_short = 1170 - short.min()
    assert h_short / h_tall == pytest.approx(0.5, abs=0.06)


def test_too_many_bars_is_rejected():
    with pytest.raises(SystemExit):
        k.draw_bars(k.gradient_bg(), list("abcdefgh"), [1] * 8)


def test_mismatched_bar_arrays_are_rejected():
    with pytest.raises(SystemExit):
        k.draw_bars(k.gradient_bg(), ["a", "b"], [1])


# ------------------------------------------------------------------ validation


def _spec(*slides):
    return {"meta": {"title": "t"}, "slides": list(slides)}


def test_valid_spec_has_no_errors(tmp_path):
    spec = _spec(
        {"type": "statement", "text": "x", "notes": "n"},
        {"type": "back"},
    )
    assert k.validate(spec, tmp_path) == []


def test_missing_speaker_notes_is_an_error(tmp_path):
    spec = _spec({"type": "statement", "text": "x"})
    errors = k.validate(spec, tmp_path)
    assert any("speaker notes" in e for e in errors)


def test_back_cover_needs_no_notes(tmp_path):
    assert k.validate(_spec({"type": "back"}), tmp_path) == []


def test_missing_required_key_is_an_error(tmp_path):
    errors = k.validate(_spec({"type": "hero-stat", "notes": "n"}), tmp_path)
    assert any("'value'" in e for e in errors)


def test_unknown_slide_type_is_an_error(tmp_path):
    errors = k.validate(_spec({"type": "carousel", "notes": "n"}), tmp_path)
    assert any("unknown type" in e for e in errors)


def test_third_chart_is_rejected(tmp_path):
    chart = {"type": "bars", "cats": ["a"], "vals": [1], "notes": "n"}
    errors = k.validate(_spec(chart, dict(chart), dict(chart)), tmp_path)
    assert any("at most 2" in e for e in errors)


def test_two_charts_are_allowed(tmp_path):
    chart = {"type": "bars", "cats": ["a"], "vals": [1], "notes": "n"}
    assert k.validate(_spec(chart, dict(chart)), tmp_path) == []


def test_unknown_scrim_is_an_error(tmp_path):
    errors = k.validate(
        _spec({"type": "statement", "text": "x", "notes": "n", "scrim": "diagonal"}), tmp_path
    )
    assert any("unknown scrim" in e for e in errors)


def test_missing_image_is_an_error(tmp_path):
    errors = k.validate(
        _spec({"type": "statement", "text": "x", "notes": "n", "image": "nope.png"}), tmp_path
    )
    assert any("image not found" in e for e in errors)


def test_shipped_example_yaml_is_valid():
    from pathlib import Path

    here = Path(__file__).parent
    spec = yaml.safe_load((here / "example.yaml").read_text(encoding="utf-8"))
    errors = [e for e in k.validate(spec, here) if "image not found" not in e]
    assert errors == [], errors


# ------------------------------------------------------------------ palette


def test_dark_tokens_match_the_documented_hex():
    assert k.GROUND_BOT == (0, 56, 65)  # #003841, the brand Dark Teal
    assert k.ACCENT == (0, 223, 248)  # #00DFF8
    assert k.NEGATIVE == (255, 82, 99)  # #FF5263


def test_named_colour_lookup():
    assert k._color({"color": "negative"}, "color", k.INK) == k.NEGATIVE
    assert k._color({"color": "#00DFF8"}, "color", k.INK) == k.ACCENT
    assert k._color({}, "color", k.INK) == k.INK


def test_unknown_colour_is_rejected():
    with pytest.raises(SystemExit):
        k._color({"color": "chartreuse"}, "color", k.INK)


# ------------------------------------------------------------------ determinism


def test_grain_is_deterministic_per_seed():
    a = k.grain(k.gradient_bg(), 42)
    b = k.grain(k.gradient_bg(), 42)
    c = k.grain(k.gradient_bg(), 43)
    assert a.tobytes() == b.tobytes()
    assert a.tobytes() != c.tobytes()


# ------------------------------------------- specs that used to clear --validate

# README.md sells `--validate` as the gate before a render. These four specs
# passed it and then failed the build; cases 1 and 3 came out as raw tracebacks.


def test_whitespace_only_text_is_rejected(tmp_path):
    errors = k.validate(_spec({"type": "statement", "text": "   ", "notes": "n"}), tmp_path)
    assert any("blank" in e for e in errors), errors


def test_whitespace_only_text_can_no_longer_crash_the_renderer():
    """wrap() returns no lines, and max() over no lines used to raise."""
    canvas = k.gradient_bg()
    y = k.para(canvas, k.M, 400, "   ", k.font("l", 50), k.INK, 1200, 60)
    assert y == 400


def test_mismatched_cats_and_vals_is_rejected(tmp_path):
    spec = _spec({"type": "bars", "cats": ["a", "b", "c"], "vals": [1, 2], "notes": "n"})
    errors = k.validate(spec, tmp_path)
    assert any("same length" in e for e in errors), errors


def test_all_zero_bar_values_are_rejected(tmp_path):
    spec = _spec({"type": "bars", "cats": ["a", "b"], "vals": [0, 0], "notes": "n"})
    errors = k.validate(spec, tmp_path)
    assert any("positive value" in e for e in errors), errors


def test_all_zero_bar_values_can_no_longer_divide_by_zero():
    """v / mx with mx == 0 raised ZeroDivisionError mid-render."""
    canvas = k.gradient_bg()
    k.draw_bars(canvas, ["a", "b"], [0, 0])  # must not raise


def test_non_numeric_bar_values_are_rejected(tmp_path):
    spec = _spec({"type": "bars", "cats": ["a"], "vals": ["x"], "notes": "n"})
    errors = k.validate(spec, tmp_path)
    assert any("non-numeric" in e for e in errors), errors


def test_unknown_colour_is_rejected_by_validate(tmp_path):
    spec = _spec({"type": "hero-stat", "value": "42", "color": "chartreuse", "notes": "n"})
    errors = k.validate(spec, tmp_path)
    assert any("chartreuse" in e for e in errors), errors


def test_unknown_colour_in_a_duo_stat_half_is_rejected(tmp_path):
    spec = _spec(
        {
            "type": "duo-stat",
            "left": {"value": "1", "color": "puce"},
            "right": {"value": "2"},
            "notes": "n",
        }
    )
    errors = k.validate(spec, tmp_path)
    assert any("puce" in e and "left.color" in e for e in errors), errors


def test_is_color_rejects_six_non_hex_characters():
    assert k.is_color("#00DFF8")
    assert k.is_color("accent")
    assert not k.is_color("zzzzzz")
    assert not k.is_color("chartreuse")
    assert not k.is_color(42)


def test_blank_point_is_rejected(tmp_path):
    spec = _spec({"type": "points", "points": ["real", "  "], "notes": "n"})
    errors = k.validate(spec, tmp_path)
    assert any("point 2 is blank" in e for e in errors), errors
