from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ...libs.media_api.types import MediaSort, UserMediaListSort
from ...libs.provider.anime.types import ProviderName, ProviderServer
from ..constants import APP_ASCII_ART
from . import defaults
from . import descriptions as desc


class GeneralConfig(BaseModel):
    """Configuration for general application behavior and integrations."""

    desktop_notification_duration: int = Field(
        default=defaults.GENERAL_DESKTOP_NOTIFICATION_DURATION,
        description=desc.GENERAL_DESKTOP_NOTIFICATION_DURATION,
    )
    preferred_tracker: Literal["local", "remote"] = Field(
        default=defaults.GENERAL_PREFERRED_TRACKER,
        description=desc.GENERAL_PREFERRED_TRACKER,
    )
    pygment_style: Literal[
        "abap",
        "algol",
        "algol_nu",
        "arduino",
        "autumn",
        "bw",
        "borland",
        "coffee",
        "colorful",
        "default",
        "dracula",
        "emacs",
        "friendly_grayscale",
        "friendly",
        "fruity",
        "github-dark",
        "gruvbox-dark",
        "gruvbox-light",
        "igor",
        "inkpot",
        "lightbulb",
        "lilypond",
        "lovelace",
        "manni",
        "material",
        "monokai",
        "murphy",
        "native",
        "nord-darker",
        "nord",
        "one-dark",
        "paraiso-dark",
        "paraiso-light",
        "pastie",
        "perldoc",
        "rainbow_dash",
        "rrt",
        "sas",
        "solarized-dark",
        "solarized-light",
        "staroffice",
        "stata-dark",
        "stata-light",
        "tango",
        "trac",
        "vim",
        "vs",
        "xcode",
        "zenburn",
    ] = Field(
        default=defaults.GENERAL_PYGMENT_STYLE, description=desc.GENERAL_PYGMENT_STYLE
    )
    preferred_spinner: Literal[
        "dots",
        "dots2",
        "dots3",
        "dots4",
        "dots5",
        "dots6",
        "dots7",
        "dots8",
        "dots9",
        "dots10",
        "dots11",
        "dots12",
        "dots8Bit",
        "line",
        "line2",
        "pipe",
        "simpleDots",
        "simpleDotsScrolling",
        "star",
        "star2",
        "flip",
        "hamburger",
        "growVertical",
        "growHorizontal",
        "balloon",
        "balloon2",
        "noise",
        "bounce",
        "boxBounce",
        "boxBounce2",
        "triangle",
        "arc",
        "circle",
        "squareCorners",
        "circleQuarters",
        "circleHalves",
        "squish",
        "toggle",
        "toggle2",
        "toggle3",
        "toggle4",
        "toggle5",
        "toggle6",
        "toggle7",
        "toggle8",
        "toggle9",
        "toggle10",
        "toggle11",
        "toggle12",
        "toggle13",
        "arrow",
        "arrow2",
        "arrow3",
        "bouncingBar",
        "bouncingBall",
        "smiley",
        "monkey",
        "hearts",
        "clock",
        "earth",
        "material",
        "moon",
        "runner",
        "pong",
        "shark",
        "dqpb",
        "weather",
        "christmas",
        "grenade",
        "point",
        "layer",
        "betaWave",
        "aesthetic",
    ] = Field(
        default=defaults.GENERAL_PREFERRED_SPINNER,
        description=desc.GENERAL_PREFERRED_SPINNER,
    )
    media_api: Literal["anilist", "jikan"] = Field(
        default=defaults.GENERAL_API_CLIENT,
        description=desc.GENERAL_API_CLIENT,
    )
    welcome_screen: bool = Field(
        default=defaults.GENERAL_WELCOME_SCREEN, description=desc.GENERAL_WELCOME_SCREEN
    )
    provider: ProviderName = Field(
        default=ProviderName.ALLANIME,
        description=desc.GENERAL_PROVIDER,
    )
    selector: Literal["default", "fzf", "rofi"] = Field(
        default_factory=defaults.GENERAL_SELECTOR,
        description=desc.GENERAL_SELECTOR,
    )
    auto_select_anime_result: bool = Field(
        default=defaults.GENERAL_AUTO_SELECT_ANIME_RESULT,
        description=desc.GENERAL_AUTO_SELECT_ANIME_RESULT,
    )
    icons: bool = Field(default=defaults.GENERAL_ICONS, description=desc.GENERAL_ICONS)
    preview: Literal["full", "text", "image", "none"] = Field(
        default_factory=defaults.GENERAL_PREVIEW,
        description=desc.GENERAL_PREVIEW,
    )
    preview_scale_up: bool = Field(
        default=defaults.GENERAL_SCALE_PREVIEW,
        description=desc.GENERAL_SCALE_PREVIEW,
    )

    image_renderer: Literal[
        "icat", "chafa", "imgcat", "system-sixels", "system-kitty", "system-default"
    ] = Field(
        default_factory=defaults.GENERAL_IMAGE_RENDERER,
        description=desc.GENERAL_IMAGE_RENDERER,
    )
    manga_viewer: Literal["feh", "icat"] = Field(
        default=defaults.GENERAL_MANGA_VIEWER,
        description=desc.GENERAL_MANGA_VIEWER,
    )
    check_for_updates: bool = Field(
        default=defaults.GENERAL_CHECK_FOR_UPDATES,
        description=desc.GENERAL_CHECK_FOR_UPDATES,
    )
    show_new_release: bool = Field(
        default=defaults.GENERAL_SHOW_NEW_RELEASE,
        description=desc.GENERAL_SHOW_NEW_RELEASE,
    )
    update_check_interval: float = Field(
        default=defaults.GENERAL_UPDATE_CHECK_INTERVAL,
        description=desc.GENERAL_UPDATE_CHECK_INTERVAL,
    )
    cache_requests: bool = Field(
        default=defaults.GENERAL_CACHE_REQUESTS,
        description=desc.GENERAL_CACHE_REQUESTS,
    )
    max_cache_lifetime: str = Field(
        default=defaults.GENERAL_MAX_CACHE_LIFETIME,
        description=desc.GENERAL_MAX_CACHE_LIFETIME,
    )
    normalize_titles: bool = Field(
        default=defaults.GENERAL_NORMALIZE_TITLES,
        description=desc.GENERAL_NORMALIZE_TITLES,
    )
    discord: bool = Field(
        default=defaults.GENERAL_DISCORD,
        description=desc.GENERAL_DISCORD,
    )
    recent: int = Field(
        default=defaults.GENERAL_RECENT,
        ge=0,
        description=desc.GENERAL_RECENT,
    )


