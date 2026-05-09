# plessas-marketplace status check (Windows PowerShell)

$InstallDir = Join-Path $env:USERPROFILE '.claude\plugins\marketplaces\plessas-marketplace'
$Pass = 0
$Total = 0

function Check {
    param($Label, $Result)
    $script:Total++
    switch ($Result) {
        'ok'   { Write-Host "[OK]   $Label" -ForegroundColor Green; $script:Pass++ }
        'warn' { Write-Host "[--]   $Label" -ForegroundColor Yellow }
        default { Write-Host "[!!]   $Label" -ForegroundColor Red }
    }
}

Write-Host '========================================'
Write-Host '  plessas-marketplace status'
Write-Host '========================================'
Write-Host ''

# Marketplace installed?
if (Test-Path (Join-Path $InstallDir '.claude-plugin')) { Check 'Marketplace installed' 'ok' } else { Check 'Marketplace NOT installed' 'fail' }

# Plugins present?
foreach ($plugin in @('decks','mail','mail-pro','meetings','chat','excel','docs')) {
    $pj = Join-Path $InstallDir "plugins\$plugin\.claude-plugin\plugin.json"
    if (Test-Path $pj) { Check "Plugin: $plugin" 'ok' } else { Check "Plugin: $plugin — MISSING" 'fail' }
}

Write-Host ''

# MCP servers built?
$outlookMcp = Join-Path $InstallDir 'plugins\mail\mcp-server\dist\server.js'
$teamsMcp   = Join-Path $InstallDir 'plugins\chat\mcp-server\dist\server.js'
if (Test-Path $outlookMcp) { Check 'outlook-bridge MCP built' 'ok' } else { Check 'outlook-bridge MCP NOT built' 'fail' }
if (Test-Path $teamsMcp)   { Check 'teams-bridge MCP built' 'ok' }   else { Check 'teams-bridge MCP NOT built' 'fail' }

Write-Host ''

# CLIs available?
if (Get-Command outlook-cli -ErrorAction SilentlyContinue) { Check 'outlook-cli available' 'ok' } else { Check 'outlook-cli NOT available' 'fail' }
if (Get-Command teams-cli -ErrorAction SilentlyContinue)   { Check 'teams-cli available' 'ok' }   else { Check 'teams-cli NOT available' 'fail' }

Write-Host ''

# Auth status
if (Get-Command outlook-cli -ErrorAction SilentlyContinue) {
    outlook-cli auth-check 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Check 'Outlook auth valid' 'ok' } else { Check 'Outlook auth EXPIRED' 'fail' }
} else { Check 'Outlook auth — CLI not installed' 'warn' }

if (Get-Command teams-cli -ErrorAction SilentlyContinue) {
    teams-cli auth-check 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Check 'Teams auth valid' 'ok' } else { Check 'Teams auth EXPIRED' 'fail' }
} else { Check 'Teams auth — CLI not installed' 'warn' }

$sigPath = Join-Path $env:USERPROFILE '.outlook-cli\signature.html'
if (Test-Path $sigPath) { Check 'Email signature exists' 'ok' } else { Check 'Email signature MISSING' 'warn' }

$claudeMd = Join-Path $env:USERPROFILE '.claude\CLAUDE.md'
if (Test-Path $claudeMd) { Check 'CLAUDE.md exists' 'ok' } else { Check 'CLAUDE.md MISSING' 'warn' }

Write-Host ''
Write-Host '========================================'
Write-Host "  $Pass / $Total checks passed"
Write-Host '========================================'
