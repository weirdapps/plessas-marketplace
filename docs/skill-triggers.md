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
- `meeting-workflows` yields to `outlook-mail` when the object is an email that
  merely concerns a meeting, because the work is mail work.

## When a skill is unsure

Every skill ends with a no-match rule: if a request sits inside its domain but
no command clearly serves it, the skill says what it can do and asks. It does
not pick the nearest command.

This matters most in `chat`, where `/chat-reply` sends the message. That
command is reached only when the request unambiguously asks to answer someone
and the target conversation is unambiguous. Otherwise the skill shows you your
messages and asks.
