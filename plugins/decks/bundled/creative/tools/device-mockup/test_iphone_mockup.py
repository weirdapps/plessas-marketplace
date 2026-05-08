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
    required_fields = {"path", "content_left", "content_top", "content_right", "content_bottom"}
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
        [sys.executable, str(script), "/nonexistent/screenshot.png"], capture_output=True, text=True
    )
    assert result.returncode != 0
