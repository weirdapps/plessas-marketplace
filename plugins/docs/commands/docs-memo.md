---
description: "Create an internal memo in Word format."
argument-hint: "<to> <subject>"
allowed-tools: Read, Write, Bash, Agent
---

# Internal Memo

Generate an internal memo in Word format (.docx).

## Workflow

1. **Create the document** using `python-docx`:
   - Install if missing: `pip3 install python-docx`
   - Use `from docx import Document` to create the document programmatically

2. **Memo structure**:
   - Header block:
     - **TO:** [recipient(s)]
     - **FROM:** [user — from CLAUDE.md identity or `<< fill in >>`]
     - **DATE:** [today, Athens timezone]
     - **SUBJECT:** [subject in bold]
   - Horizontal rule
   - Body: concise paragraphs, bullet points for action items
   - Footer: "This memo is for internal use only." (optional, based on sensitivity)

3. **Apply formatting**:
   - Font: Aptos 11pt body, Aptos 12pt bold for header labels
   - Colour: `#404040` body, `#007B85` header labels (NBG Teal)
   - Keep under 2 pages unless the content warrants more

4. **Save** to `~/Downloads/` with `YYYYMMDDHHMM_memo_<subject_slug>.docx`.

## Language

Match the user's input language. If the user writes in Greek, produce the memo in Greek (header labels: ΠΡΟΣ, ΑΠΟ, ΗΜΕΡ., ΘΕΜΑ).
