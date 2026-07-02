from __future__ import annotations

import logging
from dataclasses import dataclass

from musiclib.matcher import build_index, match_track
from musiclib.savefile import parse as parse_savefile

_log = logging.getLogger("musiclib.sync")


@dataclass
class RunSummary:
    playlists: int
    matched: int
    unmatched: int
    download_failures: int


def run_sync(
    playlist_specs,
    navidrome,
    downloader,
    state,
    *,
    scan_timeout_s: int,
    unmatched_log_path: str,
    dry_run: bool,
    logger: logging.Logger | None = None,
) -> RunSummary:
    log = logger or _log

    playlists = []
    download_failures = 0
    total = len(playlist_specs)
    for idx, spec in enumerate(playlist_specs, 1):
        log.info("Downloading %d/%d: %s%s", idx, total, spec.playlist_id,
                 " (metadata only)" if dry_run else "")
        try:
            if dry_run:
                result = downloader.save_metadata(spec)
            else:
                result = downloader.sync_playlist(spec)
            if not result.ok:
                download_failures += 1
                log.warning("Download failed for %s (rc=%s)", spec.playlist_id, result.returncode)
                continue
            playlists.append(parse_savefile(result.save_file, spec.playlist_id))
        except Exception:
            download_failures += 1
            log.exception("Discovery failed for %s; continuing", spec.playlist_id)
    log.info("Loaded %d playlist(s)", len(playlists))

    if not dry_run:
        navidrome.start_scan()
        navidrome.wait_for_scan(scan_timeout_s)

    index = build_index(navidrome.list_songs())

    matched_total = 0
    unmatched_lines: list[str] = []
    for pl in playlists:
        song_ids: list[str] = []
        for track in pl.tracks:
            song_id = match_track(track, index)
            if song_id:
                song_ids.append(song_id)
            else:
                unmatched_lines.append(f"{pl.name}\t{track.primary_artist} - {track.title}")
        matched_total += len(song_ids)
        log.info("%s: %d/%d matched", pl.name, len(song_ids), len(pl.tracks))
        if not dry_run and song_ids:
            try:
                existing = state.get_playlist_id(pl.spotify_id)
                new_id = navidrome.upsert_playlist(pl.name, song_ids, existing)
                state.set_playlist_id(pl.spotify_id, new_id)
            except Exception:
                log.exception("Playlist upsert failed for %s; continuing", pl.name)

    with open(unmatched_log_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(unmatched_lines))

    if not dry_run:
        state.save()

    return RunSummary(
        playlists=len(playlists),
        matched=matched_total,
        unmatched=len(unmatched_lines),
        download_failures=download_failures,
    )
