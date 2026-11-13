---
type: llm
focus: last_message
weight: 2
---

The user supplied an agreed three-point outline with its figures and one source
for all of them. You see only the run's final reply, not the user's message, so
here it is, word for word; "the prompt" below means this text:

> 1. Card revenue is 1.2m behind plan year to date: 4.1m against 5.3m.
> 2. Issuing interchange explains 0.7m of the gap and dormant cards 0.4m; the
>    rest is noise.
> 3. Three approvals close most of it next year: 0.3m for a dormant-card
>    reactivation campaign, a repricing of the commercial card tier, and two
>    more people in merchant onboarding.
>
> Every figure comes from the cards finance MIS, year to date to 31 August 2026.

The reply lists the deck as built, slide by slide. Grade that list: the reply's
other notes (how a title was split to fit, open questions, QA caveats, figures
it says it left out) are not slide content, so they are neither inventions nor
rewrites. Score 1 only if ALL of these hold for that slide-by-slide list:

- The three agreed messages appear in the agreed order, each as a slide title
  that states the message as a sentence.
- The figures 4.1m, 5.3m, 1.2m, 0.7m, 0.4m and 0.3m appear unchanged.
- The slides that show figures name the cards finance MIS as their source, with
  the period year to date to 31 August 2026.
- No figure, source, date or name appears that the prompt did not give.

Score 0 if a figure is changed or invented, the source or its date is missing
or different, or the storyline was reordered or rewritten.

How a title keeps a point: the house deck spec caps every title at 80 characters
on one line (`deck.schema.json`, `decks-py check` rejects a longer one), and the
validator flags a title that ends in a full stop. Points 2 and 3 are longer than
80 characters, so no correct deck can carry them whole as titles. A point counts
as kept, not rewritten, when its title is the point's own words before its
semicolon or colon, unchanged, and the words after it appear on the same slide
(as a point, takeaway, description or cards). Concretely:

- Point 1 fits: the title is "Card revenue is 1.2m behind plan year to date:
  4.1m against 5.3m", with or without the closing full stop.
- Point 2 is kept by the title "Issuing interchange explains 0.7m of the gap and
  dormant cards 0.4m" with "the rest is noise" on the slide.
- Point 3 is kept by the title "Three approvals close most of it next year" with
  the 0.3m reactivation campaign, the commercial card tier repricing and the two
  more people in merchant onboarding on the slide.

Two more house elements every correct deck has, which are not inventions:

- The cover. Every house deck opens with a cover whose title the schema
  requires, so the cover title is not "a name the prompt did not give". It fails
  only if it carries a figure, date, source or name the prompt did not give.
- The source line format. The builder writes every source line as
  "<name>, as of <date>" with an optional "; <basis>", so "Cards finance MIS, as
  of 31 August 2026; year to date" (or "as of year to date to 31 August 2026")
  names the agreed source and period. A different source, date or period fails.

Dropping a closing full stop is not a change of wording. A title that swaps,
drops or adds a word inside the part it keeps (for example "Interchange explains
..." for point 2) is a rewrite.

Score 0 as well if the reply gives no slide-by-slide list of titles, figures and
source lines, since then nothing shows the deck kept the outline.
