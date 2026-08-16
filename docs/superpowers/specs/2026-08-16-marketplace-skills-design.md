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

### D2: Descriptions carry Greek and English trigger phrases

Users write in both. Semantic matching on an English-only description does
reach Greek input, but weakly on domain nouns (κατάστημα, παρουσίαση,
σύσκεψη). Explicit Greek phrases close that gap.

The repository stays domain-neutral in every other respect. Greek trigger
phrases are user-language, not organisation-specific content, so they do not
compromise the MIT/public posture.

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

### D6: The PII gauntlet path check is broadened

`installers/pii-gauntlet.sh:190` checks for
`/Users/plessas|/SourceCode/claude-config|claude-config/shared-memory`. The
string `~/SourceCode/teams-access/dist/cli.js` matches none of them, which is
why the regression shipped green.

The check is broadened to a general `~/SourceCode/` and `$HOME/SourceCode`
pattern, with an explicit path exclusion for `docs/superpowers/plans/` and
`CHANGELOG.md`, which are historical records rather than live configuration.

This is a genuine broadening of coverage. It is not, and must not become, a
narrowing of what the check reports.

### D7: Greek trigger phrases are authored by the owner, enforced by CI

The six files ship with English trigger phrases complete and a marked slot for
Greek phrases. The owner fills all six with real phrasings before merge.

This is not a placeholder in the spec sense: it is a gated step with a named
owner and a mechanical enforcement. The CI check in `validate-plugins.yml`
requires at least one Greek-script trigger phrase per description, so the
branch cannot go green until the slots are filled.

Rationale: the owner knows how colleagues actually phrase requests. A guess
produces trigger phrases that read like a manual and match nothing.

## Description anatomy

Fixed four-part shape, 700 to 900 characters. For contrast, the plugin estate's
current skill descriptions run 108 to 572 characters with a median near 195,
and the reference skills that trigger reliably in practice run 895 to 952.

1. The plugin's domain in one clause
2. Concrete English trigger phrases in quotes
3. Concrete Greek trigger phrases in quotes
4. An explicit negative boundary naming the sibling skills

Worked example, `plugins/mail/skills/outlook-mail/SKILL.md`:

> Outlook email workflows: inbox briefings, triage, drafting replies and
> forwards, sending mail, and email-style learning. Use when the user asks
> about their inbox, unread mail, what needs answering, or wants to write,
> reply to, or forward an email. Triggers on English phrasing like "what's in
> my inbox", "brief me on my email", "reply to that", "draft an email to",
> "clean up my inbox", and on Greek phrasing like «τι έχω στο inbox», «τα μέιλ
> μου», «απάντησε στο μέιλ», «στείλε ένα μέιλ», «ποια μέιλ θέλουν απάντηση»,
> «καθάρισε το inbox». Do NOT use for Microsoft Teams messages or chats (use
> teams-chat), for meeting preparation or debriefs (use meeting-workflows), or
> for reading spreadsheets or Word documents.

Part 4 is the piece absent from every skill in the owner's estate today, and
the reason a broadly-worded skill can capture a sibling plugin's work.

## Boundary table

The four phrasings that will collide, and how they resolve:

| Phrasing | Resolves to | Discriminator |
|---|---|---|
| «σύνοψη», «περίληψη», "summary" | varies | a file or xlsx goes to `spreadsheets`; Teams or a conversation goes to `teams-chat`; inbox or mail goes to `outlook-mail` |
| «στείλε», «απάντησε», "send", "reply" | varies | mail or Outlook goes to `outlook-mail`; Teams, chat or μήνυμα goes to `teams-chat` |
| «φτιάξε» plus an object | varies | presentation, slides or deck goes to `presentations`; document, letter or memo goes to `word-documents` |
| «σύσκεψη», "meeting" | `meeting-workflows` | unless the request is about email concerning the meeting, which goes to `outlook-mail` |

`excel-to-deck` stays in `spreadsheets` because that is where the command
lives, so "κάνε το excel παρουσίαση" is not torn between two skills.

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

**CI, mechanical.** `validate-plugins.yml` gains a skill validation step: every
`SKILL.md` has `name` and `description` frontmatter; every description is at
least 400 characters; every description contains at least one Greek-script
trigger phrase and one quoted English phrase. This is a cheap guard against
regressing to the 130-character descriptions that do not fire.

**CI, portability.** The broadened `pii-gauntlet.sh` runs on the branch and
must pass, proving the `chat-reply` fix is complete and that no other
`~/SourceCode/` path is live.

**Documentation.** `docs/skill-triggers.md` tabulates each skill, the phrasings
it claims, and its negative boundaries. This doubles as the page handed to a
colleague.

**Manual smoke test.** In a clean session: one Greek phrasing per plugin, plus
the four ambiguous phrasings from the boundary table. Ten cases, each asserting
which skill fires. Recorded in `docs/skill-triggers.md`.

## Out of scope

- The `teams-bridge` `ENOENT` failure on the maintainer's machine (D5)
- Per-command skills, now or later (D1)
- Any change to command workflow logic; commands are routed to, not rewritten
- Skills for `plessas-lab` or `plessas-trading-stack`, whose descriptions have
  the same weakness but different users and no adoption argument
- The `notifications` skill overtrigger risk in `trading-hub`, noted during the
  audit, tracked separately
