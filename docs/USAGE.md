# musiclib: daily usage

## TL;DR: all updates in 3 moves

1. **New playlist** -> `madd "<public spotify url>"` (downloads + builds it).
2. **Updates to playlists you already added** -> nothing; the nightly 03:30 sync
   pulls adds/removes/reorders automatically. Want them now? -> `msync`.
3. **Get any of it onto the phone** -> Substreamer: Tailscale **on** -> open the
   playlist -> **pull-to-refresh** -> **Set available offline**.

`madd` = add new · `msync` = update everything now · Substreamer refresh +
download = the only phone step (and the only way updates reach your device).

---

The stack runs on your server (`<server>` below). If the server isn't on your
home network, reach it over **Tailscale** (or your own VPN).

## Facts
- **Server (Navidrome):** `http://<server-ip>:4533`, login `<user>` / `<password>`
  (set in `.env` next to `docker-compose.yml`).
- **Tailscale is required** to reach `<server>` from outside its network. A LAN
  address (`http://<lan-ip>:4533`) only works for devices on the same network.
- Auto-sync runs **daily at 03:30**. Manual sync via the commands below.

## Commands (run from your PC; they drive `<server>` over SSH)
- `msync`: sync now (download new/changed tracks + rebuild Navidrome playlists).
  Runs **detached** on the server; safe to close the terminal.
- `madd "<url>"`: add a public Spotify playlist URL, then sync.
- `mlog`: watch the live sync log (Ctrl-C stops watching; the sync keeps going).

Only one sync runs at a time; a second `msync` reports "already running".
(Define these as small wrappers in `~/.local/bin/`; they `ssh <server>` and call
the scripts in `scripts/`.)

## Adding music
1. Make the Spotify playlist **Public**, copy its link.
2. `madd "https://open.spotify.com/playlist/..."`  (or edit `playlists.txt` on
   the server and run `msync`).
- Public playlists only. Artist/song **Radio** playlists work; **personalized**
  ones (Discover Weekly, Daily Mix) do **not**.
- ~75–80% match on obscure tracks is normal; misses go to `/state/unmatched.log`.

## iPhone (Substreamer)
- App: **Substreamer** (Amperfy needs iOS 26). Also install **Tailscale**, sign
  in to your Tailscale account, toggle **on** (needed to reach the server).
- Add server: URL `http://<server-ip>:4533`, user `<user>`, pass `<password>`,
  Legacy Auth off.
- **Settings -> Playback:** Stream Format = **Original**, Download Format =
  **Original**, Max Bitrate = unlimited. *(Critical: otherwise Navidrome
  transcodes to Opus, which iOS can't play.)*
- Download: **Playlists** tab -> playlist -> **Set available offline**.
- New playlists not showing? **Pull-to-refresh** the Playlists list; if stubborn,
  Settings -> clear **metadata cache**, reopen.
- Offline playback needs **no network**. Tailscale is only needed while
  downloading; leave it off otherwise.

## Where things live (on the server)
- **Settings:** `docker-compose.yml` env vars (no config file).
- **Back this up:** `data/navidrome/navidrome.db` in the repo directory
  (users, playlists, play counts).
- **Music files:** Docker volume `musiclib_music`.
- **Sync state:** `state` volume (`playlists.json`, `*.spotdl`, `unmatched.log`).

## Troubleshooting
- Substreamer "connection appears offline" -> Tailscale isn't on, or you're
  signed into the wrong account.
- Stack control on the server: `docker compose ps` / `up -d` / `logs -f orchestrator`.
- Disable Tailscale **key expiry** per device (admin console) so nothing drops
  unexpectedly.
- Rebuild from scratch (e.g. on a Pi): see [GO-LIVE.md](GO-LIVE.md).
