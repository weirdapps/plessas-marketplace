# plessas-marketplace installer (Windows PowerShell)
# Usage: iwr https://raw.githubusercontent.com/weirdapps/plessas-marketplace/master/installers/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$RepoUrl    = 'https://github.com/weirdapps/plessas-marketplace.git'
$InstallDir = Join-Path $env:USERPROFILE '.claude\plugins\marketplaces\plessas-marketplace'
$ClaudeMd   = Join-Path $env:USERPROFILE '.claude\CLAUDE.md'

function Write-Ok   { param($msg) Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }

# Run a native executable and actually notice when it fails.
#
# $ErrorActionPreference = 'Stop' does NOT apply to a native command's exit
# code. Only $PSNativeCommandUseErrorActionPreference does, it defaults to
# $false, and it does not exist at all on Windows PowerShell 5.1, which is the
# default shell on Windows. So the old `npm install --silent 2>&1 | Out-Null`
# followed by Write-Ok reported success for a failed install, a failed build
# and a failed pip alike, with Out-Null destroying the diagnostics on the way
# past. Checking $LASTEXITCODE explicitly is the only form that works on both
# 5.1 and 7.x.
#
# Output is captured rather than streamed so the success path stays quiet (the
# point of --silent) while the failure path can print what actually happened.
function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]$What,        # label used in the failure message
        [Parameter(Mandatory)][string]$Exe,
        [string[]]$Arguments = @(),
        [switch]$AllowFailure                       # warn and return $false instead of aborting
    )

    # Native stderr merged into the output stream is not governed by
    # $ErrorActionPreference from PowerShell 7.2 onward, but 5.1 predates that
    # change and git and npm both write ordinary progress to stderr. Relax the
    # preference for the duration of the call so the exit code, not the noise,
    # decides the outcome.
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $global:LASTEXITCODE = 0
    try {
        $output = & $Exe @Arguments 2>&1
    } finally {
        $ErrorActionPreference = $prevEap
    }

    if ($LASTEXITCODE -ne 0) {
        if ($output) { $output | ForEach-Object { Write-Host "    $_" } }
        if ($AllowFailure) {
            Write-Warn "$What failed (exit $LASTEXITCODE)."
            return $false
        }
        Write-Fail "$What failed (exit $LASTEXITCODE). See the output above."
    }
    return $true
}

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

# npm is not optional: every MCP build and every CLI link below shells out to
# it, and it does not always ship alongside node on a corporate image.
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Fail 'npm not found (node is present but npm is not). Install Node.js from https://nodejs.org/, which bundles npm.' }
Write-Ok "npm $(npm --version)"

# Python is optional, this installer must finish without it, but when it IS
# present the VERSION matters. numpy >= 2.5.2, the floor in both
# plugins\decks\tools\nbg-keynote\requirements.txt and
# plugins\decks\bundled\creative\tools\device-mockup\requirements.txt, itself
# declares requires-python >= 3.12, so on 3.11 or older `pip install -r`
# cannot resolve. Decide once, here, instead of discovering it halfway through
# a pip resolver dump.
$pythonCmd = $null
foreach ($candidate in @('python', 'python3')) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $pythonCmd = $candidate; break }
}

$PythonOk = $false
if ($pythonCmd) {
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $global:LASTEXITCODE = 0
    try {
        $pyVer = (& $pythonCmd -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>&1) | Select-Object -First 1
    } finally {
        $ErrorActionPreference = $prevEap
    }
    if ($LASTEXITCODE -ne 0 -or -not $pyVer) { $pyVer = '0.0' }
    $pyMajor = 0
    $pyMinor = 0
    if ("$pyVer".Trim() -match '^(\d+)\.(\d+)') { $pyMajor = [int]$Matches[1]; $pyMinor = [int]$Matches[2] }
    if ($pyMajor -gt 3 -or ($pyMajor -eq 3 -and $pyMinor -ge 12)) {
        $PythonOk = $true
        Write-Ok "Python $pyVer (for decks plugin)"
    } else {
        Write-Warn "Python $pyVer found, the decks Python tools need 3.12+. /create-presentation, /create-keynote and device-mockup will be skipped; the rest installs normally. Update: https://www.python.org/downloads/"
    }
} else {
    Write-Warn 'Python not found. The decks Python tools need 3.12+. Install: https://www.python.org/downloads/'
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { Write-Fail 'Claude Code not found. Install: https://claude.ai/claude-code' }
Write-Ok 'Claude Code found'

Write-Host ''

# --- Clone or update ---
if (Test-Path (Join-Path $InstallDir '.git')) {
    Write-Host 'Marketplace already installed. Updating...'
    Push-Location $InstallDir
    try {
        Invoke-Native 'git pull (marketplace)' 'git' @('pull', '--ff-only') | Out-Null
    } finally {
        Pop-Location
    }
    Write-Ok 'Updated to latest'
} else {
    Write-Host 'Cloning plessas-marketplace...'
    $parentDir = Split-Path $InstallDir -Parent
    if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Path $parentDir -Force | Out-Null }
    Invoke-Native 'git clone (marketplace)' 'git' @('clone', $RepoUrl, $InstallDir) | Out-Null
    Write-Ok "Cloned to $InstallDir"
}

