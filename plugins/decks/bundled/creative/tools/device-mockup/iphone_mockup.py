#!/usr/bin/env python3
"""
iPhone Mockup Generator - Pixel Perfect

Creates pixel-perfect iPhone mockups using Apple device frames.
Uses flood-fill masking to ensure content only appears within the screen area.

Part of the NBG Presentations plugin for communications-marketplace.

Usage:
    python iphone_mockup.py <screenshot.png> [output.png] [--frame FRAME_KEY]

Examples:
    python iphone_mockup.py screenshot.png
    python iphone_mockup.py screenshot.png mockup.png --frame 16_pro_max_black
"""

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import numpy as np
    from PIL import Image
except ImportError:
    print("Error: Pillow and numpy required. Install with: pip install pillow numpy")
    sys.exit(1)


# Frame configurations
# content_* defines where the screenshot content should be placed
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
    "16_pro_black": {
        "path": "16 Pro - Black Titanium.png",
        "content_left": 75,
        "content_top": 100,
        "content_right": 1244,
        "content_bottom": 2693,
    },
    "16_pro_natural": {
        "path": "16 Pro - Natural Titanium.png",
        "content_left": 75,
        "content_top": 100,
        "content_right": 1244,
        "content_bottom": 2693,
    },
}

DEFAULT_FRAME = "16_pro_max_black"


def _flood_fill_screen_mask(alpha, start_x, start_y, threshold=50):
    """
    Create a screen mask by flood-filling from a starting point.

    This finds only the INNER transparent region (screen area) and
    excludes the OUTER transparent region (corners outside the phone).
    """
    from collections import deque

    h, w = alpha.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    visited = np.zeros((h, w), dtype=bool)

    queue = deque([(start_x, start_y)])
    visited[start_y, start_x] = True

    while queue:
        x, y = queue.popleft()

        if alpha[y, x] < threshold:  # Transparent pixel (screen)
            mask[y, x] = 255

            # Check 4-connected neighbors
            for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx]:
                    visited[ny, nx] = True
                    if alpha[ny, nx] < threshold:
                        queue.append((nx, ny))

    return mask


def get_frames_dir():
    """Get the device-frames asset directory."""
    # Navigate from tools/device-mockup to assets/device-frames
    tool_dir = Path(__file__).parent
    plugin_dir = tool_dir.parent.parent
    frames_dir = plugin_dir / "assets" / "device-frames"
    return frames_dir


def create_mockup(
    screenshot_path, output_path=None, frame_key=DEFAULT_FRAME, frames_dir=None
):
    """
    Create a pixel-perfect iPhone mockup.

    Args:
        screenshot_path: Path to clean screenshot (no frame artifacts)
        output_path: Output path (optional, defaults to <name>_mockup.png)
        frame_key: Which frame to use
        frames_dir: Directory containing frame PNG files

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
        sys.exit(1)

    config = FRAMES[frame_key]
    frame_path = frames_dir / config["path"]

    if not frame_path.exists():
        print(f"Frame not found: {frame_path}")
        print("Make sure device-frames assets are installed in assets/device-frames/")
        sys.exit(1)

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

    # Resize screenshot to fit content area
    screenshot_resized = screenshot.resize(
        (content_width, content_height), Image.Resampling.LANCZOS
    )

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
        ss_path = Path(screenshot_path)
        output_path = ss_path.parent / f"{ss_path.stem}_mockup.png"

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
    python iphone_mockup.py screenshot.png
    python iphone_mockup.py screenshot.png output.png
    python iphone_mockup.py screenshot.png --frame 16_pro_black

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
        "--list-frames", action="store_true", help="List available frames"
    )
    parser.add_argument("--frames-dir", help="Override device-frames directory")

    args = parser.parse_args()

    if args.list_frames:
        print("Available frames:")
        for key, config in FRAMES.items():
            print(f"  {key}: {config['path']}")
        return

    if not args.screenshot:
        parser.error("the following arguments are required: screenshot")

    create_mockup(args.screenshot, args.output, args.frame, args.frames_dir)


if __name__ == "__main__":
    main()
