# plessas-marketplace installer (Windows PowerShell)
# Usage: iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/main/installers/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$RepoUrl    = 'https://github.com/weirdapps/plessas-marketplace.git'
$InstallDir = Join-Path $env:USERPROFILE '.claude\plugins\marketplaces\plessas-marketplace'
$ClaudeMd   = Join-Path $env:USERPROFILE '.claude\CLAUDE.md'

function Write-Ok   { param($msg) Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }

Write-Host '========================================'
Write-Host '  plessas-marketplace installer'
Write-Host '========================================'
Write-Host ''

# --- Prerequisites ---
Write-Host 'Checking prerequisites...'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Fail 'git not found. Install: https://git-scm.com/downloads' }
Write-Ok "git $(git --version)"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Write-Fail 'Node.js not found. Install: https://nodejs.org/ (v20+)' }
$nodeVer = (node --version) -replace 'v','' -split '\.' | Select-Object -First 1
if ([int]$nodeVer -lt 20) { Write-Fail "Node.js v$nodeVer found, need 20+. Update: https://nodejs.org/" }
Write-Ok "Node.js $(node --version)"

if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Ok "Python $(python --version 2>&1 | ForEach-Object { $_ -replace 'Python ','' }) (for decks plugin)"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    Write-Ok "Python3 $(python3 --version 2>&1 | ForEach-Object { $_ -replace 'Python ','' }) (for decks plugin)"
} else {
    Write-Warn 'Python not found. decks plugin requires it. Install: https://www.python.org/downloads/'
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { Write-Fail 'Claude Code not found. Install: https://claude.ai/claude-code' }
Write-Ok 'Claude Code found'

Write-Host ''

# --- Clone or update ---
if (Test-Path (Join-Path $InstallDir '.git')) {
    Write-Host 'Marketplace already installed. Updating...'
    Push-Location $InstallDir
    git pull --ff-only 2>&1 | Select-Object -Last 3
    Pop-Location
    Write-Ok 'Updated to latest'
} else {
    Write-Host 'Cloning plessas-marketplace...'
    $parentDir = Split-Path $InstallDir -Parent
    if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Path $parentDir -Force | Out-Null }
    git clone $RepoUrl $InstallDir 2>&1 | Select-Object -Last 3
    Write-Ok "Cloned to $InstallDir"
}

Push-Location $InstallDir

# --- Build MCP servers ---
Write-Host ''
Write-Host 'Building MCP servers...'

if (Test-Path 'plugins\mail\mcp-server') {
    Write-Host '  Building outlook-bridge MCP...'
    Push-Location 'plugins\mail\mcp-server'
    npm install --silent 2>&1 | Out-Null
    npm run build --silent 2>&1 | Out-Null
    Pop-Location
    Write-Ok 'outlook-bridge MCP built'
}

if (Test-Path 'plugins\chat\mcp-server') {
    Write-Host '  Building teams-bridge MCP...'
    Push-Location 'plugins\chat\mcp-server'
    npm install --silent 2>&1 | Out-Null
    npm run build --silent 2>&1 | Out-Null
    Pop-Location
    Write-Ok 'teams-bridge MCP built'
}

# --- Check for outlook-cli and teams-cli ---
Write-Host ''
if (-not (Get-Command outlook-cli -ErrorAction SilentlyContinue)) {
    Write-Warn 'outlook-cli not found. Mail plugin requires it.'
    Write-Host '  Install: git clone https://github.com/weirdapps/outlook-access.git && cd outlook-access && npm install && npm run build && npm link'
} else {
    Write-Ok 'outlook-cli found'
}

if (-not (Get-Command teams-cli -ErrorAction SilentlyContinue)) {
    Write-Warn 'teams-cli not found. Chat plugin requires it.'
    Write-Host '  Install: git clone https://github.com/weirdapps/teams-access.git && cd teams-access && npm install && npm run build && npm link'
} else {
    Write-Ok 'teams-cli found'
}

# --- Drop CLAUDE.md template ---
Write-Host ''
if (-not (Test-Path $ClaudeMd)) {
    Write-Host 'No existing CLAUDE.md found. Installing team template...'
    $templateDir = Split-Path $ClaudeMd -Parent
    if (-not (Test-Path $templateDir)) { New-Item -ItemType Directory -Path $templateDir -Force | Out-Null }
    Copy-Item (Join-Path $InstallDir 'shared\claude-md-template\team-claude-md.md') $ClaudeMd -Encoding UTF8
    Write-Ok "Team CLAUDE.md installed at $ClaudeMd"
    Write-Host '  Please edit it and replace the << REPLACE >> sections with your details.'
} else {
    Write-Ok "Existing CLAUDE.md found — not overwriting. See $InstallDir\shared\claude-md-template\team-claude-md.md"
}

Pop-Location

# --- Done ---
Write-Host ''
Write-Host '========================================'
Write-Host '  Installation complete!' -ForegroundColor Green
Write-Host '========================================'
Write-Host ''
Write-Host "Next steps:"
Write-Host "  1. Run the auth wizard:  $InstallDir\installers\auth-wizard.ps1"
Write-Host "  2. Check status:         $InstallDir\installers\status.ps1"
Write-Host "  3. Open Claude Code and try: /mail-briefing"
Write-Host ''
Write-Host "Documentation: $InstallDir\docs\"
