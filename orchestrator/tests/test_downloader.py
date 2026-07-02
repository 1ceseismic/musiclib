from musiclib.downloader import Downloader, DownloadResult
from musiclib.playlists import PlaylistSpec


def _spec():
    return PlaylistSpec("https://open.spotify.com/playlist/PL1?si=x", "PL1")


# The injected runner takes the command and returns (returncode, captured_log),
# mirroring the real streaming runner.
def test_sync_builds_expected_command_without_credentials(tmp_path):
    captured = {}

    def runner(cmd):
        captured["cmd"] = cmd
        return (0, "out")

    dl = Downloader("/music", str(tmp_path), "m4a", _runner=runner)
    result = dl.sync_playlist(_spec())
    assert isinstance(result, DownloadResult)
    assert result.ok is True
    cmd = captured["cmd"]
    assert cmd[:3] == ["spotdl", "sync", "https://open.spotify.com/playlist/PL1?si=x"]
    assert "--format" in cmd and "m4a" in cmd
    assert "--client-id" not in cmd and "--client-secret" not in cmd
    assert result.save_file.endswith("PL1.spotdl")
    assert any(part == result.save_file for part in cmd)


def test_save_metadata_builds_save_command_without_credentials(tmp_path):
    captured = {}

    def runner(cmd):
        captured["cmd"] = cmd
        return (0, "out")

    dl = Downloader("/music", str(tmp_path), "m4a", _runner=runner)
    result = dl.save_metadata(_spec())
    cmd = captured["cmd"]
    assert cmd[:3] == ["spotdl", "save", "https://open.spotify.com/playlist/PL1?si=x"]
    assert "--client-id" not in cmd and "--client-secret" not in cmd
    assert result.save_file.endswith("PL1.preview.spotdl")
    assert any(part == result.save_file for part in cmd)


def test_failure_reported(tmp_path):
    dl = Downloader("/music", str(tmp_path), "m4a", _runner=lambda cmd: (1, "boom"))
    result = dl.sync_playlist(_spec())
    assert result.ok is False
    assert result.returncode == 1
    assert "boom" in result.log
