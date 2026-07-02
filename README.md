# musiclib: public Spotify playlists -> iOS offline sync

Self-hosted pipeline that mirrors public Spotify playlists into Navidrome as
native playlists for 100% offline playback via a Subsonic app (Substreamer) on
iOS. Uses spotDL's unauthenticated mode; no Spotify API account or
subscription required.

**Already running?** For day-to-day use (sync commands, adding music, the
phone), see **[docs/USAGE.md](docs/USAGE.md)**. The rest of this file is for
building/rebuilding the stack from scratch.

## How it works

```
playlists.txt ──> orchestrator ──> downloads M4A/AAC ──> /music volume
(public URLs)          │
                       └──> Navidrome playlists (port 4533)
                                    │
                             Tailscale tunnel
                                    │
                          Substreamer (iOS) ──> offline cache
```

The orchestrator reads public Spotify playlist URLs from `playlists.txt`,
downloads audio via spotDL (unauthenticated), matches tracks to local M4A files,
and writes Navidrome playlists via the Subsonic API. Playlist names are
auto-derived from the Spotify playlist. State (save files, `playlists.json`,
`unmatched.log`) lives in the `state` Docker volume. Secrets live in `.env`;
non-secret preferences in `config.yaml`. The daily sync runs at 03:30 via the
container's built-in cron.

## Prerequisites

- Docker with Compose v2
- Public Spotify playlist URLs (make playlists Public in Spotify; copy their
  links). Personalized playlists like Discover Weekly/Daily Mix can't be synced.
- Tailscale on the host + your phone, for remote access.

## Quick start

1. Copy and fill in Navidrome credentials:
   ```
   cp .env.example .env
   ```
   Edit `.env`: set `NAVIDROME_USER` and `NAVIDROME_PASSWORD`.

2. List your public Spotify playlist URLs:
   ```
   cp playlists.txt.example playlists.txt
   ```
   Edit `playlists.txt`: one public playlist URL per line. Blank lines and
   `#` comments are ignored.

3. Start Navidrome and create the admin user:
   ```
   docker compose up -d navidrome
   ```
   Open http://localhost:4533 and create the admin account. Use the same
   username and password you set for `NAVIDROME_USER`/`NAVIDROME_PASSWORD`
   in `.env`.

4. Build the orchestrator image:
   ```
   docker compose build orchestrator
   ```

5. First run in **dry-run** mode (the default; writes no playlists):
   ```
   docker compose run --rm orchestrator musiclib
   ```
   Review `unmatched.log` to see which tracks could not be matched to local
   files:
   ```
   docker compose run --rm orchestrator cat /state/unmatched.log
   ```

6. Apply for real (writes playlists to Navidrome):
   ```
   docker compose run --rm orchestrator musiclib --apply
   ```

7. Start everything and let it run on schedule:
   ```
   docker compose up -d
   ```
   The orchestrator syncs daily at 03:30 (`musiclib --apply`).

## CLI reference

```
musiclib [--config PATH] [--apply] [--dry-run]

  --config PATH   Path to config.yaml (default: /app/config.yaml)
  --apply         Write playlists to Navidrome (omit for dry-run)
  --dry-run       Force dry-run even if --apply is also passed
```

Default behaviour (no flags) is dry-run: safe to run at any time, no changes
written.

## See also

- **[docs/USAGE.md](docs/USAGE.md)**: daily operation (sync commands, adding
  music, iPhone/Substreamer setup, troubleshooting)
- [docs/GO-LIVE.md](docs/GO-LIVE.md): from-scratch / rebuild runbook
