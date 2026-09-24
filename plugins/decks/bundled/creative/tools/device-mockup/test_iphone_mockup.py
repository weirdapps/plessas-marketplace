"""Tests for iphone_mockup.py."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

# Skip entire module if Pillow/numpy not available (iphone_mockup calls sys.exit at import)
pytest.importorskip("PIL")
pytest.importorskip("numpy")

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent))
import iphone_mockup  # noqa: E402


def test_frames_dict_has_expected_keys():
    expected = {
        "16_pro_max_black",
        "16_pro_max_natural",
        "16_pro_max_white",
        "16_pro_max_desert",
        "16_pro_black",
        "16_pro_natural",
    }
    assert set(iphone_mockup.FRAMES.keys()) == expected


def test_frames_have_required_fields():
    required_fields = {
        "path",
        "content_left",
        "content_top",
        "content_right",
        "content_bottom",
    }
    for key, config in iphone_mockup.FRAMES.items():
        assert required_fields.issubset(config.keys()), f"Frame {key} missing fields"


def test_get_frames_dir_returns_path():
    result = iphone_mockup.get_frames_dir()
    assert isinstance(result, Path)
    assert result.name == "device-frames"


def test_default_frame_exists_in_frames():
    assert iphone_mockup.DEFAULT_FRAME in iphone_mockup.FRAMES


def test_list_frames_exits_cleanly():
    script = Path(__file__).parent / "iphone_mockup.py"
    result = subprocess.run(
        [sys.executable, str(script), "--list-frames"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Available frames:" in result.stdout


def test_missing_screenshot_gives_error():
    script = Path(__file__).parent / "iphone_mockup.py"
    result = subprocess.run(
        [sys.executable, str(script), "/nonexistent/screenshot.png"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


# ---------------------------------------------------- content box vs the PNG


def _measured_screen_box(frame_path):
    """The bounding box of the frame's inner transparent region.

    Same flood fill the compositor uses at paste time, so the config is checked
    against the pixels the mask will actually reveal.
    """
    import numpy as np
    from PIL import Image

    img = Image.open(frame_path).convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    width, height = img.size
    mask = iphone_mockup._flood_fill_screen_mask(alpha, width // 2, height // 2)
    ys, xs = np.nonzero(mask)
    assert xs.size, f"{frame_path.name}: no transparent screen region found"
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


@pytest.mark.parametrize("frame_key", sorted(iphone_mockup.FRAMES))
def test_content_box_matches_the_measured_screen_region(frame_key):
    """A content box smaller than the screen clips the screenshot.

    Both 16 Pro frames were configured 1170x2594 at (75, 100) against a real
    screen of 1206x2622: 27px off the left of every screenshot, with transparent
    strips down the right edge and along the bottom.
    """
    frames_dir = iphone_mockup.get_frames_dir()
    config = iphone_mockup.FRAMES[frame_key]
    frame_path = frames_dir / config["path"]
    if not frame_path.exists():
        pytest.skip(f"{frame_path} not installed")

    measured = _measured_screen_box(frame_path)
    configured = (
        config["content_left"],
        config["content_top"],
        config["content_right"],
        config["content_bottom"],
    )
    assert configured == measured, (
        f"{frame_key}: config {configured} but the PNG's screen is {measured}"
    )


# ------------------------------------------------------------- screen mask


def _reference_fill(alpha, x, y, threshold=50):
    """The pixel-by-pixel 4-connected flood fill the tool used to run, kept as the oracle."""
    from collections import deque

    import numpy as np

    h, w = alpha.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    if alpha[y, x] >= threshold:
        return mask
    seen = {(x, y)}
    queue = deque([(x, y)])
    while queue:
        cx, cy = queue.popleft()
        mask[cy, cx] = 255
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and alpha[ny, nx] < threshold:
                seen.add((nx, ny))
                queue.append((nx, ny))
    return mask


def _synthetic_frame_alpha():
    """Transparent corners outside an opaque bezel, a transparent screen inside it,
    an opaque island in the screen and a U-shaped bay reached only from below."""
    import numpy as np

    a = np.zeros((90, 60), dtype=np.uint8)
    a[5:85, 5:55] = 255  # the phone body
    a[10:80, 10:50] = 0  # the screen
    a[14:18, 24:36] = 255  # the island, an opaque hole in the screen
    a[30:60, 20:40] = 255  # a block with a bay cut into it from below
    a[35:60, 26:34] = 0
    a[6:8, 6:8] = 0  # a clear pocket in the bezel, connected to nothing
    return a


def test_screen_mask_matches_the_pixel_flood_fill():
    alpha = _synthetic_frame_alpha()
    for x, y in ((30, 70), (12, 12), (30, 16), (1, 1)):
        expected = _reference_fill(alpha, x, y)
        assert (iphone_mockup._flood_fill_screen_mask(alpha, x, y) == expected).all(), (x, y)


def test_screen_mask_is_fast_enough_to_run_per_mockup():
    """A pure-Python pixel fill took about 5s of CPU per mockup on a 16 Pro Max frame."""
    import time

    import numpy as np
    from PIL import Image

    config = iphone_mockup.FRAMES["16_pro_max_black"]
    img = Image.open(iphone_mockup.get_frames_dir() / config["path"]).convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    start = time.process_time()
    iphone_mockup._flood_fill_screen_mask(alpha, img.width // 2, img.height // 2)
    assert time.process_time() - start < 1.5


# ------------------------------------------------------------- compositing


def _shot(path, size, square=100):
    """A white screenshot with a red square in the middle."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", size, (255, 255, 255))
    cx, cy = size[0] // 2, size[1] // 2
    ImageDraw.Draw(img).rectangle(
        [cx - square // 2, cy - square // 2, cx + square // 2 - 1, cy + square // 2 - 1],
        fill=(255, 0, 0),
    )
    img.save(path)
    return path


def _red_box(path):
    import numpy as np
    from PIL import Image

    a = np.array(Image.open(path).convert("RGB")).astype(int)
    red = (a[:, :, 0] > 200) & (a[:, :, 1] < 80) & (a[:, :, 2] < 80)
    ys, xs = np.nonzero(red)
    return xs.max() - xs.min() + 1, ys.max() - ys.min() + 1


def test_screenshot_with_another_aspect_is_not_distorted(tmp_path):
    """A 750x1730 screenshot used to be stretched onto the 1320x2868 screen, 5.8%
    squashed, though the tool promises pixel-perfect mockups."""
    shot = _shot(tmp_path / "shot.png", (750, 1730))
    out = iphone_mockup.create_mockup(shot, tmp_path / "out.png")
    w, h = _red_box(out)
    assert abs(w / h - 1) < 0.02, (w, h)


def test_screenshot_with_the_screen_aspect_fills_it_exactly(tmp_path):
    shot = _shot(tmp_path / "shot.png", (1320, 2868))
    out = iphone_mockup.create_mockup(shot, tmp_path / "out.png")
    assert _red_box(out) == (100, 100)


def test_stretch_is_available_on_request(tmp_path):
    shot = _shot(tmp_path / "shot.png", (750, 1730))
    out = iphone_mockup.create_mockup(shot, tmp_path / "out.png", fit="stretch")
    w, h = _red_box(out)
    assert w / h > 1.04  # the old behaviour, now opt-in


# ------------------------------------------------------------- output path


def test_default_output_follows_the_timestamp_naming_rule(tmp_path):
    shot = _shot(tmp_path / "App Home.png", (1320, 2868))
    out = Path(iphone_mockup.create_mockup(shot))
    assert out.parent == tmp_path
    assert re.fullmatch(r"\d{12}_app_home_mockup\.png", out.name), out.name


def test_default_output_never_lands_inside_the_plugin(tmp_path, monkeypatch):
    """A bundled screenshot used to get its mockup written next to it, inside the
    installed plugin (which is replaced at the next version bump)."""
    plugin = tmp_path / "plugin"
    (plugin / "assets").mkdir(parents=True)
    work = tmp_path / "work"
    work.mkdir()
    shot = _shot(plugin / "assets" / "home.png", (1320, 2868))
    monkeypatch.setattr(iphone_mockup, "PLUGIN_ROOT", plugin, raising=False)
    monkeypatch.chdir(work)
    out = Path(iphone_mockup.create_mockup(shot))
    assert out.parent == work, out
