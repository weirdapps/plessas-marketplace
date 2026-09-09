# Migrating `commands/` to `skills/`

**Status: plan only. No files have moved.** Approved to plan, not to execute.

## Why this is on the table

Anthropic's plugin reference now lists `commands/` as "Skills as flat Markdown files. **Use
`skills/` for new plugins**", and the slash-command page says a Markdown file in
`commands/` "is the older format and still works". Slash commands and skills were merged in
v2.1.3 with, in Anthropic's words, "no change in behavior". Neither is deprecated and no
removal has been announced.

You can see the merge in this repo already. `claude plugin details mail` reports **16 skills**,
not "15 commands and 1 skill":

```
Skills (16)  archive-thread, auth-setup, decisions, draft-review, folder-tree, forward,
             inbox-briefing, mail-doctor, mail-review, outlook-mail, reply, send-mail,
             style-rollback, style-stats, style-sync, triage-inbox
```

So the runtime already treats them as one thing. The question is not whether they work; it is
whether we want the capabilities the newer format has and the older one does not.

## What migration would actually buy

A command file supports the same frontmatter as a skill **except `name` and `paths`**. The
things only a skill can do, ranked by whether this repo would use them:

| Capability | Would we use it? |
|---|---|
| `disable-model-invocation` | **Yes.** The one control that stops Claude firing a side-effecting workflow on its own. Eight commands here send, move or reply. |
| Supporting files in the skill directory | **Yes.** `mail/docs/triage-engine/*.md` is a specification loaded by path today; as a skill it would be a sibling file with progressive disclosure. |
| `name` | **Yes.** A command's name is its filename. A skill can be renamed without breaking the invocation. |
| `paths` | Probably not. Nothing here is scoped to a file glob. |
| `context: fork` plus `agent:` | **Maybe.** Could replace the separate agent files in `decks`, but see the caution below. |
| `user-invocable: false` | Marginal. Nothing here is pure background knowledge. |

Against that: 35 files move, every cross-reference between them has to be re-checked, and the
repo has just been through an audit that found five separate instances of a reference pointing
at something that had moved. That is the real cost, and it is not small.

## The classification, from the actual files

35 commands. 8 side-effecting, 16 argument-less.

### Tier 1: side-effecting, and the reason to do this at all (8)

These would become skills carrying `disable-model-invocation: true`, which is exactly the case
Anthropic names ("`/commit`, `/deploy`, `/send-slack-message` ... You don't want Claude deciding
to deploy because your code looks ready").

| Command | Sends what |
|---|---|
| `mail/send-mail` | New mail |
| `mail/reply` | Reply and reply-all |
| `mail/forward` | Forward |
| `mail/archive-thread` | Moves mail between folders |
| `mail/triage-inbox` | Batch-moves up to 20 messages |
| `mail/mail-review` | Drafts and can send |
| `mail/inbox-briefing` | Read-only by contract, but declares send tools |
| `chat/chat-reply` | **Auto-sends to Teams by default** |

**This tier is where the decision actually lies, and it is a preference decision, not a
technical one.** You have already ruled once: auto-send stays, because Teams should behave like
you at the keyboard, and the `[Claude]` prefix is now enforced in the bridge rather than in
prose. Setting `disable-model-invocation` on `chat-reply` would break exactly the flow you asked
for. If that ruling holds, Tier 1's main benefit evaporates and the case for migrating at all
gets much weaker.

A middle path exists and is worth considering separately from migration: guard the **mail**
sends, which are external and hard to retract, and leave Teams alone.

### Tier 2: plain skills, mechanical conversion (12)

Take arguments, no side effects, nothing subtle. `decks/create-presentation`,
`decks/create-keynote`, `decks/redesign-deck`, `decks/polish-slides`,
`decks/presentation-review`, `mail/decisions`, `mail/draft-review`, `mail/style-sync`,
`mail/style-stats`, `mail/style-rollback`, `meetings/meeting-prep`, `meetings/meeting-debrief`.

### Tier 3: argument-less, convert last (15)

`chat/chat-inbox`, `chat/chat-summarize`, `chat/chat-channel-digest`, `chat/chat-doctor`,
`chat/auth-setup`, `mail/folder-tree`, `mail/mail-doctor`, `mail/auth-setup`, and the seven
`excel/*` and `docs/*` commands. Lowest risk, lowest benefit. Note four of these genuinely take
no arguments and should not be given an `argument-hint` to satisfy a linter;
`validate_consistency.py` already distinguishes those cases.

## What the router skills become

Each plugin ships one router skill (`outlook-mail`, `teams-chat`, `presentations`,
`spreadsheets`, `word-documents`, `meeting-workflows`) whose job is natural-language dispatch to
the commands. If every command becomes a skill, the model can already see and invoke each one
directly, so the routers stop being the only entry point and become a tie-break layer.

That is not a reason to delete them. The individual command descriptions are terse one-liners
with no negative boundaries; the routers carry the Greek, the oblique phrasings and the "Do NOT
use for X" clauses that make routing work. **Keep them.** But the migration should shorten the
routers rather than leave two overlapping descriptions of the same workflow.

Cost check: the six routers carry roughly 1,850 of the roughly 3,900 always-on tokens across all
six plugins.

## Sequence, if it goes ahead

1. **Pilot `docs` first.** Three files, no MCP, no agents, no side effects. It tells you the real
   shape and cost for about an hour of work.
2. **Measure the pilot with `claude plugin eval` before and after**, with `--ablation
   with-without`. If a migration cannot be shown not to have made routing worse, do not do the
   other five. Note the existing `skill-trigger-probe.sh` cannot serve here: its case 2 is
   nondeterministic (four runs on identical input gave three fails and one pass), so it cannot
   resolve a change this small.
3. `excel`, then `meetings`, then `chat`, then `decks`, then `mail` last. `mail` has 15 commands
   and the densest cross-references.
4. Set the frontmatter `name` explicitly on every migrated skill. Plugin skills should not rely
   on the directory name.
5. Never ship the same capability as both `commands/x.md` and `skills/x/SKILL.md` in one plugin.

## Two cautions found the hard way

- **The `agents` key in `plugin.json` loads nothing.** A valid file list passes `claude plugin
  validate --strict` and registers zero agents. If any part of this migration involves `context:
  fork` with `agent:`, verify the agent actually loads with `claude --plugin-dir ./plugins/<p>
  plugin details <p>` rather than trusting the validator.
- **`commands` REPLACES the default scan; `skills` ADDS to it.** So the two behave differently
  during a partial migration, and a manifest that declares one and not the other will not do
  what it looks like it does.

## Recommendation

**Do the `docs` pilot. Decide the rest on its ablation delta.**

The honest position is that the strongest argument for migrating is
`disable-model-invocation`, and you have already ruled that the flow it would guard is a flow
you want. Everything else is tidiness against a real risk of breaking cross-references in a repo
that just spent a night fixing exactly that class of defect. A three-file pilot with a measured
before-and-after costs an hour and turns the question from a preference into a number.
