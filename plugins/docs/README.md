# docs v1.0

Word document creation with NBG formatting baked in. Three command shapes: generic structured doc, formal business letter, internal memo. Uses `document-skills:docx` (Anthropic's docx skill) when available for best results. Falls back to `python-docx` (auto-installed on first use) if the skill is not installed. NBG conventions (Aptos 11pt body, `#404040` text, `#007B85` headings (NBG Teal), page numbers, 2.54 cm margins).

## Commands

| Command | Description |
|---------|-------------|
| `/docs-create <topic> [type:report\|proposal\|brief\|notes]` | Structured Word document. `type` picks a section template (default: `report`) |
| `/docs-letter <recipient> <subject>` | Formal business letter — letterhead, salutation, body, valediction, signature block |
| `/docs-memo <topic>` | Internal memo — TO/FROM/DATE/RE header, structured body, optional distribution list |

## How it works

Each command:

1. Creates the document via `document-skills:docx` (preferred) or `python-docx` fallback (auto-installed if missing)
2. Asks clarifying questions if the topic is ambiguous (e.g. a memo without a clear ask)
3. Drafts the content in the appropriate structure
4. Applies NBG formatting:
   - Font: Aptos 11pt body / Aptos 14pt headings
   - Colour: `#404040` body text, `#007B85` headings (NBG Teal)
   - Margins: 2.54 cm all sides
   - Page numbers: bottom centre
5. Writes the `.docx` to `~/Downloads/` with a `YYYYMMDDHHMM_<descriptive_name>.docx` filename (Athens timezone), per the global file-naming convention

You then open the file in Word, review, and edit as needed. The plugin never modifies a document in place — every run produces a fresh timestamped file.

## Document templates

### Report

Title page · executive summary · numbered sections with headings · conclusions · appendix slot.

### Proposal

Title · problem statement · proposed solution · timeline · budget · next steps · sign-off block.

### Brief

Title · background (1-2 paragraphs) · key points (bulleted) · recommendation · author/date footer.

### Notes

Title · date · attendees (if applicable) · numbered discussion points · action items table.

### Letter (`/docs-letter`)

Letterhead with sender block · date · recipient address · salutation (`Dear <name>,` or Greek equivalent) · body paragraphs · valediction · signature block (name + title).

### Memo (`/docs-memo`)

TO/FROM/DATE/RE header block · introduction · structured body (one section per ask) · clear close (decision needed by, action requested, FYI).

## Setup

No setup required beyond installing the plugin:

```
/plugin install docs@plessas-marketplace
```

For best results, install Anthropic's `document-skills` plugin (`/plugin install document-skills`). Without it, the commands fall back to `python-docx` (auto-installed on first use).

## Tips

- **Greek and English**: pass content in either language. The plugin detects the language and uses the appropriate salutations / valedictions (`Αγαπητέ <όνομα>,` / `Με εκτίμηση,` for Greek; `Dear <name>,` / `Best regards,` for English).
- **Iteration**: re-run the command with the same topic — you'll get a new timestamped file, not an overwrite. Compare side-by-side, keep the better version.
- **Letterhead customisation**: the default letterhead uses NBG branding from `shared/brand-system/`. To override (e.g. for personal letters), pass the content with `--no-letterhead`.
- **Distribution list on memos**: include `cc:` or `distribution:` lines in your prompt and they'll appear in the header.

## License

MIT
