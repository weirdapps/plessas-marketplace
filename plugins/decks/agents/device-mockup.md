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
- `output`: the absolute `.png` path to write (in the deck's work folder when a deck asked for it).
- `frame`: a frame key, default `16_pro_max_black`.
- `fit`: `contain` (default), or `cover` when asked.

## Steps

1. Resolve both paths to absolute paths and confirm the screenshot exists (Glob).
2. For a frame key you do not recognise, list the valid ones and pick the closest:
   `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" mockup --list-frames`
3. Run:

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" mockup "<screenshot>" "<output>" --frame <key> --fit <fit>
   ```

   When the screenshot's shape differs from the screen's, `contain` keeps the whole screenshot and
   fills the gap with its own edge colour, and `cover` fills the screen and crops the edges. Never
   use `stretch`: it distorts the app. The tool prints a note when it had to fit.

   Exit 0: confirm the output file exists. Any other exit: return the tool's message verbatim
   (exit 2 covers a missing screenshot or frame, an unknown frame key, or a tool environment that
   could not be prepared; the message says which).

## Return

```text
mockup: <output>
frame: <key>
alt_text: <app and screen, e.g. "Mobile banking home screen on an iPhone">
warnings: <the tool's fit note or other problems, or "none">
```
