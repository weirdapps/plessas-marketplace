---
description: "Create an iPhone device mockup from an app screenshot: the screenshot placed inside an Apple device frame, saved as a PNG"
argument-hint: "<screenshot path> [--frame FRAME_KEY] [output path]"
allowed-tools: Bash, Read, Glob
---

<objective>
Place the user's screenshot inside an iPhone frame and save the PNG.

User request: $ARGUMENTS
</objective>

<process>

1. **Validate the input.** The screenshot must exist and be a PNG or JPEG with no bezel baked in.
   Resolve it to an absolute path. A path relative to the plugin's assets folder, such as
   `screenshots/retail-mobile/Home.png`, means
   `${CLAUDE_PLUGIN_ROOT}/assets/screenshots/retail-mobile/Home.png`.
2. **Choose the frame.** Use the requested key, else `16_pro_max_black`. List the valid keys with
   `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" mockup --list-frames`.
3. **Check the aspect ratio.** Every frame's screen is about 1 to 2.17 (width to height) and the
   tool stretches the screenshot to fit. Read the size with `file "<screenshot>"`; if the ratio is
   more than 3 per cent off, warn the user before running, because the phone would show a squashed
   screen.
4. **Run.** Output: the path the user gave, else `$HOME/Downloads/<timestamp>_<slug>_mockup.png`,
   as an absolute path, with the timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'` and the slug
   from the screenshot name.

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" mockup "<screenshot>" "<output>" --frame <key>
   ```

   Exit 2 means the tool environment could not be prepared: show the printed fix and stop.
5. **Report** the output path and the frame used.

</process>
