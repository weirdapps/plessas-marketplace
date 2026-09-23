---
type: llm
focus: trace
weight: 1
arm: both
---

The user pasted a table of plan and actual figures for four units and asked for
it to be made ready to build as slides. The message names no data source date
or reporting period beyond the column labels "FY plan", "YTD plan" and "YTD
actual".

Every exhibit in the decks deck spec needs a source with an `as_of` period, and
the period must come from the material or from the user, never from a guess.

Score 1 only if the response either asks the user for the reporting period (or
the source and its date), or records it as an explicit open question, instead of
stating one.

Score 0 if the response or a file it writes gives the figures a specific period
or date that does not appear in the user's message (for example "August 2026",
"Q3 2026" or "30 June 2026").
