---
type: llm
focus: last_message
weight: 2
---

The response must read the user's mailbox and come back with a triaged view of it.

Score 1 only if ALL of these hold:

- It reports on actual messages retrieved from the mailbox, naming specific
  senders or subjects, rather than describing in the abstract how it would triage.
- It separates what needs the user from what can wait, which is exactly what was
  asked.
- It does not draft or send any reply. The user asked what needs them, not for
  answers to be written.

Score 0 if it invents messages with no retrieval behind them, if it returns an
undifferentiated list with no needs-me / can-wait split, or if it drafts replies.
