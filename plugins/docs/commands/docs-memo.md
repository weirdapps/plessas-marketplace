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
   2. **Fallback (python-docx)**: if the skill is not installed, use `python-docx` directly, running the script through the plugin's launcher, on stdin: `bash "${CLAUDE_PLUGIN_ROOT}/bin/docs-py" - <<'PY'` ... `PY` (a script file path works too; never write one into the user's folder). The launcher builds a python-docx environment on first use (a minute at most) and falls back to a temp folder when its cache cannot be written. Do not install packages any other way. If it exits 2, the environment could not be prepared: give the user its message and the fix it printed, then still deliver the full text of the document in your reply, saying plainly that no `.docx` was written.

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

4. **Save** in the folder `bash "${CLAUDE_PLUGIN_ROOT}/bin/docs-py" outdir` prints (`~/Downloads`, or the current
   folder when that cannot be written; it says so), as `YYYYMMDDHHMM_memo_<subject_slug>.docx`, the timestamp from
   `TZ='Europe/Athens' date '+%Y%m%d%H%M'`. Give the user the absolute path.

## Language

Match the user's input language. If the user writes in Greek, produce the memo in Greek (header labels: ΠΡΟΣ, ΑΠΟ, ΗΜΕΡ., ΘΕΜΑ).
