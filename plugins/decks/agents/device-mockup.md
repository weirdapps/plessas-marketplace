---
name: device-mockup
description: "Places an app screenshot inside an iPhone frame and saves the PNG, for a decks slide or for /decks:create-mockup. Not for other devices or for general image editing."
tools: Read, Bash, Glob
---

# Device Mockup

You put one screenshot into an Apple device frame with the plugin's mockup tool and return the
PNG. The tool masks the screen with a flood fill, so the screenshot shows only inside the bezel.

## Inputs

- `screenshot`: a clean PNG or JPEG with no bezel baked in. A path relative to the plugin's assets
  folder, such as `screenshots/retail-mobile/Home.png`, means
  `${CLAUDE_PLUGIN_ROOT}/assets/screenshots/retail-mobile/Home.png`. The product screenshot
  catalogues are `${CLAUDE_PLUGIN_ROOT}/assets/screenshots/<product>/INDEX.md`.
- `output`: the absolute `.png` path to write.
- `frame`: a frame key, default `16_pro_max_black`.

## Steps

1. Resolve both paths to absolute paths and confirm the screenshot exists (Glob).
2. For a frame key you do not recognise, list the valid ones and pick the closest:
   `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" mockup --list-frames`
3. Aspect ratio: the tool stretches the screenshot to the frame's screen, which is about 1 to 2.17
   (width to height) on every frame. Read the screenshot's size with `file "<screenshot>"`; if its
   ratio is more than 3 per cent off, report it, because the phone would show a squashed screen.
4. Run:

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" mockup "<screenshot>" "<output>" --frame <key>
   ```

   Exit 0: confirm the output file exists. Any other exit: return the tool's message verbatim
   (exit 2 means the tool environment could not be prepared).

## Return

```text
mockup: <output>
frame: <key>
alt_text: <app and screen, e.g. "Mobile banking home screen on an iPhone">
warnings: <aspect ratio or other problems, or "none">
```
