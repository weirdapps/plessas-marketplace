#!/usr/bin/env bash
# Resolve M365 SharePoint host from (in priority order):
#   1) PLESSAS_SHAREPOINT_HOST environment variable     (works non-interactively)
#   2) ~/.outlook-cli/config.json {"sharepoint_host"}   (works non-interactively)
#   3) Interactive prompt (then persist to config.json) (requires TTY)
#
# Echoes the resolved host on stdout. Returns 0 on success, 1 if no TTY and no
# Priority 1 or 2 source is available.
#
# Persist step uses sys.argv to pass user input to python — avoids any shell
# interpolation into python source.

set -euo pipefail

prompt_tenant() {
  local config_dir="$HOME/.outlook-cli"
  local config_file="$config_dir/config.json"

  # Priority 1: env var
  if [ -n "${PLESSAS_SHAREPOINT_HOST:-}" ]; then
    echo "$PLESSAS_SHAREPOINT_HOST"
    return 0
  fi

  # Priority 2: persisted config.
  # Tolerate read failure (corrupt JSON, permission issue) — fall through to
  # the prompt path. The python helper receives the path via argv and prints
  # the host, or empty string on any failure.
  if [ -f "$config_file" ]; then
    local persisted
    persisted=$(python3 -c "
import json, sys
try:
    print(json.load(open(sys.argv[1])).get('sharepoint_host', ''))
except Exception:
    pass
" "$config_file" 2>/dev/null)
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

  # Persist via sys.argv to avoid shell interpolation into python source
  # (closes the injection vector that string-interpolating $host would open).
  mkdir -p "$config_dir"
  if ! python3 -c "
import json, os, sys
path = sys.argv[1]
host = sys.argv[2]
data = {}
if os.path.exists(path):
    try:
        data = json.load(open(path))
    except Exception:
        data = {}
data['sharepoint_host'] = host
json.dump(data, open(path, 'w'), indent=2)
" "$config_file" "$host"; then
    printf '[FAIL] Could not persist tenant host to %s\n' "$config_file" >&2
    return 1
  fi
  chmod 600 "$config_file"
  printf '[OK]   Tenant host saved to %s\n' "$config_file" >&2

  echo "$host"
}
