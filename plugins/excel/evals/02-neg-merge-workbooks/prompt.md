---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
runs: 3
tags: [negative, excel]
---

I have about forty CSV exports sitting in one folder and I need them merged into
a single workbook, one tab per file, tab named after the file. Nothing else, just
the merge.
