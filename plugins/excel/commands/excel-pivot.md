---
description: "Build a pivot table from an Excel workbook — suggest or execute groupings, aggregations, and insights."
argument-hint: "<file> [intent]"
allowed-tools: Read, Write, Bash, Skill(document-skills:xlsx)
---

# Excel Pivot

Build pivot-style analysis from an Excel workbook.

## Workflow

1. **Invoke `document-skills:xlsx`** to read the file.

2. **If no intent specified**: analyse the data structure and suggest 2-3 useful pivots based on the columns available. Present suggestions and let the user pick.

3. **If intent specified**: build the pivot:
   - Parse the intent to identify: group-by columns, value columns, aggregation (sum/avg/count)
   - Execute the pivot using openpyxl or pandas via the xlsx skill
   - Present the result as a formatted table

4. **Save output** to `~/Downloads/` with the standard `YYYYMMDDHHMM_pivot_<descriptor>.xlsx` naming.

5. **Insight commentary**: after the pivot, add 2-3 sentences of insight — what the data shows, any trends, anything surprising.

## NBG conventions

- Currency: EUR
- Sort by value descending unless the user specifies otherwise
- For time-series pivots, use quarterly grouping by default
