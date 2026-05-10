# rule-matcher

Stage 1 of the triage cascade. Match an email against the user's `~/.claude/triage/rules.yaml`.

## Inputs

- `email`: { id, sender_email, sender_domain, subject, content_class?, has_attachments }
- `rules`: parsed from rules.yaml

## Algorithm

For each rule (in file order — first match wins):

1. Evaluate `when` predicates AND-style (all must match)
2. If matched, return `{ rule_name, action }`
3. If no rule matches, return `{ rule_name: null, action: null }` — caller proceeds to Stage 2 LLM

## Predicate semantics

- `sender`: exact case-insensitive match
- `sender_contains`: substring case-insensitive
- `sender_domain_in`: extract domain (`split('@')[1].toLowerCase()`), check membership
- `subject_contains`: substring case-insensitive (Greek-aware via `Intl.Collator`)
- `subject_matches`: regex (compile with `i` flag; surface compile errors at rule-load time, not match-time)
- `content_class`: equality against Outlook's classification (e.g. `IPM.Note`, `IPM.Schedule.Meeting.Request`)
- `has_attachments`: boolean equality
