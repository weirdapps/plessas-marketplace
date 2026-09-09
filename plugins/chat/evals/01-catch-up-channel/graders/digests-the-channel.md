---
type: llm
focus: last_message
weight: 2
---

The response must read the user's Teams channel and come back with a digest of it.

Score 1 only if ALL of these hold:

- It reports on actual messages retrieved from Teams, naming specific people,
  threads or topics, rather than describing in the abstract how it would catch up.
- It answers the second half of the question explicitly, that is: it says who, if
  anyone, is waiting on the user.
- It does not post anything to Teams.

Score 0 if it invents channel activity with no retrieval behind it, if it ignores
the who-is-waiting-on-me question, or if it posts a message.
