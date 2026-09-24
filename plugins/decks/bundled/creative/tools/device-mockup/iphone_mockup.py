#!/usr/bin/env python3
"""
iPhone Mockup Generator - Pixel Perfect

Creates pixel-perfect iPhone mockups using Apple device frames.
Uses flood-fill masking to ensure content only appears within the screen area,
and never distorts the screenshot unless asked to.

Part of the decks plugin (plessas-marketplace). Run it through the plugin
launcher, which provides Pillow and numpy:

Usage:
    decks-py mockup <screenshot.png> [output.png] [--frame FRAME_KEY] [--fit MODE]

Examples:
    decks-py mockup screenshot.png
    decks-py mockup screenshot.png ~/Downloads/202609231200_home_mockup.png --frame 16_pro_max_black
"""

import argparse
import re
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import numpy as np
    from PIL import Image
except ImportError:
    print(
        "Error: Pillow and numpy are required. Run this tool through the plugin launcher "
        "(decks-py mockup ...), which builds an environment that has them."
    )
    sys.exit(2)


# Frame configurations
# content_* defines where the screenshot content should be placed, and must be
# the exact bounding box of the frame PNG's inner transparent region. Anything
# smaller clips the screenshot and leaves a transparent strip inside the bezel.
# test_iphone_mockup.py re-measures every PNG by flood fill and fails on drift.
# Paths are relative to the assets/device-frames directory
FRAMES: dict[str, dict[str, Any]] = {
    "16_pro_max_black": {
        "path": "16 Pro Max - Black Titanium.png",
        "content_left": 100,
        "content_top": 100,  # Screen starts at y=100 (below DI and rounded corners)
        "content_right": 1419,
        "content_bottom": 2967,
    },
    "16_pro_max_natural": {
        "path": "16 Pro Max - Natural Titanium.png",
        "content_left": 100,
        "content_top": 100,
        "content_right": 1419,
        "content_bottom": 2967,
    },
    "16_pro_max_white": {
        "path": "16 Pro Max - White Titanium.png",
        "content_left": 100,
        "content_top": 100,
        "content_right": 1419,
        "content_bottom": 2967,
    },
    "16_pro_max_desert": {
        "path": "16 Pro Max - Desert Titanium.png",
        "content_left": 100,
        "content_top": 100,
        "content_right": 1419,
        "content_bottom": 2967,
    },
    # Both 16 Pro frames were 1170x2594 at (75, 100) against a measured screen of
    # 1206x2622: 27px of the screenshot clipped off the left, with transparent
    # strips left down the right edge and along the bottom. The two PNGs differ
    # by 2px in where their screen starts, so they carry different boxes.
    "16_pro_black": {
        "path": "16 Pro - Black Titanium.png",
        "content_left": 102,
        "content_top": 100,
        "content_right": 1307,
        "content_bottom": 2721,
    },
    "16_pro_natural": {
        "path": "16 Pro - Natural Titanium.png",
        "content_left": 100,
        "content_top": 100,
        "content_right": 1305,
        "content_bottom": 2721,
    },
}

DEFAULT_FRAME = "16_pro_max_black"

# How a screenshot whose aspect differs from the screen's is fitted to it.
#   contain  the whole screenshot, scaled without distortion; the leftover bands
#            take the colour of the screenshot's own edge (the default)
#   cover    fills the screen without distortion; the overflow is cropped, centred
#   stretch  fills the screen exactly, distorting the screenshot
FITS = ("contain", "cover", "stretch")
DEFAULT_FIT = "contain"
ASPECT_TOLERANCE = 0.01  # within 1%, the screenshot is simply scaled to the screen

# The plugin root (device-mockup -> tools -> creative -> bundled -> decks). Default
# outputs never land under it: the installed plugin is replaced at every version bump.
PLUGIN_ROOT = Path(__file__).resolve().parents[4]


