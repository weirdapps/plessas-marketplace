---
description: "Create an iPhone device mockup from an app screenshot: the screenshot placed inside an Apple device frame, saved as a PNG"
argument-hint: "<screenshot path> [--frame FRAME_KEY] [--fit contain|cover] [output path]"
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
3. **Choose the fit** for a screenshot whose shape differs from the phone's screen: `contain` (the
   default) keeps the whole screenshot and fills the gap with its own edge colour; `cover` fills the
   screen and crops the edges. Never `stretch`: it distorts the app.
4. **Run.** Output: the path the user gave, else `$HOME/Downloads/<timestamp>_<slug>_mockup.png`,
   as an absolute path, with the timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'` and the slug
   from the screenshot name.

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" mockup "<screenshot>" "<output>" --frame <key> --fit <fit>
   ```

   Exit 2 means the tool could not run (a missing screenshot or frame, an unknown frame key, or an
   environment that could not be prepared): show the message and fix it printed and stop.
5. **Report** the output path, the frame used, and the tool's note if it had to fit the screenshot.

</process>
