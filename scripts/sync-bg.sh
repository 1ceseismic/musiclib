#!/usr/bin/env bash
# Start a sync DETACHED on this host: it keeps running after the caller (and any
# SSH session) disconnects, and returns immediately. Output goes to a log file
# you can tail anytime.
#
# Auto-queue: if a sync is already running, this records a pending request (the
# running instance re-runs afterward) instead of starting a concurrent one.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="/tmp/musiclib-sync.out"
LOCK="/tmp/musiclib-sync.lock"
PENDING="/tmp/musiclib-sync.pending"

if ! flock -n "$LOCK" true 2>/dev/null; then
  : > "$PENDING"
  echo "A sync is already running on $(hostname) — your changes are queued and"
  echo "will sync automatically right after it finishes."
  echo "Watch:  mlog"
  exit 0
fi

# nohup + detached: ignores SIGHUP, FDs go to the log (not the SSH channel), so
# the SSH call returns and the work continues independently. Any args (playlist
# IDs to prioritise) are forwarded to sync.sh.
nohup "$DIR/sync.sh" "$@" > "$LOG" 2>&1 < /dev/null &

echo "Sync started in background on $(hostname) — safe to close this terminal."
echo "Watch progress:  mlog   (or: ssh $(hostname) tail -f $LOG)"
