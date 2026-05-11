---
description: "Create a formal business letter in Word format."
argument-hint: "<recipient> <subject>"
allowed-tools: Read, Write, Bash, Agent
---

# Formal Letter

Generate a formal business letter in Word format (.docx).

## Workflow

1. **Create the document** using `python-docx`:
   - Install if missing: `pip3 install python-docx`
   - Use `from docx import Document` to create the document programmatically

2. **Letter structure**:
   - Sender block (top right): user fills in or uses signature from `~/.outlook-cli/signature.html`
   - Date (Athens timezone, formatted per language: DD/MM/YYYY for Greek, Month DD, YYYY for English)
   - Recipient block (left-aligned)
   - Subject line (bold)
   - Salutation (formal: "Αξιότιμε/η..." for Greek, "Dear..." for English)
   - Body paragraphs
   - Closing ("Με εκτίμηση," / "Sincerely,")
   - Signature block

3. **Apply formatting**:
   - Font: Aptos 11pt
   - Single-spaced body, double-space between paragraphs
   - No paragraph indentation (block style)

4. **Save** to `~/Downloads/` with `YYYYMMDDHHMM_letter_<recipient_slug>.docx`.
