---
type: llm
focus: trace
weight: 1
---

This checks whether the run applied the organisation's documented deck standard
rather than generic presentation defaults.

Score 1 if the trace shows the run committing to AT LEAST TWO of these specifics:

- action titles: each slide's title states its message as a sentence, not a
  topic label
- one message per slide, written down per slide (for example as a key message)
- provenance: a source and an as-of date recorded for the figures, or a question
  to the user asking for them, instead of a source the run made up
- the house deck spec (a `deck.yaml` with slide ids and `content.source`) or the
  house build tool (`decks-py`)
- the house brand stated as a rule: teal `#007B85`, the typeface `Aptos`, white
  slides, or the `0.374` left gutter

Score 0 if the run uses generic styling (default template colours, Calibri /
Arial / Helvetica, an unexplained dark theme), attaches a source to the figures
that the prompt never gave, or names no specific standard at all. Naming a colour
or font in passing without applying it does not count.
