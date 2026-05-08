# Workflow: excel

Analyse Excel workbooks — summary, pivot, variance, and deck handoff.

## Commands

| Command | What it does |
|---|---|
| `/excel-summary <path>` | Structure overview, KPIs, anomalies |
| `/excel-pivot <path> [intent]` | Build pivot analysis (auto-suggest if no intent) |
| `/excel-variance <path> [base] [target]` | Compare two periods/columns/sheets |
| `/excel-to-deck <path> [audience]` | Extract insights and hand off to `/create-presentation` |

## Example session

```
You: /excel-summary ~/Downloads/q4_revenue.xlsx
Claude: [reads workbook via document-skills:xlsx]
Claude: 3 sheets, 450 rows. Key KPIs: Revenue €12.3M (+8%), Volume 45K...
```

## Tips

- Currency defaults to EUR unless specified otherwise
- `/excel-to-deck` bridges directly into the `decks` plugin
- Output files saved to `~/Downloads/` with timestamped names
