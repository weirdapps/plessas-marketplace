# excel v1.0

Excel analysis commands tuned for executive use. Summarise structure and KPIs, build pivots from a description, run period-over-period variance, and hand off insights to the `decks` plugin to produce a presentation.

Self-contained — reads Excel files via `openpyxl` and analyses with `pandas` (auto-installed on first use if missing). NBG-shaped defaults (EUR currency, fiscal-year orientation, Aptos styling). No external CLIs or plugins to install.

## Commands

| Command | Description |
|---------|-------------|
| `/excel-summary <file>` | Structure + key KPIs + data quality flags + anomaly check |
| `/excel-pivot <file>` | Build a pivot table from a natural-language description (groupings, aggregations, filters) |
| `/excel-variance <file>` | Variance analysis between two periods, columns, or sheets |
| `/excel-to-deck <file>` | Extract the key insights and hand off to the `decks` plugin to produce a NBG-branded PPTX |

## How it works

Each command:

1. Reads the workbook via `openpyxl` (sheets, headers, types, formulas) — if `openpyxl` is not installed, the command auto-installs it via `pip3 install openpyxl pandas`
2. Runs the requested analysis (KPI extraction, pivot, variance, insight selection)
3. Returns the result either as inline tables in the conversation, a written-out `.xlsx` file in `~/Downloads/` (with a `YYYYMMDDHHMM_*.xlsx` timestamp prefix per the global file-naming convention), or — for `/excel-to-deck` — a structured handoff to the `decks` plugin

For variance and pivot operations, the command first surfaces its assumptions ("I'll group by Region, sum Revenue, compare Q4 vs Q3") and asks you to confirm before producing the output. This avoids burning cycles on a wrong interpretation of an ambiguous request.

## Setup

No setup required beyond installing the plugin:

```
/plugin install excel@plessas-marketplace
```

Python packages `openpyxl` and `pandas` are auto-installed on first use if missing.

## Tips

- **File paths**: pass either an absolute path or a relative path from your current working directory. Tilde expansion (`~/Downloads/...`) works.
- **Greek headers**: fully supported. The summary uses the workbook's own column names verbatim, no translation.
- **Formulas vs values**: the underlying skill reads computed values, not formula text. If a cell shows `#REF!` or `#NAME?`, the analysis will flag it as a data-quality issue, not a formula error.
- **Multi-sheet workbooks**: `/excel-summary` walks every sheet by default. Pass `--sheet "<name>"` to scope to one.
- **Output location**: ad-hoc artefacts (pivots, variance reports) write to `~/Downloads/` — not into the workbook itself. Source files are never modified in place.

## Common pattern

Quarterly review workflow:

```
/excel-summary ~/Downloads/q3_results.xlsx
# … review the KPI summary, identify the one or two stories worth pursuing …
/excel-variance ~/Downloads/q3_results.xlsx Q3 vs Q2 by Product Line
# … check the deltas, confirm the narrative …
/excel-to-deck ~/Downloads/q3_results.xlsx --audience ExCo
# … hand off to /create-presentation in the decks plugin …
```

## License

MIT
