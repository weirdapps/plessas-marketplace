---
description: "Display the Outlook folder hierarchy with message counts as a Unicode tree"
argument-hint: ""
allowed-tools: mcp__outlook-bridge__outlook_list_folders
---

# /folder-tree

Display the Outlook folder hierarchy with message counts.

## Implementation

1. Call `mcp__outlook-bridge__outlook_list_folders` with `recursive: true`
2. Render the result as a Unicode tree:
   - `📁 Inbox (47)` for branch nodes
   - Indent children with `├──` / `└──` glyphs
   - Color folders by item count: `>500` red, `>100` yellow, `0` grey, otherwise default
3. Print to terminal. Read-only; no confirmation needed.

## Tree format example

```
📁 Inbox (47 unread)
├── 📁 Newsletters (231)
├── 📁 Competitive-Intel (84)
├── 📁 Vendors
│   ├── 📁 Microsoft (12)
│   └── 📁 Adobe (3)
└── 📁 Archive-2026 (1834)
```
