---
description: "Create a formal business letter in Word format."
argument-hint: "<recipient> <subject>"
allowed-tools: Read, Write, Bash, Agent, Skill(document-skills:docx)
---

# Formal Letter

Generate a formal business letter in Word format (.docx).

## Workflow

0. **Read the house style guide** first: `${CLAUDE_PLUGIN_ROOT}/shared/style-guide.md`. It carries the NBG defaults every document in this plugin must follow (no em-dashes, never invent NBG executive names, `#007B85` headings, post-generation XML verification, and no `_v1` / `_final` filename suffixes).

1. **Create the document**, trying these methods in order:
   1. **`document-skills:docx` skill** (preferred): invoke via `Skill(document-skills:docx)`. If the skill is available it handles document creation and styling natively.
   2. **Fallback (python-docx)**: if the skill is not installed, use `python-docx` directly, running Python through `uv`, which installs nothing permanently: `uv run --no-project --with python-docx python -c "..."`. Without `uv`, use a venv (`python3 -m venv .venv && .venv/bin/pip install python-docx`). A bare `pip3 install` fails with `externally-managed-environment` on PEP 668 systems; use `--break-system-packages` only as a last resort.

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
   - Font: Aptos 11pt body, Aptos 14pt headings
   - Colour: `#404040` body text, `#007B85` headings (NBG Teal)
   - Single-spaced body, double-space between paragraphs
   - No paragraph indentation (block style)

4. **Save** to `~/Downloads/` with `YYYYMMDDHHMM_letter_<recipient_slug>.docx`.
