---
type: llm
focus: last_message
weight: 2
arm: both
---

The user asked for the numbers to be made ready to build as slides.

Score 1 only if ALL of these hold:

- The response contains a slide-by-slide outline, each slide carrying its own
  message rather than a topic label.
- Exact figures from the table are attached to specific slides. Vague framing
  ("show the shortfall") with no numbers scores 0.
- It names a chart type for at least one slide.

Score 0 if the response only analyses the table and stops, only offers to make
slides, or produces a generic deck skeleton with no numbers from this data in it.
