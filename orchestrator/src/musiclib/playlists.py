from __future__ import annotations

import re
from dataclasses import dataclass


class PlaylistsError(Exception):
    pass


@dataclass(frozen=True)
class PlaylistSpec:
    url: str
    playlist_id: str


_ID_RE = re.compile(r"playlist[/:]([A-Za-z0-9]+)")


def extract_playlist_id(url: str) -> str:
    match = _ID_RE.search(url)
    if not match:
        raise PlaylistsError(f"Not a Spotify playlist URL: {url}")
    return match.group(1)


def load_playlists(path: str) -> list[PlaylistSpec]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError as exc:
        raise PlaylistsError(f"playlists file not found: {path}") from exc

    specs: list[PlaylistSpec] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        specs.append(PlaylistSpec(url=line, playlist_id=extract_playlist_id(line)))

    if not specs:
        raise PlaylistsError(f"No playlist URLs found in {path}")
    return specs


def select(specs: list[PlaylistSpec], ids) -> list[PlaylistSpec]:
    """Keep only the specs whose playlist_id is in `ids` (order preserved)."""
    wanted = set(ids)
    return [s for s in specs if s.playlist_id in wanted]
