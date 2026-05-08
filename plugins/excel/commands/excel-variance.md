---
name: excel-variance
description: Variance analysis between two periods, columns, or sheets in an Excel workbook.
args:
  - name: file
    description: "Path to the .xlsx file."
    required: true
  - name: base
    description: "Base period/column/sheet name for comparison."
    required: false
  - name: target
    description: "Target period/column/sheet name for comparison."
    required: false
---

# Excel Variance

Compare two data sets within an Excel workbook and produce a variance analysis.

## Workflow

1. **Invoke `document-skills:xlsx`** to read the file.

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
