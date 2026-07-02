import json
import pytest
from musiclib.savefile import parse, SaveFileError


def _song(name, artist, album, dur_s, sid, pos, isrc=""):
    return {
        "name": name, "artists": [artist], "artist": artist,
        "album_name": album, "duration": dur_s, "isrc": isrc,
        "song_id": sid, "list_name": "Gym Mix",
        "list_position": pos, "list_length": 2,
    }


def test_parse_builds_playlist_ordered_by_position(tmp_path):
    p = tmp_path / "pl.spotdl"
    # written out of order; parse must sort by list_position
    p.write_text(json.dumps([
        _song("Second", "B", "AlbB", 200, "s2", 2, isrc="US2"),
        _song("First", "A", "AlbA", 180, "s1", 1, isrc=""),
    ]))
    pl = parse(str(p), "PL1")
    assert pl.spotify_id == "PL1"
    assert pl.name == "Gym Mix"
    assert [t.title for t in pl.tracks] == ["First", "Second"]
    first = pl.tracks[0]
    assert first.primary_artist == "A"
    assert first.album == "AlbA"
    assert first.duration_ms == 180_000        # seconds -> ms
    assert first.isrc is None                  # "" -> None
    assert pl.tracks[1].isrc == "US2"


def test_parse_rejects_null_list_name(tmp_path):
    p = tmp_path / "track.spotdl"
    p.write_text(json.dumps([{
        "name": "X", "artists": ["A"], "artist": "A", "album_name": "Al",
        "duration": 100, "isrc": "", "song_id": "s1",
        "list_name": None, "list_position": None, "list_length": None,
    }]))
    with pytest.raises(SaveFileError):
        parse(str(p), "PL1")


def test_parse_rejects_empty_array(tmp_path):
    p = tmp_path / "empty.spotdl"
    p.write_text("[]")
    with pytest.raises(SaveFileError):
        parse(str(p), "PL1")


def test_parse_sync_format_dict(tmp_path):
    # `spotdl sync` writes {"type":"sync","query":[...],"songs":[...]}
    # rather than a plain list. parse must handle both shapes.
    p = tmp_path / "sync.spotdl"
    p.write_text(json.dumps({
        "type": "sync",
        "query": ["https://open.spotify.com/playlist/PL1"],
        "songs": [
            _song("Second", "B", "AlbB", 200, "s2", 2),
            _song("First", "A", "AlbA", 180, "s1", 1),
        ],
    }))
    pl = parse(str(p), "PL1")
    assert pl.name == "Gym Mix"
    assert [t.title for t in pl.tracks] == ["First", "Second"]


def test_parse_rejects_empty_sync_songs(tmp_path):
    p = tmp_path / "sync_empty.spotdl"
    p.write_text(json.dumps({"type": "sync", "query": [], "songs": []}))
    with pytest.raises(SaveFileError):
        parse(str(p), "PL1")
