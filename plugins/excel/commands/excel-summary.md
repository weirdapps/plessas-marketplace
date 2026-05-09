---
description: "Analyse and summarise an Excel workbook — structure, KPIs, anomalies, data quality."
argument-hint: "<file>"
allowed-tools: Read, Bash, Skill(document-skills:xlsx)
---

# Excel Summary

Read an Excel workbook and produce a structured summary suitable for a busy executive.

## Workflow

1. **Invoke `document-skills:xlsx`** to read the file. Use the Skill tool to load the xlsx skill, then read the workbook.

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
