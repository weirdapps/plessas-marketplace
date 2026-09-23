---
description: "Rebuild an existing deck (.pptx, .docx or .pdf) to NBG standards: a new storyline and layout from its extracted content, keeping every figure and source, then build, render and QA"
argument-hint: "<path to .pptx, .docx or .pdf> [instructions] [folder to save in]"
allowed-tools: Read, Bash, Glob, Skill(decks:create-presentation)
---

<objective>
Rebuild the user's existing deck on the NBG format with a stronger storyline, without changing
what it says.

User request: $ARGUMENTS
</objective>

<process>

1. **Find the file.** It must be an existing `.pptx`, `.docx` or `.pdf`. Pasted text with no file is
   a new deck: run `/decks:create-presentation` with it instead. A keynote built by
   `/decks:create-keynote` is rebuilt from its YAML, not redesigned.
2. **Show what is off-standard** (optional, `.pptx` only): run
   `bash "${CLAUDE_PLUGIN_ROOT}/bin/decks-py" validate "<file>" --format json` and tell the user in
   one line how many brand checks the original fails. Exit 2 means the tool environment could not be
   prepared: show its printed fix and stop.
3. **Run the pipeline** by invoking `/decks:create-presentation` through the Skill tool with these
   arguments:

   ```text
   <absolute path of the file>
   mode: redesign (restructure the storyline freely; keep the meaning, every figure, every source
   and the speaker notes; add nothing the original does not contain)
   <the user's own instructions, if any>
   <the folder to save in, if the user named one>
   ```

   `/decks:create-presentation` extracts the content, runs storyline, outline checkpoint, storyboard,
   build and the QA gate, and delivers the new deck under a new timestamped name. The original file
   is never modified.

</process>
