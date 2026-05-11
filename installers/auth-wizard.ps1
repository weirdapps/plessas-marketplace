# plessas-marketplace auth wizard (Windows PowerShell)

$ErrorActionPreference = 'Continue'

function Write-Ok   { param($msg) Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red }

# Load tenant-prompt helper
. "$PSScriptRoot\lib\tenant-prompt.ps1"

Write-Host '========================================'
Write-Host '  plessas-marketplace auth wizard'
Write-Host '========================================'
Write-Host ''
Write-Host 'This will authenticate outlook-cli and teams-cli.'
Write-Host 'Each step opens a browser window for M365 sign-in.'
Write-Host ''

# --- Step 1: Outlook ---
Write-Host '--- Step 1/3: Outlook (outlook-cli login) ---'
if (Get-Command outlook-cli -ErrorAction SilentlyContinue) {
    $authResult = outlook-cli auth-check 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Write-Ok 'outlook-cli already authenticated'
    } else {
        Write-Host 'Opening browser for Outlook sign-in...'
        $spHost = Get-TenantHost
        outlook-cli login --sharepoint-host $spHost
        $checkResult = outlook-cli auth-check 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) { Write-Ok 'outlook-cli authenticated' }
        else { Write-Fail 'outlook-cli auth check failed after login' }
    }
} else {
    Write-Warn 'outlook-cli not installed — skipping.'
}

Write-Host ''

# --- Step 2: Teams ---
Write-Host '--- Step 2/3: Teams (teams-cli login) ---'
if (Get-Command teams-cli -ErrorAction SilentlyContinue) {
    $authResult = teams-cli auth-check 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Write-Ok 'teams-cli already authenticated'
    } else {
        Write-Host 'Opening browser for Teams sign-in...'
        teams-cli login
        $checkResult = teams-cli auth-check 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) { Write-Ok 'teams-cli authenticated' }
        else { Write-Fail 'teams-cli auth check failed after login' }
    }
} else {
    Write-Warn 'teams-cli not installed — skipping.'
}

Write-Host ''

# --- Step 3: Signature ---
Write-Host '--- Step 3/3: Email signature capture ---'
$sigPath = Join-Path $env:USERPROFILE '.outlook-cli\signature.html'
if ((Get-Command outlook-cli -ErrorAction SilentlyContinue) -and ((outlook-cli auth-check 2>&1 | Out-String) -and $LASTEXITCODE -eq 0)) {
    if (Test-Path $sigPath) {
        Write-Ok "Signature already exists at $sigPath"
    } else {
        Write-Host 'Capturing signature from your latest sent email...'
        outlook-cli capture-signature 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Ok 'Signature captured' }
        else { Write-Warn 'Signature capture failed — set up manually later' }
    }
} else {
    Write-Warn 'Skipping signature capture — outlook-cli not authenticated'
}

Write-Host ''
Write-Host '========================================'
Write-Host '  Auth wizard complete!' -ForegroundColor Green
Write-Host '========================================'
Write-Host ''
$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
Write-Host "Check overall status: $scriptDir\status.ps1"
