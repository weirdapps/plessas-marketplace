"""Basic tests for iphone_mockup.py."""

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