class StreamConfig(BaseModel):
    """Configuration specific to video streaming and playback."""

    player: Literal["mpv", "vlc"] = Field(
        default=defaults.STREAM_PLAYER,
        description=desc.STREAM_PLAYER,
    )
    quality: Literal["360", "480", "720", "1080"] = Field(
        default=defaults.STREAM_QUALITY,
        description=desc.STREAM_QUALITY,
    )
    translation_type: Literal["sub", "dub"] = Field(
        default=defaults.STREAM_TRANSLATION_TYPE,
        description=desc.STREAM_TRANSLATION_TYPE,
    )
    server: ProviderServer = Field(
        default=ProviderServer.TOP,
        description=desc.STREAM_SERVER,
    )
    auto_next: bool = Field(
        default=defaults.STREAM_AUTO_NEXT,
        description=desc.STREAM_AUTO_NEXT,
    )
    continue_from_watch_history: bool = Field(
        default=defaults.STREAM_CONTINUE_FROM_WATCH_HISTORY,
        description=desc.STREAM_CONTINUE_FROM_WATCH_HISTORY,
    )
    preferred_watch_history: Literal["local", "remote"] = Field(
        default=defaults.STREAM_PREFERRED_WATCH_HISTORY,
        description=desc.STREAM_PREFERRED_WATCH_HISTORY,
    )
    auto_skip: bool = Field(
        default=defaults.STREAM_AUTO_SKIP,
        description=desc.STREAM_AUTO_SKIP,
    )
    episode_complete_at: int = Field(
        default=defaults.STREAM_EPISODE_COMPLETE_AT,
        ge=0,
        le=100,
        description=desc.STREAM_EPISODE_COMPLETE_AT,
    )
    ytdlp_format: str = Field(
        default=defaults.STREAM_YTDLP_FORMAT,
        description=desc.STREAM_YTDLP_FORMAT,
    )
    force_forward_tracking: bool = Field(
        default=defaults.STREAM_FORCE_FORWARD_TRACKING,
        description=desc.STREAM_FORCE_FORWARD_TRACKING,
    )
    default_media_list_tracking: Literal["track", "disabled", "prompt"] = Field(
        default=defaults.STREAM_DEFAULT_MEDIA_LIST_TRACKING,
        description=desc.STREAM_DEFAULT_MEDIA_LIST_TRACKING,
    )
    sub_lang: str = Field(
        default=defaults.STREAM_SUB_LANG,
        description=desc.STREAM_SUB_LANG,
    )

    use_ipc: bool = Field(
        default_factory=defaults.STREAM_USE_IPC,
        description=desc.STREAM_USE_IPC,
    )


