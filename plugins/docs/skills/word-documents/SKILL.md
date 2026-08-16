---
name: word-documents
description: Anything to do with producing a formal written document in Word: a structured document from a brief, a business letter to an external party, or an internal memo. Use this whenever the deliverable is a written document rather than slides or an email, however the request is phrased, for example "I need this in writing", "something official for the regulator", "write it up properly", "put it on letterhead", or in Greek «γράψ' το επίσημα», «θέλω μια επιστολή», «κάν' το σημείωμα», «βγάλ' το σε Word». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for slide decks (use presentations), for email, including formal email (use outlook-mail), or for reading spreadsheets (use spreadsheets).
---

# Word documents

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| a structured document from a brief or content | `/docs:docs-create` |
| a formal letter to someone outside the organisation | `/docs:docs-letter` |
| an internal memo | `/docs:docs-memo` |

Letter versus memo is audience, not tone: a letter goes outside, a memo stays
inside. If the audience is unclear, ask.

## When nothing fits

If the request is clearly about a written document but no row above serves it,
say what this plugin can do and ask. Do not pick the nearest row.

"Formal" alone does not mean a document. A formal message sent by email is
still email and belongs to outlook-mail.
