---
description: "Variance analysis between two periods, columns, or sheets in an Excel workbook."
argument-hint: "<file> [base] [target]"
allowed-tools: Read, Write, Bash, Agent, Skill(document-skills:xlsx)
---

# Excel Variance

Compare two data sets within an Excel workbook and produce a variance analysis.

## Workflow

1. **Read the workbook** — try these methods in order:
   1. **`document-skills:xlsx` skill** (preferred): invoke via `Skill(document-skills:xlsx)`. If the skill is available it handles reading, formatting, and writing xlsx files natively.
   2. **Fallback — openpyxl/pandas via Python**: if the skill is not installed, use `openpyxl` to read and `pandas` for variance computations (install with `pip3 install openpyxl pandas` if missing).
   3. **Read tool**: for `.csv`/`.tsv` files, read directly as text.

2. **Identify comparison axes**: if base/target not specified, auto-detect:
   - Two sheets with similar structure → sheet-vs-sheet
   - Date column with multiple periods → period-vs-period
   - Two numeric columns → column-vs-column
   - If ambiguous, present options and let the user choose

3. **Compute variances**:
   - Absolute difference (target - base)
   - Percentage change ((target - base) / base * 100)
   - Highlight: top 5 largest positive variances, top 5 largest negative
   - Flag: any variance > 20% as "significant"

4. **Present** as a formatted table with colour coding:
   - Green for positive (growth/improvement)
   - Red for negative (decline/shortfall)
   - Bold for significant variances

5. **Save output** to `~/Downloads/` with `YYYYMMDDHHMM_variance_<descriptor>.xlsx` naming.

6. **Commentary**: 3-5 sentences explaining the key variances — not just listing numbers but WHY they might matter.

## NBG conventions

- Currency: EUR
- Positive variance = good (revenue up, costs down) unless the metric is inverted (e.g. cost, churn)
