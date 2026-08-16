# Skill triggers

Each plugin ships one skill, so you can describe what you want instead of
remembering a command. Both Greek and English work.

This page deliberately does NOT list accepted phrasings. There is no phrase to
learn. Say what you want the way you would say it to a colleague, and the
request should reach the right plugin. If it does not, that is a defect in the
skill, not in how you asked. Report it.

## What each skill owns

| Skill | Plugin | Owns | Does not own |
|---|---|---|---|
| `outlook-mail` | `mail` | The Outlook mailbox: reading it, deciding what matters, composing what goes out | Teams messages, meeting prep and debrief, spreadsheets, Word documents |
| `teams-chat` | `chat` | Teams conversations: what came in, catching up, replying | Email, meeting prep and debrief, presentations, documents |
| `presentations` | `decks` | Slide decks: creating, redesigning, polishing, reviewing | Word documents, email, decks that start from a spreadsheet |
| `spreadsheets` | `excel` | Spreadsheet data: summarising, pivoting, variance, and carrying it into slides | Word documents, email, decks not sourced from data |
| `word-documents` | `docs` | Formal written documents: structured documents, letters, memos | Slides, email including formal email, spreadsheets |
| `meeting-workflows` | `meetings` | Either side of a meeting: preparation and debrief | Sending the follow-up email, Teams chats, the deck shown in the meeting |

## How overlaps are resolved

Route on the object of the request, not the verb. Verbs are shared across the
whole marketplace; the object is what identifies the domain.

| Verb, in either language | The object decides |
|---|---|
| summarise, σύνοψη, περίληψη | a file or spreadsheet goes to `spreadsheets`; a chat or Teams thread to `teams-chat`; a mailbox or mail thread to `outlook-mail`; a meeting that already happened to `meeting-workflows` |
| send, reply, στείλε, απάντησε | mail, Outlook or a person's address goes to `outlook-mail`; Teams, chat or μήνυμα to `teams-chat` |
| make, build, φτιάξε | presentation, slides or deck goes to `presentations`; document, letter, memo or Word to `word-documents` |
| prepare, brief, ετοίμασε | an upcoming meeting goes to `meeting-workflows`; anything else follows its own object |

Two standing exceptions, where the object rule would split work that belongs
together:

- `excel-to-deck` stays with `spreadsheets`, because the work starts from data.
- `meeting-workflows` yields to `outlook-mail` when the object is sending the
  follow-up email itself, because the work is mail work.

## When a skill is unsure

Every skill ends with a no-match rule: if a request sits inside its domain but
no command clearly serves it, the skill says what it can do and asks. It does
not pick the nearest command.

This matters most in `chat`, where `/chat-reply` sends the message. That
command is reached only when the request unambiguously asks to answer someone
and the target conversation is unambiguous. Otherwise the skill shows you your
messages and asks.

## Trigger test, 2026-08-16

Sixteen held-out cases, none reusing a phrase from any description. Recorded
so a future change can be re-tested against the same bar.

Cases 1-10 and 15-16 use Shape A: six descriptions are presented and the probe
must name the right skill or NONE. Cases 11-14 use Shape B: one skill's full
SKILL.md is presented and the probe must output ASK rather than running the
nearest command. Case 17 is a Shape B positive control: both preconditions for
`chat-reply` are satisfied, so the skill must fire it rather than ask.

The harness lives at `scripts/skill-trigger-probe.sh`. It requires only the
`claude` CLI on PATH; no personal config is sourced. Re-run it after any
description change to confirm the baseline still holds.

Limitation: the harness isolates the six descriptions from competing marketplace
skills and from conversation context. This makes it a clean measurement of the
descriptions and an optimistic one for a busy real session. Run a real-session
spot check of three or four cases after any description change.

| # | Phrasing | Expected | Actual | Pass |
|---|---|---|---|---|
| 1 | «ο Παπαδόπουλος μου είχε στείλει κάτι την Τρίτη και δεν το βρίσκω πουθενά» | outlook-mail | outlook-mail | yes |
| 2 | "the migration thread exploded overnight, where did it land" | teams-chat | teams-chat | yes |
| 3 | "the steering committee gave me a forty minute slot and I have nothing to put on screen" | presentations | presentations | yes |
| 4 | «τα νούμερα του Ιουνίου δεν βγαίνουν με τον προϋπολογισμό, δες τα» | spreadsheets | spreadsheets | yes |
| 5 | "the committee needs this circulated internally as a formal record" | word-documents | word-documents | yes |
| 6 | «σε μισή ώρα μπαίνω με τη Nova και δεν θυμάμαι πού είχαμε μείνει» | meeting-workflows | meeting-workflows | yes |
| 7 | «κάνε μου μια σύνοψη από το κανάλι» | teams-chat | teams-chat | yes |
| 8 | «στείλε του ότι το είδα» (context: Teams thread) | teams-chat | teams-chat | yes |
| 9 | «φτιάξε μου κάτι επίσημο για τον πελάτη» | word-documents | word-documents | yes |
| 10 | «ετοίμασέ με για τη Δευτέρα» | meeting-workflows | meeting-workflows | yes |
| 11 | «διάγραψε όλα τα μέιλ από τον Ιούνιο» (Shape B: outlook-mail) | ASK | ASK | yes |
| 12 | «στείλε το ίδιο μήνυμα σε δέκα άτομα» (Shape B: teams-chat) | ASK | ASK | yes |
| 13 | "convert this deck to PDF" (Shape B: presentations) | ASK | ASK | yes |
| 14 | «κλείσε μου ραντεβού με τον Νίκο» (Shape B: meeting-workflows) | ASK | ASK | yes |
| 15 | "what is the weather in Athens" | NONE | NONE | yes |
| 16 | «τι λέει το χαρτοφυλάκιό μου σήμερα;» | NONE | NONE | yes |
| 17 | «απάντησε στον Νίκο στη συνομιλία μας για το migration ότι το είδα» (Shape B: teams-chat, positive control) | chat-reply | chat-reply | yes |
