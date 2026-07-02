from __future__ import annotations

import json
import os


class State:
    def __init__(self, state_dir: str):
        self.path = os.path.join(state_dir, "playlists.json")
        self._map: dict[str, str] = {}

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def load(self) -> None:
        if not self.exists():
            self._map = {}
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            self._map = json.load(fh)

    def get_playlist_id(self, spotify_id: str) -> str | None:
        return self._map.get(spotify_id)

    def set_playlist_id(self, spotify_id: str, navidrome_id: str) -> None:
        self._map[spotify_id] = navidrome_id

    def save(self) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self._map, fh, indent=2)
        os.replace(tmp, self.path)
