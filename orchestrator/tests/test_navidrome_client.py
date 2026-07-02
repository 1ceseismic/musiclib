import json

from musiclib.navidrome_client import NavidromeClient
from musiclib.models import NavidromeSong


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class FakeSession:
    """Records calls and returns queued payloads keyed by endpoint."""

    def __init__(self, payloads):
        self.payloads = payloads  # dict: endpoint -> list of payloads (popped) or single
        self.calls = []

    def get(self, url, params=None, timeout=None):
        endpoint = url.rsplit("/", 1)[-1]
        self.calls.append((endpoint, params))
        payload = self.payloads[endpoint]
        if isinstance(payload, list):
            payload = payload.pop(0)
        return FakeResponse(payload)


def _ok(body):
    return {"subsonic-response": {"status": "ok", **body}}


def test_list_songs_paginates():
    page1 = _ok({"searchResult3": {"song": [
        {"id": "s1", "title": "T1", "artist": "A1", "album": "Al1", "duration": 200},
    ]}})
    page2 = _ok({"searchResult3": {}})  # empty -> stop
    sess = FakeSession({"search3": [page1, page2]})
    client = NavidromeClient("http://nav:4533", "admin", "pw", _session=sess)
    songs = client.list_songs()
    assert songs == [NavidromeSong("s1", "T1", "A1", "Al1", 200)]


def test_upsert_creates_and_returns_id():
    sess = FakeSession({"createPlaylist": _ok({"playlist": {"id": "p99"}})})
    client = NavidromeClient("http://nav:4533", "admin", "pw", _session=sess)
    pid = client.upsert_playlist("Gym Mix", ["s1", "s2"])
    assert pid == "p99"
    endpoint, params = sess.calls[0]
    assert endpoint == "createPlaylist"
    assert params["name"] == "Gym Mix"
    assert params["songId"] == ["s1", "s2"]


def test_scan_status_parsed():
    sess = FakeSession({"getScanStatus": _ok({"scanStatus": {"scanning": False, "count": 42}})})
    client = NavidromeClient("http://nav:4533", "admin", "pw", _session=sess)
    assert client.get_scan_status() == (False, 42)


def test_auth_params_present():
    sess = FakeSession({"getScanStatus": _ok({"scanStatus": {"scanning": False, "count": 0}})})
    client = NavidromeClient("http://nav:4533", "admin", "pw", _session=sess)
    client.get_scan_status()
    _, params = sess.calls[0]
    assert params["u"] == "admin"
    assert "t" in params and "s" in params and params["f"] == "json"
