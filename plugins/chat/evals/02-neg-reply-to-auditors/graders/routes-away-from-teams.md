---
type: llm
focus: last_message
weight: 1
---

The user asked for a reply on an email thread, not a Teams message.

Score 1 if the response treats this as email work: it says this belongs to email
and hands it off, or says it cannot reach the mailbox here, or asks which thread
is meant.

Score 0 if the response opens Teams, looks for a Teams chat or channel, posts to
Teams, or otherwise converts the request into a Teams message.
