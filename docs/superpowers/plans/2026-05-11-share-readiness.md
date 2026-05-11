# plessas-marketplace Share-Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `plessas-marketplace` installable by a Mac or Windows teammate from a fresh clone — `install.{sh,ps1}` succeeds, `auth-wizard.{sh,ps1}` does not pin them to the maintainer's M365 tenant, and no plugin silently fails because of a hardcoded `~/SourceCode/...` path or a private-repo dependency.

**Architecture:** Six sequential phases. (1) Unblock the install pipeline — pin npm deps to the versions actually tested, add the missing Python venv install on Windows. (2) Parameterize the M365 tenant — replace the hardcoded `groupnbg.sharepoint.com` with a first-run prompt persisted to `~/.outlook-cli/config.json`. (3) Close cross-platform gaps in plugin docs — `/tmp/` paths, mac-only example blocks, AppleScript fallbacks. (4) Move `mail-pro` out of this marketplace into `plessas-lab` (it depends on the private `second-brain` repo and is structurally maintainer-only). (5) Documentation — Windows install code blocks in README, PowerShell troubleshooting recipes, honest disclosure that `decks` is NBG-branded by design. (6) Verification — PII gauntlet, plugin validator, fresh install on both OSes.

**Tech Stack:** Bash 4+ and PowerShell 5.1+ installers; TypeScript 5.9 + Node 20 LTS for the bundled MCP servers; Python 3.11+ for the `decks` Python tools; Playwright via `outlook-cli` and `teams-cli`; `python-pptx` for slides.

**Out of scope (deliberate maintainer decisions, do not touch in this plan):**

- The NBG-branded `decks` plugin stays NBG-branded. The 22 "Plessas signature / Plessas KPI Card" references in `plugins/decks/shared/brand-system/{colors,layouts,typography,charts}.md` are intentional — this is the maintainer's NBG brand system. The marketplace README will disclose this honestly (Task 5.4) but the brand-system docs themselves do not change.
- The `chat` plugin's `chat-reply.md` keeps its conservative "NEVER auto-send" default. This conflicts with the maintainer's personal `~/.claude/CLAUDE.md` Teams rule, but the marketplace default is the safer one for shared use; the maintainer overrides locally. No change.
- "Plessas pushes updates" / "Plessas's name" attributions in `docs/FAQ.md`. This is the maintainer's marketplace; the attribution is accurate. No change.
- `plessas-trading` work — handled in a separate plan.

---

## File Structure

**New files:**

- `installers/lib/tenant-prompt.sh` — shared Bash helper to prompt for and persist M365 tenant host
- `installers/lib/tenant-prompt.ps1` — same, for PowerShell
- `docs/WINDOWS.md` — single page with Windows-specific install + troubleshooting steps cross-linked from per-plugin READMEs

**Modified files:**

- `plugins/mail/mcp-server/package.json` — pin TS / @types/node / vitest, add engines.node
- `plugins/chat/mcp-server/package.json` — same
- `installers/install.ps1` — add Python venv install block matching install.sh:78-97
- `installers/auth-wizard.sh` — call tenant-prompt.sh, drop hardcoded `groupnbg.sharepoint.com`
- `installers/auth-wizard.ps1` — same with tenant-prompt.ps1
- `plugins/mail/mcp-server/src/tools/doctor.ts` — read tenant from config, not hardcoded
- `plugins/mail/QUICKSTART.md` — replace `groupnbg.sharepoint.com` with `<your-tenant>.sharepoint.com`
- `shared/claude-md-template/team-claude-md.md` — same replacement
- `plugins/mail/commands/mail-review.md` — split mac-only clipboard example into three OS variants
- `plugins/mail/agents/email-handler.md` — same split
- `plugins/mail/commands/inbox-briefing.md` — replace `/tmp/mail_att` with cross-platform tempdir
- `plugins/decks/commands/redesign-deck.md` — same for `/tmp/deck_extracted.md`
- `plugins/meetings/agents/meeting-intelligence.md` — guard 3 AppleScript blocks with `[[ "$OSTYPE" == "darwin"* ]]`
- `plugins/meetings/shared/calendar-access.md` — same
- `plugins/decks/commands/{create-presentation,presentation-review}.md` — auto-create `~/.claude/presentations/{pending,reviewed}/`
- `plugins/decks/agents/graphics-renderer.md` — same
- `plugins/decks/orchestrator/nbg-presenter/AGENT.md` — same
- `.claude-plugin/marketplace.json` — remove `mail-pro` entry; bump metadata version
- `README.md` — Windows install code blocks, Chrome/Edge prereq, NBG-decks disclosure
- `docs/TROUBLESHOOTING.md` — PowerShell recipes for the 6 most common issues
- `installers/pii-gauntlet.sh` — leave allowlist for "Plessas" alone (per scope decision); only verify gauntlet still passes after changes
- `CHANGELOG.md` — entry per phase

**Moved (to `plessas-lab`):**

- `plugins/mail-pro/` (entire directory) — see Phase 4
- `.claude-plugin/marketplace.json` mail-pro entry — see Phase 4

**Deleted:**

- `plugins/mail-pro/` (after copy verified)

---

## Phase 1 — Unblock the install pipeline