Push-Location $InstallDir

# --- Build MCP servers ---
Write-Host ''
Write-Host 'Building MCP servers...'

if (Test-Path 'plugins\mail\mcp-server') {
    Write-Host '  Building outlook-bridge MCP...'
    Push-Location 'plugins\mail\mcp-server'
    try {
        Invoke-Native 'npm install (outlook-bridge)'   'npm' @('install', '--silent')     | Out-Null
        Invoke-Native 'npm run build (outlook-bridge)' 'npm' @('run', 'build', '--silent') | Out-Null
    } finally {
        Pop-Location
    }
    Write-Ok 'outlook-bridge MCP built'
}

if (Test-Path 'plugins\chat\mcp-server') {
    Write-Host '  Building teams-bridge MCP...'
    Push-Location 'plugins\chat\mcp-server'
    try {
        Invoke-Native 'npm install (teams-bridge)'   'npm' @('install', '--silent')     | Out-Null
        Invoke-Native 'npm run build (teams-bridge)' 'npm' @('run', 'build', '--silent') | Out-Null
    } finally {
        Pop-Location
    }
    Write-Ok 'teams-bridge MCP built'
}

# --- Warm the plugin cache, which is the tree Claude Code actually executes ---
#
# The builds above warm THIS clone. Claude Code does not run plugins from here:
# it runs them from ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/.
# The copy made at `/plugin install` time contains exactly the git-tracked
# files, and mcp-server\dist and node_modules are BOTH gitignored, so nothing
# built above can ever reach the tree that runs. The first real MCP call then
# pays run.sh's `npm ci` plus build, the 30-to-60-second first-call stall.
#
# The cache directory does not exist until `/plugin install` has run, so on a
# genuine first install this finds nothing and says so. Re-run the installer
# afterwards and it warms them. The cache is keyed by plugin VERSION, not by
# marketplace commit, so a warmed build survives until the next version bump.
$CacheDir = Join-Path $env:USERPROFILE '.claude\plugins\cache\plessas-marketplace'
Write-Host ''
Write-Host 'Warming the plugin cache (the tree Claude Code actually executes)...'
# $found counts plugins present in the cache; $warmed counts those now built.
# They differ when a build fails, and conflating them made a build error print
# the "run /plugin install first" advice on top of it, pointing at the wrong fix.
$found = 0
$warmed = 0
if (Test-Path $CacheDir) {
    foreach ($mcpDir in (Get-ChildItem -Path $CacheDir -Filter 'mcp-server' -Recurse -Directory -Depth 2 -ErrorAction SilentlyContinue)) {
        if (-not (Test-Path (Join-Path $mcpDir.FullName 'package.json'))) { continue }
        $pluginName = Split-Path (Split-Path $mcpDir.FullName -Parent) -Parent | Split-Path -Leaf
        $found++
        $built = (Test-Path (Join-Path $mcpDir.FullName 'dist\server.js')) -and (Test-Path (Join-Path $mcpDir.FullName 'node_modules'))
        if ($built) {
            Write-Ok "$pluginName MCP already warm in the cache"
            $warmed++
            continue
        }
        Write-Host "  Building $pluginName MCP in the cache..."
        Push-Location $mcpDir.FullName
        try {
            $okInstall = Invoke-Native "npm install (cache: $pluginName)"   'npm' @('install', '--silent')      -AllowFailure
            $okBuild   = $false
            if ($okInstall) {
                $okBuild = Invoke-Native "npm run build (cache: $pluginName)" 'npm' @('run', 'build', '--silent') -AllowFailure
            }
        } finally {
            Pop-Location
        }
        if ($okInstall -and $okBuild) {
            Write-Ok "$pluginName MCP built in the cache"
            $warmed++
        } else {
            Write-Warn "$pluginName MCP failed to build in the cache. Its first call will rebuild and may stall 30-60s."
        }
    }
}
if ($found -eq 0) {
    Write-Warn 'No installed plugins in the cache yet. Expected on a first install: do the /plugin steps printed at the end, then re-run this installer. Skipping it only costs a 30-60s stall on each bundled MCP first call.'
}

