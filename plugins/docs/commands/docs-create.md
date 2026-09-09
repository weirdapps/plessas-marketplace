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
   2. **Fallback (python-docx)**: if the skill is not installed, use `python-docx` directly, running Python through `uv`, which installs nothing permanently: `uv run --no-project --with python-docx python -c "..."`. Without `uv`, use a venv (`python3 -m venv .venv && .venv/bin/pip install python-docx`). A bare `pip3 install` fails with `externally-managed-environment` on PEP 668 systems; use `--break-system-packages` only as a last resort. Use `from docx import Document` and apply styles via the python-docx API.

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

4. **Save** to `~/Downloads/` with `YYYYMMDDHHMM_<topic_slug>.docx` naming.

5. Present the file path and a brief summary of what was created.
