from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from musiclib.models import NavidromeSong, Track

_FEAT_RE = re.compile(r"\b(feat\.?|ft\.?|featuring)\b.*$", re.IGNORECASE)
_BRACKET_FEAT_RE = re.compile(r"[\(\[]\s*(feat\.?|ft\.?|featuring)\b[^\)\]]*[\)\]]", re.IGNORECASE)
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.casefold()
    s = _BRACKET_FEAT_RE.sub(" ", s)
    s = _FEAT_RE.sub(" ", s)
    s = _PUNCT_RE.sub(" ", s)
    return " ".join(s.split())


def _tokens(s: str) -> set[str]:
    return set(normalize(s).split())


def build_index(songs: Iterable[NavidromeSong]) -> dict[str, list[NavidromeSong]]:
    """Index Navidrome songs by normalized title (the most stable field)."""
    index: dict[str, list[NavidromeSong]] = {}
    for song in songs:
        index.setdefault(normalize(song.title), []).append(song)
    return index


def match_track(track: Track, index: dict[str, list[NavidromeSong]]) -> str | None:
    """Map a Spotify track to a Navidrome song id.

    Matches on title, requiring the Spotify lead artist to be contained in the
    Navidrome artist credit (Navidrome stores the full "feat." credit while
    Spotify gives only the lead). Album then duration break ties.
    """
    candidates = index.get(normalize(track.title))
    if not candidates:
        return None

    lead = _tokens(track.primary_artist)
    compatible = [s for s in candidates if lead and lead <= _tokens(s.artist)]
    if not compatible:
        return None

    album = normalize(track.album)
    pool = [s for s in compatible if normalize(s.album) == album] or compatible

    target_s = track.duration_ms / 1000
    best = min(pool, key=lambda s: abs(s.duration_s - target_s))
    return best.id