# --- Warm the decks Python environments ---
# The decks prompts run every Python tool through plugins\decks\bin\decks-py (a
# bash script; Claude Code on Windows runs its Bash tool in Git Bash, which is
# also what runs it here). It keeps one environment per tool in
# ~/.cache/nbg-decks, keyed by that tool's requirements.txt, and builds it on
# first use. This step only builds them now.
#
# It used to build <tool>\.venv inside this marketplace clone, while Claude Code
# runs the plugin from its version-keyed cache copy, where no venv ever existed.
# Every failure here warns and continues: the decks Python tools are optional,
# the install is not.
$bashCmd = Get-Command bash -ErrorAction SilentlyContinue
if ($PythonOk -and $bashCmd) {
    Write-Host ''
    Write-Host 'Preparing the decks Python environments...'
    $launcher = Join-Path $InstallDir 'plugins\decks\bin\decks-py'
    if (Invoke-Native 'decks-py setup' $bashCmd.Source @($launcher, 'setup') -AllowFailure) {
        Write-Ok 'decks Python environments ready'
    } else {
        Write-Warn 'decks-py setup failed (output above). The decks tools will retry on first use.'
    }
} elseif ($PythonOk) {
    Write-Host ''
    Write-Warn 'bash (Git for Windows) not found, so the decks Python environments were not prepared. Claude Code needs Git Bash anyway; they build on first use once it is installed.'
} else {
    Write-Host ''
    Write-Warn 'Skipping the decks Python environments (see the Python line above). They build on first use once Python 3.12+ is installed; everything else installs normally.'
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
        Write-Ok "$CliName already on PATH (not managed by this installer), skipping"
        return
    }

    if (Test-Path (Join-Path $target '.git')) {
        Write-Host "  Updating $RepoName..."
        Push-Location $target
        try {
            Invoke-Native "git pull ($RepoName)" 'git' @('pull', '--ff-only') | Out-Null
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "  Cloning $RepoName..."
        Invoke-Native "git clone ($RepoName)" 'git' @('clone', '--depth', '1', $repoUrl, $target) | Out-Null
    }

    Write-Host "  Building $CliName..."
    Push-Location $target
    try {
        Invoke-Native "npm install ($RepoName)"   'npm' @('install', '--silent')     | Out-Null
        Invoke-Native "npm run build ($RepoName)" 'npm' @('run', 'build', '--silent') | Out-Null

        Write-Host "  Linking $CliName globally (npm link)..."
        # A failed link is recoverable by hand and the marketplace itself is
        # already installed by this point, so warn rather than abort.
        $linked = Invoke-Native "npm link ($CliName)" 'npm' @('link', '--silent') -AllowFailure
    } finally {
        Pop-Location
    }

    if (-not $linked) {
        Write-Warn "npm link failed for $CliName. On systems with a global npm under Program Files, try an elevated shell: cd $target; npm link"
        return
    }

    if (Get-Command $CliName -ErrorAction SilentlyContinue) {
        Write-Ok "$CliName installed and linked"
    } else {
        $global:LASTEXITCODE = 0
        $npmPrefix = (npm prefix -g 2>&1) | Select-Object -First 1
        if ($LASTEXITCODE -ne 0 -or -not $npmPrefix) { $npmPrefix = '<npm prefix -g>' }
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
    # Copy-Item has no -Encoding parameter in any PowerShell version. With
    # $ErrorActionPreference = 'Stop' the parameter-binding failure was
    # TERMINATING, and this branch runs only when ~/.claude/CLAUDE.md does not
    # exist yet, i.e. on exactly the fresh install it exists to serve: every
    # prior [OK], then a red ParameterBindingException, and the completion
    # banner and next steps below were never reached. Copy-Item already copies
    # bytes verbatim, so the parameter was never doing anything. The bash
    # sibling uses a plain `cp` and has always been correct.
    Copy-Item (Join-Path $InstallDir 'shared\claude-md-template\team-claude-md.md') $ClaudeMd
    Write-Ok "Team CLAUDE.md installed at $ClaudeMd"
    Write-Host '  Please edit it and replace the << REPLACE >> sections with your details.'
} else {
    Write-Ok "Existing CLAUDE.md found, not overwriting. See $InstallDir\shared\claude-md-template\team-claude-md.md"
}

Pop-Location

# --- Done ---
Write-Host ''
Write-Host '========================================'
Write-Host '  Installation complete!' -ForegroundColor Green
Write-Host '========================================'
Write-Host ''
Write-Host 'Next steps (preferred, runs inside Claude Code):'
Write-Host '  1. /plugin marketplace add weirdapps/plessas-marketplace'
Write-Host '  2. /plugin install mail@plessas-marketplace   (and chat, decks, meetings, excel, docs as desired)'
Write-Host '  3. Re-run this installer once. Claude Code executes plugins from'
Write-Host '     ~\.claude\plugins\cache\, not from this clone, and that cache does not'
Write-Host '     exist until step 2. Re-running prebuilds the bundled MCP servers there;'
Write-Host '     skipping it costs a 30-60s stall on each one first call.'
Write-Host '  4. /mail:auth-setup                            (and /chat:auth-setup if chat is installed)'
Write-Host '  5. Try /inbox-briefing'
Write-Host ''
Write-Host 'Legacy alternative (deprecated, still works):'
Write-Host "  $InstallDir\installers\auth-wizard.ps1"
Write-Host "  $InstallDir\installers\status.ps1"
Write-Host ''
Write-Host "Documentation: $InstallDir\docs\"