The current `package.json` files in both bundled MCPs declare `"typescript": "^6.0.3"`, `"@types/node": "^25.6.2"`, `"vitest": "^4.0.0"`. Those versions exist on npm — but the code has only been verified against `typescript 5.9.3` (what's currently in `node_modules`). A teammate cloning today does `npm install`, gets TS 6 (with breaking changes vs 5.x), and may see compile failures the maintainer never saw. Pin to what was tested. Separately, `install.ps1` checks for Python but never builds the venv that the `decks` plugin's Python tools need; on Windows the plugin is structurally broken until this is fixed.

### Task 1.1: Pin outlook-bridge MCP deps to tested versions

**Why:** Drift between declared SemVer ranges and installed versions. `node_modules/typescript/package.json` reports 5.9.3; declared range is `^6.0.3`. Same drift for `@types/node` (25.6.2 declared, ?.x.x installed) and `vitest` (4.0.0 declared, ?.x.x installed). Anchor everything to what the maintainer actually built and tested against.

**Files:**

- Modify: `plugins/mail/mcp-server/package.json`
- Test: `cd plugins/mail/mcp-server && rm -rf node_modules package-lock.json && npm install && npm run build && npm test`

- [ ] **Step 1: Inspect actually-installed versions** to know what to pin to.

```bash
for dep in typescript @types/node vitest @modelcontextprotocol/sdk; do
  echo "=== $dep ==="
  cat ~/SourceCode/plessas-marketplace/plugins/mail/mcp-server/node_modules/$dep/package.json 2>/dev/null \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])" 2>/dev/null \
    || echo "(not installed)"
done
```

Expected output (representative): `typescript 5.9.3`, `@types/node 22.x.x`, `vitest 3.x.x`, `@modelcontextprotocol/sdk 1.x.x`.

- [ ] **Step 2: Rewrite `plugins/mail/mcp-server/package.json`** to:

```json
{
  "name": "outlook-bridge-mcp",
  "version": "0.4.1",
  "private": true,
  "type": "module",
  "main": "dist/server.js",
  "engines": {
    "node": ">=20"
  },
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "outlook-tool": "github:weirdapps/outlook-access"
  },
  "devDependencies": {
    "typescript": "~5.9.3",
    "vitest": "^3.0.0",
    "@types/node": "^22.0.0"
  }
}
```

Notes on the version choices:

- `~5.9.3` (tilde, not caret) allows patch bumps within 5.9.x but blocks an automatic upgrade to TS 6.x — which has known breaking changes around module resolution and `--isolatedDeclarations`. Use the actual installed version from Step 1 if it differs.
- `@types/node ^22.0.0` matches Node 22 LTS; the marketplace requires Node 20+ but @types/node v22 is backwards-compatible.
- `vitest ^3.0.0` is the last stable line before vitest 4 (which added breaking config changes).
- Bumped MCP version `0.4.0` → `0.4.1` to mark a published change.

- [ ] **Step 3: Verify exact versions match what was installed.** If Step 1 showed different installed versions for `@types/node` or `vitest`, adjust Step 2 to match those instead. The principle: pin to what was tested, not to what npm latest advertises.

- [ ] **Step 4: Clean install + verify build.**

```bash
cd ~/SourceCode/plessas-marketplace/plugins/mail/mcp-server
rm -rf node_modules package-lock.json dist
npm install 2>&1 | tail -5
```

Expected: exit code 0, output ending with `added N packages` and no `npm error` lines.

- [ ] **Step 5: Verify build.**

```bash
npm run build
ls -la dist/server.js
```

Expected: `dist/server.js` exists, > 1 KB.

- [ ] **Step 6: Verify tests pass.**

```bash
npm test 2>&1 | tail -10
```

Expected: vitest summary line ending in `Tests N passed (N)` and no `failed` count.

- [ ] **Step 7: Commit.**

```bash
cd ~/SourceCode/plessas-marketplace
git add plugins/mail/mcp-server/package.json plugins/mail/mcp-server/package-lock.json
git commit -m "fix(mail-mcp): pin TS/types-node/vitest to tested versions, add engines.node"
```

### Task 1.2: Pin teams-bridge MCP deps to tested versions

Mirror of Task 1.1.

**Files:**

- Modify: `plugins/chat/mcp-server/package.json`
- Test: `cd plugins/chat/mcp-server && rm -rf node_modules package-lock.json && npm install && npm run build && npm test`

- [ ] **Step 1: Inspect actually-installed versions** (substitute path):

```bash
for dep in typescript @types/node vitest @modelcontextprotocol/sdk; do
  echo "=== $dep ==="
  cat ~/SourceCode/plessas-marketplace/plugins/chat/mcp-server/node_modules/$dep/package.json 2>/dev/null \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])" 2>/dev/null \
    || echo "(not installed)"
done
```

- [ ] **Step 2: Rewrite `plugins/chat/mcp-server/package.json`** matching the same pattern as Task 1.1 Step 2 (substitute name `teams-bridge-mcp`, version `0.2.1`, dependency `teams-cli` instead of `outlook-tool`).

```json
{
  "name": "teams-bridge-mcp",
  "version": "0.2.1",
  "private": true,
  "type": "module",
  "main": "dist/server.js",
  "engines": {
    "node": ">=20"
  },
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "teams-cli": "github:weirdapps/teams-access"
  },
  "devDependencies": {
    "typescript": "~5.9.3",
    "vitest": "^3.0.0",
    "@types/node": "^22.0.0"
  }
}
```

- [ ] **Step 3: Clean install + verify build + verify tests** (same commands as Task 1.1 Steps 4-6 with chat path).

- [ ] **Step 4: Commit.**

```bash
git add plugins/chat/mcp-server/package.json plugins/chat/mcp-server/package-lock.json
git commit -m "fix(chat-mcp): pin TS/types-node/vitest to tested versions, add engines.node"
```

### Task 1.3: Add Python venv build to PowerShell installer

**Why:** `installers/install.sh:78-97` builds Python venvs for `plugins/decks/tools/nbg-presentation/` (python-pptx slides) and `plugins/decks/bundled/creative/tools/device-mockup/` (Pillow-based mockup tools). `installers/install.ps1` only verifies Python exists at lines 30-36 then jumps straight to MCP build at line 60. Result: on a fresh Windows install, every `decks` command that shells out to one of those Python tools fails with `ModuleNotFoundError: No module named 'pptx'` (or similar).

**Files:**

- Modify: `installers/install.ps1`
- Test: `pwsh installers/install.ps1` after `Remove-Item -Recurse -Force` of the install dir

- [ ] **Step 1: Read existing `install.ps1`** to confirm the insertion point. The current structure is:
  - Lines 1-39: prerequisites check
  - Lines 43-56: clone or update
  - Lines 60-80: build MCP servers
  - Line 80 ends with the chat MCP build closing brace
  - Line 82+: install outlook-cli and teams-cli

We add the Python venv block between the existing line 80 and line 82.

- [ ] **Step 2: Insert the Python venv install block.** Use Edit, replacing the blank line after the chat MCP block:

```powershell
# --- Install Python deps for decks ---
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) { $pythonCmd = 'python' }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $pythonCmd = 'python3' }

if ($pythonCmd) {
    $decksReq = Join-Path $InstallDir 'plugins\decks\tools\nbg-presentation\requirements.txt'
    if (Test-Path $decksReq) {
        Write-Host ''
        Write-Host 'Installing Python dependencies for decks...'
        $venvDir = Join-Path $InstallDir 'plugins\decks\tools\nbg-presentation\.venv'
        if (-not (Test-Path $venvDir)) {
            & $pythonCmd -m venv $venvDir
        }
        $pip = Join-Path $venvDir 'Scripts\pip.exe'
        if (-not (Test-Path $pip)) { $pip = Join-Path $venvDir 'bin\pip' }  # WSL fallback
        & $pip install -q -r $decksReq 2>&1 | Select-Object -Last 3
        Write-Ok 'decks Python deps installed'
    }

    $mockupReq = Join-Path $InstallDir 'plugins\decks\bundled\creative\tools\device-mockup\requirements.txt'
    if (Test-Path $mockupReq) {
        $venvDir = Join-Path $InstallDir 'plugins\decks\bundled\creative\tools\device-mockup\.venv'
        if (-not (Test-Path $venvDir)) {
            & $pythonCmd -m venv $venvDir
        }
        $pip = Join-Path $venvDir 'Scripts\pip.exe'
        if (-not (Test-Path $pip)) { $pip = Join-Path $venvDir 'bin\pip' }
        & $pip install -q -r $mockupReq 2>&1 | Select-Object -Last 3
        Write-Ok 'device-mockup Python deps installed'
    }
} else {
    Write-Warn 'Python not found — skipping decks Python dep install. Install Python 3.11+ then re-run installer.'
}

```

The insertion point in current `install.ps1` is between line 80 (`Write-Ok 'teams-bridge MCP built'` closing brace) and line 82 (`# --- Install outlook-cli and teams-cli ---`).

- [ ] **Step 3: Test on Windows or WSL.**

If you have a Windows machine or VM:

```powershell
Remove-Item -Recurse -Force $env:USERPROFILE\.claude\plugins\marketplaces\plessas-marketplace -ErrorAction SilentlyContinue
pwsh installers\install.ps1
```

Expected: section "Installing Python dependencies for decks..." appears, ending with `[OK] decks Python deps installed`.

If you're on Mac and have no Windows access, run the script under PowerShell-on-Mac (`brew install --cask powershell` then `pwsh`):

```bash
brew install --cask powershell  # if not already installed
pwsh -File ~/SourceCode/plessas-marketplace/installers/install.ps1
```

Expected: same output. The Python venv may end up at `.venv/bin/pip` (Mac/Linux Python convention) rather than `.venv/Scripts/pip.exe` — the fallback line in Step 2 covers both.

- [ ] **Step 4: Verify the Python tools actually work.**

```bash
~/.claude/plugins/marketplaces/plessas-marketplace/plugins/decks/tools/nbg-presentation/.venv/bin/python -c "import pptx; print(pptx.__version__)"
```

Expected: a version string like `1.0.x`, no `ModuleNotFoundError`.

- [ ] **Step 5: Commit.**

```bash
git add installers/install.ps1
git commit -m "fix(installer): build decks Python venvs on Windows (parity with install.sh)"
```

### Task 1.4: Pin GitHub deps in MCP package.json with commit SHAs

**Why:** Both MCPs declare `"outlook-tool": "github:weirdapps/outlook-access"` and `"teams-cli": "github:weirdapps/teams-access"` — no branch, no SHA. Every fresh `npm install` re-pulls the head commit of `master` of those repos. A maintainer push to either repo immediately rolls forward for every teammate. This is a hidden non-determinism that makes "what version did the teammate get?" unanswerable.

**Files:**

- Modify: `plugins/mail/mcp-server/package.json`
- Modify: `plugins/chat/mcp-server/package.json`

- [ ] **Step 1: Get the current SHA of each repo's master branch.**

```bash
for repo in outlook-access teams-access; do
  echo "=== $repo ==="
  git ls-remote https://github.com/weirdapps/$repo.git refs/heads/master | awk '{print $1}'
done
```

Record the two SHAs.

- [ ] **Step 2: Update outlook-bridge to pin SHA.**

In `plugins/mail/mcp-server/package.json`, change:

```diff
-    "outlook-tool": "github:weirdapps/outlook-access"
+    "outlook-tool": "github:weirdapps/outlook-access#<SHA>"
```

(Substitute the actual SHA from Step 1.)

- [ ] **Step 3: Update teams-bridge to pin SHA.**

In `plugins/chat/mcp-server/package.json`, change:

```diff
-    "teams-cli": "github:weirdapps/teams-access"
+    "teams-cli": "github:weirdapps/teams-access#<SHA>"
```

- [ ] **Step 4: Verify clean install pulls the pinned SHA.**

```bash
cd ~/SourceCode/plessas-marketplace/plugins/mail/mcp-server
rm -rf node_modules package-lock.json
npm install 2>&1 | tail -3
cat node_modules/outlook-tool/.git-info 2>/dev/null || cat package-lock.json | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['packages']['node_modules/outlook-tool']['resolved'])"
```

Expected: the URL printed contains the SHA from Step 1.

- [ ] **Step 5: Document the bump procedure** in `installers/README.md`:

```markdown
## Updating bundled CLIs

`outlook-cli` and `teams-cli` are pinned to specific commits in the MCP `package.json` files. To pull a newer version:

```bash
# Get the new SHA
git ls-remote https://github.com/weirdapps/outlook-access.git refs/heads/master | awk '{print $1}'

# Update the pin in plugins/mail/mcp-server/package.json
# Then rebuild
cd plugins/mail/mcp-server && rm -rf node_modules package-lock.json && npm install && npm run build
```

Same for teams-cli in plugins/chat/mcp-server/package.json.

```

- [ ] **Step 6: Commit.**

```bash
git add plugins/mail/mcp-server/package.json plugins/mail/mcp-server/package-lock.json plugins/chat/mcp-server/package.json plugins/chat/mcp-server/package-lock.json installers/README.md
git commit -m "fix(mcp): pin outlook-cli and teams-cli to specific commit SHAs for reproducibility"
```

---

## Phase 2 — Parameterize the M365 tenant

`installers/auth-wizard.sh:28` and `installers/auth-wizard.ps1:25` both hardcode `outlook-cli login --sharepoint-host groupnbg.sharepoint.com`. The bundled outlook-bridge MCP also references this hostname in `plugins/mail/mcp-server/src/tools/doctor.ts:43` (the doctor's "fix it" hint). A teammate from any other org cannot authenticate without manually editing these files. Replace with a first-run prompt; persist the answer to `~/.outlook-cli/config.json`; re-use on subsequent runs.

### Task 2.1: Create shared tenant-prompt helper (Bash)

**Files:**

- Create: `installers/lib/tenant-prompt.sh`

- [ ] **Step 1: Create `installers/lib/`** if missing.

```bash
mkdir -p ~/SourceCode/plessas-marketplace/installers/lib
```

- [ ] **Step 2: Write `installers/lib/tenant-prompt.sh`** with the following content:

```bash
#!/usr/bin/env bash
# Resolve M365 SharePoint host from (in priority order):
#   1) PLESSAS_SHAREPOINT_HOST environment variable
#   2) ~/.outlook-cli/config.json {"sharepoint_host": "..."}
#   3) Interactive prompt (then persist to config.json)
#
# Echoes the resolved host on stdout. Returns 0 on success, 1 if no TTY and no
# pre-existing config (so non-interactive installs in CI without env var fail loudly).

set -euo pipefail

prompt_tenant() {
  local config_dir="$HOME/.outlook-cli"
  local config_file="$config_dir/config.json"

  # Priority 1: env var
  if [ -n "${PLESSAS_SHAREPOINT_HOST:-}" ]; then
    echo "$PLESSAS_SHAREPOINT_HOST"
    return 0
  fi

  # Priority 2: persisted config
  if [ -f "$config_file" ]; then
    local persisted
    persisted=$(python3 -c "import json,sys;d=json.load(open('$config_file'));print(d.get('sharepoint_host',''))" 2>/dev/null || echo "")
    if [ -n "$persisted" ]; then
      echo "$persisted"
      return 0
    fi
  fi

  # Priority 3: interactive prompt
  if [ ! -t 0 ]; then
    printf '[FAIL] Cannot prompt for SharePoint host (no TTY) and no PLESSAS_SHAREPOINT_HOST set or %s file present.\n' "$config_file" >&2
    printf '       Set PLESSAS_SHAREPOINT_HOST=<your-tenant>.sharepoint.com and re-run.\n' >&2
    return 1
  fi

  printf '\n' >&2
  printf 'Enter your Microsoft 365 SharePoint host (e.g. contoso.sharepoint.com).\n' >&2
  printf 'Find it in any SharePoint URL you own: https://<this-part>.sharepoint.com/...\n' >&2
  printf 'Tenant SharePoint host: ' >&2
  local host
  read -r host
  if [ -z "$host" ]; then
    printf '[FAIL] No host entered.\n' >&2
    return 1
  fi

  # Persist
  mkdir -p "$config_dir"
  python3 -c "
import json, os
path = '$config_file'
data = {}
if os.path.exists(path):
    try:
        data = json.load(open(path))
    except Exception:
        data = {}
data['sharepoint_host'] = '$host'
json.dump(data, open(path, 'w'), indent=2)
"
  chmod 600 "$config_file"
  printf '[OK]   Tenant host saved to %s\n' "$config_file" >&2

  echo "$host"
}
```

- [ ] **Step 3: Make executable.**

```bash
chmod +x ~/SourceCode/plessas-marketplace/installers/lib/tenant-prompt.sh
```

- [ ] **Step 4: Test the helper interactively.**

```bash
rm -f ~/.outlook-cli/config.json
unset PLESSAS_SHAREPOINT_HOST
source ~/SourceCode/plessas-marketplace/installers/lib/tenant-prompt.sh
echo "result: $(prompt_tenant)"
# Type "test.sharepoint.com" at the prompt
cat ~/.outlook-cli/config.json
```

Expected output ends with: `{"sharepoint_host": "test.sharepoint.com"}` and `result: test.sharepoint.com`.

- [ ] **Step 5: Test the persisted-read path.**

```bash
echo "second call: $(prompt_tenant)"
```

Expected: prints `test.sharepoint.com` immediately, no prompt.

- [ ] **Step 6: Test the env-var override path.**

```bash
PLESSAS_SHAREPOINT_HOST=overridden.sharepoint.com bash -c 'source ~/SourceCode/plessas-marketplace/installers/lib/tenant-prompt.sh; echo "env: $(prompt_tenant)"'
```

Expected: prints `env: overridden.sharepoint.com`.

- [ ] **Step 7: Test the no-TTY-no-config failure path.**

```bash
rm -f ~/.outlook-cli/config.json
echo | bash -c 'source ~/SourceCode/plessas-marketplace/installers/lib/tenant-prompt.sh; prompt_tenant' 2>&1
```

Expected: stderr contains `Cannot prompt for SharePoint host (no TTY)`, exit code 1.

- [ ] **Step 8: Commit.**

```bash
git add installers/lib/tenant-prompt.sh
git commit -m "feat(installer): add tenant-prompt.sh — env > config.json > interactive"
```

### Task 2.2: Create shared tenant-prompt helper (PowerShell)

**Files:**

- Create: `installers/lib/tenant-prompt.ps1`

- [ ] **Step 1: Write `installers/lib/tenant-prompt.ps1`.**

```powershell
# Resolve M365 SharePoint host from (in priority order):
#   1) $env:PLESSAS_SHAREPOINT_HOST environment variable
#   2) $env:USERPROFILE\.outlook-cli\config.json {"sharepoint_host": "..."}
#   3) Interactive prompt (then persist to config.json)
#
# Returns the resolved host. Throws if no interactive host can be resolved.

function Get-TenantHost {
    $configDir  = Join-Path $env:USERPROFILE '.outlook-cli'
    $configFile = Join-Path $configDir 'config.json'

    # Priority 1: env var
    if ($env:PLESSAS_SHAREPOINT_HOST) {
        return $env:PLESSAS_SHAREPOINT_HOST
    }

    # Priority 2: persisted config
    if (Test-Path $configFile) {
        try {
            $cfg = Get-Content $configFile -Raw | ConvertFrom-Json
            if ($cfg.sharepoint_host) { return $cfg.sharepoint_host }
        } catch {}
    }

    # Priority 3: interactive prompt
    if (-not [Environment]::UserInteractive) {
        throw "Cannot prompt for SharePoint host (non-interactive). Set PLESSAS_SHAREPOINT_HOST=<your-tenant>.sharepoint.com and re-run."
    }

    Write-Host ''
    Write-Host 'Enter your Microsoft 365 SharePoint host (e.g. contoso.sharepoint.com).'
    Write-Host 'Find it in any SharePoint URL you own: https://<this-part>.sharepoint.com/...'
    $host_ = Read-Host 'Tenant SharePoint host'
    if (-not $host_) {
        throw 'No host entered.'
    }

    # Persist
    if (-not (Test-Path $configDir)) { New-Item -ItemType Directory -Path $configDir -Force | Out-Null }
    $existing = @{}
    if (Test-Path $configFile) {
        try {
            $existing = (Get-Content $configFile -Raw | ConvertFrom-Json) | ConvertTo-HashTable
        } catch {}
    }
    $existing['sharepoint_host'] = $host_
    $existing | ConvertTo-Json | Set-Content -Path $configFile -Encoding UTF8

    Write-Host "[OK]   Tenant host saved to $configFile" -ForegroundColor Green
    return $host_
}

# Helper for Step 7 (PSCustomObject -> hashtable)
function ConvertTo-HashTable {
    param([Parameter(ValueFromPipeline)]$obj)
    $out = @{}
    if ($obj) { $obj.PSObject.Properties | ForEach-Object { $out[$_.Name] = $_.Value } }
    return $out
}
```

- [ ] **Step 2: Test interactively (Windows or pwsh on Mac).**

```powershell
Remove-Item $env:USERPROFILE\.outlook-cli\config.json -ErrorAction SilentlyContinue
$env:PLESSAS_SHAREPOINT_HOST = $null
. ~/SourceCode/plessas-marketplace/installers/lib/tenant-prompt.ps1
$h = Get-TenantHost
# Type "test.sharepoint.com"
Write-Host "result: $h"
Get-Content $env:USERPROFILE\.outlook-cli\config.json
```

Expected: `{"sharepoint_host":"test.sharepoint.com"}` printed.

- [ ] **Step 3: Test the env-var override path.**

```powershell
$env:PLESSAS_SHAREPOINT_HOST = 'envvar.sharepoint.com'
. ~/SourceCode/plessas-marketplace/installers/lib/tenant-prompt.ps1
Write-Host "env: $(Get-TenantHost)"
```

Expected: `env: envvar.sharepoint.com`.

- [ ] **Step 4: Commit.**

```bash
git add installers/lib/tenant-prompt.ps1
git commit -m "feat(installer): add tenant-prompt.ps1 — env > config.json > interactive (PowerShell)"
```

### Task 2.3: Wire tenant prompt into auth-wizard.sh

**Files:**

- Modify: `installers/auth-wizard.sh`

- [ ] **Step 1: Add the source line near the top** of `installers/auth-wizard.sh`. Insert after line 11 (after `fail() { ... }`):

```bash
# Load tenant-prompt helper
source "$(dirname "$0")/lib/tenant-prompt.sh"
```

- [ ] **Step 2: Replace the hardcoded `--sharepoint-host` line.** Currently line 28:

```bash
outlook-cli login --sharepoint-host groupnbg.sharepoint.com || warn "outlook-cli login failed or was cancelled"
```

Change to:

```bash
local sp_host
sp_host=$(prompt_tenant) || fail "Could not resolve SharePoint host. Aborting."
outlook-cli login --sharepoint-host "$sp_host" || warn "outlook-cli login failed or was cancelled"
```

(Note: the `local` keyword only works inside a function. Since this is at script top level, drop `local`.)

Final replacement:

```bash
sp_host=$(prompt_tenant) || fail "Could not resolve SharePoint host. Aborting."
outlook-cli login --sharepoint-host "$sp_host" || warn "outlook-cli login failed or was cancelled"
```

- [ ] **Step 3: Smoke-test the wizard end-to-end on Mac.**

```bash
rm -f ~/.outlook-cli/config.json
unset PLESSAS_SHAREPOINT_HOST
~/SourceCode/plessas-marketplace/installers/auth-wizard.sh
# Enter a test host like "test.sharepoint.com" at the prompt
# (login itself will fail unless you actually have a tenant — that's fine for this test)
```

Expected: prompt for "Tenant SharePoint host:" appears before the browser opens; no `groupnbg.sharepoint.com` mentioned anywhere in output.

- [ ] **Step 4: Commit.**

```bash
git add installers/auth-wizard.sh
git commit -m "feat(auth-wizard): prompt for tenant host instead of hardcoding groupnbg"
```

### Task 2.4: Wire tenant prompt into auth-wizard.ps1

**Files:**

- Modify: `installers/auth-wizard.ps1`

- [ ] **Step 1: Add the source line near the top.** After the function declarations (after line 7):

```powershell
# Load tenant-prompt helper
. "$PSScriptRoot\lib\tenant-prompt.ps1"
```

- [ ] **Step 2: Replace the hardcoded `--sharepoint-host` line.** Currently line 25:

```powershell
outlook-cli login --sharepoint-host groupnbg.sharepoint.com
```

Change to:

```powershell
$spHost = Get-TenantHost
outlook-cli login --sharepoint-host $spHost
```

- [ ] **Step 3: Smoke-test in pwsh.**

```powershell
Remove-Item $env:USERPROFILE\.outlook-cli\config.json -ErrorAction SilentlyContinue
$env:PLESSAS_SHAREPOINT_HOST = $null
pwsh ~/SourceCode/plessas-marketplace/installers/auth-wizard.ps1
```

Expected: same prompt flow as Task 2.3.

- [ ] **Step 4: Commit.**

```bash
git add installers/auth-wizard.ps1
git commit -m "feat(auth-wizard.ps1): prompt for tenant host instead of hardcoding groupnbg"
```

### Task 2.5: Replace hardcoded sharepoint-host in MCP doctor.ts

**Why:** The bundled `outlook-bridge` MCP includes a `doctor` tool that reports auth status. Its error message hardcodes `groupnbg.sharepoint.com` in the suggested fix, leaking the maintainer's tenant in every teammate's MCP output.

**Files:**

- Modify: `plugins/mail/mcp-server/src/tools/doctor.ts`
- Test: `cd plugins/mail/mcp-server && npm run build && npm test`

- [ ] **Step 1: Read the current file** to find the exact string.

```bash
grep -n "groupnbg" ~/SourceCode/plessas-marketplace/plugins/mail/mcp-server/src/tools/doctor.ts
```

Expected: line 43 contains the hardcoded string.

- [ ] **Step 2: Replace with a config-or-placeholder lookup.** Edit the file to read from `~/.outlook-cli/config.json` if present:

```typescript
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

function suggestedTenantHost(): string {
  const configPath = path.join(os.homedir(), '.outlook-cli', 'config.json');
  try {
    const cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (cfg.sharepoint_host) return cfg.sharepoint_host as string;
  } catch {}
  return '<your-tenant>.sharepoint.com';
}
```

Then replace the literal `groupnbg.sharepoint.com` in the error message at line 43 with `${suggestedTenantHost()}` (template literal interpolation).

- [ ] **Step 3: Rebuild + test.**

```bash
cd ~/SourceCode/plessas-marketplace/plugins/mail/mcp-server
npm run build
npm test 2>&1 | tail -10
```

Expected: build OK, tests pass. If tests reference the old string, update them to match the new config-driven behavior.

- [ ] **Step 4: Commit.**

```bash
git add plugins/mail/mcp-server/src/tools/doctor.ts plugins/mail/mcp-server/dist/
git commit -m "fix(mail-mcp): read tenant host from config in doctor message"
```

### Task 2.6: Replace hardcoded sharepoint-host in plugin docs

**Why:** Three doc files mention `groupnbg.sharepoint.com` literally:

- `plugins/mail/QUICKSTART.md` — lines 38 and 134
- `shared/claude-md-template/team-claude-md.md` — line 116
- `plugins/mail/mcp-server/src/tools/doctor.ts` — handled in Task 2.5

**Files:**

- Modify: `plugins/mail/QUICKSTART.md`
- Modify: `shared/claude-md-template/team-claude-md.md`

- [ ] **Step 1: Find the exact occurrences.**

```bash
grep -rn "groupnbg.sharepoint.com" ~/SourceCode/plessas-marketplace/plugins/mail/QUICKSTART.md ~/SourceCode/plessas-marketplace/shared/claude-md-template/
```

- [ ] **Step 2: Edit `plugins/mail/QUICKSTART.md`** — replace each `groupnbg.sharepoint.com` with `<your-tenant>.sharepoint.com` and add this paragraph above the first occurrence:

```markdown
> **Tenant host:** the auth wizard will prompt you for your M365 tenant SharePoint host on first run (e.g. `contoso.sharepoint.com`). Find it in any SharePoint URL you own: `https://<this-part>.sharepoint.com/...`. The answer is persisted to `~/.outlook-cli/config.json` and reused on subsequent runs.
```

- [ ] **Step 3: Edit `shared/claude-md-template/team-claude-md.md`** — replace the `groupnbg.sharepoint.com` reference at line 116 with `<your-tenant>.sharepoint.com` and add a note that the auth wizard handles this.

- [ ] **Step 4: Verify zero remaining hits.**

```bash
grep -rn "groupnbg" ~/SourceCode/plessas-marketplace --include="*.md" --include="*.sh" --include="*.ps1" --include="*.ts"
```

Expected: zero results (or only matches inside `.git/`, `node_modules/`, which we filter).

- [ ] **Step 5: Commit.**

```bash
git add plugins/mail/QUICKSTART.md shared/claude-md-template/team-claude-md.md
git commit -m "docs: replace hardcoded groupnbg with placeholder + auth-wizard note"
```

---

## Phase 3 — Cross-platform gaps

### Task 3.1: Replace `/tmp/` paths with cross-platform tempdir

**Why:** Three files use literal `/tmp/...` paths. `/tmp/` exists on macOS and Linux but NOT on native Windows (Windows uses `%TEMP%`, typically `C:\Users\<u>\AppData\Local\Temp\`). When the agent reads `Args: { "out": "/tmp/mail_att" }` it will pass that literal path; on Windows it will create `C:\tmp\mail_att\` (allowed by mkdir but in a non-standard location) or fail outright depending on permissions.

The fix: use a marker like `${TMPDIR}` that the agent can resolve, or instruct the agent to use `os.path.join(tempfile.gettempdir(), 'mail_att')` semantics. Easiest for an agent reading markdown: write the path as `<TEMP_DIR>/mail_att` with a one-line note about resolution.

**Files:**

- Modify: `plugins/mail/commands/mail-review.md` — lines 123, 129, 137
- Modify: `plugins/mail/commands/inbox-briefing.md` — lines 68, 74
- Modify: `plugins/decks/commands/redesign-deck.md` — line 19

- [ ] **Step 1: Edit `plugins/mail/commands/mail-review.md`.**

Replace:

```
Args: { "id": "<Id>", "out": "/tmp/mail_att", "overwrite": true }
```

With:

```
Args: { "id": "<Id>", "out": "<TEMP_DIR>/mail_att", "overwrite": true }
```

Where `<TEMP_DIR>` is resolved by the agent as:

- macOS/Linux: `$TMPDIR` if set, else `/tmp`
- Windows: `$env:TEMP` (PowerShell) or `%TEMP%` (cmd)

Add a single line near the top of the file (after the frontmatter):

```markdown
> Path conventions: `<TEMP_DIR>` resolves to the OS temp directory (`$TMPDIR` or `/tmp` on macOS/Linux, `$env:TEMP` on Windows). Resolve before passing to tools.
```

Same for the cleanup line:

```diff
-Clean up temp files after extraction: `rm -rf /tmp/mail_att/*`
+Clean up temp files after extraction (cross-platform: use `find <TEMP_DIR>/mail_att -type f -delete` on Mac/Linux or `Remove-Item $env:TEMP\mail_att\* -Recurse -Force` on Windows).
```

And the markitdown example:

```diff
-markitdown "/tmp/mail_att/filename.pptx" | head -200
+markitdown "<TEMP_DIR>/mail_att/filename.pptx" | head -200
```

- [ ] **Step 2: Edit `plugins/mail/commands/inbox-briefing.md`** — replace the `/tmp/mail_att` references at lines 68 and 74 with `<TEMP_DIR>/mail_att`. Add the same path-conventions note near the top.

- [ ] **Step 3: Edit `plugins/decks/commands/redesign-deck.md`** — replace the `/tmp/deck_extracted.md` reference at line 19 with `<TEMP_DIR>/deck_extracted.md`. Add the same note.

- [ ] **Step 4: Verify no remaining `/tmp/` references in plugins.**

```bash
grep -rn "/tmp/" ~/SourceCode/plessas-marketplace/plugins/ --include="*.md"
```

Expected: zero results, or only in code-fenced literal Bash examples that are explicitly OS-tagged.

- [ ] **Step 5: Commit.**

```bash
git add plugins/mail/commands/mail-review.md plugins/mail/commands/inbox-briefing.md plugins/decks/commands/redesign-deck.md
git commit -m "fix(plugins): use <TEMP_DIR> placeholder instead of /tmp for cross-platform"
```

### Task 3.2: Expand single-OS clipboard example into per-OS code blocks

**Why:** `mail-review.md` lines 299-308 and `email-handler.md` lines 358-364 already document three OS-specific clipboard recipes — but the only fenced code block shown is the macOS `textutil | pbcopy` recipe. An agent skimming the document grabs that block and runs it on Windows, where `textutil` and `pbcopy` don't exist.

The fix: replace the single mac code block with three labeled blocks (one per OS). Same content the inline list already mentions; just promote each to its own code block so the agent picks the right one.

**Files:**

- Modify: `plugins/mail/commands/mail-review.md` — block at lines 305-309
- Modify: `plugins/mail/agents/email-handler.md` — same block

- [ ] **Step 1: Edit `plugins/mail/commands/mail-review.md`.** Replace the single `# macOS example:` block with:

````markdown
   **macOS:**
   ```bash
   printf '<html><body style="font-family: Aptos, sans-serif; font-size: 12pt; color: #404040; text-align: justify;">Draft body here</body></html>' \
     | textutil -stdin -format html -convert rtf -stdout | pbcopy
   ```

   **Windows (PowerShell):**
   ```powershell
   $html = '<html><body style="font-family: Aptos, sans-serif; font-size: 12pt; color: #404040; text-align: justify;">Draft body here</body></html>'
   $html | Set-Clipboard -AsHtml
   ```

   **Linux (X11 with xclip):**
   ```bash
   printf '<html><body style="font-family: Aptos, sans-serif; font-size: 12pt; color: #404040; text-align: justify;">Draft body here</body></html>' \
     | xclip -selection clipboard -t text/html
   ```
````

- [ ] **Step 2: Edit `plugins/mail/agents/email-handler.md`** — apply the same three-block replacement at lines 358-364.

- [ ] **Step 3: Verify by skimming the rendered Markdown.** No fenced bash block should be presented as the single-OS option.

- [ ] **Step 4: Commit.**

```bash
git add plugins/mail/commands/mail-review.md plugins/mail/agents/email-handler.md
git commit -m "fix(mail): show clipboard recipes as per-OS code blocks (not mac-only)"
```

### Task 3.3: Guard AppleScript fallbacks in meeting-intelligence agent

**Why:** `plugins/meetings/agents/meeting-intelligence.md` contains 3 fenced AppleScript blocks (lines 62-104, 154-176, 181-?) presented as "EMERGENCY FALLBACK" paths. They're not OS-guarded — an agent on Windows reads them and tries to run `osascript`, which doesn't exist, getting a confusing `command not found`.

**Files:**

- Modify: `plugins/meetings/agents/meeting-intelligence.md`
- Modify: `plugins/meetings/shared/calendar-access.md`

- [ ] **Step 1: Audit the exact AppleScript block locations.**

```bash
grep -n "osascript\|tell application" ~/SourceCode/plessas-marketplace/plugins/meetings/agents/meeting-intelligence.md ~/SourceCode/plessas-marketplace/plugins/meetings/shared/calendar-access.md
```

- [ ] **Step 2: For each AppleScript fenced block, prepend a guard line.** For example, the block at line 62 currently starts:

````markdown
osascript <<'APPLESCRIPT'
tell application "Microsoft Outlook"
...
APPLESCRIPT
````

Change to:

````markdown
**macOS only — skip on Windows/Linux:**

```bash
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo "Skipping AppleScript fallback — not on macOS." >&2
  exit 0
fi
osascript <<'APPLESCRIPT'
tell application "Microsoft Outlook"
...
APPLESCRIPT
```
````

Apply to all 3 blocks in `meeting-intelligence.md` and any in `calendar-access.md`.

- [ ] **Step 3: Add a top-of-file note** (after the frontmatter) explaining the macOS-only nature of all AppleScript fallbacks:

```markdown
> **Cross-platform note:** AppleScript fallback paths in this agent (`tell application "Microsoft Outlook"`, `tell application "Mail"`, etc.) only run on macOS. On Windows or Linux, the agent should rely on `mcp__outlook-bridge__*` tools and skip the AppleScript blocks entirely. The OS guards are explicit at each block.
```

- [ ] **Step 4: Verify all blocks now have guards.**

```bash
# Each AppleScript block should be preceded by an OSTYPE check within ~5 lines
grep -B5 "osascript <<" ~/SourceCode/plessas-marketplace/plugins/meetings/agents/meeting-intelligence.md | grep "OSTYPE"
```

Expected: count of OSTYPE matches ≥ count of `osascript <<` matches.

- [ ] **Step 5: Commit.**

```bash
git add plugins/meetings/agents/meeting-intelligence.md plugins/meetings/shared/calendar-access.md
git commit -m "fix(meetings): guard AppleScript fallbacks with OSTYPE check"
```

### Task 3.4: Auto-create `~/.claude/presentations/{pending,reviewed}/` on first use

**Why:** The `decks` plugin's "self-improvement loop" expects `~/.claude/presentations/pending/` and `~/.claude/presentations/reviewed/` to exist. The renderer auto-creates `pending/` (per `graphics-renderer.md:905`), but `create-presentation.md:18` *checks* the dir without creating it. On first-ever run, the check returns "no drafts pending" — that's fine — but the architecture intent is for the dir to exist so the user can manually drop edits there too. Same for `reviewed/`.

**Files:**

- Modify: `plugins/decks/commands/create-presentation.md`
- Modify: `plugins/decks/commands/presentation-review.md`
- Modify: `plugins/decks/orchestrator/nbg-presenter/AGENT.md`

- [ ] **Step 1: Add an idempotent dir-creation step** in `create-presentation.md` near the top of the orchestrator instructions. Before the "Check `~/.claude/presentations/pending/`" line:

```markdown
0. **Ensure persistence dirs exist** (idempotent — does nothing if already present):
   ```bash
   mkdir -p ~/.claude/presentations/pending ~/.claude/presentations/reviewed
   ```

```

- [ ] **Step 2: Add the same step at the top of `presentation-review.md`.**

- [ ] **Step 3: Verify in `nbg-presenter/AGENT.md`** at line 380 that the dir creation is documented as the renderer's responsibility (it already is — leave intact).

- [ ] **Step 4: Test.**

```bash
rm -rf ~/.claude/presentations/
# (then run /create-presentation in a Claude session)
ls -la ~/.claude/presentations/
```

Expected: both `pending/` and `reviewed/` exist after first run.

- [ ] **Step 5: Commit.**

```bash
git add plugins/decks/commands/create-presentation.md plugins/decks/commands/presentation-review.md
git commit -m "fix(decks): auto-create ~/.claude/presentations/{pending,reviewed} dirs"
```

---

## Phase 4 — Move mail-pro to plessas-lab

`mail-pro` has two structural maintainer-only properties:

1. `plugins/mail-pro/scripts/style-sync.py:42` hardcodes `SENDER_FILTER = "%plessas%"`.
2. Six `.md` files under `plugins/mail-pro/` reference `~/SourceCode/second-brain/data/brain.db` — a private repo.

Per maintainer decision, mail-pro stays as-is (do not parameterize) but moves to `plessas-lab` (the maintainer's personal/lab marketplace, currently not shared but potentially shareable later). This phase mirrors a `git mv plugin → other repo` workflow without losing history.

### Task 4.1: Copy mail-pro to plessas-lab/plugins/mail-pro/

**Files:**

- Source: `~/SourceCode/plessas-marketplace/plugins/mail-pro/` (entire directory)
- Destination: `~/SourceCode/plessas-lab/plugins/mail-pro/`

- [ ] **Step 1: Verify the source contents.**

```bash
find ~/SourceCode/plessas-marketplace/plugins/mail-pro -type f | sort
```

Expected: 5 files (README.md, scripts/style-sync.py, .claude-plugin/plugin.json, commands/comm-report.md, commands/style-rebuild.md).

- [ ] **Step 2: Copy the directory tree.**

```bash
cp -r ~/SourceCode/plessas-marketplace/plugins/mail-pro ~/SourceCode/plessas-lab/plugins/mail-pro
```

- [ ] **Step 3: Verify the copy.**

```bash
diff -rq ~/SourceCode/plessas-marketplace/plugins/mail-pro ~/SourceCode/plessas-lab/plugins/mail-pro
```

Expected: zero output (identical tree).

- [ ] **Step 4: Stage in the lab repo.**

```bash
cd ~/SourceCode/plessas-lab
git add plugins/mail-pro/
git status
```

Expected: 5 new files staged under `plugins/mail-pro/`.

- [ ] **Step 5: Defer commit until Task 4.2.**

### Task 4.2: Add mail-pro entry to plessas-lab marketplace.json

**Why:** The `plessas-lab` `marketplace.json` uses a different schema from `plessas-marketplace` — per-plugin entries declare `version`, `author`, `license`, `keywords` inline instead of relying on the plugin's own `plugin.json`. Add the mail-pro entry to match this pattern.

**Files:**

- Modify: `~/SourceCode/plessas-lab/.claude-plugin/marketplace.json`

- [ ] **Step 1: Read the existing lab marketplace.json schema** (already verified — it has 5 plugins, each with `name/source/description/version/author/license/keywords`).

- [ ] **Step 2: Add the mail-pro entry** between the `chat-watch` entry and the closing `]`. Insert after line 91 (the chat-watch closing brace):

```json
    },
    {
      "name": "mail-pro",
      "source": "./plugins/mail-pro",
      "description": "Maintainer-only companion to a `mail` plugin. Adds /comm-report (relationship analytics) and /style-rebuild (corpus-driven style guide). Requires the maintainer's private second-brain SQLite DB at ~/SourceCode/second-brain/data/brain.db. Not portable.",
      "version": "1.0.0",
      "author": {
        "name": "weirdapps"
      },
      "license": "MIT",
      "keywords": [
        "mail",
        "analytics",
        "internal"
      ]
    }
```

(Final closing `]` and `}` stay as-is.)

- [ ] **Step 3: Bump lab marketplace metadata version.**

```diff
-    "version": "1.1.0",
+    "version": "1.2.0",
```

- [ ] **Step 4: Validate the JSON.**

```bash
python3 -c "import json; json.load(open(__import__('os').path.expanduser('~/SourceCode/plessas-lab/.claude-plugin/marketplace.json')); print('OK')"
```

Expected: `OK`.

- [ ] **Step 5: Commit on plessas-lab.**

```bash
cd ~/SourceCode/plessas-lab
git add .claude-plugin/marketplace.json plugins/mail-pro/
git commit -m "feat: add mail-pro plugin (moved from plessas-marketplace)

mail-pro is maintainer-only — depends on the private second-brain SQLite
DB and hardcodes a sender filter. Lives in the lab marketplace because
it's not shareable as-is, but the lab plays host to other maintainer
tools too."
```

### Task 4.3: Remove mail-pro from plessas-marketplace marketplace.json

**Files:**

- Modify: `~/SourceCode/plessas-marketplace/.claude-plugin/marketplace.json`

- [ ] **Step 1: Open the file** and locate the `mail-pro` entry (lines 22-28 currently).

- [ ] **Step 2: Delete that entry** including the comma separator. The block to remove:

```json
    {
      "name": "mail-pro",
      "version": "1.0.0",
      "category": "communications",
      "source": "./plugins/mail-pro",
      "description": "Optional companion to `mail` for users with the second-brain knowledge store. Adds /comm-report (relationship analytics) and /style-rebuild (corpus-driven style guide). Requires private second-brain repo access."
    },
```

After deletion, ensure the `meetings` entry (which previously came after) still has a leading comma if needed.

- [ ] **Step 3: Validate JSON.**

```bash
python3 -c "import json; m=json.load(open(__import__('os').path.expanduser('~/SourceCode/plessas-marketplace/.claude-plugin/marketplace.json')); print('plugins:', [p['name'] for p in m['plugins']])"
```

Expected: `plugins: ['decks', 'mail', 'meetings', 'chat', 'excel', 'docs']` — note: 6 plugins, no mail-pro.

- [ ] **Step 4: Defer commit until Task 4.4.**

### Task 4.4: Delete plugins/mail-pro/ from plessas-marketplace

**Files:**

- Delete: `~/SourceCode/plessas-marketplace/plugins/mail-pro/` (entire directory)

- [ ] **Step 1: Confirm the lab copy is complete and committed.** Re-run the diff:

```bash
diff -rq ~/SourceCode/plessas-marketplace/plugins/mail-pro ~/SourceCode/plessas-lab/plugins/mail-pro
```

Expected: zero output. If non-zero, STOP and reconcile before deleting.

- [ ] **Step 2: Confirm Task 4.2 commit is in plessas-lab.**

```bash
cd ~/SourceCode/plessas-lab && git log --oneline -1 -- plugins/mail-pro/
```

Expected: a commit message mentioning "moved from plessas-marketplace".

- [ ] **Step 3: Remove from plessas-marketplace.**

```bash
cd ~/SourceCode/plessas-marketplace
git rm -r plugins/mail-pro/
```

- [ ] **Step 4: Commit the marketplace.json change + plugin removal together.**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore: remove mail-pro plugin (moved to plessas-lab)

mail-pro was maintainer-only — hardcoded SENDER_FILTER, dependency on
the private second-brain SQLite DB. Now lives in plessas-lab where
that constraint is acceptable."
```

### Task 4.5: Update mail-pro README to reflect its new home

**Files:**

- Modify: `~/SourceCode/plessas-lab/plugins/mail-pro/README.md`

- [ ] **Step 1: Open the README** and add a top callout explaining the marketplace move:

```markdown
> **Maintainer-only.** This plugin requires the maintainer's private `second-brain` SQLite database at `~/SourceCode/second-brain/data/brain.db` and hardcodes `SENDER_FILTER = "%plessas%"` in `scripts/style-sync.py`. It's installed from the `plessas-lab` marketplace because it's not portable as-is. If you're not the maintainer, the `mail` plugin in `plessas-marketplace` covers the cross-platform use cases.
```

- [ ] **Step 2: Update any internal references** that pointed at the marketplace's `~/SourceCode/plessas-marketplace/...` path. For mail-pro, these are mostly in `commands/comm-report.md` and `commands/style-rebuild.md` — verify none reference `plessas-marketplace` explicitly:

```bash
grep -rn "plessas-marketplace" ~/SourceCode/plessas-lab/plugins/mail-pro/
```

Expected: zero hits.

- [ ] **Step 3: Commit.**

```bash
cd ~/SourceCode/plessas-lab
git add plugins/mail-pro/README.md
git commit -m "docs(mail-pro): callout maintainer-only status, document move from plessas-marketplace"
```

---

## Phase 5 — Documentation

### Task 5.1: Add Windows install commands as code blocks in README.md

**Why:** Top-level README.md mentions "Windows: open PowerShell and run …" parenthetically (line ~69) but never as a fenced code block. A user copying-pasting from the README cannot distinguish "step you run on Mac" from "step you run on Windows."

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Read the current install section** to map structure.

```bash
sed -n '40,100p' ~/SourceCode/plessas-marketplace/README.md
```

- [ ] **Step 2: Restructure the install section** to side-by-side OS panes.

Replace the current single-flow install with:

````markdown
## Install

### Prerequisites (both OSes)

- **Claude Code** — install from https://claude.ai/claude-code
- **Node.js 20+** — install from https://nodejs.org/
- **Python 3.11+** — install from https://www.python.org/downloads/
- **Git** — `git --version` should report v2.30+
- **Chrome or Edge browser** — required for `outlook-cli` and `teams-cli` first-time auth (Playwright drives the browser session capture)

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.sh | bash
~/.claude/plugins/marketplaces/plessas-marketplace/installers/auth-wizard.sh
~/.claude/plugins/marketplaces/plessas-marketplace/installers/status.sh
```

### Windows (PowerShell)

```powershell
iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.ps1 | iex
& "$env:USERPROFILE\.claude\plugins\marketplaces\plessas-marketplace\installers\auth-wizard.ps1"
& "$env:USERPROFILE\.claude\plugins\marketplaces\plessas-marketplace\installers\status.ps1"
```

> **First-run prompt:** the auth wizard will ask for your Microsoft 365 SharePoint host (e.g. `contoso.sharepoint.com`). The answer is saved to `~/.outlook-cli/config.json` and reused. Override with `PLESSAS_SHAREPOINT_HOST=...` env var if needed.
````

- [ ] **Step 3: Verify the rendered Markdown** by viewing in a Markdown previewer. The OS sections should be visually distinct.

- [ ] **Step 4: Commit.**

```bash
git add README.md
git commit -m "docs(README): show Mac and Windows install as labeled code blocks; add Chrome/Edge prereq"
```

### Task 5.2: Add PowerShell troubleshooting recipes to docs/TROUBLESHOOTING.md

**Why:** `docs/TROUBLESHOOTING.md` (321 lines) has 2 mentions of Windows. All recipes are Bash. A Windows user hitting `outlook-cli not on PATH` or `npm link permission denied` has no recipe.

**Files:**

- Modify: `docs/TROUBLESHOOTING.md`

- [ ] **Step 1: For each existing Bash recipe, add a labeled `**Windows (PowerShell):**` follow-on block.** The most-needed recipes:

  1. `outlook-cli not on PATH` — Mac fix is `echo 'export PATH=$(npm prefix -g)/bin:$PATH' >> ~/.zshrc`. Windows equivalent:

     ```powershell
     $npmPrefix = npm prefix -g
     [Environment]::SetEnvironmentVariable('PATH', "$npmPrefix\bin;$env:PATH", 'User')
     # Restart PowerShell
     ```

  2. `npm link permission denied` — Mac fix is `sudo npm link`. Windows equivalent:

     ```powershell
     # Run PowerShell as Administrator, then:
     cd $env:USERPROFILE\.claude\plugins\marketplaces\plessas-marketplace\installers\deps\outlook-access
     npm link
     ```

  3. `outlook-cli auth-check fails after login` — same Bash recipe applies; add note that on Windows the Playwright session may be stored at `%LOCALAPPDATA%\Playwright` (not `~/Library/Application Support/Playwright`).
  4. `Python venv not found` — Mac fix is `python3 -m venv .venv`. Windows equivalent:

     ```powershell
     python -m venv .venv
     .\.venv\Scripts\pip install -r requirements.txt
     ```

  5. `tenant host wrong` — both OSes: `rm ~/.outlook-cli/config.json` (Mac/Linux) or `Remove-Item $env:USERPROFILE\.outlook-cli\config.json` (Windows), then re-run auth wizard.
  6. `MCP server failed to start` — both OSes: `cd plugins/mail/mcp-server && rm -rf node_modules dist && npm install && npm run build`. On Windows: prepend `Remove-Item -Recurse -Force` instead of `rm -rf`.

- [ ] **Step 2: Add a "Windows-specific gotchas" section at the bottom** of `TROUBLESHOOTING.md`:

```markdown
## Windows-specific gotchas

- **Long path names:** Windows defaults to a 260-char path limit. The marketplace install dir is short, but if you nest `npm install` inside `installers/deps/<repo>/node_modules/...`, you may hit the limit. Enable long path support:
  ```powershell
  # As Administrator:
  New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
  git config --system core.longpaths true
  ```

- **Execution policy:** PowerShell may refuse to run `.ps1` scripts. Allow them for the current user:

  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

- **Browser channel:** `outlook-cli`/`teams-cli` use Playwright's `channel: "chrome"`. If you have only Edge installed, set `PLAYWRIGHT_BROWSER_CHANNEL=msedge`.

```

- [ ] **Step 3: Commit.**

```bash
git add docs/TROUBLESHOOTING.md
git commit -m "docs(troubleshooting): add PowerShell recipes + Windows-specific gotchas"
```

### Task 5.3: Add NBG-decks disclosure to README

**Why:** Per maintainer decision, the `decks` plugin remains NBG-branded. A teammate cloning the marketplace needs to know upfront so they don't get surprised by NBG colors, the NBG-Template-GR.pptx, and the storyline-architect agent identifying as "NBG presentation director."

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Add a "Per-plugin notes" section** after the install section. The decks entry should read:

```markdown
## Per-plugin notes

- **`decks`** is NBG-branded. The brand-system docs (`plugins/decks/shared/brand-system/{colors,layouts,typography,charts}.md`), the storyline-architect agent persona, and the `NBG-Template-GR.pptx` template all assume NBG corporate identity. If you're not at NBG, the framework is still useful (storyline → storyboard → renderer → QA), but you'll want to swap the template, replace the color palette in `colors.md`, and edit the agent prompts to reference your brand. The `decks` agents are designed to be brand-aware via the brand-system docs, so most of the customization is a single search-and-replace of "NBG" with your brand name.
- **`mail`, `meetings`, `chat`, `excel`, `docs`** are brand-agnostic.
- **`mail-pro`** lives in `plessas-lab` (maintainer-only — depends on private SQLite knowledge store).
```

- [ ] **Step 2: Commit.**

```bash
git add README.md
git commit -m "docs(README): disclose NBG branding in decks plugin upfront"
```

### Task 5.4: Update CHANGELOG.md

**Files:**

- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add a new top entry** dated today:

```markdown
## [2.1.0] — 2026-05-11

### Added
- `installers/lib/tenant-prompt.{sh,ps1}` — first-run prompt for M365 SharePoint host, persisted to `~/.outlook-cli/config.json`, env-overridable via `PLESSAS_SHAREPOINT_HOST`
- Python venv install on Windows (`install.ps1` parity with `install.sh`)
- Windows install code blocks + Chrome/Edge prereq + NBG-decks disclosure in README
- PowerShell troubleshooting recipes + Windows-specific gotchas section in `docs/TROUBLESHOOTING.md`
- `<TEMP_DIR>` placeholder convention for cross-platform temp paths

### Changed
- `outlook-bridge` MCP: pinned `typescript ~5.9`, `@types/node ^22`, `vitest ^3`, added `engines.node >=20`
- `teams-bridge` MCP: same dep pins
- `outlook-cli` and `teams-cli` GitHub deps now pinned to specific commit SHAs (no more drift on every install)
- `auth-wizard.{sh,ps1}` no longer hardcode `groupnbg.sharepoint.com` — now prompt
- `outlook-bridge` MCP `doctor` tool reads tenant from config instead of hardcoding
- `mail/commands/mail-review.md` + `mail/agents/email-handler.md` clipboard recipes shown as per-OS code blocks
- `meetings/agents/meeting-intelligence.md` AppleScript fallbacks now OSTYPE-guarded

### Removed
- `mail-pro` plugin moved to `plessas-lab` (was maintainer-only — depended on private second-brain DB and hardcoded sender filter)

### Fixed
- `decks` plugin Python tools no longer fail on Windows (venv now built by installer)
- `decks` self-improvement loop dirs (`~/.claude/presentations/{pending,reviewed}/`) now auto-created
```

- [ ] **Step 2: Bump marketplace.json version.**

```diff
   "name": "plessas-marketplace",
   "description": "Cross-platform Claude Code plugins for productivity at NBG: decks, mail, meetings, chat, excel, docs.",
+  "metadata": {
+    "version": "2.1.0"
+  },
   "owner": { "name": "weirdapps" },
```

(Verify the existing schema — if `metadata.version` doesn't currently exist in marketplace.json, add it; if it does, just bump.)

- [ ] **Step 3: Commit.**

```bash
git add CHANGELOG.md .claude-plugin/marketplace.json
git commit -m "chore: bump marketplace to 2.1.0; document share-readiness changes"
```

---

## Phase 6 — Verification

### Task 6.1: Run PII gauntlet

**Files:** none modified

- [ ] **Step 1: Execute the gauntlet in CI mode.**

```bash
cd ~/SourceCode/plessas-marketplace
bash installers/pii-gauntlet.sh --mode=ci 2>&1 | tail -20
```

Expected: exit code 0, output contains no `[FAIL]` lines.

- [ ] **Step 2: If new failures appear** (e.g., `groupnbg` reference still in some doc we missed), grep for the failing pattern and fix:

```bash
grep -rln "groupnbg" --include="*.md" --include="*.sh" --include="*.ps1" --include="*.ts"
```

- [ ] **Step 3: Re-run gauntlet** until clean.

### Task 6.2: Run plugin manifest validator

**Files:** none modified

- [ ] **Step 1: Locate the validator.**

```bash
find ~/SourceCode/plessas-marketplace -name "validate*.py" -o -name "validate*.sh" 2>/dev/null
```

- [ ] **Step 2: Run it.**

```bash
python3 ~/SourceCode/plessas-marketplace/scripts/validate_consistency.py 2>&1
```

Expected: exit 0, output ends with `OK` or `All N plugins valid`.

- [ ] **Step 3: Run the GitHub Actions workflow locally if `act` is installed.**

```bash
command -v act && act -W .github/workflows/validate-plugins.yml --dryrun
```

### Task 6.3: Fresh-clone install on Mac

**Files:** none modified

- [ ] **Step 1: Tear down the existing install.**

```bash
rm -rf ~/.claude/plugins/marketplaces/plessas-marketplace
rm -f ~/.outlook-cli/config.json
unset PLESSAS_SHAREPOINT_HOST
```

- [ ] **Step 2: Run the installer from the local working tree** (don't curl from GitHub yet — we want to test the in-progress branch).

```bash
bash ~/SourceCode/plessas-marketplace/installers/install.sh 2>&1 | tee /tmp/install-mac.log
```

Expected: ends with `Installation complete!`, no `[FAIL]` lines.

- [ ] **Step 3: Run the auth wizard** with a fake tenant host (don't actually log in).

```bash
~/SourceCode/plessas-marketplace/installers/auth-wizard.sh
# At prompt, type: test.sharepoint.com
# Then Ctrl+C the browser launch
```

Expected: prompt appears, no reference to `groupnbg`.

- [ ] **Step 4: Run status.**

```bash
~/SourceCode/plessas-marketplace/installers/status.sh
```

Expected: green checks for installed components.

- [ ] **Step 5: Smoke-test a plugin** that doesn't need auth:

```bash
# In Claude Code session
/plugin list
# Confirm decks, mail, meetings, chat, excel, docs are installed
```

### Task 6.4: Fresh-clone install on Windows (or pwsh-on-Mac)

**Files:** none modified

- [ ] **Step 1: Tear down + run the PowerShell installer.**

```powershell
Remove-Item -Recurse -Force $env:USERPROFILE\.claude\plugins\marketplaces\plessas-marketplace -ErrorAction SilentlyContinue
Remove-Item $env:USERPROFILE\.outlook-cli\config.json -ErrorAction SilentlyContinue
$env:PLESSAS_SHAREPOINT_HOST = $null

pwsh ~/SourceCode/plessas-marketplace/installers/install.ps1 2>&1 | Tee-Object /tmp/install-win.log
```

Expected: ends with `Installation complete!`. The "Installing Python dependencies for decks..." section appears (Task 1.3 verification).

- [ ] **Step 2: Run auth wizard.**

```powershell
pwsh ~/SourceCode/plessas-marketplace/installers/auth-wizard.ps1
# At prompt, type: test.sharepoint.com
```

Expected: prompt, no reference to `groupnbg`.

- [ ] **Step 3: Verify Python venv exists.**

```powershell
ls ~/.claude/plugins/marketplaces/plessas-marketplace/plugins/decks/tools/nbg-presentation/.venv
```

Expected: `bin/` (Mac/Linux pwsh) or `Scripts/` (Windows pwsh) directory present.

### Task 6.5: Update presentation-self-improvement-loop test

**Files:** none modified

- [ ] **Step 1: Confirm the auto-create works.**

```bash
rm -rf ~/.claude/presentations/
# Run /create-presentation in a Claude session with a 1-slide test deck
ls ~/.claude/presentations/pending/
```

Expected: directory exists and contains a draft record JSON.

### Task 6.6: Final commit + push

- [ ] **Step 1: Verify git status is clean.**

```bash
cd ~/SourceCode/plessas-marketplace && git status
```

- [ ] **Step 2: Push the branch.**

```bash
git push origin <branch-name>
```

- [ ] **Step 3: Open a PR** with the title "Share-readiness: Mac+Windows install, tenant prompt, mail-pro move".

- [ ] **Step 4: Wait for CI to pass** (PII gauntlet, validate-plugins, CodeQL, SonarCloud).

- [ ] **Step 5: Merge to master.** Tag as `v2.1.0`.

```bash
git tag v2.1.0
git push --tags
```

---

## Self-review checklist

Before marking the plan complete, the executing engineer should verify:

- [ ] **Spec coverage:** Every audit finding listed in the source critical-audit (the conversation that produced this plan) has a corresponding task here, OR is explicitly listed in the "Out of scope" section above. Check by skimming the audit's "What I'd actually do" list against the Phase headings.

- [ ] **No placeholders:** Search the plan for `TBD`, `TODO`, `implement later`, `add appropriate error handling`, `similar to Task N`. Zero hits expected.

- [ ] **Path consistency:** Every `~/SourceCode/plessas-marketplace/...` reference in the plan resolves to an actual file (or a file the plan creates). Spot-check 5 random paths.

- [ ] **OS coverage:** Every install/build step has both a Mac/Linux command and a Windows/PowerShell command (where applicable).

- [ ] **Verification commands:** Every code change has a "verify by running X" step with expected output.

- [ ] **Frequent commits:** Each task ends in a `git commit` step. No multi-task batched commits.

---

## Estimated effort

- Phase 1: 4 hours (~4 tasks, dep version pinning + venv block)
- Phase 2: 6 hours (~6 tasks, tenant prompt across sh/ps1/MCP/docs)
- Phase 3: 4 hours (~4 tasks, cross-platform doc edits)
- Phase 4: 2 hours (~5 tasks, mail-pro migration; minor edits to existing files)
- Phase 5: 4 hours (~4 tasks, README + TROUBLESHOOTING + CHANGELOG)
- Phase 6: 4 hours (verification on both OSes)

**Total: ~24 hours / ~3 working days for one engineer.**
