# promote-rule

Stage 3 — self-learning. After /triage-inbox runs, scan the audit log for repeated LLM suggestions of the same (sender_domain → folder) pair.

## Detection

Read `~/.claude/triage/audit-log.jsonl`. For each unique `(sender_domain, suggested_folder)` pair where `rule_or_llm == "llm"`:

- Count occurrences in the last 30 days
- If count >= 3, add to `~/.claude/triage/pending-promotions.json`:

```json
{
  "sender_domain": "microsoft.com",
  "suggested_folder": "Inbox/Vendors/Microsoft",
  "occurrences": 3,
  "last_seen": "2026-04-22T13:14:00Z"
}
```

## User prompt

At the end of /triage-inbox, if pending-promotions.json is non-empty:

```
3 patterns are ready to promote to rules:
1. sender_domain: microsoft.com → Inbox/Vendors/Microsoft (3 occurrences)
2. ...

Promote all? [y/n/select]
```

On `y`: append rules to `~/.claude/triage/rules.yaml`, clear pending-promotions.json.

## Safety

- Never auto-promote — user must explicitly confirm.
- Never promote a `keep_locked` sender's pattern.
- Audit-log the promotion event itself.
