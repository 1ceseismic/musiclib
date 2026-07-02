from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass

from musiclib.playlists import PlaylistSpec


@dataclass(frozen=True)
class DownloadResult:
    playlist_id: str
    ok: bool
    returncode: int
    log: str
    save_file: str


def _stream_run(cmd: list[str]) -> tuple[int, str]:
    """Run cmd, streaming combined stdout/stderr to stdout live (so progress
    appears in logs) while capturing it for the result."""
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    captured: list[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        captured.append(line)
    proc.wait()
    return proc.returncode, "".join(captured)


class Downloader:
    def __init__(self, music_dir: str, state_dir: str, audio_format: str,
                 _runner=_stream_run):
        self.music_dir = music_dir
        self.state_dir = state_dir
        self.audio_format = audio_format
        self._runner = _runner

    def _run(self, cmd: list[str], playlist_id: str, save_file: str) -> DownloadResult:
        returncode, log = self._runner(cmd)
        return DownloadResult(
            playlist_id=playlist_id,
            ok=(returncode == 0),
            returncode=returncode,
            log=log,
            save_file=save_file,
        )

    def sync_playlist(self, spec: PlaylistSpec) -> DownloadResult:
        save_file = os.path.join(self.state_dir, f"{spec.playlist_id}.spotdl")
        output = os.path.join(self.music_dir, "{artist}", "{album}", "{title}.{output-ext}")
        cmd = [
            "spotdl", "sync", spec.url,
            "--save-file", save_file,
            "--output", output,
            "--format", self.audio_format,
        ]
        return self._run(cmd, spec.playlist_id, save_file)

    def save_metadata(self, spec: PlaylistSpec) -> DownloadResult:
        save_file = os.path.join(self.state_dir, f"{spec.playlist_id}.preview.spotdl")
        cmd = ["spotdl", "save", spec.url, "--save-file", save_file]
        return self._run(cmd, spec.playlist_id, save_file)
