---
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write]
runs: 3
tags: [routing, excel]
---

Finance sent the September pack and we are 1.2m under plan for the quarter. This
is what is in it:

| Unit        | Plan Q3 | Actual Q3 | Plan Q2 | Actual Q2 |
|-------------|---------|-----------|---------|-----------|
| Issuing     | 2.40    | 1.85      | 2.30    | 2.34      |
| Acquiring   | 1.60    | 1.52      | 1.55    | 1.58      |
| Prepaid     | 0.70    | 0.44      | 0.65    | 0.63      |
| Merchant FX | 0.60    | 0.29      | 0.55    | 0.57      |

I need to know where the gap actually is before Monday, not just that it exists.
