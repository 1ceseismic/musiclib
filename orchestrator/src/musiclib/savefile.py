from __future__ import annotations

import json

from musiclib.models import Playlist, Track


class SaveFileError(Exception):
    pass


def parse(path: str, playlist_id: str) -> Playlist:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    # `spotdl save` writes a plain list of songs; `spotdl sync` writes
    # {"type": "sync", "query": [...], "songs": [...]}. Normalize both.
    songs = data.get("songs", []) if isinstance(data, dict) else data

    if not songs:
        raise SaveFileError(f"empty save file: {path}")

    list_name = songs[0].get("list_name")
    if not list_name:
        raise SaveFileError(
            f"save file has no list_name (not a public playlist?): {path}"
        )

    ordered = sorted(
        songs,
        key=lambda s: (s.get("list_position") is None, s.get("list_position") or 0),
    )

    tracks = tuple(
        Track(
            title=s.get("name", ""),
            artists=tuple(s.get("artists") or [s.get("artist", "")]),
            album=s.get("album_name", ""),
            duration_ms=int((s.get("duration") or 0) * 1000),
            isrc=(s.get("isrc") or None),
            spotify_id=s.get("song_id", ""),
        )
        for s in ordered
    )
    return Playlist(spotify_id=playlist_id, name=list_name, tracks=tracks)
