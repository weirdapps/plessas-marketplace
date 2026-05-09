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

# --- Install outlook-cli and teams-cli ---
# Both CLIs live in their own repos (weirdapps/outlook-access, weirdapps/teams-access).
# We clone them into installers\deps inside the marketplace, build, and `npm link`
# so `outlook-cli` and `teams-cli` are available on PATH.
Write-Host ''
Write-Host 'Installing required CLIs (outlook-cli, teams-cli)...'

$DepsDir = Join-Path $InstallDir 'installers\deps'
if (-not (Test-Path $DepsDir)) { New-Item -ItemType Directory -Path $DepsDir -Force | Out-Null }

function Install-CliFromRepo {
    param(
        [string]$RepoName,    # e.g. outlook-access
        [string]$CliName      # e.g. outlook-cli
    )
    $repoUrl = "https://github.com/weirdapps/$RepoName.git"
    $target  = Join-Path $DepsDir $RepoName

    # If the CLI is already on PATH AND we don't manage it (no clone in deps\),
    # respect the existing install and skip.
    if ((Get-Command $CliName -ErrorAction SilentlyContinue) -and -not (Test-Path (Join-Path $target '.git'))) {
        Write-Ok "$CliName already on PATH (not managed by this installer) — skipping"
        return
    }

    if (Test-Path (Join-Path $target '.git')) {
        Write-Host "  Updating $RepoName..."
        Push-Location $target
        git pull --ff-only 2>&1 | Select-Object -Last 2
        Pop-Location
    } else {
        Write-Host "  Cloning $RepoName..."
        git clone --depth 1 $repoUrl $target 2>&1 | Select-Object -Last 2
    }

    Write-Host "  Building $CliName..."
    Push-Location $target
    npm install --silent 2>&1 | Out-Null
    npm run build --silent 2>&1 | Out-Null

    Write-Host "  Linking $CliName globally (npm link)..."
    npm link --silent 2>&1 | Out-Null
    Pop-Location

    if (Get-Command $CliName -ErrorAction SilentlyContinue) {
        Write-Ok "$CliName installed and linked"
    } else {
        $npmPrefix = npm prefix -g
        Write-Warn "$CliName built but not on PATH. Add $npmPrefix\bin to PATH."
    }
}

Install-CliFromRepo -RepoName 'outlook-access' -CliName 'outlook-cli'
Install-CliFromRepo -RepoName 'teams-access'   -CliName 'teams-cli'

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
Write-Host "  3. Open Claude Code and try: /inbox-briefing"
Write-Host ''
Write-Host "Documentation: $InstallDir\docs\"
