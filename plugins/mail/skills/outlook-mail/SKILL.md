---
name: outlook-mail
description: "Anything to do with the user's Outlook mailbox: reading it, deciding what in it matters, and composing what goes out of it. Covers inbox briefings and triage, finding and summarising messages or threads, drafting replies and forwards, sending new mail, and learning the user's writing style. Use this whenever a request concerns email, however it is phrased, for example \"what needs my attention today\", \"anything urgent from the auditors\", \"answer Maria\", \"put together a note to the team\", or in Greek «τι τρέχει στο μέιλ μου», «ποιος περιμένει απάντηση», «γράψε στον Κώστα», «βγάλε μου μια σύνοψη από τα χθεσινά». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for Microsoft Teams messages or chats (use teams-chat), for preparing or debriefing meetings (use meeting-workflows), or for reading spreadsheets or Word documents."
---

# Outlook mail

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| see what is in the mailbox and what matters | `/mail:inbox-briefing` |
| the same, plus drafted replies ready to review | `/mail:mail-review` |
| sort, file or clean up the mailbox | `/mail:triage-inbox` |
| answer a message | `/mail:reply` |
| pass a message on to someone else | `/mail:forward` |
| write a new message | `/mail:send-mail` |
| file a finished thread away | `/mail:archive-thread` |
| know what was decided across recent mail | `/mail:decisions` |
| learn how past drafts differed from what was actually sent | `/mail:draft-review` |
| see the folder structure | `/mail:folder-tree` |
| teach the plugin their writing style | `/mail:style-sync` |
| inspect or undo style learning | `/mail:style-stats`, `/mail:style-rollback` |
| fix mail access or authentication | `/mail:mail-doctor`, `/mail:auth-setup` |

<!-- safety-guardrails:v1 -->
## Send-safety blacklist (irreversible)

These hold for every route above.

- NEVER dispatch (`--send-now`) without showing the draft and getting explicit confirmation. Default is draft-first.
- Verify the recipient: primary and CC must be your own configured primary address; never send FROM a forwarding alias.
- Do NOT add any [Claude] / AI tag to email (that is a Teams-only rule), and do NOT alter the user signature.
- Never send on empty, placeholder, or errored content; if the body failed to generate, STOP and report.

## When nothing fits

If the request is clearly about email but no row above serves it, say what this
plugin can do and ask which the user wants. Do not pick the nearest row.
