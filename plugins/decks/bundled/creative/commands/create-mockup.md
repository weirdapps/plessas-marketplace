---
description: "Create a pixel-perfect iPhone device mockup from a screenshot"
argument-hint: "<screenshot-path> [--frame FRAME_KEY]"
allowed-tools: Bash, Read, Write
---

<objective>
Create a pixel-perfect iPhone device mockup by placing a screenshot inside an Apple device frame.

User request: $ARGUMENTS
</objective>

<process>
## Workflow

1. **Validate input**: Confirm the screenshot file exists and is a PNG/JPG image
2. **Select frame**: Use the specified frame key or default to `16_pro_max_black`
3. **Run mockup tool**: Execute the iphone_mockup.py script from the plugin's tools directory:

   ```bash
   cd "${CLAUDE_PLUGIN_ROOT}/bundled/creative/tools/device-mockup"
   ./.venv/bin/python3 iphone_mockup.py "<screenshot-path>" [output.png] [--frame FRAME_KEY]
   ```

   `${CLAUDE_PLUGIN_ROOT}` is the plugin's own root; do not try to derive it from `$0`, which is not
   set in a command prompt. The venv is built by `installers/install.sh`. If `.venv/bin/python3` is
   missing, tell the user to run the installer rather than falling back to a bare `python3`, which
   will not have Pillow.

4. **Report result**: Show the output path and mockup dimensions

## Available Frames

| Frame Key | Description |
|-----------|-------------|
| `16_pro_max_black` | iPhone 16 Pro Max - Black Titanium (default) |
| `16_pro_max_natural` | iPhone 16 Pro Max - Natural Titanium |
| `16_pro_max_white` | iPhone 16 Pro Max - White Titanium |
| `16_pro_max_desert` | iPhone 16 Pro Max - Desert Titanium |
| `16_pro_black` | iPhone 16 Pro - Black Titanium |
| `16_pro_natural` | iPhone 16 Pro - Natural Titanium |

## Prerequisites

- Python 3 with Pillow and numpy: `pip install pillow numpy`
- Device frame assets in `assets/device-frames/`
</process>

<examples>
## Usage Examples

### Basic mockup (default frame)

```
/create-mockup ~/screenshots/app-home.png
```

### Specific frame

```
/create-mockup ~/screenshots/app-home.png --frame 16_pro_black
```

### Custom output path

```
/create-mockup ~/screenshots/app-home.png ~/Desktop/mockup.png --frame 16_pro_max_natural
```

### List available frames

```
/create-mockup --list-frames
```

</examples>
