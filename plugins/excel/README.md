# excel v1.0

Excel analysis commands tuned for executive use. Summarise structure and KPIs, build pivots from a description, run period-over-period variance, and hand off insights to the `decks` plugin to produce a presentation.

Uses `document-skills:xlsx` (Anthropic's xlsx skill) when available for best results. Falls back to `openpyxl`/`pandas` (auto-installed on first use) if the skill is not installed. NBG-shaped defaults (EUR currency, fiscal-year orientation, Aptos styling).

## Commands

| Command | Description |
|---------|-------------|
| `/excel-summary <file>` | Structure + key KPIs + data quality flags + anomaly check |
| `/excel-pivot <file>` | Build a pivot table from a natural-language description (groupings, aggregations, filters) |
| `/excel-variance <file>` | Variance analysis between two periods, columns, or sheets |
| `/excel-to-deck <file>` | Extract the key insights and hand off to the `decks` plugin to produce a NBG-branded PPTX |

## How it works

Each command:

1. Reads the workbook via `document-skills:xlsx` (preferred) or `openpyxl`/`pandas` fallback (auto-installed if missing)
2. Runs the requested analysis (KPI extraction, pivot, variance, insight selection)
3. Returns the result either as inline tables in the conversation, a written-out `.xlsx` file in `~/Downloads/` (with a `YYYYMMDDHHMM_*.xlsx` timestamp prefix per the global file-naming convention), or (for `/excel-to-deck`) a written deck brief plus the `decks` command to run next

Variance and pivot requests are interpreted from your natural-language description. The commands do not pause to confirm that interpretation before computing, so if the output groups or aggregates the wrong way, restate the request more explicitly and re-run.

## Setup

No setup required beyond installing the plugin:

```
/plugin install excel@plessas-marketplace
```

For best results, install Anthropic's `document-skills` plugin (`/plugin install document-skills@anthropic-agent-skills`). Without it, the commands fall back to `openpyxl`/`pandas` (auto-installed on first use).

## Tips

- **File paths**: pass either an absolute path or a relative path from your current working directory. Tilde expansion (`~/Downloads/...`) works.
- **Greek headers**: fully supported. The summary uses the workbook's own column names verbatim, no translation.
- **Formulas vs values**: the underlying skill reads computed values, not formula text. If a cell shows `#REF!` or `#NAME?`, the analysis will flag it as a data-quality issue, not a formula error.
- **Multi-sheet workbooks**: `/excel-summary` walks every sheet; it takes a file path only, with no flag to scope to a single sheet.
- **Output location**: ad-hoc artefacts (pivots, variance reports) write to `~/Downloads/`, not into the workbook itself. Source files are never modified in place.

## Common pattern

Quarterly review workflow:

```
/excel-summary ~/Downloads/q3_results.xlsx
# … review the KPI summary, identify the one or two stories worth pursuing …
/excel-variance ~/Downloads/q3_results.xlsx Q3 vs Q2 by Product Line
# … check the deltas, confirm the narrative …
/excel-to-deck ~/Downloads/q3_results.xlsx ExCo
# … then run the /create-presentation command that excel-to-deck prints …
```

## License

MIT
