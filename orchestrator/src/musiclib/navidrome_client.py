from __future__ import annotations

import hashlib
import secrets
import time

from musiclib.models import NavidromeSong

API_VERSION = "1.16.1"


class NavidromeError(Exception):
    pass


class NavidromeClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        client: str = "musiclib",
        _session=None,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = client
        if _session is not None:
            self.session = _session
        else:
            import requests

            self.session = requests.Session()

    def _auth_params(self) -> dict:
        salt = secrets.token_hex(8)
        token = hashlib.md5((self.password + salt).encode("utf-8")).hexdigest()
        return {
            "u": self.username,
            "t": token,
            "s": salt,
            "v": API_VERSION,
            "c": self.client,
            "f": "json",
        }

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        merged = self._auth_params()
        if params:
            merged.update(params)
        url = f"{self.base_url}/rest/{endpoint}"
        resp = self.session.get(url, params=merged, timeout=60)
        resp.raise_for_status()
        body = resp.json()["subsonic-response"]
        if body.get("status") != "ok":
            raise NavidromeError(f"{endpoint}: {body.get('error')}")
        return body

    def start_scan(self) -> None:
        self._get("startScan")

    def get_scan_status(self) -> tuple[bool, int]:
        status = self._get("getScanStatus")["scanStatus"]
        return bool(status.get("scanning", False)), int(status.get("count", 0))

    def wait_for_scan(self, timeout_s: int, poll_s: float = 2.0, _sleep=time.sleep) -> None:
        elapsed = 0.0
        while elapsed < timeout_s:
            scanning, _ = self.get_scan_status()
            if not scanning:
                return
            _sleep(poll_s)
            elapsed += poll_s

    def list_songs(self) -> list[NavidromeSong]:
        songs: list[NavidromeSong] = []
        offset = 0
        page_size = 500
        while True:
            body = self._get(
                "search3",
                {"query": "", "songCount": page_size, "songOffset": offset,
                 "artistCount": 0, "albumCount": 0},
            )
            page = body.get("searchResult3", {}).get("song", [])
            if not page:
                break
            for s in page:
                songs.append(
                    NavidromeSong(
                        id=s["id"],
                        title=s.get("title", ""),
                        artist=s.get("artist", ""),
                        album=s.get("album", ""),
                        duration_s=int(s.get("duration", 0)),
                    )
                )
            offset += len(page)
        return songs

    def get_playlists(self) -> dict[str, str]:
        body = self._get("getPlaylists")
        items = body.get("playlists", {}).get("playlist", [])
        return {p["name"]: p["id"] for p in items}

    def upsert_playlist(
        self, name: str, song_ids: list[str], playlist_id: str | None = None
    ) -> str:
        params: dict = {"name": name, "songId": song_ids}
        if playlist_id:
            params["playlistId"] = playlist_id
        body = self._get("createPlaylist", params)
        return body["playlist"]["id"]
