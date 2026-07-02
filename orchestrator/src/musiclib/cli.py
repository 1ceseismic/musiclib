from __future__ import annotations

import argparse
import logging
import os
import sys

from musiclib.config import load_config
from musiclib.downloader import Downloader
from musiclib.navidrome_client import NavidromeClient
from musiclib.playlists import load_playlists, select
from musiclib.state import State
from musiclib.sync import run_sync


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="musiclib")
    parser.add_argument("--config", default="/app/config.yaml")
    parser.add_argument("--apply", action="store_true", help="write playlists (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="force dry-run")
    parser.add_argument("--only", action="append", metavar="PLAYLIST_ID",
                        help="sync only these playlist id(s) (repeatable)")
    args = parser.parse_args(argv)

    cfg = load_config(args.config, os.environ)
    logging.basicConfig(level=cfg.log_level, format="%(asctime)s %(levelname)s %(message)s")

    dry_run = not args.apply or args.dry_run

    specs = load_playlists(cfg.playlists_file)
    if args.only:
        specs = select(specs, args.only)
        if not specs:
            logging.getLogger("musiclib").warning(
                "--only matched no playlists in %s: %s", cfg.playlists_file, args.only)
            return 0
    downloader = Downloader(cfg.music_dir, cfg.state_dir, cfg.audio_format)
    navidrome = NavidromeClient(cfg.navidrome_url, cfg.navidrome_user, cfg.navidrome_password)
    state = State(cfg.state_dir)
    state.load()

    summary = run_sync(
        specs, navidrome, downloader, state,
        scan_timeout_s=cfg.scan_timeout_s,
        unmatched_log_path=os.path.join(cfg.state_dir, "unmatched.log"),
        dry_run=dry_run,
    )
    logging.getLogger("musiclib").info("Done (dry_run=%s): %s", dry_run, summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
