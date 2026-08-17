# Natural-language triggering for the six plugins: design

**Date:** 2026-08-16
**Status:** approved, pending implementation plan
**Branch:** `feat/natural-language-skills`

## Problem

All six plugins are command-only. There is not a single `SKILL.md` in the
repository. A colleague who installs `mail` or `decks` gets nothing until they
learn and type `/inbox-briefing` or `/create-presentation`.

This is an adoption ceiling, not a tidiness problem. The plugins are used by
many people at the owner's organisation, most of whom write in Greek and none
of whom memorise a 35-command surface. The workflows are good; the entry point
is the bottleneck.

A secondary problem surfaced during the audit for this work: one command has
regressed into a maintainer-only state, and the guardrail that should have
caught it has a gap. Both are fixed here because the skills layer will route
natural language into that command.

## Decisions

### D1: One skill per plugin, acting as a router

Six `SKILL.md` files, one per plugin. Each skill's body is a routing table
that dispatches to the plugin's existing commands. No workflow logic is
copied; the command files (117 to 388 lines each) remain the single source of
truth.

Rejected: one skill per command (35 files). Maximum trigger precision, but 35
descriptions competing in the same context window is the exact collision
problem observed elsewhere in the owner's plugin estate, plus a large public
diff and permanent context inflation.

Rejected: one marketplace-wide router skill. Breaks the repository's stated
"each plugin is self-contained" principle. Someone installing only `excel`
would carry a skill referencing five plugins they do not have.

### D2: Descriptions describe an intent space, not a phrase list

The governing constraint, stated by the owner: we cannot predict what a user
will ask or how they will phrase it. A description built as an enumeration of
trigger phrases is wrong by construction, because whatever is enumerated, the
next colleague phrases it differently.

So each description states three things and relies on the model to generalise
from them:

1. **The domain**, as a bounded intent space. Not "runs /inbox-briefing" but
   "anything to do with the user's Outlook mailbox: reading it, deciding what
   matters in it, and composing what goes out of it."
2. **A handful of diverse exemplars**, explicitly labelled as illustrative and
   non-exhaustive, chosen to span the range of the space rather than to cover
   it. Their job is calibration, so the model can tell where the edges are.
   Three to five per language is enough; more implies a lookup table and
   invites the model to treat unlisted phrasings as out of scope.
3. **The negative boundary**, naming the sibling skill that owns adjacent
   ground.

Greek and English both appear. Semantic matching on an English-only
description does reach Greek input, but weakly on domain nouns (παρουσίαση,
σύσκεψη, φύλλο). A few Greek exemplars anchor those nouns; they are not
attempting coverage.

The repository stays domain-neutral in every other respect. Greek exemplars are
user-language, not organisation-specific content, so they do not compromise the
MIT/public posture.

### D2a: The skill body carries the routing intelligence

Following from D2: if the description gets the model into the right plugin,
the body is what gets it to the right command. The body is written as intent
mapping, not keyword matching. Each entry states what the user is trying to
achieve and which command serves it, so an unanticipated phrasing still lands
by meaning.

Each body ends with an explicit no-match rule: when a request is inside the
plugin's domain but no command clearly serves it, the skill states what the
plugin can do and asks, rather than guessing into the nearest command. This
matters most in `chat`, where `chat-reply` auto-sends (D4). Guessing is the
one failure mode an open-ended trigger surface makes more likely, so it is
handled explicitly rather than left to chance.

### D3: All 35 commands are reachable, with today's behaviour unchanged

Natural language can reach any command. No new confirmation gate is added on
top of what commands already do.

This is safe because the safety already lives in the command bodies, which is
the correct place for it. Verified: `send-mail`, `reply` and `forward` are
draft-first by default and only dispatch on an explicit `send_now`;
`triage-inbox` states "no move without explicit per-session confirmation".

The one exception is `chat-reply`, which auto-sends. See D4.

### D4: `chat-reply` keeps auto-send; only its portability is fixed

Owner decision, 2026-08-16. This **reverses** the decision recorded at
`docs/superpowers/plans/2026-05-11-share-readiness.md` line 14, which kept the
public default at "NEVER auto-send" and had the maintainer override locally.

The reversal is recorded in `CHANGELOG.md` and `plugins/chat/README.md` so the
repository does not hold two contradictory positions. Without that record, a
future session reading the May plan will revert this change. That is precisely
how the current regression occurred.

Consequence for the skills layer: ambiguity in the `chat` domain must land on
`chat-inbox` or `chat-summarize`, never on `chat-reply`. `chat-reply` is
reached only when the phrasing explicitly asks to reply. This is handled by
routing precision in the skill body, not by a new gate.

