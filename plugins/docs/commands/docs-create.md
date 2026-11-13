---
description: "Create a structured Word document from content or a brief."
argument-hint: "<topic> [type:report|proposal|brief|notes]"
allowed-tools: Read, Write, Bash, Agent, Skill(document-skills:docx)
---

# Create Word Document

Generate a structured Word document (.docx) from content provided by the user.

## Workflow

0. **Read the house style guide** first: `${CLAUDE_PLUGIN_ROOT}/shared/style-guide.md`. It carries the NBG defaults every document in this plugin must follow (no em-dashes, never invent NBG executive names, `#007B85` headings, post-generation XML verification, and no `_v1` / `_final` filename suffixes).

1. **Create the document**, trying these methods in order:
   1. **`document-skills:docx` skill** (preferred): invoke via `Skill(document-skills:docx)`. If the skill is available it handles document creation, styling, and formatting natively.
   2. **Fallback (python-docx)**: if the skill is not installed, use `python-docx` directly, running the script through the plugin's launcher, on stdin: `bash "${CLAUDE_PLUGIN_ROOT}/bin/docs-py" - <<'PY'` ... `PY` (a script file path works too; never write one into the user's folder). The launcher builds a python-docx environment on first use (a minute at most) and falls back to a temp folder when its cache cannot be written. Do not install packages any other way. If it exits 2, the environment could not be prepared: give the user its message and the fix it printed, then still deliver the full text of the document in your reply, saying plainly that no `.docx` was written. Use `from docx import Document` and apply styles via the python-docx API.

2. **Structure the document** based on type:
   - **Report**: title page, table of contents, executive summary, sections with headings, conclusions
   - **Proposal**: title, problem statement, proposed solution, timeline, budget, next steps
   - **Brief**: title, background, key points (bulleted), recommendation
   - **Notes**: title, date, attendees (if applicable), numbered points, action items

3. **Apply NBG formatting**:
   - Font: Aptos 11pt body, Aptos 14pt headings
   - Colour: `#404040` body text, `#007B85` headings (NBG Teal)
   - Margins: 2.54cm all sides (Word default)
   - Page numbers: bottom centre
   - Language: match user's input language (Greek or English)

4. **Save** in the folder `bash "${CLAUDE_PLUGIN_ROOT}/bin/docs-py" outdir` prints (`~/Downloads`, or the current
   folder when that cannot be written; it says so), as `YYYYMMDDHHMM_<topic_slug>.docx`, the timestamp from
   `TZ='Europe/Athens' date '+%Y%m%d%H%M'`. Give the user the absolute path.

5. Present the file path and a brief summary of what was created.
