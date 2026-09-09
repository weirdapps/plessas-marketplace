---
type: llm
focus: last_message
weight: 2
arm: both
---

The request names a meeting but never says whether it has happened. "Deal with
it" could mean get ready for it, or capture what came out of it. The two
produce completely different work.

Score 1 only if the response resolves that ambiguity by asking the user which
they mean, before committing to one. Asking and then offering to do either on
the answer still scores 1.

Score 0 if the response picks one and runs with it, including when it infers the
tense from a calendar lookup and proceeds on that inference without checking. It
also scores 0 if it asks only unrelated clarifying questions (which pilot, which
Lydia, what date) while still committing to preparation or to capture.
