---
description: "Extract key insights from an Excel workbook and prepare a deck brief for the decks plugin."
argument-hint: "<file> [audience]"
allowed-tools: Read, Write, Bash, Agent, Skill(document-skills:xlsx)
---

# Excel to Deck

Bridge from data analysis to presentation creation.

## Workflow

1. **Read the workbook**, trying these methods in order:
   1. **`document-skills:xlsx` skill** (preferred): invoke via `Skill(document-skills:xlsx)`. If the skill is available it handles reading, formatting, and writing xlsx files natively.
   2. **Fallback (openpyxl/pandas via Python)**: if the skill is not installed, use `openpyxl` to read and `pandas` for analysis, running Python through `uv`, which installs nothing permanently: `uv run --no-project --with openpyxl --with pandas python -c "..."`. Without `uv`, use a venv (`python3 -m venv .venv && .venv/bin/pip install openpyxl pandas`). A bare `pip3 install` fails with `externally-managed-environment` on PEP 668 systems; use `--break-system-packages` only as a last resort.
   3. **Read tool**: for `.csv`/`.tsv` files, read directly as text.

2. **Extract presentation-worthy insights**:
   - Top 3-5 KPIs with current values and trends
   - Key variances or changes worth highlighting
   - Any anomalies or risks
   - A recommended narrative arc (what story does this data tell?)

3. **Prepare a content brief** for the `decks` plugin:
   - Title suggestion
   - 5-8 slide outline with one key message per slide
   - Data points for each slide (exact numbers, not vague)
   - Chart recommendations per slide (bar, line, doughnut, never pie)

4. **Write the brief to a file**: save it to `~/Downloads/YYYYMMDDHHMM_deck_brief_<workbook-slug>.md`, taking the timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'`. Use these exact section headings so the brief is machine-readable: `## Title`, `## Audience`, `## Slide outline`, `## Data points`, `## Chart recommendations`.

5. **Hand the path to the user**: this command does NOT invoke the `decks` plugin, and no automatic handoff exists. Print the next command for the user to run, quoting the file path, for example:

   ```
   /create-presentation from the brief at ~/Downloads/202603211430_deck_brief_q1_revenue.md
   ```

## Audience-aware formatting

- **Board/ExCo**: strategic framing, big-picture numbers, doughnut charts, minimal detail
- **Team standup**: operational detail, tables, action items
- **External**: polished, context-heavy, no internal jargon

## NBG conventions

- Currency: EUR
- Chart colours: NBG palette (see the `decks` plugin's `shared/brand-system/`, present only when `decks` is installed)
- Font: Aptos throughout
