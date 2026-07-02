import json
from musiclib.sync import run_sync, RunSummary
from musiclib.models import NavidromeSong
from musiclib.playlists import PlaylistSpec
from musiclib.downloader import DownloadResult


def _write_savefile(path, list_name, songs):
    data = []
    for s in songs:
        data.append({
            "name": s["name"], "artists": [s["artist"]], "artist": s["artist"],
            "album_name": s["album"], "duration": s["dur_s"], "isrc": "",
            "song_id": s["sid"], "list_name": list_name,
            "list_position": s["pos"], "list_length": len(songs),
        })
    path.write_text(json.dumps(data))


def _index_songs():
    return [NavidromeSong("n1", "Song One", "Artist X", "Album A", 200)]


class FakeNavidrome:
    def __init__(self):
        self.scans = 0
        self.upserts = []
    def start_scan(self):
        self.scans += 1
    def wait_for_scan(self, timeout_s):
        pass
    def list_songs(self):
        return _index_songs()
    def get_playlists(self):
        return {}
    def upsert_playlist(self, name, song_ids, playlist_id=None):
        self.upserts.append((name, song_ids, playlist_id))
        return "navpl1"


class FakeState:
    def __init__(self):
        self.map = {}
        self.saved = False
    def get_playlist_id(self, sid):
        return self.map.get(sid)
    def set_playlist_id(self, sid, nid):
        self.map[sid] = nid
    def save(self):
        self.saved = True


def _make_downloader(tmp_path, list_name="Gym Mix", songs=None, raise_on=None):
    songs = songs or [
        {"name": "Song One", "artist": "Artist X", "album": "Album A", "dur_s": 200, "sid": "t1", "pos": 1},
        {"name": "Missing", "artist": "Nobody", "album": "Nowhere", "dur_s": 100, "sid": "t2", "pos": 2},
    ]

    class FakeDownloader:
        def __init__(self):
            self.synced = []
            self.previewed = []
        def _emit(self, spec, suffix, bucket):
            if raise_on and spec.playlist_id == raise_on:
                raise OSError("spotdl failed")
            bucket.append(spec.playlist_id)
            path = tmp_path / f"{spec.playlist_id}{suffix}"
            _write_savefile(path, list_name, songs)
            return DownloadResult(spec.playlist_id, True, 0, "", str(path))
        def sync_playlist(self, spec):
            return self._emit(spec, ".spotdl", self.synced)
        def save_metadata(self, spec):
            return self._emit(spec, ".preview.spotdl", self.previewed)

    return FakeDownloader()


def _specs():
    return [PlaylistSpec("https://open.spotify.com/playlist/pl1", "pl1")]


def test_apply_run_matches_and_upserts(tmp_path):
    nav, st, dl = FakeNavidrome(), FakeState(), _make_downloader(tmp_path)
    log = tmp_path / "unmatched.log"
    summary = run_sync(_specs(), nav, dl, st,
                       scan_timeout_s=10, unmatched_log_path=str(log), dry_run=False)
    assert isinstance(summary, RunSummary)
    assert summary.playlists == 1
    assert summary.matched == 1
    assert summary.unmatched == 1
    assert dl.synced == ["pl1"]
    assert dl.previewed == []
    assert nav.scans == 1
    assert nav.upserts == [("Gym Mix", ["n1"], None)]
    assert st.map["pl1"] == "navpl1"
    assert st.saved is True
    assert "Missing" in log.read_text()


def test_dry_run_uses_save_metadata_and_writes_nothing(tmp_path):
    nav, st, dl = FakeNavidrome(), FakeState(), _make_downloader(tmp_path)
    summary = run_sync(_specs(), nav, dl, st,
                       scan_timeout_s=10, unmatched_log_path=str(tmp_path / "u.log"),
                       dry_run=True)
    assert summary.matched == 1
    assert dl.previewed == ["pl1"]     # metadata-only
    assert dl.synced == []             # no audio download
    assert nav.scans == 0              # no scan
    assert nav.upserts == []           # no playlist writes
    assert st.saved is False           # no state write


def test_run_continues_when_a_playlist_raises(tmp_path):
    nav, st = FakeNavidrome(), FakeState()
    dl = _make_downloader(tmp_path, raise_on="bad")
    specs = [
        PlaylistSpec("https://open.spotify.com/playlist/bad", "bad"),
        PlaylistSpec("https://open.spotify.com/playlist/pl1", "pl1"),
    ]
    summary = run_sync(specs, nav, dl, st,
                       scan_timeout_s=10, unmatched_log_path=str(tmp_path / "u.log"),
                       dry_run=False)
    assert dl.synced == ["pl1"]            # bad raised, good still processed
    assert summary.download_failures == 1
    assert summary.playlists == 1
    assert nav.upserts == [("Gym Mix", ["n1"], None)]
    assert st.map.get("pl1") == "navpl1"
    assert st.saved is True


def test_run_continues_when_upsert_raises(tmp_path):
    songs = [{"name": "Song One", "artist": "Artist X", "album": "Album A",
              "dur_s": 200, "sid": "t1", "pos": 1}]

    class DL:
        def __init__(self):
            self.synced = []

        def _emit(self, spec, suffix):
            self.synced.append(spec.playlist_id)
            path = tmp_path / f"{spec.playlist_id}{suffix}"
            # name the playlist after its id so we can target the upsert failure
            _write_savefile(path, spec.playlist_id, songs)
            return DownloadResult(spec.playlist_id, True, 0, "", str(path))

        def sync_playlist(self, spec):
            return self._emit(spec, ".spotdl")

        def save_metadata(self, spec):
            return self._emit(spec, ".preview.spotdl")

    class Nav(FakeNavidrome):
        def upsert_playlist(self, name, song_ids, playlist_id=None):
            if name == "bad":
                raise RuntimeError("subsonic 500")
            self.upserts.append((name, song_ids, playlist_id))
            return "nav-" + name

    nav, st, dl = Nav(), FakeState(), DL()
    specs = [
        PlaylistSpec("https://open.spotify.com/playlist/bad", "bad"),
        PlaylistSpec("https://open.spotify.com/playlist/good", "good"),
    ]
    summary = run_sync(specs, nav, dl, st, scan_timeout_s=10,
                       unmatched_log_path=str(tmp_path / "u.log"), dry_run=False)
    assert nav.upserts == [("good", ["n1"], None)]   # bad raised; good still upserted
    assert st.map.get("good") == "nav-good"
    assert st.map.get("bad") is None
    assert st.saved is True                          # save still ran despite the failure
    assert summary.download_failures == 0
