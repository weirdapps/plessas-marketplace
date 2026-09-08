---
description: "Create an internal memo in Word format."
argument-hint: "<to> <subject>"
allowed-tools: Read, Write, Bash, Agent, Skill(document-skills:docx)
---

# Internal Memo

Generate an internal memo in Word format (.docx).

## Workflow

0. **Read the house style guide** first: `${CLAUDE_PLUGIN_ROOT}/shared/style-guide.md`. It carries the NBG defaults every document in this plugin must follow (no em-dashes, never invent NBG executive names, `#007B85` headings, post-generation XML verification, and no `_v1` / `_final` filename suffixes).

1. **Create the document**, trying these methods in order:
   1. **`document-skills:docx` skill** (preferred): invoke via `Skill(document-skills:docx)`. If the skill is available it handles document creation and styling natively.
   2. **Fallback (python-docx)**: if the skill is not installed, use `python-docx` directly, running Python through `uv`, which installs nothing permanently: `uv run --no-project --with python-docx python -c "..."`. Without `uv`, use a venv (`python3 -m venv .venv && .venv/bin/pip install python-docx`). A bare `pip3 install` fails with `externally-managed-environment` on PEP 668 systems; use `--break-system-packages` only as a last resort.

2. **Memo structure**:
   - Header block:
     - **TO:** [recipient(s)]
     - **FROM:** [user, from CLAUDE.md identity or `<< fill in >>`]
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
