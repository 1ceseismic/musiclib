from musiclib.matcher import normalize, build_index, match_track
from musiclib.models import Track, NavidromeSong


def test_normalize_strips_feat_and_accents():
    assert normalize("Beyoncé - Déjà Vu (feat. Jay-Z)") == normalize("beyonce - deja vu")
    assert normalize("Song ft. Someone") == normalize("song")


def test_normalize_collapses_punctuation():
    assert normalize("Hello,  World!!") == "hello world"


def test_normalize_keeps_unicode_letters():
    # CJK/non-latin letters must survive (not be stripped to empty)
    assert normalize("空想") == "空想"


def _track(title, artist, album, ms, artists=None):
    return Track(title, artists or (artist,), album, ms, None, "sp1")


def test_match_exact_single_candidate():
    song = NavidromeSong("n1", "Title", "Artist", "Album", 200)
    idx = build_index([song])
    t = _track("Title", "Artist", "Album", 200_000)
    assert match_track(t, idx) == "n1"


def test_match_when_navidrome_has_featured_artists():
    # Spotify gives the lead artist; Navidrome stores lead + featured.
    song = NavidromeSong("n1", "5", "Dean Blunt Elias Ronnenfelt", "Lucre", 200)
    idx = build_index([song])
    t = _track("5", "Dean Blunt", "Lucre", 200_000)
    assert match_track(t, idx) == "n1"


def test_match_rejects_different_artist_same_title():
    idx = build_index([NavidromeSong("n1", "Hallelujah", "Bob", "X", 200)])
    t = _track("Hallelujah", "Alice", "X", 200_000)
    assert match_track(t, idx) is None


def test_match_disambiguates_by_duration():
    s_short = NavidromeSong("short", "Title", "Artist", "Album", 180)
    s_long = NavidromeSong("long", "Title", "Artist", "Album", 240)
    idx = build_index([s_short, s_long])
    t = _track("Title", "Artist", "Album", 239_000)  # ~239s -> long
    assert match_track(t, idx) == "long"


def test_match_prefers_same_album():
    s_a = NavidromeSong("a", "Title", "Artist", "Album A", 200)
    s_b = NavidromeSong("b", "Title", "Artist", "Album B", 200)
    idx = build_index([s_a, s_b])
    t = _track("Title", "Artist", "Album B", 200_000)
    assert match_track(t, idx) == "b"


def test_match_returns_none_when_absent():
    idx = build_index([NavidromeSong("n1", "Other", "Artist", "Album", 200)])
    t = _track("Title", "Artist", "Album", 200_000)
    assert match_track(t, idx) is None