### D5: The `chat-reply` regression is fixed at the same time

Commit `c75ca37`, whose stated purpose was README badges, replaced the public
plugin's draft-and-approve default with the maintainer's personal
configuration, introducing four maintainer-only artefacts into a public file:
an absolute path under `~/SourceCode/`, the maintainer's name, a reference to
a personal `CLAUDE.md` override, and the auto-send default itself.

Root cause of the hardcoded path: the bundled `teams-bridge` MCP tools fail
with `ENOENT` on the maintainer's machine, so the maintainer's own
configuration invokes the CLI by absolute path. That workaround leaked into
the public file. The maintainer's personal `CLAUDE.md` already carries the
workaround independently, so routing the public file through the MCP costs the
maintainer nothing.

The `teams-bridge` `ENOENT` failure is a real bug and is out of scope here.

### D6: The PII gauntlet path check is broadened and split

The original single check named one specific repo path, which is why
`teams-access/dist/cli.js` shipped green.

The fix is implemented as three separate checks.

The first names the private repos explicitly and carries **no exclusion at all**.
A private checkout's on-disk location is a leak wherever it appears, including in
a historical record, so the documenting-not-leaking argument does not reach it.

The second covers generic local source-tree paths (`~/SourceCode`,
`$HOME/SourceCode`) and applies a path exclusion for all of `docs/superpowers/`,
which quotes those patterns in order to document them. That exclusion is a
carve-out for **public**-repo command examples only; the check above is what
covers the excluded directory for anything private.

The third covers absolute maintainer home paths and carries no exclusion.
`CHANGELOG.md` is excluded from none of them.

Revised 2026-08-17. The two-check version shipped with a stated justification
that the absolute-home-paths check still covered the excluded directory. It did
not: that pattern returns zero hits under `docs/superpowers/`, so the exclusion
was uncovered for a day. Splitting the private-repo names into their own
unexcluded check is what actually closes it, and it keeps `apply_exclusion`
path-scoped, which its own contract requires.

The reason for splitting rather than broadening the single check: a combined
check with a path exclusion would silently disable the home-path half inside
every excluded path. This branch's own two spec and plan documents immediately
fell into that hole when a trial combined check was run against them, confirming
that the exclusion must not cover both pattern families.

This is a genuine broadening of coverage. It is not, and must not become, a
narrowing of what the check reports.

### D7: All six skills are authored complete; no owner input is a merge gate

Superseded an earlier draft of this decision that asked the owner to supply
real Greek phrasings before merge. That ask only made sense while the
descriptions were phrase lists whose coverage had to be right. Under D2 the
exemplars are calibration samples, so authoring them is a writing task, not a
knowledge-elicitation task, and it is done here.

The owner reviews the result like any other change. Nothing in the branch
waits on owner-supplied content.

## Description anatomy

Three parts, in this order, 600 to 900 characters. For contrast, the plugin
estate's current skill descriptions run 108 to 572 characters with a median
near 195, and the reference skills that trigger reliably in practice run 895
to 952.

1. **Domain**, stated as an intent space wide enough to absorb phrasings
   nobody anticipated
2. **Exemplars**, three to five per language, prefixed with wording that marks
   them as samples rather than a list ("for example", not "triggers on")
3. **Negative boundary**, naming the sibling skill that owns adjacent ground

Worked example, `plugins/mail/skills/outlook-mail/SKILL.md`:

> Anything to do with the user's Outlook mailbox: reading it, deciding what in
> it matters, and composing what goes out of it. Covers inbox briefings and
> triage, finding and summarising messages or threads, drafting replies and
> forwards, sending new mail, and learning the user's writing style. Use this
> whenever a request concerns email, however it is phrased, for example "what
> needs my attention today", "anything urgent from the auditors", "answer
> Maria", "put together a note to the team", or in Greek «τι τρέχει στο μέιλ
> μου», «ποιος περιμένει απάντηση», «γράψε στον Κώστα», «βγάλε μου μια
> σύνοψη από τα χθεσινά». These are samples, not an exhaustive list: judge by
> meaning. Do NOT use for Microsoft Teams messages or chats (use teams-chat),
> for meeting preparation or debriefs (use meeting-workflows), or for reading
> spreadsheets or Word documents.

