"""
VLC player integration for Viu.

This module provides the VlcPlayer class, which implements the BasePlayer interface for the VLC media player.
"""

import logging
import shutil
import subprocess

from ....core.config import VlcConfig
from ....core.exceptions import ViuError
from ....core.patterns import TORRENT_REGEX, YOUTUBE_REGEX
from ....core.utils import detect
from ..base import BasePlayer
from ..params import PlayerParams
from ..types import PlayerResult

logger = logging.getLogger(__name__)


class VlcPlayer(BasePlayer):
    """
    VLC player implementation for Viu.

    Provides playback functionality using the VLC media player, supporting desktop, mobile, and torrent scenarios.
    """

    def __init__(self, config: VlcConfig):
        """
        Initialize the VlcPlayer with the given VLC configuration.

        Args:
            config: VlcConfig object containing VLC-specific settings.
        """
        self.config = config
        self.executable = shutil.which("vlc")

    def play(self, params: PlayerParams) -> PlayerResult:
        """
        Play the given media using VLC, handling desktop, mobile, and torrent scenarios.

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

    def play_with_ipc(self, params: PlayerParams, socket_path: str) -> subprocess.Popen:
        """
        Not implemented for VLC player.
        """
        raise NotImplementedError("play_with_ipc is not implemented for VLC player.")

    def _play_on_mobile(self, params: PlayerParams) -> PlayerResult:
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
                "org.videolan.vlc/org.videolan.vlc.gui.video.VideoPlayerActivity",
                "-e",
                "title",
                params.title,
            ]

        subprocess.run(args)

        return PlayerResult(episode=params.episode)

    def _play_on_desktop(self, params: PlayerParams) -> PlayerResult:
        """
        Play media on a desktop environment using VLC.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            PlayerResult: Information about the playback session.
        """
        if not self.executable:
            raise ViuError("VLC executable not found in PATH.")

        if TORRENT_REGEX.search(params.url):
            return self._stream_on_desktop_with_webtorrent_cli(params)

        args = [self.executable, params.url]
        if params.subtitles:
            for sub in params.subtitles:
                args.extend(["--sub-file", sub])
                break
        if params.title:
            args.extend(["--video-title", params.title])

        if self.config.args:
            args.extend(self.config.args.split(","))

        subprocess.run(args, encoding="utf-8")
        return PlayerResult(episode=params.episode)

    def _stream_on_desktop_with_webtorrent_cli(
        self, params: PlayerParams
    ) -> PlayerResult:
        """
        Stream torrent media using the webtorrent CLI and VLC.

        Args:
            params: PlayerParams object containing playback parameters.

        Returns:
            PlayerResult: Information about the playback session.
        """
        WEBTORRENT_CLI = shutil.which("webtorrent")
        if not WEBTORRENT_CLI:
            raise ViuError("Please Install webtorrent cli inorder to stream torrents")

        args = [WEBTORRENT_CLI, params.url, "--vlc"]

        if self.config.args:
            args.append("--player-args")
            args.extend(self.config.args.split(","))

        subprocess.run(args)
        return PlayerResult(episode=params.episode)


if __name__ == "__main__":
    from ....core.constants import APP_ASCII_ART

    print(APP_ASCII_ART)
    url = input("Enter the url you would like to stream: ")
    vlc = VlcPlayer(VlcConfig())
    player_result = vlc.play(PlayerParams(url=url, title="", query="", episode=""))
    print(player_result)
