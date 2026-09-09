---
type: llm
focus: last_message
weight: 1
---

This is a mechanical file-conversion task: merge N CSVs into one workbook, one
sheet each. It is not analysis.

Score 1 if the response treats it as a file operation, that is: it moves toward
performing or scripting the merge, or asks where the folder is, or hands it to a
spreadsheet file tool.

Score 0 if the response instead offers to analyse, summarise, pivot or chart the
data, proposes KPIs or data-quality findings, or turns the merge into a reporting
exercise. Offering analysis as an unsolicited extra on top of the merge also
scores 0.