def _flood_fill_screen_mask(alpha, start_x, start_y, threshold=50):
    """
    Create a screen mask by flood-filling from a starting point.

    This finds only the INNER transparent region (screen area) and
    excludes the OUTER transparent region (corners outside the phone).

    Connectivity is resolved on horizontal runs of transparent pixels rather
    than on pixels: a frame row holds a handful of runs, so the whole screen is a
    few thousand runs joined row to row, where a pixel-by-pixel breadth-first fill
    visited four million pixels in Python (about 5s of CPU per mockup). Two runs
    in neighbouring rows touch when their columns overlap, which is exactly
    4-connectivity.
    """
    clear = np.asarray(alpha) < threshold
    h, w = clear.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    if not clear[start_y, start_x]:
        return mask

    # Each run as (start, end) columns, end exclusive, listed row by row.
    edges = np.diff(np.pad(clear.astype(np.int8), ((0, 0), (1, 1))), axis=1)
    run_rows, run_starts = np.nonzero(edges == 1)
    _, run_ends = np.nonzero(edges == -1)
    runs: list[list[tuple[int, int]]] = [[] for _ in range(h)]
    for r, s, e in zip(run_rows.tolist(), run_starts.tolist(), run_ends.tolist(), strict=True):
        runs[r].append((s, e))

    seed = next(i for i, (s, e) in enumerate(runs[start_y]) if s <= start_x < e)
    seen = {(start_y, seed)}
    queue = deque([(start_y, seed)])
    while queue:
        r, i = queue.popleft()
        s, e = runs[r][i]
        mask[r, s:e] = 255
        for nr in (r - 1, r + 1):
            if 0 <= nr < h:
                for j, (ns, ne) in enumerate(runs[nr]):
                    if ns < e and s < ne and (nr, j) not in seen:
                        seen.add((nr, j))
                        queue.append((nr, j))
    return mask


def get_frames_dir():
    """Get the device-frames asset directory, resolved from this file, never the cwd."""
    # Navigate from tools/device-mockup to assets/device-frames
    tool_dir = Path(__file__).resolve().parent
    plugin_dir = tool_dir.parent.parent
    frames_dir = plugin_dir / "assets" / "device-frames"
    return frames_dir


def _edge_colour(img):
    """The median colour of the screenshot's outermost pixels."""
    a = np.asarray(img.convert("RGBA"))
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    return tuple(int(v) for v in np.median(border, axis=0))


