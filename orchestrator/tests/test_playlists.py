import pytest
from musiclib.playlists import (
    PlaylistSpec, PlaylistsError, extract_playlist_id, load_playlists, select,
)


def test_select_filters_by_id():
    a = PlaylistSpec("urlA", "A")
    b = PlaylistSpec("urlB", "B")
    c = PlaylistSpec("urlC", "C")
    assert select([a, b, c], ["B"]) == [b]
    assert select([a, b, c], ["A", "C"]) == [a, c]
    assert select([a, b, c], ["Z"]) == []


def test_extract_id_from_url_with_query():
    assert extract_playlist_id("https://open.spotify.com/playlist/37i9dQZF1DXabc?si=xyz") == "37i9dQZF1DXabc"


def test_extract_id_from_uri():
    assert extract_playlist_id("spotify:playlist:37i9dQZF1DXabc") == "37i9dQZF1DXabc"


def test_extract_id_rejects_non_playlist():
    with pytest.raises(PlaylistsError):
        extract_playlist_id("https://open.spotify.com/track/123")


def test_load_skips_blanks_and_comments(tmp_path):
    p = tmp_path / "playlists.txt"
    p.write_text(
        "# my playlists\n"
        "\n"
        "https://open.spotify.com/playlist/AAA?si=1\n"
        "   # indented comment\n"
        "  https://open.spotify.com/playlist/BBB  \n"
    )
    specs = load_playlists(str(p))
    assert specs == [
        PlaylistSpec("https://open.spotify.com/playlist/AAA?si=1", "AAA"),
        PlaylistSpec("https://open.spotify.com/playlist/BBB", "BBB"),
    ]


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(PlaylistsError):
        load_playlists(str(tmp_path / "nope.txt"))


def test_load_empty_raises(tmp_path):
    p = tmp_path / "playlists.txt"
    p.write_text("# only comments\n\n")
    with pytest.raises(PlaylistsError):
        load_playlists(str(p))
