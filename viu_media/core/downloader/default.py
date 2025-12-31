"""Default downloader implementation without yt-dlp dependency."""

import itertools
import logging
import shutil
import subprocess
import tempfile
import urllib.parse
from pathlib import Path
from typing import Optional

import httpx
from rich import print
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.prompt import Confirm
from ..utils.file import sanitize_filename
from ..utils.detect import get_clean_env
from ..exceptions import ViuError
from ..patterns import TORRENT_REGEX
from ..utils.networking import get_remote_filename
from .base import BaseDownloader
from .model import DownloadResult
from .params import DownloadParams

logger = logging.getLogger(__name__)


class DefaultDownloader(BaseDownloader):
    """Default downloader that uses httpx for downloads without yt-dlp dependency."""

    def download(self, params: DownloadParams) -> DownloadResult:
        """Download video and optionally subtitles, returning detailed results."""
        try:
            video_path = None
            sub_paths = []
            merged_path = None

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
        """Download video using httpx with progress tracking."""
        anime_title = sanitize_filename(params.anime_title)
        episode_title = sanitize_filename(params.episode_title)

        dest_dir = self.config.downloads_dir / anime_title
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Get file extension from URL or headers
        file_extension = self._get_file_extension(params.url, params.headers)
        if params.force_unknown_ext and not file_extension:
            file_extension = ".unknown_video"
        elif not file_extension:
            file_extension = ".mp4"  # default fallback

        video_path = dest_dir / f"{episode_title}{file_extension}"

        # Check if file already exists
        if video_path.exists() and not params.prompt:
            logger.info(f"File already exists: {video_path}")
            return video_path
        elif video_path.exists() and params.prompt:
            if not Confirm.ask(
                f"File exists: {video_path.name}. Overwrite?", default=False
            ):
                return video_path

        # Download with progress tracking
        self._download_with_progress(
            params.url, video_path, params.headers, params.silent, params.progress_hooks
        )

        # Handle unknown video extension normalization
        if video_path.suffix == ".unknown_video":
            normalized_path = video_path.with_suffix(".mp4")
            print("Normalizing path...")
            shutil.move(video_path, normalized_path)
            print("Successfully normalized path")
            return normalized_path

        return video_path

    def _get_file_extension(self, url: str, headers: dict) -> str:
        """Determine file extension from URL or content headers."""
        # First try to get from URL
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        if path and "." in path:
            return Path(path).suffix

        # Try to get from response headers
        try:
            with self.client.stream("HEAD", url, headers=headers) as response:
                content_type = response.headers.get("content-type", "")
                if "video/mp4" in content_type:
                    return ".mp4"
                elif "video/webm" in content_type:
                    return ".webm"
                elif "video/x-matroska" in content_type:
                    return ".mkv"
                elif "video/x-msvideo" in content_type:
                    return ".avi"
                elif "video/quicktime" in content_type:
                    return ".mov"

                # Try content-disposition header
                content_disposition = response.headers.get("content-disposition", "")
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip("\"'")
                    return Path(filename).suffix
        except Exception:
            pass

        return ""

    def _download_with_progress(
        self,
        url: str,
        output_path: Path,
        headers: dict,
        silent: bool,
        progress_hooks: list | None = None,
    ):
        """Download file with rich progress bar and progress hooks."""
        progress_hooks = progress_hooks or []

        # Always show download start message
        print(f"[cyan]Starting download of {output_path.name}...[/]")

        try:
            with self.client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                # Initialize progress display - always show progress
                progress = None
                task_id = None

                if total_size > 0:
                    progress = Progress(
                        TextColumn(
                            "[bold blue]{task.fields[filename]}", justify="right"
                        ),
                        BarColumn(bar_width=None),
                        "[progress.percentage]{task.percentage:>3.1f}%",
                        "•",
                        DownloadColumn(),
                        "•",
                        TransferSpeedColumn(),
                        "•",
                        TimeRemainingColumn(),
                    )
                else:
                    # Progress without total size (indeterminate)
                    progress = Progress(
                        TextColumn(
                            "[bold blue]{task.fields[filename]}", justify="right"
                        ),
                        TextColumn("[green]{task.completed} bytes"),
                        "•",
                        TransferSpeedColumn(),
                    )

                progress.start()
                task_id = progress.add_task(
                    "download",
                    filename=output_path.name,
                    total=total_size if total_size > 0 else None,
                )

                try:
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                chunk_size = len(chunk)
                                downloaded += chunk_size

                                # Always update progress bar
                                if progress is not None and task_id is not None:
                                    progress.update(task_id, advance=chunk_size)

                                # Call progress hooks
                                if progress_hooks:
                                    progress_info = {
                                        "downloaded_bytes": downloaded,
                                        "total_bytes": total_size,
                                        "filename": output_path.name,
                                        "status": "downloading",
                                    }
                                    for hook in progress_hooks:
                                        try:
                                            hook(progress_info)
                                        except Exception as e:
                                            logger.warning(f"Progress hook failed: {e}")

                finally:
                    if progress:
                        progress.stop()

                # Always show completion message
                print(f"[green]✓ Download completed: {output_path.name}[/]")

                # Call completion hooks
                if progress_hooks:
                    completion_info = {
                        "downloaded_bytes": downloaded,
                        "total_bytes": total_size or downloaded,
                        "filename": output_path.name,
                        "status": "finished",
                    }
                    for hook in progress_hooks:
                        try:
                            hook(completion_info)
                        except Exception as e:
                            logger.warning(f"Progress hook failed: {e}")

        except httpx.HTTPError as e:
            # Call error hooks
            if progress_hooks:
                error_info = {
                    "downloaded_bytes": 0,
                    "total_bytes": 0,
                    "filename": output_path.name,
                    "status": "error",
                    "error": str(e),
                }
                for hook in progress_hooks:
                    try:
                        hook(error_info)
                    except Exception as hook_error:
                        logger.warning(f"Progress hook failed: {hook_error}")
            raise ViuError(f"Failed to download video: {e}")

    def _download_subs(self, params: DownloadParams) -> list[Path]:
        """Download subtitles from provided URLs."""
        anime_title = sanitize_filename(params.anime_title)
        episode_title = sanitize_filename(params.episode_title)
        base = self.config.downloads_dir / anime_title
        downloaded_subs = []

        for i, sub_url in enumerate(params.subtitles):
            try:
                response = self.client.get(sub_url, headers=params.headers)
                response.raise_for_status()

                # Determine filename
                filename = get_remote_filename(response)
                if not filename:
                    if len(params.subtitles) == 1:
                        filename = f"{episode_title}.srt"
                    else:
                        filename = f"{episode_title}.{i}.srt"

                sub_path = base / filename

                # Write subtitle content
                with open(sub_path, "w", encoding="utf-8") as f:
                    f.write(response.text)

                downloaded_subs.append(sub_path)

                print(f"Downloaded subtitle: {filename}")

            except httpx.HTTPError as e:
                logger.error(f"Failed to download subtitle {i}: {e}")
                print(f"[red]Failed to download subtitle {i}: {e}[/red]")

        return downloaded_subs

    def _merge_subtitles(
        self, params: DownloadParams, video_path: Path, sub_paths: list[Path]
    ) -> Optional[Path]:
        """Merge subtitles with video using ffmpeg and return the path to the merged file."""
        ffmpeg_executable = shutil.which("ffmpeg")
        if not ffmpeg_executable:
            raise ViuError("Please install ffmpeg in order to merge subtitles")

        merged_filename = video_path.stem + ".mkv"

        # Prepare subtitle input arguments
        subs_input_args = list(
            itertools.chain.from_iterable(
                [["-i", str(sub_path)] for sub_path in sub_paths]
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            temp_output_path = temp_dir / merged_filename

            # Construct ffmpeg command
            args = [
                ffmpeg_executable,
                "-hide_banner",
                "-i",
                str(video_path),  # Main video input
                *subs_input_args,  # All subtitle inputs
                "-c",
                "copy",  # Copy streams without re-encoding
                "-map",
                "0:v",  # Map video from first input
                "-map",
                "0:a",  # Map audio from first input
            ]

            # Map subtitle streams from each subtitle input
            for i in range(len(sub_paths)):
                args.extend(["-map", f"{i + 1}:s"])

            args.append(str(temp_output_path))

            print(f"[cyan]Starting subtitle merge for {video_path.name}...[/]")

            try:
                # Run ffmpeg - use silent flag to control ffmpeg output, not progress
                subprocess.run(
                    args,
                    capture_output=params.silent,  # Only suppress ffmpeg output if silent
                    text=True,
                    check=True,
                    env=get_clean_env(),
                )

                final_output_path = video_path.parent / merged_filename

                # Handle existing file
                if final_output_path.exists():
                    if not params.prompt or Confirm.ask(
                        f"File exists ({final_output_path}). Overwrite?",
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
                    f"[green bold]Subtitles merged successfully.[/] Output: {final_output_path}"
                )

                return final_output_path

            except subprocess.CalledProcessError as e:
                error_msg = f"FFmpeg failed: {e.stderr if e.stderr else str(e)}"
                logger.error(error_msg)
                print(f"[red bold]Merge failed:[/] {error_msg}")
                return None
            except Exception as e:
                error_msg = f"Unexpected error during merge: {e}"
                logger.error(error_msg)
                print(f"[red bold]Unexpected error:[/] {error_msg}")
                return None