def fit_screenshot(screenshot, width, height, fit=DEFAULT_FIT):
    """The screenshot at the screen's size. Never distorted unless `fit` is 'stretch'."""
    if fit not in FITS:
        raise ValueError(f"unknown fit {fit!r}; use one of {FITS}")
    sw, sh = screenshot.size
    mismatch = (sw / sh) / (width / height) - 1
    if fit == "stretch" or abs(mismatch) <= ASPECT_TOLERANCE:
        return screenshot.resize((width, height), Image.Resampling.LANCZOS)
    print(
        f"Note: the screenshot's aspect differs from the screen's by {abs(mismatch):.1%}; "
        f"fitted with --fit {fit} (no distortion). A screenshot from the same device fills "
        f"the screen exactly."
    )
    scale = max(width / sw, height / sh) if fit == "cover" else min(width / sw, height / sh)
    scaled = screenshot.resize(
        (max(1, round(sw * scale)), max(1, round(sh * scale))), Image.Resampling.LANCZOS
    )
    if fit == "cover":
        x, y = (scaled.width - width) // 2, (scaled.height - height) // 2
        return scaled.crop((x, y, x + width, y + height))
    canvas = Image.new("RGBA", (width, height), _edge_colour(screenshot))
    canvas.paste(scaled, ((width - scaled.width) // 2, (height - scaled.height) // 2))
    return canvas


def default_output(screenshot_path, now=None):
    """YYYYMMDDHHMM_<name>_mockup.png, the house naming rule, beside the screenshot.

    A screenshot that is one of the plugin's own assets gets its mockup in the
    current directory instead (or ~/Downloads), never inside the installed plugin.
    """
    src = Path(screenshot_path).resolve()
    stamp = (now or datetime.now()).strftime("%Y%m%d%H%M")
    slug = re.sub(r"[^a-z0-9]+", "_", src.stem.lower()).strip("_") or "screenshot"
    folder = src.parent
    if folder.is_relative_to(PLUGIN_ROOT):
        folder = Path.cwd().resolve()
        if folder.is_relative_to(PLUGIN_ROOT):
            folder = Path.home() / "Downloads"
    return folder / f"{stamp}_{slug}_mockup.png"


def create_mockup(
    screenshot_path, output_path=None, frame_key=DEFAULT_FRAME, frames_dir=None, fit=DEFAULT_FIT
):
    """
    Create a pixel-perfect iPhone mockup.

    Args:
        screenshot_path: Path to clean screenshot (no frame artifacts)
        output_path: Output path (optional, defaults to default_output())
        frame_key: Which frame to use
        frames_dir: Directory containing frame PNG files
        fit: contain (default), cover or stretch; see FITS

    Returns:
        Path to created mockup
    """
    if frames_dir is None:
        frames_dir = get_frames_dir()
    else:
        frames_dir = Path(frames_dir)

    # Get frame config
    if frame_key not in FRAMES:
        print(f"Unknown frame: {frame_key}")
        print(f"Available frames: {list(FRAMES.keys())}")
        sys.exit(2)

    config = FRAMES[frame_key]
    frame_path = frames_dir / config["path"]

    if not frame_path.exists():
        print(f"Frame not found: {frame_path}")
        print(f"The device frames ship in {get_frames_dir()}; the plugin install is incomplete.")
        sys.exit(2)

    if not Path(screenshot_path).exists():
        print(f"Screenshot not found: {screenshot_path}")
        sys.exit(2)

    # Load images
    screenshot = Image.open(screenshot_path).convert("RGBA")
    frame = Image.open(frame_path).convert("RGBA")

    # Calculate content dimensions
    content_left = config["content_left"]
    content_top = config["content_top"]
    content_right = config["content_right"]
    content_bottom = config["content_bottom"]
    content_width = content_right - content_left + 1
    content_height = content_bottom - content_top + 1

    print(f"Screenshot: {screenshot.size}")
    print(f"Frame: {frame.size}")
    print(f"Content area: {content_width}x{content_height}")

    # Fit the screenshot to the content area, preserving its aspect ratio
    screenshot_resized = fit_screenshot(screenshot, content_width, content_height, fit)

    # Create result canvas
    result = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    result.paste(screenshot_resized, (content_left, content_top))

    # Create screen mask using flood-fill from center
    # This ensures we only include the INNER transparent area (screen)
    # and exclude the OUTER transparent area (corners outside phone)
    frame_array = np.array(frame)
    alpha = frame_array[:, :, 3]
    fw, fh = frame.size

    screen_mask_array = _flood_fill_screen_mask(alpha, fw // 2, fh // 2)
    screen_mask = Image.fromarray(screen_mask_array, mode="L")

    # Apply mask to screenshot - only show where frame is transparent
    result_masked = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    result_masked.paste(result, (0, 0), screen_mask)

    # Composite: masked screenshot + frame overlay
    final = Image.alpha_composite(result_masked, frame)

    # Determine output path
    if output_path is None:
        output_path = default_output(screenshot_path)
    output_path = Path(output_path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save result
    final.save(str(output_path), "PNG")
    print(f"Mockup saved: {output_path}")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Create pixel-perfect iPhone mockups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    decks-py mockup screenshot.png
    decks-py mockup screenshot.png output.png
    decks-py mockup screenshot.png --frame 16_pro_black
    decks-py mockup screenshot.png --fit cover

Without an output path the mockup is written beside the screenshot as
YYYYMMDDHHMM_<name>_mockup.png (in the current directory when the screenshot
is one of the plugin's own assets).

Available frames:
    16_pro_max_black (default)
    16_pro_max_natural
    16_pro_max_white
    16_pro_max_desert
    16_pro_black
    16_pro_natural
        """,
    )

    parser.add_argument("screenshot", nargs="?", help="Path to screenshot image")
    parser.add_argument("output", nargs="?", help="Output path (optional)")
    parser.add_argument(
        "--frame",
        "-f",
        default=DEFAULT_FRAME,
        choices=list(FRAMES.keys()),
        help=f"iPhone frame to use (default: {DEFAULT_FRAME})",
    )
    parser.add_argument(
        "--fit",
        default=DEFAULT_FIT,
        choices=FITS,
        help="how a screenshot of another aspect fills the screen: contain (whole, no "
        "distortion; default), cover (fill and crop, no distortion) or stretch (distorts)",
    )
    parser.add_argument("--list-frames", action="store_true", help="List available frames")
    parser.add_argument("--frames-dir", help="Override device-frames directory")

    args = parser.parse_args()

    if args.list_frames:
        print("Available frames:")
        for key, config in FRAMES.items():
            print(f"  {key}: {config['path']}")
        return

    if not args.screenshot:
        parser.error("the following arguments are required: screenshot")

    create_mockup(args.screenshot, args.output, args.frame, args.frames_dir, args.fit)


if __name__ == "__main__":
    main()
