---
type: llm
focus: trace
weight: 1
---

This checks whether the run applied the organisation's documented document
standard rather than generic word-processor defaults.

Score 1 if the trace shows the run committing to AT LEAST TWO of these specifics:

- the typeface `Aptos`
- body text colour `#404040`
- heading colour `#007B85`
- an explicit statement that em-dashes are not used

Score 0 if the styling is generic (Calibri, Times New Roman, Cambria, unspecified
defaults) or if no standard is named at all.
