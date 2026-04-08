"""
IINA player integration for Viu.

This module provides the IinaPlayer class,
which implements the BasePlayer interface for the IINA media player.
"""

import logging
import shutil
import subprocess
from pathlib import Path

from ....core.constants import PLATFORM
from ....core.exceptions import ViuError
from ....core.patterns import TORRENT_REGEX
from ....core.utils import detect
from ....core.config import IinaConfig
from ..base import BasePlayer
from ..params import PlayerParams
from ..types import PlayerResult

logger = logging.getLogger(__name__)

IINA_APP_EXECUTABLES = (
    Path("/Applications/IINA.app/Contents/MacOS/iina-cli"),
    Path("/Applications/IINA.app/Contents/MacOS/IINA"),
    Path.home() / "Applications/IINA.app/Contents/MacOS/iina-cli",
    Path.home() / "Applications/IINA.app/Contents/MacOS/IINA",
)


class IinaPlayer(BasePlayer):
    def __init__(self, config: IinaConfig):
        self.config = config
        self.executable = self._find_executable()

    def play(self, params: PlayerParams) -> PlayerResult:
        if PLATFORM != "darwin":
            raise ViuError("IINA is only supported on macOS.")

        if params.syncplay:
            raise ViuError("Syncplay is not supported for IINA.")

        if TORRENT_REGEX.search(params.url):
            raise ViuError("Torrent playback is not supported for IINA.")

        return self._play_on_desktop(params)

    def play_with_ipc(self, params: PlayerParams, socket_path: str):
        raise NotADirectoryError("play_with_ipc is not implemented for IINA player.")

    def _play_on_desktop(self, params: PlayerParams) -> PlayerResult:
        if not self.executable:
            raise ViuError(
                "IINA executable not found. Install IINA or expose iina-cli in PATH."
            )

        args = [self.executable, params.url]
        args.extend(self._create_iina_cli_options(params))

        subprocess.run(
            args,
            encoding="utf-8",
            check=False,
            env=detect.get_clean_env(),
        )
        return PlayerResult(episode=params.episode)

    def _find_executable(self) -> str | None:
        for executable_name in ("iina-cli", "iina"):
            executable = shutil.which(executable_name)
            if executable:
                return executable

        for app_executable in IINA_APP_EXECUTABLES:
            if app_executable.exists():
                return str(app_executable)

        return None

    def _create_iina_cli_options(self, params: PlayerParams) -> list[str]:
        iina_args = []

        if params.headers:
            header_str = ",".join([f"{k}:{v}" for k, v in params.headers.items()])
            iina_args.append(f"--http-header-fields={header_str}")
        if params.subtitles:
            for sub in params.subtitles:
                iina_args.append(f"--sub-file={sub}")
        if params.start_time:
            iina_args.append(f"--start={params.start_time}")
        if params.title:
            iina_args.append(f"--title={params.title}")
        if self.config.args:
            iina_args.extend(self.config.args.split(","))

        return iina_args


if __name__ == "__main__":
    from ....core.constants import APP_ASCII_ART

    print(APP_ASCII_ART)
    url = input("Enter the url you would like to stream: ")
    iina = IinaPlayer(IinaConfig())
    player_result = iina.play(PlayerParams(episode="", query="", url=url, title=""))
    print(player_result)
