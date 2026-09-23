---
type: llm
focus: trace
weight: 2
---

The user supplied an agreed three-point outline with its figures and one source
for all of them.

Score 1 only if ALL of these hold for the slide specification the run wrote
(a deck spec file, slide code, or an explicit slide-by-slide structure in the
trace):

- The three agreed messages appear in the agreed order, each as a slide title
  that states the message as a sentence.
- The figures 4.1m, 5.3m, 1.2m, 0.7m, 0.4m and 0.3m appear unchanged.
- The slides that show figures name the cards finance MIS as their source, with
  the period year to date to 31 August 2026.
- No figure, source, date or name appears that the prompt did not give.

Score 0 if a figure is changed or invented, the source or its date is missing
or different, or the storyline was reordered or rewritten.
