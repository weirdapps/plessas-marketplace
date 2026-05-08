# Email Style Guide — Template

> **What this is:** A template for the `mail` plugin's style guide. The plugin uses this to match your voice when drafting replies. Copy to `<plugin-root>/shared/style-guide.md` and customise the `<< REPLACE >>` blocks. For best results, regenerate it from your actual sent mail using `/mail-style-rebuild` after a few weeks of usage.

---

## Identity

`<< REPLACE >>` Your name, role, and email. Example:
> Name Surname — Role at NBG
> - Email: firstname.lastname@nbg.gr (primary)
> - Always CC self on replies — Archive is the canonical source for sent mail

## Signature Block (auto-appended by Outlook)

> The mail plugin's drafting commands NEVER include the signature in reply text — Outlook adds it automatically from `~/.outlook-cli/signature.html`.

`<< REPLACE >>` Your signature lines. Example:
```
Name Surname
Role
Address
M: +30 ..., E: name@nbg.gr
```

---

## Language Defaults

Greek is the dominant language for internal NBG communication. Mixed Greek/English (English loanwords, business jargon, code-switching) is normal. Pure English is reserved for international external contacts.

**Heuristic:** if the recipient's previous reply was in Greek, reply in Greek. If they wrote in English, reply in English. When in doubt with Greek-speaking colleagues at NBG, default to Greek.

`<< REPLACE >>` if your defaults differ.

---

## Tone Patterns

### Greetings (Greek)

| Time of day | Greeting |
|---|---|
| Morning (until ~13:00) | Καλημέρα |
| Afternoon / evening | Καλησπέρα |
| First contact in long time | Καλησπέρα <name>, ελπίζω να είσαι καλά |

### Greetings (English)

| Recipient relationship | Greeting |
|---|---|
| Internal colleague | Hi <Firstname>, |
| External, formal | Dear <Mr./Ms. Lastname>, |
| External, established | Hi <Firstname>, |

### Sign-offs (Greek)

| Tone | Sign-off |
|---|---|
| Default | Ευχαριστώ, |
| Formal | Με εκτίμηση, |
| Informal / repeated thread | Ευχ, |

### Sign-offs (English)

| Tone | Sign-off |
|---|---|
| Default | Thanks, |
| Formal | Best regards, |
| Informal | Cheers, |

`<< REPLACE >>` Add your patterns. Particularly: any pet-names or special addressing for specific recipients (family, close colleagues, your manager). Keep these in your personal-only customisation file at `~/.claude/private/email-style-personal.md` if you don't want them shipped in this guide.

---

## Subject Line Rules

- ALWAYS lowercase, except acronyms (NBG, KPI, ATM, IRIS) and proper nouns
- 5-9 words ideal
- Lead with the noun ("payment terminal rollout — phase 2") not the verb ("re: please review payment...")
- Re: / FW: prefixes auto-added by Outlook; don't manually type them

## Body Format Rules

- Aptos 12pt, colour `#404040`
- NO `<p>` tags — use `<br>` for line break, `<br><br>` for paragraph break
- Bullet lists: `<ul><li>...</li></ul>` with inline styling for the list items
- Tables: inline styled `<table>` with `border-collapse: collapse`, header row in bold
- Headings inside body: `<b>` (NOT `<h1>`/`<h2>` — they render with browser defaults)
- Hyperlinks: `<a href="...">visible text</a>` — full URL never in body

---

## Email Categories & Patterns

### Informational / Research / Data emails

- **Subject**: ultra-brief English label
- **Body**: minimal greeting (or none), straight to the data, no Greek intro lines
- **Attachments**: charts/screenshots inline, full data files attached
- **Sign-off**: `Thanks,` or omitted

### VBM / Budget / Directive emails

- **Subject**: simple, action-oriented
- **Body**: inline actions assigned by name (`@Name: ...`)
- **Strategic context**: 2-3 sentences upfront
- **Concrete asks**: numbered, with deadlines
- **Sign-off**: standard

### Boss / Senior briefing emails

Two distinct shapes:

**External-content briefings** (forwarding/summarising what came from outside)
- Facts only, minimal opinion
- Source attribution at top
- Bold the lead point in green (`<span style="color:#00B050;font-weight:bold;">...</span>`)

**Internal/performance briefings** (your own analysis)
- Synthesis upfront, three bullets
- Bold the lead point in green
- Detail and tables below
- Recommendation at the end

### Status update emails (action-item follow-ups)

- Keep the original agreed text verbatim (so the recipient remembers what was promised)
- Add progress notes in **dark red** (`<span style="color:#C00000;">progress: ...</span>`)
- Mark completed items with `<s>strikethrough</s>` of the original

---

## Recipient Profiles

The `mail` plugin maintains a per-recipient profile in `<plugin-root>/shared/recipient-profiles.db`. Each profile tracks:

- Greeting/sign-off patterns from your past replies to that recipient
- Typical email length (short/medium/long)
- Topic clusters
- Last-contact date
- Language (Greek / English / mixed)

This file is **per-user and gitignored** — it grows organically from your sent mail. Do NOT commit it.

`<< REPLACE >>` Optionally enumerate explicit overrides for specific recipients here:

```
- recipient.name@nbg.gr — always Greek, always brief, always CC their assistant
- another.name@external.com — formal English only, full title, 24-hour response window
```

---

## Drafting Workflow

When the `mail` plugin drafts a reply, it:

1. Pulls the thread context
2. Reads the recipient profile (or uses defaults if new)
3. Reads this style guide
4. Reads any personal overlay at `~/.claude/private/email-style-personal.md`
5. Generates a draft (no signature — Outlook appends)
6. Creates an Outlook draft (does NOT send)
7. You review and send manually

`/mail-draft-review` lets you compare what you sent vs. what Claude drafted, and feeds corrections back into this guide.

---

## Maintenance

- After ~1 month of usage: run `/mail-style-rebuild` to regenerate this guide from your actual sent mail
- `/mail-style-sync` does an incremental update with new sent mail since last sync
- `/mail-style-stats` shows accuracy trends (drafted vs. actual)
- `/mail-style-rollback` restores a previous version from backup
