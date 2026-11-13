#!/usr/bin/env bash
# Runs in the empty workspace with HOME set to the run's own temporary home (see
# case.yaml). rmdir removes only an empty folder, so this can never delete files.
set -euo pipefail
if [ -d "$HOME/Downloads" ] && [ ! -L "$HOME/Downloads" ]; then
  rmdir "$HOME/Downloads"
fi
[ -e "$HOME/Downloads" ] || ln -s "$PWD" "$HOME/Downloads"
