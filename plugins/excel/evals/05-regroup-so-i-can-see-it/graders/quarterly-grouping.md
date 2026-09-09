---
type: llm
focus: last_message
weight: 2
arm: both
---

The data is a nine-month time series. The regrouping asked for has a default
period: quarters.

Score 1 only if the response rolls the nine months into calendar quarters (Q1 =
Jan-Mar, Q2 = Apr-Jun, Q3 = Jul-Sep) and presents the regrouped figures on that
basis, arithmetically correctly.

Score 0 if it leaves the data monthly, groups into halves, thirds, rolling
windows or any other period, offers quarters only as one option among several
without producing them, or gets the quarterly sums wrong.
