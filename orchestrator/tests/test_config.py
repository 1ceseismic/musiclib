import pytest
from musiclib.config import load_config, ConfigError

YAML = """
navidrome_url: http://navidrome:4533
music_dir: /music
state_dir: /state
audio_format: m4a
scan_timeout_s: 300
log_level: INFO
playlists_file: /app/playlists.txt
"""

ENV = {
    "NAVIDROME_USER": "admin",
    "NAVIDROME_PASSWORD": "pw",
}


def test_load_merges_yaml_and_env(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(YAML)
    cfg = load_config(str(p), ENV)
    assert cfg.navidrome_url == "http://navidrome:4533"
    assert cfg.navidrome_user == "admin"
    assert cfg.audio_format == "m4a"
    assert cfg.scan_timeout_s == 300
    assert cfg.playlists_file == "/app/playlists.txt"


def test_playlists_file_defaults(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(
        "navidrome_url: http://navidrome:4533\n"
        "music_dir: /music\nstate_dir: /state\n"
    )
    cfg = load_config(str(p), ENV)
    assert cfg.playlists_file == "/app/playlists.txt"


def test_missing_secret_lists_all_missing(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(YAML)
    with pytest.raises(ConfigError) as exc:
        load_config(str(p), {})
    msg = str(exc.value)
    assert "NAVIDROME_USER" in msg and "NAVIDROME_PASSWORD" in msg
