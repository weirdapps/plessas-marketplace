---
type: llm
focus: last_message
weight: 1
arm: both
---

This is a fault report about the application, not a request to analyse data. The
user wants the hang and the circular-reference warning diagnosed.

Score 1 if the response treats it as troubleshooting: tracing the circular
reference, iterative-calculation or recalculation settings, add-ins, file repair
or corruption, a local-versus-shared difference, or asking for the detail needed
to narrow it down.

Score 0 if the response instead offers to summarise, pivot, chart or analyse
what is in the workbook, proposes KPIs or data-quality findings about its
contents, or asks for the file in order to run analysis on it. Offering analysis
as an unsolicited extra on top of the diagnosis also scores 0.
