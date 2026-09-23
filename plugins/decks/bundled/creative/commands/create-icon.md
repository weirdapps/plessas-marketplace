---
description: "Get an NBG duotone icon for a slide: a match from the shipped icon library, or a new SVG drawn to the brand spec"
argument-hint: "<icon concept> [folder to save in]"
allowed-tools: Agent, Read, Write, Glob, Grep, Bash
---

<objective>
Give the user one on-brand icon for the concept they describe.

User request: $ARGUMENTS
</objective>

<process>

1. **Library first.** The plugin ships a duotone icon library in the house style. Grep
   `${CLAUDE_PLUGIN_ROOT}/assets/icons/INDEX.md` for the concept and one or two synonyms, confirm the
   file exists with Glob under `${CLAUDE_PLUGIN_ROOT}/assets/icons/`, and Read the PNG to check it
   fits. If it does, offer it: copy it to the output folder if the user wants a copy, and give its
   deck.yaml form (the path relative to the plugin's assets folder, such as `icons/money/Coins.png`).

2. **Otherwise draw one.** Output: `<folder>/<timestamp>_<slug>.svg`, folder the one the user named
   or `$HOME/Downloads`, as an absolute path; timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'`;
   slug from the concept.
   Dispatch `decks:icon-designer` with the concept, that output path and the background (light
   unless the user says dark). If the Agent tool is unavailable or denied, Read
   `${CLAUDE_PLUGIN_ROOT}/agents/icon-designer.md` and follow it yourself, reading any
   `CLAUDE_PLUGIN_ROOT` placeholder in it as this plugin's folder.

3. **Report** the file path and its alt text. The SVG opens in PowerPoint (Insert, Pictures), and in
   a deck spec it goes into an `image` or a card or step `icon` field.

</process>
