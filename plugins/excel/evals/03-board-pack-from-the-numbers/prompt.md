---
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
runs: 1
tags: [handoff, excel]
---

The board sees the payments numbers on Thursday. This is what Finance sent,
flattened out of the workbook:

| Unit        | FY plan | YTD plan | YTD actual |
|-------------|---------|----------|------------|
| Issuing     | 9.60    | 7.20     | 5.42       |
| Acquiring   | 6.40    | 4.80     | 4.71       |
| Prepaid     | 2.80    | 2.10     | 1.19       |
| Merchant FX | 2.40    | 1.80     | 0.88       |

I want this in front of them as slides, not as a table. Get it ready to build.
