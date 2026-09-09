---
type: llm
focus: last_message
weight: 2
---

The request is forward-looking: prepare the user for a meeting that has not
happened yet.

Score 1 only if ALL of these hold:

- The response is preparation for an upcoming meeting, not a record of a past one.
  If it captures decisions and action items from a meeting that already happened,
  score 0.
- It looks up, or states that it is looking up, the actual calendar entry for
  tomorrow at nine rather than inventing one.
- It addresses the history with this counterparty, which is the specific thing the
  user said they could not remember.

Score 0 if it produces a post-meeting debrief, if it fabricates attendees or prior
decisions with no retrieval behind them, or if it only offers a generic
preparation checklist with nothing specific to this meeting.
