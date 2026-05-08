---
name: docs-create
description: Create a structured Word document from content or a brief.
args:
  - name: topic
    description: "Topic or title for the document."
    required: true
  - name: type
    description: "Document type: report, proposal, brief, notes. Default: report."
    required: false
---

# Create Word Document

Generate a structured Word document (.docx) from content provided by the user.

## Workflow

1. **Invoke `document-skills:docx`** to set up document creation.

2. **Structure the document** based on type:
   - **Report**: title page, table of contents, executive summary, sections with headings, conclusions
   - **Proposal**: title, problem statement, proposed solution, timeline, budget, next steps
   - **Brief**: title, background, key points (bulleted), recommendation
   - **Notes**: title, date, attendees (if applicable), numbered points, action items

3. **Apply NBG formatting**:
   - Font: Aptos 11pt body, Aptos 14pt headings
   - Colour: `#404040` body text, `#003841` headings
   - Margins: 2.54cm all sides (Word default)
   - Page numbers: bottom centre
   - Language: match user's input language (Greek or English)

4. **Save** to `~/Downloads/` with `YYYYMMDDHHMM_<topic_slug>.docx` naming.

5. Present the file path and a brief summary of what was created.
