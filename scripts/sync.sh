#!/usr/bin/env bash
# Run the music sync: download new/changed tracks + (re)build Navidrome playlists.
#
# Optional args = playlist IDs to PRIORITISE: the first pass syncs only those
# (so a freshly-added playlist appears fast), then a full pass runs. With no
# args it's just a full sync.
#
# Concurrency: only one sync runs at a time (flock). A request that arrives mid-
# run sets a "pending" marker; this instance then loops and runs a full pass
# afterward, so nothing is lost and nothing runs concurrently.
set -euo pipefail
cd "$(dirname "$0")/.."

LOCK="/tmp/musiclib-sync.lock"
PENDING="/tmp/musiclib-sync.pending"
priority_ids=("$@")

exec 9>"$LOCK"
if ! flock -n 9; then
  : > "$PENDING"
  echo "A sync is already running. Queued a follow-up for your changes." >&2
  exit 0
fi

first=1
while : ; do
  rm -f "$PENDING"
  args=(--apply)
  if [ "$first" -eq 1 ] && [ "${#priority_ids[@]}" -gt 0 ]; then
    for id in "${priority_ids[@]}"; do args+=(--only "$id"); done
  fi
  first=0
  docker compose run --rm orchestrator musiclib "${args[@]}"
  [ -f "$PENDING" ] || break
  echo ">>> changes were queued during the sync. Running a full sync to pick them up..."
done
