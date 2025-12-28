import itertools
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx
from rich import print
from rich.prompt import Confirm

import yt_dlp
from yt_dlp.utils import sanitize_filename

from ..exceptions import ViuError
from ..patterns import TORRENT_REGEX
from ..utils.networking import get_remote_filename
from .base import BaseDownloader
from .model import DownloadResult
from .params import DownloadParams

logger = logging.getLogger(__name__)


class YtDLPDownloader(BaseDownloader):
    def download(self, params: DownloadParams) -> DownloadResult:
        """Download video and optionally subtitles, returning detailed results."""
        try:
            video_path = None
            sub_paths = []
            merged_path = None

            logger.debug(f"Starting download for URL: {params.url}")
            logger.debug(f"Using Headers: {params.headers}")

            if TORRENT_REGEX.match(params.url):
                from .torrents import download_torrent_with_webtorrent_cli

                anime_title = sanitize_filename(params.anime_title)
                episode_title = sanitize_filename(params.episode_title)
                dest_dir = self.config.downloads_dir / anime_title
                dest_dir.mkdir(parents=True, exist_ok=True)

                video_path = dest_dir / episode_title
                video_path = download_torrent_with_webtorrent_cli(
                    video_path, params.url
                )
            else:
                video_path = self._download_video(params)

            if params.subtitles:
                sub_paths = self._download_subs(params)
                if params.merge:
                    merged_path = self._merge_subtitles(params, video_path, sub_paths)

            return DownloadResult(
                success=True,
                video_path=video_path,
                subtitle_paths=sub_paths,
                merged_path=merged_path,
                anime_title=params.anime_title,
                episode_title=params.episode_title,
            )

        except KeyboardInterrupt:
            print()
            print("Aborted!")
            return DownloadResult(
                success=False,
                error_message="Download aborted by user",
                anime_title=params.anime_title,
                episode_title=params.episode_title,
            )
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return DownloadResult(
                success=False,
                error_message=str(e),
                anime_title=params.anime_title,
                episode_title=params.episode_title,
            )

    def _download_video(self, params: DownloadParams) -> Path:
        anime_title = sanitize_filename(params.anime_title)
        episode_title = sanitize_filename(params.episode_title)
        opts = {
            "http_headers": params.headers,
            "outtmpl": f"{self.config.downloads_dir}/{anime_title}/{episode_title}.%(ext)s",
            "silent": params.silent,
            "verbose": params.verbose,
            "format": params.vid_format,
            "compat_opts": ("allow-unsafe-ext",)
            if params.force_unknown_ext
            else tuple(),
            "progress_hooks": params.progress_hooks,
            "nocheckcertificate": params.no_check_certificate,
            "logger": params.logger,
        }
        opts = opts
        if params.force_ffmpeg or params.hls_use_mpegts or params.hls_use_h264:
            opts = opts | {
                "external_downloader": {"default": "ffmpeg"},
                "external_downloader_args": {
                    "ffmpeg_i1": ["-v", "error", "-stats"],
                },
            }
        if params.hls_use_mpegts:
            opts = opts | {
                "hls_use_mpegts": True,
                "outtmpl": ".".join(opts["outtmpl"].split(".")[:-1])
                + ".ts",  # force .ts extension
            }
        elif params.hls_use_h264:
            opts = (
                opts
                | {
                    "external_downloader_args": opts["external_downloader_args"]
                    | {
                        "ffmpeg_o1": [
                            "-c:v",
                            "copy",
                            "-c:a",
                            "aac",
                            "-bsf:a",
                            "aac_adtstoasc",
                            "-q:a",
                            "1",
                            "-ac",
                            "2",
                            "-af",
                            "loudnorm=I=-22:TP=-2.5:LRA=11,alimiter=limit=-1.5dB",  # prevent clipping from HE-AAC to AAC convertion
                        ],
                    }
                }
            )

        # TODO: Confirm this type issues
        with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore
            info = ydl.extract_info(params.url, download=True)
            if info:
                _video_path = info["requested_downloads"][0]["filepath"]  # type: ignore
                if _video_path.endswith(".unknown_video"):
                    print("Normalizing path...")
                    _vid_path = _video_path.replace(".unknown_video", ".mp4")
                    shutil.move(_video_path, _vid_path)
                    _video_path = _vid_path
                    print("successfully normalized path")
                return Path(_video_path)
            else:
                dest_dir = self.config.downloads_dir / anime_title
                video_path = dest_dir / episode_title
                return video_path

    def _download_subs(self, params: DownloadParams) -> list[Path]:
        anime_title = sanitize_filename(params.anime_title)
        episode_title = sanitize_filename(params.episode_title)
        base = self.config.downloads_dir / anime_title
        downloaded_subs = []
        for i, sub in enumerate(params.subtitles):
            response = self.client.get(sub)
            try:
                response.raise_for_status()
            except httpx.HTTPError:
                raise ViuError("Failed to download sub: {e}")

            filename = get_remote_filename(response)
            if not filename:
                filename = (
                    episode_title + ".srt"
                    if len(params.subtitles)
                    else str(i) + episode_title + ".srt"
                )
            sub_path = base / filename
            with open(sub_path, "w") as f:
                f.write(response.text)
            downloaded_subs.append(sub_path)
        return downloaded_subs

    def _merge_subtitles(
        self, params, video_path: Path, sub_paths: list[Path]
    ) -> Path | None:
        """Merge subtitles with video and return the path to the merged file."""
        self.FFMPEG_EXECUTABLE = shutil.which("ffmpeg")
        if not self.FFMPEG_EXECUTABLE:
            raise ViuError("Please install ffmpeg in order to merge subs")
        merged_filename = video_path.stem + ".mkv"

        subs_input_args = list(
            itertools.chain.from_iterable(
                [["-i", str(sub_path)] for sub_path in sub_paths]
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            temp_output_path = temp_dir / merged_filename

            # Construct the ffmpeg command arguments
            args = [
                self.FFMPEG_EXECUTABLE,
                "-hide_banner",
                "-i",
                str(video_path),  # Main video input
                *subs_input_args,  # All subtitle inputs
                "-c",
                "copy",  # Copy streams without re-encoding
                # Map all video and audio streams from the first input (video_path)
                "-map",
                "0:v",
                "-map",
                "0:a",
            ]

            # Dynamically map subtitle streams from each subtitle input
            # Input indices for subtitle files start from 1 (0 is the video)
            for i in range(len(sub_paths)):
                args.extend(
                    ["-map", f"{i + 1}:s"]
                )  # Map all subtitle streams from input i+1

            args.append(str(temp_output_path))

            print(f"[cyan]Starting subtitle merge for {video_path.name}...[/]")

            # Run the ffmpeg command
            try:
                subprocess.run(args)
                final_output_path = video_path.parent / merged_filename

                if final_output_path.exists():
                    if not params.prompt or Confirm.ask(
                        f"File exists({final_output_path}) would you like to overwrite it",
                        default=True,
                    ):
                        print(
                            f"[yellow]Overwriting existing file: {final_output_path}[/]"
                        )
                        final_output_path.unlink()
                        shutil.move(str(temp_output_path), str(final_output_path))
                    else:
                        print("[yellow]Merge cancelled: File not overwritten.[/]")
                        return None
                else:
                    shutil.move(str(temp_output_path), str(final_output_path))

                # Clean up original files if requested
                if params.clean:
                    print("[cyan]Cleaning original files...[/]")
                    video_path.unlink()
                    for sub_path in sub_paths:
                        sub_path.unlink()

                print(
                    f"[green bold]Subtitles merged successfully.[/] Output file: {final_output_path}"
                )
                return final_output_path

            except Exception as e:
                print(f"[red bold]An unexpected error[/] occurred: {e}")
                return None
