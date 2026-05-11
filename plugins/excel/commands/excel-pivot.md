---
description: "Build a pivot table from an Excel workbook — suggest or execute groupings, aggregations, and insights."
argument-hint: "<file> [intent]"
allowed-tools: Read, Write, Bash, Agent
---

# Excel Pivot

Build pivot-style analysis from an Excel workbook.

## Workflow

1. **Read the workbook** using one of these methods (try in order):
   - **openpyxl/pandas via Python** (preferred): use `openpyxl` to read and `pandas` for pivot operations — install with `pip3 install openpyxl pandas` if missing
   - **Desktop Commander MCP** (`mcp__desktop-commander__read_file`): reads `.xlsx` natively as JSON 2D arrays
   - **Read tool**: for `.csv`/`.tsv` files, read directly as text

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