Two things this example is doing deliberately. The exemplars are phrased the
way a colleague actually speaks, including obliquely ("anything urgent from
the auditors" never says the word email). And the explicit "judge by meaning"
instruction tells the model not to read the samples as a whitelist, which is
the failure mode of a phrase list.

Part 3 is the piece absent from every skill in the owner's estate today, and
the reason a broadly-worded skill can capture a sibling plugin's work.

## Tie-break policy

Per D2 the skills are open-ended, so collisions are resolved by a rule, not by
a lookup of known-colliding phrases. The rule: **route on the object, not the
verb.** Verbs are shared across the whole estate; the object of the request is
what identifies the domain.

| Verb, in either language | Object that decides |
|---|---|
| summarise, σύνοψη, περίληψη | a file or spreadsheet goes to `spreadsheets`; a chat or Teams thread goes to `teams-chat`; a mailbox or thread goes to `outlook-mail`; a meeting that already happened goes to `meeting-workflows` |
| send, reply, στείλε, απάντησε | mail, Outlook, a person's address goes to `outlook-mail`; Teams, chat, μήνυμα goes to `teams-chat` |
| make, build, φτιάξε | presentation, slides, deck goes to `presentations`; document, letter, memo, Word goes to `word-documents` |
| prepare, brief, ετοίμασε | an upcoming meeting goes to `meeting-workflows`; anything else follows its own object |

Two standing exceptions where the object rule would split work that belongs
together:

`excel-to-deck` stays in `spreadsheets` because that is where the command
lives, so "κάνε το excel παρουσίαση" is not torn between two skills.

`meeting-workflows` yields to `outlook-mail` when the object is an email that
merely concerns a meeting, because the work is mail work.

When the object is genuinely absent or unclear, the no-match rule in D2a
applies: the skill asks rather than guessing.

## Files

Created:

```
plugins/mail/skills/outlook-mail/SKILL.md
plugins/chat/skills/teams-chat/SKILL.md
plugins/decks/skills/presentations/SKILL.md
plugins/excel/skills/spreadsheets/SKILL.md
plugins/docs/skills/word-documents/SKILL.md
plugins/meetings/skills/meeting-workflows/SKILL.md
docs/skill-triggers.md
```

Skills are auto-discovered from `plugins/<plugin>/skills/<skill>/SKILL.md`. No
`plugin.json` change is required: verified against all seven plugins in the
owner's estate that ship skills, none of which declares a `skills` key.

Modified:

```
plugins/chat/commands/chat-reply.md    MCP call, no name, no CLAUDE.md reference
plugins/chat/README.md                 record the auto-send default
plugins/mail/commands/send-mail.md:95  tenant-neutral placeholder
installers/pii-gauntlet.sh:190         broaden the path check
.github/workflows/validate-plugins.yml add SKILL.md frontmatter validation
CHANGELOG.md                           record D4 and the regression fix
README.md                              document natural-language triggering
```

## Verification

**CI, mechanical.** `validate-plugins.yml` gains a skill validation step:
every `SKILL.md` has `name` and `description` frontmatter; every description
is at least 400 characters, contains Greek-script text, and contains a
negative boundary clause. Deliberately three weak structural floors, not a
quality gate. They exist to stop a future edit regressing to a 130-character
description that never fires. They must not grow into rules about which
phrases a description contains, which would reintroduce the enumeration
D2 rejects.

**CI, portability.** The broadened `pii-gauntlet.sh` runs on the branch and
must pass, proving the `chat-reply` fix is complete and that no other
`~/SourceCode/` path is live.

**Documentation.** `docs/skill-triggers.md` states each skill's domain, its
negative boundaries, and the tie-break policy. It does not list accepted
phrasings, which would teach colleagues to speak in commands again and would
defeat the point. It doubles as the page handed to a colleague.

**Manual smoke test, held-out by construction.** The test only proves anything
if the phrasings are ones the descriptions never saw. Sixteen cases in a clean
session, none of them reusing an exemplar from any description:

- Six oblique requests, one per plugin, that never name the plugin's object
  directly (for example "τι πήγε στραβά χθες με τους ελεγκτές" for `mail`)
- Four verb-collision cases drawn from the tie-break policy, one per verb row
- Four requests inside a plugin's domain that no command serves, asserting the
  D2a no-match rule asks instead of guessing
- Two out-of-domain requests, asserting no skill fires at all

Each case records the phrasing, the skill that fired, and whether that was
correct. Any miss is a description defect, fixed by widening the domain
statement or sharpening a boundary, never by adding the missed phrase as an
exemplar. Adding the phrase would pass the test and leave the real gap open.

## Out of scope

- The `teams-bridge` `ENOENT` failure on the maintainer's machine (D5)
- Per-command skills, now or later (D1)
- Any change to command workflow logic; commands are routed to, not rewritten
- Skills for `plessas-lab` or `plessas-trading-stack`, whose descriptions have
  the same weakness but different users and no adoption argument
- The `notifications` skill overtrigger risk in `trading-hub`, noted during the
  audit, tracked separately
