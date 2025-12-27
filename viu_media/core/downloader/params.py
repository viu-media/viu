from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class DownloadParams:
    url: str
    anime_title: str
    episode_title: str
    silent: bool
    progress_hooks: list[Callable] = field(default_factory=list)
    logger: object | None = None
    vid_format: str = "best"
    force_unknown_ext: bool = False
    verbose: bool = False
    headers: dict[str, str] = field(default_factory=dict)
    subtitles: list[str] = field(default_factory=list)
    merge: bool = False
    clean: bool = False
    prompt: bool = True
    force_ffmpeg: bool = False
    hls_use_mpegts: bool = False
    hls_use_h264: bool = False
    no_check_certificate: bool = True
