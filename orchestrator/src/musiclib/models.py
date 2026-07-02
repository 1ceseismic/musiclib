from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    title: str
    artists: tuple[str, ...]
    album: str
    duration_ms: int
    isrc: str | None
    spotify_id: str

    @property
    def primary_artist(self) -> str:
        return self.artists[0] if self.artists else ""


@dataclass(frozen=True)
class Playlist:
    spotify_id: str
    name: str
    tracks: tuple[Track, ...]


@dataclass(frozen=True)
class NavidromeSong:
    id: str
    title: str
    artist: str
    album: str
    duration_s: int
