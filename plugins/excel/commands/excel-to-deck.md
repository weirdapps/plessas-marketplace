---
description: "Extract key insights from an Excel workbook and hand off to the decks plugin to create a presentation."
argument-hint: "<file> [audience]"
allowed-tools: Read, Write, Bash, Agent
---

# Excel to Deck

Bridge from data analysis to presentation creation.

## Workflow

1. **Read the workbook** using one of these methods (try in order):
   - **openpyxl/pandas via Python** (preferred): use `openpyxl` to read and `pandas` for analysis — install with `pip3 install openpyxl pandas` if missing
   - **Desktop Commander MCP** (`mcp__desktop-commander__read_file`): reads `.xlsx` natively as JSON 2D arrays
   - **Read tool**: for `.csv`/`.tsv` files, read directly as text

2. **Extract presentation-worthy insights**:
   - Top 3-5 KPIs with current values and trends
   - Key variances or changes worth highlighting
   - Any anomalies or risks
   - A recommended narrative arc (what story does this data tell?)

3. **Prepare a content brief** for the `decks` plugin:
   - Title suggestion
   - 5-8 slide outline with one key message per slide
   - Data points for each slide (exact numbers, not vague)
   - Chart recommendations per slide (bar, line, doughnut — never pie)

4. **Hand off** to `/create-presentation` with the prepared brief.

5. **The decks plugin** takes over from here — the user sees the full deck creation workflow.

## Audience-aware formatting

- **Board/ExCo**: strategic framing, big-picture numbers, doughnut charts, minimal detail
- **Team standup**: operational detail, tables, action items
- **External**: polished, context-heavy, no internal jargon

## NBG conventions

- Currency: EUR
- Chart colours: NBG palette (see shared/brand-system/)
- Font: Aptos throughout
