"""
IINA player integration for Viu.

This module provides the IinaPlayer class,
which implements the BasePlayer interface for the IINA media player.
"""

import logging
import shutil
import subprocess
from pathlib import Path

from ....core.config import IinaConfig
from ....core.constants import PLATFORM
from ....core.exceptions import ViuError
from ....core.patterns import TORRENT_REGEX
from ....core.utils import detect
from ..base import BasePlayer
from ..params import PlayerParams
from ..types import PlayerResult

logger = logging.getLogger(__name__)

IINA_APP_EXECUTABLES = (
    Path("/Applications/IINA.app/Contents/MacOS/iina-cli"),
    Path.home() / "Applications/IINA.app/Contents/MacOS/iina-cli",
)


class IinaPlayer(BasePlayer):
    def __init__(self, config: IinaConfig):
        self.config = config
        self.executable = self._find_executable()

    def play(self, params: PlayerParams) -> PlayerResult:
        if PLATFORM != "darwin":
            raise ViuError("IINA is only supported on macOS.")

        if params.syncplay:
            raise ViuError("Viu's IINA integration does not support Syncplay.")

        if TORRENT_REGEX.search(params.url):
            raise ViuError("Unable to play torrents with IINA.")

        if not self.executable:
            raise ViuError(
                "IINA executable not found. Install IINA or expose `iina-cli` in PATH."
            )

        args = self._build_iina_command(params)

        subprocess.run(args, check=False, env=detect.get_clean_env())
        return PlayerResult(episode=params.episode)

    def play_with_ipc(self, params: PlayerParams, socket_path: str):
        raise NotImplementedError("play_with_ipc is not implemented for IINA player.")

    def _build_iina_command(self, params: PlayerParams) -> list[str]:
        args = [self.executable]
        args.append(params.url)

        if mpv_args := self._create_iina_mpv_options(params):
            args.append("--")
            args.extend(mpv_args)

        logger.debug("Starting IINA with args: %s", args)
        return args

    def _find_executable(self) -> str | None:
        executable = shutil.which("iina-cli")
        if executable:
            return executable

        for app_executable in IINA_APP_EXECUTABLES:
            if app_executable.exists():
                return str(app_executable)

        return None

    def _create_iina_mpv_options(self, params: PlayerParams) -> list[str]:
        mpv_args = []

        if params.title:
            mpv_args.append(f"--force-media-title={params.title}")
        if params.subtitles:
            for sub in params.subtitles:
                mpv_args.append(f"--sub-file={sub}")
        if params.start_time:
            mpv_args.append(f"--start={params.start_time}")
        if params.headers:
            header_str = ",".join(f"{k}:{v}" for k, v in params.headers.items())
            mpv_args.append(f"--http-header-fields={header_str}")
        if self.config.args:
            mpv_args.extend(
                arg.strip() for arg in self.config.args.split(",") if arg.strip()
            )

        return mpv_args


if __name__ == "__main__":
    from ....core.constants import APP_ASCII_ART

    print(APP_ASCII_ART)
    url = input("Enter the url you would like to stream: ")
    iina = IinaPlayer(IinaConfig())
    player_result = iina.play(PlayerParams(episode="", query="", url=url, title=""))
    print(player_result)
