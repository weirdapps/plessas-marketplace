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
