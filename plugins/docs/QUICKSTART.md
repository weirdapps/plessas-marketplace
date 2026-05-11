# docs — Quickstart

A 5-minute path from zero to "my Word document is drafted, branded, and saved."

## What it does

Creates Word documents (`.docx`) with NBG formatting baked in — Aptos 11pt body, `#404040` text, `#007B85` headings (NBG Teal), 2.54 cm margins, page numbers bottom centre. Three command shapes: a generic structured document (report / proposal / brief / notes), a formal business letter (letterhead, salutation, valediction, signature block), and an internal memo (TO / FROM / DATE / RE header). Greek and English are both supported — the language of your prompt drives the salutations and valedictions automatically (`Αξιότιμε…` / `Με εκτίμηση,` for Greek; `Dear…` / `Sincerely,` for English). Self-contained — uses `python-docx` for document generation (auto-installed on first use if missing). No external CLIs, no MCP servers, no API keys.

## Prerequisites

- Claude Code installed

That's it.

## Install

Inside Claude Code:

```
/plugin install docs@plessas-marketplace
```

## Authenticate

None required. All operations are local — files are written straight to `~/Downloads/`.

## Your first command

```
/docs-memo "Q1 Cards review — recommendations for Q2"
```

Output (typical):

```
Creating internal memo…

TO:        Cards leadership team
FROM:      D. Plessas, AGM Cards & Digital Business
DATE:      10 May 2026
RE:        Q1 Cards review — recommendations for Q2

────────────────────────────────────────────────────────

Q1 closed +12% vs plan on revenue, with credit-card fee mix
shifting 4 points higher than budget. Three areas warrant a
Q2 course-correction.

1. Pricing — fee-restructure rollout is on track; legal
   defence holds (small annual fee equivalent to prior multi-year).
   Recommend ExCo approval by end-May to lock the Q3 P&L assumption.

2. Acquisition — digital channel CSAT dropped 4 points after
   the April release. A/B inconclusive; recommend a controlled
   rollback plus targeted follow-up with Customer Insights.

3. Risk — fraud loss ratio is 8 bps under benchmark; the Fraud
   team should keep the current rule set. No change needed.

Decision needed by Friday 16 May on items 1 and 2.

────────────────────────────────────────────────────────

File written: ~/Downloads/202605101430_q1_cards_review_recommendations_for_q2.docx
```

Open the file in Word. Edit as needed. The plugin never touches it again.

## Top 3 commands

| Command | What it does |
|---|---|
| `/docs-create <topic> [type:report\|proposal\|brief\|notes]` | Structured Word document with template (default: `report`) |
| `/docs-letter <recipient> <subject>` | Formal business letter — letterhead, salutation, body, valediction, signature |
| `/docs-memo <topic>` | Internal memo with TO / FROM / DATE / RE header |

## Common patterns

**Memo to leadership team**:

```
/docs-memo "Cards Q1 review"
```

**Formal letter to regulator**:

```
/docs-letter "Bank of Greece, Supervision" "Quarterly compliance update"
```

**Internal proposal** (board paper, sponsor brief, etc.):

```
/docs-create "New mobile credit card product" type:proposal
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Greek text uses wrong font | Aptos handles Greek correctly. If you see boxes or squares, your Word install may be missing Aptos. Install: Microsoft 365 → Insider build, or use the Aptos Display package from the Office font installer |
| Letterhead missing on `/docs-letter` | Default uses NBG branding from `shared/brand-system/`. Pass `--no-letterhead` to suppress. To customise, edit `shared/brand-system/` files (advanced — talk to the marketplace maintainer) |
| Document opened blank in Word | Some Word installs need 'Trust documents from the internet' enabled. Try opening in macOS Pages first to verify the file is intact, then back to Word |
| Output filename has timestamp prefix | By design. Iterations get a NEW timestamp, not a version suffix. Compare side-by-side, keep the better one. Older versions stay sortable in `~/Downloads` |

## Where things live

- **All output**: `~/Downloads/YYYYMMDDHHMM_<descriptive_name>.docx` (Athens timezone)
- **Source documents are NEVER modified in place** — every run produces a fresh timestamped file. To iterate, re-run the command; you'll get a new file alongside the old one

## Want more?

- Architecture and template details: see [README.md](README.md)
- All commands: type `/` in Claude Code, scroll to the `docs:` group
