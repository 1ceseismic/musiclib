#!/usr/bin/env bash
# Add one or more PUBLIC Spotify playlist URLs to playlists.txt (skipping
# duplicates), then sync ONLY the newly-added playlist(s) so they appear fast
# (a full sweep of everything else still runs nightly, or via `msync`).
# URLs may be passed as arguments or on stdin (one per line). Runs detached.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/.."

if [ "$#" -gt 0 ]; then
  urls=("$@")
else
  mapfile -t urls
fi

new_ids=()
for raw in "${urls[@]}"; do
  url="$(printf '%s' "$raw" | tr -d '[:space:]')"
  [ -n "$url" ] || continue
  if grep -qxF "$url" playlists.txt 2>/dev/null; then
    echo "already present: $url"
    continue
  fi
  printf '%s\n' "$url" >> playlists.txt
  plid="$(printf '%s' "$url" | sed -E 's#.*playlist[/:]([A-Za-z0-9]+).*#\1#')"
  new_ids+=("$plid")
  echo "added (prioritised): $url"
done

if [ "${#new_ids[@]}" -eq 0 ]; then
  echo "Nothing new to add. Not syncing."
  exit 0
fi

exec "$DIR/sync-bg.sh" "${new_ids[@]}"
