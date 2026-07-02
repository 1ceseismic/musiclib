from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import yaml


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    navidrome_url: str
    navidrome_user: str
    navidrome_password: str
    music_dir: str
    state_dir: str
    audio_format: str
    scan_timeout_s: int
    log_level: str
    playlists_file: str


_REQUIRED_ENV = {
    "navidrome_user": "NAVIDROME_USER",
    "navidrome_password": "NAVIDROME_PASSWORD",
}


def load_config(yaml_path: str, env: Mapping[str, str]) -> Config:
    with open(yaml_path, "r", encoding="utf-8") as fh:
        prefs = yaml.safe_load(fh) or {}

    missing = [name for name in _REQUIRED_ENV.values() if not env.get(name)]
    if missing:
        raise ConfigError("Missing required env vars: " + ", ".join(sorted(missing)))

    return Config(
        navidrome_url=prefs["navidrome_url"],
        navidrome_user=env["NAVIDROME_USER"],
        navidrome_password=env["NAVIDROME_PASSWORD"],
        music_dir=prefs["music_dir"],
        state_dir=prefs["state_dir"],
        audio_format=prefs.get("audio_format", "m4a"),
        scan_timeout_s=int(prefs.get("scan_timeout_s", 300)),
        log_level=prefs.get("log_level", "INFO"),
        playlists_file=prefs.get("playlists_file", "/app/playlists.txt"),
    )
