---
type: llm
focus: trace
weight: 1
---

This checks whether the run applied the organisation's documented brand standard
rather than generic presentation defaults.

Score 1 if the trace shows the run committing to AT LEAST TWO of these specifics:

- the brand colour `#007B85` (teal), or an explicit statement that teal replaces
  green as the primary brand colour
- the typeface `Aptos`
- white or off-white (`#FFFFFF` / `#F5F8F6`) slide backgrounds, stated as a rule
- action titles (a title that states the message, not a topic label)
- the left gutter value `0.374`

Score 0 if the run uses generic styling (default template colours, Calibri /
Arial / Helvetica, an unexplained dark theme) or names no specific standard at all.
Naming a colour or font in passing without applying it does not count.
