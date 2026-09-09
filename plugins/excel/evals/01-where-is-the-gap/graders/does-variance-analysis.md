---
type: llm
focus: last_message
weight: 2
---

The response must decompose the shortfall against plan, not merely restate it.

Score 1 only if ALL of these hold:

- It computes per-unit variance against plan (actual minus plan) for the quarter.
- It ranks or otherwise identifies which units drive most of the gap. Issuing
  (-0.55) and Merchant FX (-0.31) are the two largest absolute misses; Merchant FX
  (-52%) and Prepaid (-37%) are the largest in percentage terms. A correct answer
  must surface the largest contributors on at least one of those two bases and be
  arithmetically right about it.
- It says something about what changed, using the Q2 columns as the comparison
  point, rather than treating Q3 in isolation.

Score 0 if the response only summarises the table, only totals the columns, or
gets the direction or the arithmetic of the variance wrong.
