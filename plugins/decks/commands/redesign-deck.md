---
description: "Rebuild an existing deck (.pptx or .pdf) to NBG standards: a new storyline and layout from its extracted content, keeping every figure and source, then build, render and QA"
argument-hint: "<path to .pptx or .pdf> [instructions] [folder to save in]"
allowed-tools: Read, Bash, Glob, Skill(decks:create-presentation)
---

<objective>
Rebuild the user's existing deck on the NBG format with a stronger storyline, without changing
what it says.

User request: $ARGUMENTS
</objective>

<process>

1. **Find the file.** It must be an existing `.pptx` or `.pdf`. A Word file cannot be extracted:
   ask the user to save it as PDF. Pasted text with no file is a new deck: run
   `/decks:create-presentation` with it instead. A keynote built by `/decks:create-keynote` is
   rebuilt from its YAML, not redesigned.
2. **Show what is off-standard** (optional, `.pptx` only): run
   `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" validate "<file>" --format json` and tell the user in
   one line how many brand checks the original fails (`summary.failed`). Exit 2 means it could not
   run: show the message and fix it printed and stop.
3. **Run the pipeline** by invoking `/decks:create-presentation` through the Skill tool with these
   arguments:

   ```text
   <absolute path of the file>
   mode: redesign (restructure the storyline freely; keep the meaning, every figure, every source
   and the speaker notes; add nothing the original does not contain)
   <the user's own instructions, if any>
   <the folder to save in, if the user named one>
   ```

   `/decks:create-presentation` extracts the content, asks for the image files of any pictures the
   new deck must keep (extraction does not carry pictures over), runs the storyline, the outline
   checkpoint, the storyboard, the build and the QA gate, and delivers the new deck under a new
   timestamped name. The original file is never modified.

</process>
