# Resolve M365 SharePoint host from (in priority order):
#   1) $env:PLESSAS_SHAREPOINT_HOST environment variable     (works non-interactively)
#   2) $env:USERPROFILE\.outlook-cli\config.json {"sharepoint_host"}  (works non-interactively)
#   3) Interactive prompt (then persist to config.json)      (requires interactive session)
#
# Returns the resolved host. Throws if no interactive host can be resolved.
#
# Safe by construction: ConvertTo-Json escapes user input correctly when writing
# the config file — no string-interpolation injection risk like the Bash sibling.

function Get-TenantHost {
    $homeDir    = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
    $configDir  = Join-Path $homeDir '.outlook-cli'
    $configFile = Join-Path $configDir 'config.json'

    # Priority 1: env var
    if ($env:PLESSAS_SHAREPOINT_HOST) {
        return $env:PLESSAS_SHAREPOINT_HOST
    }

    # Priority 2: persisted config.
    # Tolerate read failure (corrupt JSON, permission issue) — fall through to prompt.
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
    $hostInput = Read-Host 'Tenant SharePoint host'
    if (-not $hostInput) {
        throw 'No host entered.'
    }

    # Persist using ConvertTo-Json (handles escaping safely).
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    $existing = @{}
    if (Test-Path $configFile) {
        try {
            $obj = Get-Content $configFile -Raw | ConvertFrom-Json
            $obj.PSObject.Properties | ForEach-Object { $existing[$_.Name] = $_.Value }
        } catch {
            # Corrupt config — start fresh
            $existing = @{}
        }
    }
    $existing['sharepoint_host'] = $hostInput

    try {
        $existing | ConvertTo-Json | Set-Content -Path $configFile -Encoding UTF8
    } catch {
        Write-Error "Could not persist tenant host to $configFile : $_"
        throw
    }

    Write-Host "[OK]   Tenant host saved to $configFile" -ForegroundColor Green
    return $hostInput
}
