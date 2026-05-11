# Workflow: docs

Create Word documents — reports, letters, memos.

## Commands

| Command | What it does |
|---|---|
| `/docs-create <topic> [type]` | Generic document (report, proposal, brief, notes) |
| `/docs-letter <recipient> <subject>` | Formal business letter |
| `/docs-memo <to> <subject>` | Internal memo |

## Example session

```
You: /docs-memo "Cards Team" "Q4 priorities update"
Claude: [creates structured memo via document-skills:docx]
Claude: Memo saved to ~/Downloads/202605091200_memo_q4_priorities_update.docx
```

## Tips

- Language matches your input — Greek in, Greek out
- Font: Aptos 11pt body, brand headings in #007B85 (NBG Teal)
- All files saved to `~/Downloads/` with `YYYYMMDDHHMM_` prefix
