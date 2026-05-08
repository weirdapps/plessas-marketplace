# Claude Code — Team Configuration Template

> **What this is:** A baseline `CLAUDE.md` template optimized for productivity work at NBG (mail, decks, meetings, Teams chat, Excel, Word). Drop this into `~/.claude/CLAUDE.md` (or merge into your existing one). Customize the sections marked `<< REPLACE >>` with your own details. Add personal preferences below.

---

## Identity

`<< REPLACE >>` Your name, role, and primary email. Example:
> Name Surname — Role at NBG
> firstname.lastname@nbg.gr

---

## Email Preferences

- Always send in **HTML format** using the `--html` parameter for Outlook compatibility
- Convert markdown to proper HTML with tables, styling, and formatting
- Use inline CSS for consistent rendering across email clients
- Font: **Aptos 12pt, color #404040**. NO `<p>` tags — use `<br>` for line breaks, `<br><br>` for paragraph spacing
- Subject: ALWAYS lowercase. Content starts lowercase unless FULL format (greeting like "Καλημέρα"/"Καλησπέρα")
- Always CC yourself on outgoing mail

---

## Clipboard for Outlook (and other rich-text destinations)

When putting content on the clipboard (`pbcopy`) that may be pasted into Outlook, Word, or any rich-text destination, format as **RTF** — not raw markdown or plain text. Markdown shows as literal `**asterisks**` and `# hashes` in Outlook, which is unusable.

**Default**: RTF. Exceptions only when explicitly told "plain text", "markdown", or "for terminal/code".

### Pipeline (macOS)

1. Build HTML with inline styling matching email standards: Aptos 12pt, color `#404040`. Use `<br>`/`<br><br>` for line breaks (NO `<p>` tags). `<b>`, `<i>`, `<hr>` convert cleanly.
2. Convert HTML → RTF: `textutil -convert rtf input.html -output output.rtf`
3. Place on clipboard as RTF class so Outlook recognises it as rich text:
   `osascript -e 'set the clipboard to (read POSIX file "/abs/path/output.rtf" as «class RTF »)'`

### One-liner

```bash
textutil -convert rtf input.html -output /tmp/clip.rtf && osascript -e 'set the clipboard to (read POSIX file "/tmp/clip.rtf" as «class RTF »)'
```

**When NOT to use RTF**: explicit request for markdown/plain text/code; content is code/JSON/config (formatting would corrupt indentation); destination is markdown-aware (GitHub, Notion, Obsidian, Slack code blocks).

> **Windows users:** the macOS `textutil`/`osascript` pipeline does not apply. Use Outlook's native paste-as-HTML (Ctrl+Shift+V → paste as HTML) or an HTML→RTF converter of your choice.

---

## File Output & Naming Rules

- **Ad-hoc files go to `~/Downloads`** — never save generated artefacts (charts, reports, visualisations, org charts, etc.) inside project repos. Use `~/Downloads` to avoid codebase contamination.
- **File naming convention**: `YYYYMMDDHHMM_descriptive_name.ext` (Athens timezone, all lowercase, spaces/hyphens → underscores). Always run `TZ='Europe/Athens' date '+%Y%m%d%H%M'` to get the timestamp — never hardcode or guess.
- **NO version suffixes**: Never append `_v1`, `_v2`, `_final`, `_revised`, `_draft`, etc. The `YYYYMMDDHHMM` prefix IS the version — a fresh timestamp on each save makes versions sortable and unambiguous. Iterations get a NEW timestamp, not a version tag. Applies to ALL file types.
- **Temp/working files**: ALL intermediate files, test outputs, scratch work go to `~/Downloads/`.

---

## Workflow Patterns

### For Complex Tasks: Plan First

- Start complex features with `/plan-first` or Shift+Tab into plan mode
- Review the plan before executing
- Use `superpowers:writing-plans` for structured planning

### For Coding Tasks: Test First (TDD)

- Use `/test-first` to enforce test-driven development
- Write failing tests, then implementation, then refactor
- Use `superpowers:test-driven-development` skill

### For Multi-Part Tasks: Parallel Agents

- Use `/parallel <description>` to spawn agents with worktree isolation
- Each agent works on an isolated copy of the repo
- Use `superpowers:dispatching-parallel-agents` for coordination
- Limit to 2-4 parallel agents for manageable coordination