class OtherConfig(BaseModel):
    pass


class WorkerConfig(OtherConfig):
    """Configuration for the background worker service."""

    enabled: bool = Field(
        default=True,
        description="Enable the background worker for notifications and queued downloads.",
    )
    notification_check_interval: int = Field(
        default=15,  # in minutes
        ge=1,
        description="How often to check for new AniList notifications (in minutes).",
    )
    download_check_interval: int = Field(
        default=5,  # in minutes
        ge=1,
        description="How often to process the download queue (in minutes).",
    )
    download_check_failed_interval: int = Field(
        default=60,  # in minutes
        ge=1,
        description="How often to process the failed download queue (in minutes).",
    )
    auto_download_new_episode: bool = Field(
        default=True,
        description="Whether to automatically download a new episode that has been notified",
    )


class SessionsConfig(OtherConfig):
    dir: Path = Field(
        default_factory=lambda: defaults.SESSIONS_DIR,
        description=desc.SESSIONS_DIR,
    )


class FzfConfig(OtherConfig):
    """Configuration specific to the FZF selector."""

    opts: str = Field(
        default_factory=lambda: defaults.FZF_OPTS.read_text(encoding="utf-8"),
        description=desc.FZF_OPTS,
    )
    header_color: str = Field(
        default=defaults.FZF_HEADER_COLOR, description=desc.FZF_HEADER_COLOR
    )
    header_ascii_art: str = Field(
        default_factory=lambda: APP_ASCII_ART.read_text(encoding="utf-8"),
        description=desc.FZF_HEADER_ASCII_ART,
    )
    preview_header_color: str = Field(
        default=defaults.FZF_PREVIEW_HEADER_COLOR,
        description=desc.FZF_PREVIEW_HEADER_COLOR,
    )
    preview_separator_color: str = Field(
        default=defaults.FZF_PREVIEW_SEPARATOR_COLOR,
        description=desc.FZF_PREVIEW_SEPARATOR_COLOR,
    )


class RofiConfig(OtherConfig):
    """Configuration specific to the Rofi selector."""

    theme_main: Path = Field(
        default_factory=lambda: Path(str(defaults.ROFI_THEME_MAIN)),
        description=desc.ROFI_THEME_MAIN,
    )
    theme_preview: Path = Field(
        default_factory=lambda: Path(str(defaults.ROFI_THEME_PREVIEW)),
        description=desc.ROFI_THEME_PREVIEW,
    )
    theme_confirm: Path = Field(
        default_factory=lambda: Path(str(defaults.ROFI_THEME_CONFIRM)),
        description=desc.ROFI_THEME_CONFIRM,
    )
    theme_input: Path = Field(
        default_factory=lambda: Path(str(defaults.ROFI_THEME_INPUT)),
        description=desc.ROFI_THEME_INPUT,
    )


class MpvConfig(OtherConfig):
    """Configuration specific to the MPV player integration."""

    args: str = Field(default=defaults.MPV_ARGS, description=desc.MPV_ARGS)
    pre_args: str = Field(
        default=defaults.MPV_PRE_ARGS,
        description=desc.MPV_PRE_ARGS,
    )


class VlcConfig(OtherConfig):
    """Configuration specific to the vlc player integration."""

    args: str = Field(default=defaults.VLC_ARGS, description=desc.VLC_ARGS)


class AnilistConfig(OtherConfig):
    """Configuration for interacting with the AniList API."""

    per_page: int = Field(
        default=defaults.ANILIST_PER_PAGE,
        gt=0,
        le=50,
        description=desc.ANILIST_PER_PAGE,
    )
    sort_by: MediaSort = Field(
        default=MediaSort.SEARCH_MATCH,
        description=desc.ANILIST_SORT_BY,
    )
    media_list_sort_by: UserMediaListSort = Field(
        default=UserMediaListSort.MEDIA_POPULARITY_DESC,
        description=desc.ANILIST_MEDIA_LIST_SORT_BY,
    )
    preferred_language: Literal["english", "romaji"] = Field(
        default=defaults.ANILIST_PREFERRED_LANGUAGE,
        description=desc.ANILIST_PREFERRED_LANGUAGE,
    )


class JikanConfig(OtherConfig):
    """Configuration for the Jikan API (currently none)."""

    per_page: int = Field(
        default=defaults.ANILIST_PER_PAGE,
        gt=0,
        le=50,
        description=desc.ANILIST_PER_PAGE,
    )
    sort_by: MediaSort = Field(
        default=MediaSort.SEARCH_MATCH,
        description=desc.ANILIST_SORT_BY,
    )
    media_list_sort_by: UserMediaListSort = Field(
        default=UserMediaListSort.MEDIA_POPULARITY_DESC,
        description=desc.ANILIST_MEDIA_LIST_SORT_BY,
    )
    preferred_language: Literal["english", "romaji"] = Field(
        default=defaults.ANILIST_PREFERRED_LANGUAGE,
        description=desc.ANILIST_PREFERRED_LANGUAGE,
    )


