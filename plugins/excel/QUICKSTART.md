# excel — Quickstart

A 5-minute path from zero to "my Excel workbook is summarised, pivoted, varianced, and ready for ExCo."

## What it does

Reads any Excel file (`.xlsx`, `.xls`, `.xlsm`) and runs analysis tuned for executive use. Summarises structure and KPIs, builds pivot tables from a natural-language description, runs period-over-period variance with the periods auto-detected, and hands off the insights to the `decks` plugin to produce a NBG-branded presentation. NBG-shaped defaults throughout: EUR currency, fiscal-year orientation (January-December), Aptos styling on any generated output. No external CLIs to install — the plugin wraps `document-skills:xlsx`, which is built into Claude Code.

## Prerequisites

- Claude Code installed

That's it. No external CLIs, no auth, no cloud account.

## Install

Inside Claude Code:

```
/plugin install excel@plessas-marketplace
```

That's it. No further configuration files to edit.

## Authenticate

None required. Excel files are read locally on your laptop. No cloud round-trip, no credentials, no tenant config.

## Your first command

```
/excel-summary ~/Downloads/cards_q1_results.xlsx
```

Output (typical):

```
═══════════════════════════════════════════════
EXCEL SUMMARY — cards_q1_results.xlsx
═══════════════════════════════════════════════

STRUCTURE
───────────────────────────────────────────────
- 3 sheets: P&L, Branch Detail, Customer Mix
- 1,200 rows total (40 / 980 / 180)
- Date range: 2025-01-01 to 2026-03-31 (5 quarters)

TOP KPIs (Q1 2026)
───────────────────────────────────────────────
- Cards Revenue:  €42.3M  (+12% YoY,  +4% QoQ)
- ARPU (active):  €58.40  (+6%  YoY)
- Active cards:   2.4M    (+3%  YoY)
- Fee mix (credit / debit):  61% / 39%  (was 56% / 44% Q1 2025)

DATA QUALITY
───────────────────────────────────────────────
- 3 blanks in Branch column (rows 412, 487, 631 in Branch Detail)
- 1 outlier: Branch 0142 fee revenue 4.2σ above mean — verify
- All other columns: clean

RECOMMENDED NEXT STEP
───────────────────────────────────────────────
Run /excel-variance on Q1 2026 vs Q1 2025 by Product Line
to surface what's driving the +12% YoY beat.
═══════════════════════════════════════════════
```

## Top 3 commands

| Command | What it does |
|---|---|
| `/excel-summary <file>` | Structure, top KPIs, data quality flags, anomalies, suggested next step |
| `/excel-pivot <file>` | Natural-language pivot — e.g. "group by Region, sum Revenue, compare 2026 vs 2025" |
| `/excel-variance <file>` | Period-over-period variance with auto-detected base/target periods |

Bonus: `/excel-to-deck <file>` — extract the headline insights and hand off to the `decks` plugin to build an ExCo-ready PPTX.

## Common patterns

**Quarterly review** (full pipeline to ExCo deck):

```
/excel-summary ~/Downloads/cards_q1_results.xlsx
# … pick the one or two stories worth telling …
/excel-variance ~/Downloads/cards_q1_results.xlsx
# … confirm what's driving the deltas …
/excel-to-deck ~/Downloads/cards_q1_results.xlsx --audience ExCo
# … hands off to /create-presentation in the decks plugin …
```

**Quick KPI check before a meeting** (90 seconds):

```
/excel-summary ~/Downloads/branch_pnl_april.xlsx
```

**Build a pivot you'd normally PT-by-hand**:

```
/excel-pivot ~/Downloads/customer_attrition_2026.xlsx \
  "group by Branch, sum Revenue and Costs, sort by Revenue desc"
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Greek headers mangled | Open the file once in Excel and re-save as `.xlsx`. Legacy `.xls` or CSV-renamed-as-xlsx files often have encoding issues. |
| Formulas show as `#REF!` or `#NAME?` | The plugin reads computed values, not formula text. The summary will flag the cell as a data-quality issue — fix the formula in Excel and retry. |
| Pivot output looks wrong | The plugin shows its assumptions before computing ("I'll group by Region, sum Revenue…"). Confirm them. If wrong, restate the pivot more explicitly — e.g. "group by Branch (column F), not by Region (column C)". |
| Multi-sheet workbook only analysed first sheet | By default `/excel-summary` walks every sheet. If it stopped at one, pass `--sheet "<name>"` to scope to one explicitly, or re-run and ask for "all sheets". |

## Where things live

- **Generated artefacts** (pivots, variance reports): `~/Downloads/YYYYMMDDHHMM_<descriptive_name>.xlsx`
- **Source files**: never modified in place — every output is a new file in `~/Downloads/`

## Want more?

- Architecture, NBG conventions, and full command reference: see [README.md](README.md)
- For the `/excel-to-deck` handoff: install the `decks` plugin (`/plugin install decks@plessas-marketplace`)
- All commands: type `/` in Claude Code, scroll to the `excel:` group
