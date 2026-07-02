from musiclib.state import State


def test_roundtrip(tmp_path):
    s = State(str(tmp_path))
    assert s.exists() is False
    s.load()
    assert s.get_playlist_id("pl1") is None
    s.set_playlist_id("pl1", "n1")
    s.save()

    assert s.exists() is True
    s2 = State(str(tmp_path))
    s2.load()
    assert s2.get_playlist_id("pl1") == "n1"


def test_load_missing_is_empty(tmp_path):
    s = State(str(tmp_path))
    s.load()
    assert s.get_playlist_id("nope") is None