class DownloadsConfig(OtherConfig):
    """Configuration for download related options"""

    downloader: Literal["auto", "default", "yt-dlp"] = Field(
        default=defaults.DOWNLOADS_DOWNLOADER, description=desc.DOWNLOADS_DOWNLOADER
    )
    downloads_dir: Path = Field(
        default_factory=lambda: defaults.DOWNLOADS_DOWNLOADS_DIR,
        description=desc.DOWNLOADS_DOWNLOADS_DIR,
    )
    enable_tracking: bool = Field(
        default=defaults.DOWNLOADS_ENABLE_TRACKING,
        description=desc.DOWNLOADS_ENABLE_TRACKING,
    )
    max_concurrent_downloads: int = Field(
        default=defaults.DOWNLOADS_MAX_CONCURRENT,
        ge=1,
        description=desc.DOWNLOADS_MAX_CONCURRENT,
    )
    max_retry_attempts: int = Field(
        default=defaults.DOWNLOADS_RETRY_ATTEMPTS,
        ge=0,
        description=desc.DOWNLOADS_RETRY_ATTEMPTS,
    )
    retry_delay: int = Field(
        default=defaults.DOWNLOADS_RETRY_DELAY,
        ge=0,
        description=desc.DOWNLOADS_RETRY_DELAY,
    )
    merge_subtitles: bool = Field(
        default=defaults.DOWNLOADS_MERGE_SUBTITLES,
        description=desc.DOWNLOADS_MERGE_SUBTITLES,
    )
    cleanup_after_merge: bool = Field(
        default=defaults.DOWNLOADS_CLEANUP_AFTER_MERGE,
        description=desc.DOWNLOADS_CLEANUP_AFTER_MERGE,
    )

    server: ProviderServer = Field(
        default=ProviderServer.TOP,
        description=desc.STREAM_SERVER,
    )

    ytdlp_format: str = Field(
        default=defaults.STREAM_YTDLP_FORMAT,
        description=desc.STREAM_YTDLP_FORMAT,
    )
    no_check_certificate: bool = Field(
        default=defaults.DOWNLOADS_NO_CHECK_CERTIFICATE,
        description=desc.DOWNLOADS_NO_CHECK_CERTIFICATE,
    )


class MediaRegistryConfig(OtherConfig):
    """Configuration for registry related options"""

    media_dir: Path = Field(
        default=defaults.MEDIA_REGISTRY_DIR,
        description=desc.MEDIA_REGISTRY_DIR,
    )

    index_dir: Path = Field(
        default=defaults.MEDIA_REGISTRY_INDEX_DIR,
        description=desc.MEDIA_REGISTRY_INDEX_DIR,
    )


class AppConfig(BaseModel):
    """The root configuration model for the Viu application."""

    general: GeneralConfig = Field(
        default_factory=GeneralConfig,
        description=desc.APP_GENERAL,
    )
    stream: StreamConfig = Field(
        default_factory=StreamConfig,
        description=desc.APP_STREAM,
    )
    downloads: DownloadsConfig = Field(
        default_factory=DownloadsConfig, description=desc.APP_DOWNLOADS
    )
    anilist: AnilistConfig = Field(
        default_factory=AnilistConfig,
        description=desc.APP_ANILIST,
    )
    jikan: JikanConfig = Field(
        default_factory=JikanConfig,
        description=desc.APP_JIKAN,
    )
    fzf: FzfConfig = Field(
        default_factory=FzfConfig,
        description=desc.APP_FZF,
    )
    rofi: RofiConfig = Field(
        default_factory=RofiConfig,
        description=desc.APP_ROFI,
    )
    mpv: MpvConfig = Field(default_factory=MpvConfig, description=desc.APP_MPV)
    vlc: VlcConfig = Field(default_factory=VlcConfig, description=desc.APP_VLC)
    media_registry: MediaRegistryConfig = Field(
        default_factory=MediaRegistryConfig, description=desc.APP_MEDIA_REGISTRY
    )
    sessions: SessionsConfig = Field(
        default_factory=SessionsConfig, description=desc.APP_SESSIONS
    )
    worker: WorkerConfig = Field(
        default_factory=WorkerConfig,
        description="Configuration for the background worker service.",
    )
