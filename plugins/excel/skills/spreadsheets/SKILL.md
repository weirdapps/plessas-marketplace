---
name: spreadsheets
description: Anything to do with reading, analysing or explaining spreadsheet data: summarising what a workbook contains, pivoting and regrouping it, explaining why a number moved against plan or against last period, and handing the analysis to a deck. Use this whenever the subject is a spreadsheet or the numbers inside one, however the request is phrased, for example "what is going on in this file", "why is Q3 short", "break it down by region", "I need this in slides for tomorrow", or in Greek «τι λέει αυτό το αρχείο», «γιατί πέφτει το τρίμηνο», «σπάσ' το ανά μονάδα», «κάν' το παρουσίαση». These are samples, not an exhaustive list: judge by meaning, not by matching words. Do NOT use for Word documents (use word-documents), for email (use outlook-mail), or for building a deck that does not start from spreadsheet data (use presentations).
---

# Spreadsheets

Route by what the user is trying to achieve, not by the words they used.

| The user wants to | Run |
|---|---|
| understand what a workbook holds | `/excel:excel-summary` |
| regroup or cross-tabulate the data | `/excel:excel-pivot` |
| explain a gap against plan, budget or a prior period | `/excel:excel-variance` |
| carry the analysis into slides | `/excel:excel-to-deck` |

`/excel:excel-to-deck` stays here rather than in presentations, because the
work starts from the data. Route "turn this file into slides" here.

## When nothing fits

If the request is clearly about a spreadsheet but no row above serves it, say
what this plugin can do and ask. Do not pick the nearest row.
