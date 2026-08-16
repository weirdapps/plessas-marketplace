---
name: presentations
description: Anything to do with building, improving or reviewing slide decks: producing a deck from a brief or from raw content, redesigning an existing one, tightening slides that already work, preparing a full-bleed keynote for a stage talk, and reviewing a deck before it ships. Use this whenever the deliverable is slides, however the request is phrased, for example "I need something for the board on Thursday", "make this presentable", "this deck is a mess", "I am speaking at the conference", or in Greek «θέλω κάτι για το ΔΣ», «φτιάξε μου διαφάνειες», «κάν' το πιο παρουσιάσιμο», «ετοιμάζω μια ομιλία». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for Word documents, letters or memos (use word-documents), for email (use outlook-mail), or for analysing a spreadsheet, including turning one into slides (use spreadsheets).
---

# Presentations

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| a new deck from a brief or from content | `/decks:create-presentation` |
| a dark full-bleed deck for a stage talk | `/decks:create-keynote` |
| an existing deck rebuilt to standard | `/decks:redesign-deck` |
| existing slides tightened, not rebuilt | `/decks:polish-slides` |
| a deck checked before it ships | `/decks:presentation-review` |

The line between redesign and polish is scope: redesign changes structure and
layout, polish leaves both alone. If the user's intent sits between the two,
ask which they mean rather than choosing.

## When nothing fits

If the request is clearly about slides but no row above serves it, say what
this plugin can do and ask. Do not pick the nearest row.

A request that starts from a spreadsheet belongs to the spreadsheets skill,
which owns `/excel:excel-to-deck`, even though the output is a deck.
