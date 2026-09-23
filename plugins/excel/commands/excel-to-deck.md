---
description: "Turn an Excel workbook's key numbers into a deck spec (deck.yaml) and hand it to the decks plugin, which confirms the outline and builds the slides."
argument-hint: "<file> [audience]"
allowed-tools: Read, Write, Bash, Agent, Skill(document-skills:xlsx), Skill(decks:create-presentation)
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

3. **Find the provenance.** Every slide that shows numbers needs a source: the workbook's file name and sheet, and the period the figures describe (`as_of`, e.g. `YTD August 2026`). Take the period from the workbook itself (sheet names, headers, a date cell). If the workbook does not state it, ask the user; never guess one.

4. **Write the deck spec** to `$HOME/Downloads/YYYYMMDDHHMM_deck_spec_<workbook-slug>.yaml` (as an absolute path), taking the timestamp from `TZ='Europe/Athens' date '+%Y%m%d%H%M'`. It is the decks plugin's input format (`deck.schema.json` in that plugin), in this shape:

   ```yaml
   presentation:
     title: "<deck title>"
     audience: "<audience>"
     purpose: "<why this deck exists>"
     main_recommendation: "<the one-sentence answer>"
     language: en            # el for a Greek deck
   slides:
     - {id: S01, type: cover, key_message: "<...>", content: {title: "<60 chars max>"}}
     - id: S02
       type: chart           # chart | table | kpi | content
       key_message: "<the one thing this slide says>"
       so_what: "<why the audience cares>"
       content:
         title: "<action title: a full sentence with the number, 80 chars max>"
         source: {name: "<workbook.xlsx, sheet Summary>", as_of: "<period>"}
       chart:
         type: bar           # bar | bar_horizontal | bar_stacked | area_line (trends) | doughnut (never pie)
         data:
           categories: ["Issuing", "Acquiring"]
           series: [{name: "YTD actual", values: [5.42, 4.71]}]
         unit: "EUR m"
     - {id: S09, type: back_cover}
   ```

   A `table` slide carries `table: {headers: [...], rows: [[...], ...]}` (14 rows at most), a `kpi` slide `kpis: [{value: "5.4m", label: "YTD issuing revenue"}]` (4 at most), a `content` slide `content.points` (3 to 6). Use 5-8 slides, one message each, exact numbers only. The spec carries no colours or fonts: the decks builder applies the brand.

5. **Hand off to decks.** If `/decks:create-presentation` is available (the `decks` plugin is installed), invoke it through the Skill tool with the spec's absolute path and the audience. It checks the spec, confirms the outline with the user and builds the deck. If it is not available, tell the user to install the `decks` plugin and print the command to run once it is, quoting the path:

   ```
   /decks:create-presentation ~/Downloads/202603211430_deck_spec_q1_revenue.yaml
   ```

## Audience-aware formatting

- **Board/ExCo**: strategic framing, big-picture numbers, doughnut charts, minimal detail
- **Team standup**: operational detail, tables, action items
- **External**: polished, context-heavy, no internal jargon

## NBG conventions

- Currency: EUR
- Language: the audience's language (`language: el` for Greek); pre-formatted KPI values in a Greek deck use the decimal comma (`5,4`)