### Context Management

- Use `/compact [focus]` during long sessions to free context
- After major sections of long workflows, compact before next section

---

## NBG Terminology

- **Direct reports** (in NBG context): the people who report directly to a given executive. Does NOT include Deputies.
- **Leadership team**: All direct reports + Deputies + sector heads + υδντές.
- Deputies are part of the leadership team under their respective divisions, not direct reports.

In Greek: use **"Εθνική Τράπεζα"** (NOT "Εθνική Τράπεζα της Ελλάδος"). In English: **"National Bank of Greece"**.

---

## Coding Behaviour

- **Surface ambiguity**: If multiple interpretations exist, present them — don't pick silently. If uncertain, ask before implementing.
- **Simplicity first**: No features, abstractions, or "flexibility" beyond what was asked. If 200 lines could be 50, rewrite.
- **Surgical changes**: Don't improve adjacent code, comments, or formatting. Match existing style. If you notice unrelated dead code, mention it — don't delete it.
- **Clean up your own mess**: Remove imports/variables/functions that YOUR changes made unused. Don't remove pre-existing dead code unless asked.
- **Goal-driven execution**: For multi-step tasks, state a brief plan with verification checks per step before starting.

---

## Cross-Plugin Rules

- **Re-auth continuity**: When a re-auth hook fires and completes, ALWAYS continue the interrupted task immediately. Never stop, pause, or ask the user to repeat their request.
- **Calendar queries**: PRIMARY = `mcp__outlook-bridge__outlook_list_calendar` / `outlook_get_event` (M365-synced via outlook-cli, structured JSON). NEVER use AppleScript with macOS Calendar — it's out of sync with M365.
- **Mail reads**: PRIMARY = `mcp__outlook-bridge__outlook_list_mail` / `outlook_get_mail` (HTTP via outlook-cli, no concurrency limit).
- **Mail send**: PRIMARY = `outlook-cli send-mail` (creates draft + activates Outlook desktop; `--send-now` to dispatch immediately). Also: `outlook-cli reply`, `reply-all`, `forward`. Signature from `~/.outlook-cli/signature.html` is auto-appended. CC-self is on by default.
- **Teams reads**: PRIMARY = `mcp__teams-bridge__teams_*` tools (read chats, list channels, fetch messages). Auth via `teams-cli login`.
- **Teams send**: `mcp__teams-bridge__teams_send_message` (chat sends only — channel sends require additional Graph scopes).
- **outlook-cli auth**: If a tool returns `auth_required`, run `outlook-cli login --sharepoint-host groupnbg.sharepoint.com` (NOT `nbg.sharepoint.com` — the latter doesn't exist for this tenant).
- **outlook-cli concurrency**: For batch get-mail bursts, cap at concurrency=2 to avoid M365 ApplicationThrottled (HTTP 429).
- **WebSearch**: May fail on some models. Use `Agent` tool with `model: "sonnet"` as a fallback for web searches.
- **LLM calls in code**: All LLM-invoking code MUST go through the local `claude` CLI via `subprocess.run(["claude", "--model", "sonnet", "--print"], input=prompt, ...)` — which routes via Vertex AI on NBG-managed machines (billed to NBG). NEVER add the `anthropic` Python SDK to dependencies, NEVER write `from anthropic import Anthropic`, NEVER `curl https://api.anthropic.com`. Default model: Sonnet (configurable). Mock `subprocess.run` in tests, not the SDK.

---

## Brand Specs

NBG brand specs (colours, fonts, logos, layout grids) live in this marketplace at `shared/brand-system/`. Plugins that need brand assets reference that directory. See `shared/brand-system/README.md` for the canonical spec.

Default email/text colour: `#404040`. Default font: Aptos 12pt.

---

## Email Style

A baseline email style guide lives at `shared/email-style-template/style-guide-template.md`. The `mail` plugin reads from `<plugin-root>/shared/style-guide.md` — point that at the template, OR overlay your personal style customisations in `~/.claude/private/email-style-personal.md` (if you maintain one).

---

## Personal Customisations (you add below this line)

`<< REPLACE >>` Add your personal preferences, custom commands, recipient pet-names, peer addressing conventions, etc. below this line.
