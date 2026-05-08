---
name: triage-engine
description: Triage engine — rule + LLM cascade for /triage-inbox. See rule-matcher.md, llm-classifier.md, promote-rule.md.
---

# Triage Engine

Three-stage cascade for inbox triage, invoked by `/triage-inbox`:

1. **Stage 1 — rule matcher** (`rule-matcher.md`): Match each email against the user's `~/.claude/triage/rules.yaml`. First match wins.
2. **Stage 2 — LLM classifier** (`llm-classifier.md`): For unmatched emails, ask Claude Haiku 4.5 to suggest a destination from the user's existing folder list.
3. **Stage 3 — promote-rule** (`promote-rule.md`): After the run, scan the audit log for repeated LLM suggestions and surface them as candidate rules for user-confirmed promotion.

See each sub-doc for inputs, outputs, and semantics.
