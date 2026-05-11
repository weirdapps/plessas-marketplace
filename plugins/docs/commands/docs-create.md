---
description: "Create a structured Word document from content or a brief."
argument-hint: "<topic> [type:report|proposal|brief|notes]"
allowed-tools: Read, Write, Bash, Agent
---

# Create Word Document

Generate a structured Word document (.docx) from content provided by the user.

## Workflow

1. **Create the document** using `python-docx`:
   - Install if missing: `pip3 install python-docx`
   - Use `from docx import Document` to create the document programmatically
   - Apply styles, fonts, and formatting via python-docx API

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
