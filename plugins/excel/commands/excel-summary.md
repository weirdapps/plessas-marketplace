---
description: "Analyse and summarise an Excel workbook — structure, KPIs, anomalies, data quality."
argument-hint: "<file>"
allowed-tools: Read, Bash, Agent
---

# Excel Summary

Read an Excel workbook and produce a structured summary suitable for a busy executive.

## Workflow

1. **Read the workbook** using one of these methods (try in order):
   - **openpyxl via Python** (preferred): `python3 -c "import openpyxl; wb = openpyxl.load_workbook('<file>', data_only=True); ..."` — install with `pip3 install openpyxl` if missing
   - **Desktop Commander MCP** (`mcp__desktop-commander__read_file`): reads `.xlsx` natively as JSON 2D arrays
   - **Read tool**: for `.csv`/`.tsv` files, read directly as text

2. **Analyse each sheet**:
   - Row/column count, headers, data types
   - Identify KPI columns (numeric columns with labels like "Revenue", "P&L", "Volume", "Growth", etc.)
   - Surface the top-level numbers (totals, averages, max/min)
   - Flag anomalies: blanks in critical columns, outlier values (>3 SD), negative values where positive expected
   - Note date ranges if date columns exist

3. **Produce a summary** with:
   - **Structure**: N sheets, M total rows, key columns per sheet
   - **KPIs**: the 3-5 most important metrics with their current values
   - **Data quality**: any blanks, inconsistencies, or formatting issues
   - **Anomalies**: anything surprising in the data
   - **Recommendation**: what analysis would be most valuable next (pivot, variance, chart)

## NBG conventions

- Currency: EUR (assume unless stated otherwise)
- Decimal separator: comma in Greek context, period in English
- Fiscal year: January-December
- Font for any generated output: Aptos 12pt
