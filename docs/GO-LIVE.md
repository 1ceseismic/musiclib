# Go Live: Setup Checklist

Runbook for building the stack from scratch (e.g. on a new box / Pi).
**Already running? Daily use is in [USAGE.md](USAGE.md).** Prereqs: Docker + Compose.

## 1. Playlists (no Spotify login)
Make your playlists **Public**, then list their URLs:
```bash
cp playlists.txt.example playlists.txt   # then edit: one public playlist URL per line
```

## 2. Credentials
```bash
cp .env.example .env       # set NAVIDROME_USER / NAVIDROME_PASSWORD
```

## 3. Start Navidrome + create admin
`docker compose up -d navidrome` -> open http://localhost:4533 -> create admin matching .env.

## 4. Build
`docker compose build orchestrator`

## 5. Dry run (default, writes nothing)
`docker compose run --rm orchestrator musiclib` -> review `/state/unmatched.log`.

## 6. Apply
`docker compose run --rm orchestrator musiclib --apply`

## 7. Schedule
`docker compose up -d`  (daily 03:30).

## 8. Remote access (Tailscale, on the HOST not in Docker)
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4      # note this address
```

## 9. iPhone (Substreamer)
- Install **Substreamer** + **Tailscale** (sign into the same tailnet, toggle on).
- Add server: URL `http://<tailnet-ip>:4533`, your Navidrome user/pass, Legacy Auth off.
- **Settings -> Playback:** Stream Format = **Original**, Download Format = **Original**
  (else it transcodes to Opus, which iOS can't play).
- **Playlists** tab -> pick a playlist -> **Set available offline**. New playlists
  not showing -> pull-to-refresh (clear metadata cache if stubborn).

---

### Cheat sheet
| Action | Command |
|---|---|
| Dry run (safe) | `docker compose run --rm orchestrator musiclib` |
| Apply now | `docker compose run --rm orchestrator musiclib --apply` |
| View unmatched | `docker compose run --rm orchestrator cat /state/unmatched.log` |
| Logs (cron) | `docker compose logs -f orchestrator` |

### Notes
- CLI defaults to **dry-run**; only `--apply` writes playlists. The daily cron passes `--apply`.
- Secrets live in `.env` (never committed). Prefs (format=m4a, scan timeout, schedule target) in `config.yaml`.
- Audio: M4A/AAC. Source: public Spotify playlists listed in `playlists.txt` (unauthenticated mode). YouTube not supported in v1.
- Moving to a Raspberry Pi later: copy the repo + `.env` + `playlists.txt`, `docker compose up -d --build`, reinstall Tailscale on the Pi (step 8). Images are multi-arch.
