# Day One — Your first hour with plessas-marketplace

You've installed the marketplace and authenticated. Here's what to try.

## 1. Check everything's working

```bash
# macOS / Linux
~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh

# Windows PowerShell
~\.claude\plugins\marketplaces\plessas-marketplace\installers\status.ps1
```

You should see 15/15 green checks.

## 2. Try each plugin (5 minutes)

Open Claude Code and type these commands:

### Mail — see your inbox

```
/inbox-briefing
```

This reads your Outlook inbox and produces a briefing with summaries, priorities, and suggested actions.

### Chat — see your Teams unreads

```
/chat-inbox
```

This summarises your recent Microsoft Teams chats and highlights anything that needs a reply.

### Excel — analyse a spreadsheet

```
/excel-summary ~/Downloads/any-file.xlsx
```

Replace with any .xlsx file you have. Claude will read the structure, surface KPIs, and flag anomalies.

### Docs — create a Word document

```
/docs-create quarterly update
```

Claude produces a structured .docx file and saves it to ~/Downloads/.

### Decks — create a presentation

```
/create-presentation Q4 results summary for leadership
```

This runs the full multi-agent pipeline: storyline → storyboard → graphics → QA. Takes a few minutes.

### Meetings — prepare for your next meeting

```
/meeting-prep
```

Claude reads your calendar, identifies your next meeting, and prepares a briefing with attendee dossiers.

## 3. Customise your CLAUDE.md

Edit `~/.claude/CLAUDE.md` and replace the `<< REPLACE >>` sections with your own name, email, and preferences. This personalises how Claude addresses you and your contacts.

## 4. When something goes wrong

- **Auth expired?** Re-run the auth bootstrap inside Claude Code: `/mail:auth-setup` for Outlook, `/chat:auth-setup` for Teams. Both take `--force-reauth`. (The terminal scripts `installers/auth-wizard.sh` / `.ps1` still work but are deprecated.)
- **Plugin not loading?** Run the status script (step 1 above) and share the output.
- **Need help?** Open an issue at [github.com/weirdapps/plessas-marketplace/issues](https://github.com/weirdapps/plessas-marketplace/issues)

## 5. What's next

- **Email style learning**: the guide calibrates itself as you use `/mail-review`. After a week, run `/style-sync` for a batch update from your sent mail. (`/style-rebuild` is not in this marketplace; it ships with the optional `mail-pro` plugin in [`plessas-lab`](https://github.com/weirdapps/plessas-lab).)
- **Pivot and variance**: try `/excel-pivot` and `/excel-variance` on a financial report
- **Teams digest**: try `/chat-channel-digest` on a busy channel to catch up
