# Workflow: mail-pro

Corpus-driven mail analytics that require the [`second-brain`](https://github.com/weirdapps/second-brain) knowledge store. Currently a private repo — request access from the marketplace maintainer.

If you don't have second-brain access, skip this plugin entirely. Everything here is opt-in; the base [`mail`](mail.md) plugin works without it.

## Key commands

| Command | What it does |
|---|---|
| `/comm-report` | Strategic communication health report — relationship heatmap, response patterns, delegation effectiveness, language trends. Needs the full ingested corpus. |
| `/style-rebuild` | Full corpus analysis to (re-)generate a statistically-grounded style guide with per-recipient profiles. One-shot — run after major life or role changes, not periodically. |

## Background script

```
plugins/mail-pro/scripts/style-sync.py
```

Runs daily via launchd / cron after the second-brain ingest pipeline. Updates aggregate metrics (counts, language/sentiment distributions, drift alerts) in `plugins/mail/shared/style-guide.md`. Does NOT touch per-recipient profiles — those require Claude-assisted analysis via `/style-rebuild`.

The script is invoked from `~/SourceCode/second-brain/scripts/launchd/wrappers/sb-daily-sync.sh` after the daily ingest. Override the DB location with `--db /path/to/your/brain.db` if you keep second-brain elsewhere.

## Setup

1. Get access to `weirdapps/second-brain` from the maintainer
2. Clone and follow its README to populate the database (this is multi-week — start ASAP)
3. Once `~/SourceCode/second-brain/data/brain.db` exists, the commands and the launchd-driven daily sync just work

## Tips

- The first `/style-rebuild` run takes a long time (full corpus = thousands of emails). Use it once, then let `/style-sync` (in the base `mail` plugin) and `style-sync.py` (in this plugin) do the daily incremental updates.
- `/comm-report` is most useful weekly or monthly. Don't run it daily — analytics need a meaningful new-email delta to surface trends.
