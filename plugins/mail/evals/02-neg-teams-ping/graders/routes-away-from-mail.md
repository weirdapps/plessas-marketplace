---
type: llm
focus: last_message
weight: 1
---

The user asked for a Microsoft Teams message, not an email.

Score 1 if the response treats this as Teams work: it says this belongs to Teams
and hands it off, or says it cannot reach Teams here, or asks which Teams
conversation to use.

Score 0 if the response drafts or sends an email, opens a mailbox, proposes an
email subject line, or otherwise converts the request into email.
