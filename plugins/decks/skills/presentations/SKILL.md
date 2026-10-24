---
name: presentations
description: "Anything to do with building, improving or reviewing slide decks: producing a deck from a brief or from raw content (as PowerPoint, as an HTML deck the reader edits in the browser and saves as PDF, or as a keynote), redesigning an existing one, tightening slides that already work, preparing a full-bleed keynote for a stage talk, and reviewing a deck before it ships. Use this whenever the deliverable is slides, however the request is phrased, for example \"I need something for the board on Thursday\", \"make this presentable\", \"this deck is a mess\", \"I am speaking at the conference\", or in Greek «θέλω κάτι για το ΔΣ», «φτιάξε μου διαφάνειες», «κάν' το πιο παρουσιάσιμο», «ετοιμάζω μια ομιλία». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for Word documents, letters or memos (use word-documents), for email (use outlook-mail), or for analysing a spreadsheet, including turning one into slides (use spreadsheets)."
---

# Presentations

Route by what the user is trying to achieve, not by the words they used, with one exception: the
format of a new deck follows the word the user chose, and you never switch it on your own.

| The user asks for | Format | Run |
|---|---|---|
| a presentation, deck or slides, nothing more («φτιάξε μια παρουσίαση») | PowerPoint | `/decks:create-presentation` |
| an **HTML** presentation («φτιάξε μια HTML παρουσίαση»), or a deck to edit in the browser and send as PDF | HTML | `/decks:create-html-deck` |
| a **keynote** («keynote παρουσίαση»), or a dark full-bleed deck for a stage talk | Keynote (PowerPoint) | `/decks:create-keynote` |
| an **HTML keynote** («HTML keynote»): the keynote format, editable in the browser | Keynote (HTML) | `/decks:create-html-deck --keynote` |

| The user wants to | Run |
|---|---|
| a new deck from a brief or from content | the format row above |
| an existing deck rebuilt to standard | `/decks:redesign-deck` |
| existing slides tightened, not rebuilt | `/decks:polish-slides` |
| a deck checked before it ships, with nothing changed | `/decks:review-deck` |
| the plugin to learn from their edits to a deck it built | `/decks:presentation-review` |
| one icon, infographic or phone mockup rather than a deck | `/decks:create-icon`, `/decks:create-infographic`, `/decks:create-mockup` |

The line between redesign and polish is scope: redesign changes structure and
layout, polish leaves both alone. If the user's intent sits between the two,
ask which they mean rather than choosing.

The line between review and polish is who changes the deck: review-deck only
reports a verdict and the fixes, polish applies them. "Check it" is review;
"check it and fix it" is polish.

An existing HTML deck (a `.html` this plugin built, edited by its reader or not) is changed,
re-checked and exported with `/decks:create-html-deck`, giving it the file's path: it rebuilds
the file, which keeps the reader's edits and refreshes the editor.

## When nothing fits

If the request is clearly about slides but no row above serves it, say what
this plugin can do and ask. Do not pick the nearest row.

A request that starts from a spreadsheet belongs to the spreadsheets skill,
which owns `/excel:excel-to-deck`, even though the output is a deck.
