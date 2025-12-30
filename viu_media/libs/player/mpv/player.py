"""
MPV player integration for Viu.

This module provides the MpvPlayer class, which implements the BasePlayer interface for the MPV media player.
"""

import logging
import re
import shutil
import subprocess

from ....core.config import MpvConfig
from ....core.exceptions import ViuError
from ....core.patterns import TORRENT_REGEX, YOUTUBE_REGEX
from ....core.utils import detect
from ..base import BasePlayer
from ..params import PlayerParams
from ..types import PlayerResult

logger = logging.getLogger(__name__)

MPV_AV_TIME_PATTERN = re.compile(r"AV: ([0-9:]*) / ([0-9:]*) \(([0-9]*)%\)")


class MpvPlayer(BasePlayer):
    """
    MPV player implementation for Viu.

    Provides playback functionality using the MPV media player, supporting desktop, mobile, torrents, and syncplay.
    """

    def __init__(self, config: MpvConfig):
        """
        Initialize the MpvPlayer with the given MPV configuration.

        Args:
            config: MpvConfig object containing MPV-specific settings.
        """
        self.config = config
        self.executable = shutil.which("mpv")

    def play(self, params):
        """
        Play the given media using MPV, handling desktop, mobile, torrent, and syncplay scenarios.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            PlayerResult: Information about the playback session.
        """
        if TORRENT_REGEX.match(params.url) and detect.is_running_in_termux():
            raise ViuError("Unable to play torrents on termux")
        elif params.syncplay and detect.is_running_in_termux():
            raise ViuError("Unable to play with syncplay on termux")
        elif detect.is_running_in_termux():
            return self._play_on_mobile(params)
        else:
            return self._play_on_desktop(params)

    def _play_on_mobile(self, params) -> PlayerResult:
        """
        Play media on a mobile device using Android intents.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            PlayerResult: Information about the playback session.
        """
        if YOUTUBE_REGEX.match(params.url):
            args = [
                "nohup",
                "am",
                "start",
                "--user",
                "0",
                "-a",
                "android.intent.action.VIEW",
                "-d",
                params.url,
                "-n",
                "com.google.android.youtube/.UrlActivity",
            ]
        else:
            args = [
                "nohup",
                "am",
                "start",
                "--user",
                "0",
                "-a",
                "android.intent.action.VIEW",
                "-d",
                params.url,
                "-n",
                "is.xyz.mpv/.MPVActivity",
            ]

        subprocess.run(args)

        return PlayerResult(params.episode)

    def _play_on_desktop(self, params) -> PlayerResult:
        """
        Play media on a desktop environment using MPV.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            PlayerResult: Information about the playback session.
        """
        if not self.executable:
            raise ViuError("MPV executable not found in PATH.")

        if TORRENT_REGEX.search(params.url):
            return self._stream_on_desktop_with_webtorrent_cli(params)
        elif params.syncplay:
            return self._stream_on_desktop_with_syncplay(params)
        else:
            return self._stream_on_desktop_with_subprocess(params)

    def _stream_on_desktop_with_subprocess(self, params: PlayerParams) -> PlayerResult:
        """
        Stream media using MPV via subprocess, capturing playback times.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            PlayerResult: Information about the playback session, including stop and total time.
        """
        mpv_args = [self.executable, params.url]

        mpv_args.extend(self._create_mpv_cli_options(params))

        pre_args = self.config.pre_args.split(",") if self.config.pre_args else []

        stop_time = None
        total_time = None

        proc = subprocess.run(
            pre_args + mpv_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if proc.stdout:
            for line in reversed(proc.stdout.split("\n")):
                match = MPV_AV_TIME_PATTERN.search(line.strip())
                if match:
                    stop_time = match.group(1)
                    total_time = match.group(2)
                    break
        return PlayerResult(
            episode=params.episode, total_time=total_time, stop_time=stop_time
        )

    def play_with_ipc(self, params: PlayerParams, socket_path: str) -> subprocess.Popen:
        """
        Stream using MPV with IPC (Inter-Process Communication) for enhanced features.

        Args:
            params: PlayerParams object containing playback parameters.
            socket_path: Path to the IPC socket for player control.

        Returns:
            subprocess.Popen: The running MPV process.
        """
        mpv_args = [
            self.executable,
            f"--input-ipc-server={socket_path}",
            "--idle=yes",
            "--force-window=yes",
            params.url,
        ]

        # Add custom MPV arguments
        mpv_args.extend(self._create_mpv_cli_options(params))

        # Add pre-args if configured
        pre_args = self.config.pre_args.split(",") if self.config.pre_args else []

        logger.info(f"Starting MPV with IPC socket: {socket_path}")

        process = subprocess.Popen(pre_args + mpv_args)

        return process

    def _stream_on_desktop_with_webtorrent_cli(
        self, params: PlayerParams
    ) -> PlayerResult:
        """
        Stream torrent media using the webtorrent CLI and MPV.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            PlayerResult: Information about the playback session.
        """
        WEBTORRENT_CLI = shutil.which("webtorrent")
        if not WEBTORRENT_CLI:
            raise ViuError("Please Install webtorrent cli inorder to stream torrents")

        args = [WEBTORRENT_CLI, params.url, "--mpv"]
        if mpv_args := self._create_mpv_cli_options(params):
            args.append("--player-args")
            args.extend(mpv_args)

        subprocess.run(args)
        return PlayerResult(params.episode)

    def _stream_on_desktop_with_syncplay(self, params: PlayerParams) -> PlayerResult:
        """
        Stream media using Syncplay for synchronized playback with friends.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            PlayerResult: Information about the playback session.
        """
        SYNCPLAY_EXECUTABLE = shutil.which("syncplay")
        if not SYNCPLAY_EXECUTABLE:
            raise ViuError(
                "Please install syncplay to be able to stream with your friends"
            )
        args = [SYNCPLAY_EXECUTABLE, params.url]
        if mpv_args := self._create_mpv_cli_options(params):
            args.append("--")
            args.extend(mpv_args)
        subprocess.run(args)

        return PlayerResult(params.episode)

    def _create_mpv_cli_options(self, params: PlayerParams) -> list[str]:
        """
        Create a list of MPV CLI options based on playback parameters.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            list[str]: List of MPV CLI arguments.
        """
        mpv_args = []
        if params.headers:
            header_str = ",".join([f"{k}:{v}" for k, v in params.headers.items()])
            mpv_args.append(f"--http-header-fields={header_str}")

        if params.subtitles:
            for sub in params.subtitles:
                mpv_args.append(f"--sub-file={sub}")

        if params.start_time:
            mpv_args.append(f"--start={params.start_time}")

        if params.title:
            mpv_args.append(f"--title={params.title}")

        if self.config.args:
            mpv_args.extend(self.config.args.split(","))
        return mpv_args


if __name__ == "__main__":
    from ....core.constants import APP_ASCII_ART

    print(APP_ASCII_ART)
    url = input("Enter the url you would like to stream: ")
    mpv = MpvPlayer(MpvConfig())
    player_result = mpv.play(PlayerParams(episode="", query="", url=url, title=""))
    print(player_result)
