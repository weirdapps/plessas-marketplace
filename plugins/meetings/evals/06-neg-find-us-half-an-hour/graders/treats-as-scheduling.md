---
type: llm
focus: last_message
weight: 1
arm: both
---

This is a scheduling request: find free time and create a calendar hold. It is
not preparation for a meeting and not a record of one.

Score 1 if the response treats it as scheduling: looking at availability,
proposing candidate slots, saying it cannot create or write calendar entries
here, or asking for the constraints it needs to pick a slot.

Score 0 if the response instead produces a pre-meeting briefing, attendee
dossiers or talking points, captures decisions and action items, or turns the
booking into preparation work. Offering a briefing as an unsolicited extra on
top of the scheduling also scores 0.
