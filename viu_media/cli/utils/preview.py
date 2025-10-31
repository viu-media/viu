import logging
import re
from hashlib import sha256
import sys
from typing import Dict, List, Optional

import httpx

from ...core.config import AppConfig
from ...core.constants import APP_CACHE_DIR, PLATFORM, SCRIPTS_DIR
from ...core.utils.file import AtomicWriter
from ...libs.media_api.types import (
    AiringScheduleResult,
    Character,
    MediaItem,
    MediaReview,
)
from . import ansi
from .preview_workers import PreviewWorkerManager


def get_rofi_preview(
    media_items: List[MediaItem], titles: List[str], config: AppConfig
) -> str:
    # Ensure cache directories exist on startup
    IMAGES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    INFO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    return (
        "".join(
            [
                f"{title}\0icon\x1f{_get_image(item)}\n"
                for item, title in zip(media_items, titles)
            ]
        )
        + "Back\nExit"
    )


def _get_image(item: MediaItem) -> str:
    if not item.cover_image:
        return ""

    hash_id = sha256(item.title.english.encode("utf-8")).hexdigest()
    image_path = IMAGES_CACHE_DIR / f"{hash_id}.png"

    if image_path.exists():
        return str(image_path)

    if not item.cover_image.large:
        return ""

    try:
        with httpx.stream(
            "GET", item.cover_image.large, follow_redirects=True
        ) as response:
            response.raise_for_status()
            with AtomicWriter(image_path, "wb", encoding=None) as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
        return str(image_path)
    except Exception as e:
        logger.error(f"Failed to download image {item.cover_image.large}: {e}")
        return ""


def get_rofi_episode_preview(
    episodes: List[str], media_item: MediaItem, config: AppConfig
) -> str:
    # Ensure cache directories exist on startup
    IMAGES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    INFO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    return (
        "".join(
            [
                f"{episode}\0icon\x1f{_get_episode_image(episode, media_item)}\n"
                for episode in episodes
            ]
        )
        + "Back\nExit"
    )


def _get_episode_image(episode: str, media_item: MediaItem) -> str:
    if media_item.streaming_episodes and media_item.streaming_episodes.get(episode):
        stream = media_item.streaming_episodes[episode]
        image_url = stream.thumbnail
    else:
        if not media_item.cover_image:
            return ""
        image_url = media_item.cover_image.large
    if not image_url:
        return ""

    hash_id = sha256(
        f"{media_item.title.english}_Episode_{episode}".encode("utf-8")
    ).hexdigest()
    image_path = IMAGES_CACHE_DIR / f"{hash_id}.png"

    if image_path.exists():
        return str(image_path)

    try:
        with httpx.stream("GET", image_url, follow_redirects=True) as response:
            response.raise_for_status()
            with AtomicWriter(image_path, "wb", encoding=None) as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
        return str(image_path)
    except Exception as e:
        logger.error(
            f"Failed to download image {image_url} for {media_item.title.english}: {e}"
        )
        return ""


logger = logging.getLogger(__name__)

# os.environ["SHELL"] = sys.executable

PREVIEWS_CACHE_DIR = APP_CACHE_DIR / "previews"
IMAGES_CACHE_DIR = PREVIEWS_CACHE_DIR / "images"
INFO_CACHE_DIR = PREVIEWS_CACHE_DIR / "info"
REVIEWS_CACHE_DIR = PREVIEWS_CACHE_DIR / "reviews"
CHARACTERS_CACHE_DIR = PREVIEWS_CACHE_DIR / "characters"
AIRING_SCHEDULE_CACHE_DIR = PREVIEWS_CACHE_DIR / "airing_schedule"

FZF_SCRIPTS_DIR = SCRIPTS_DIR / "fzf"
TEMPLATE_PREVIEW_SCRIPT = (FZF_SCRIPTS_DIR / "preview.py").read_text(encoding="utf-8")
TEMPLATE_REVIEW_PREVIEW_SCRIPT = ""
TEMPLATE_CHARACTER_PREVIEW_SCRIPT = ""
TEMPLATE_AIRING_SCHEDULE_PREVIEW_SCRIPT = ""
DYNAMIC_PREVIEW_SCRIPT = ""

EPISODE_PATTERN = re.compile(r"^Episode\s+(\d+)\s-\s.*")

# Global preview worker manager instance
_preview_manager: Optional[PreviewWorkerManager] = None


def create_preview_context():
    """
    Create a context manager for preview operations.

    This can be used in menu functions to ensure proper cleanup:

    ```python
    with create_preview_context() as preview_ctx:
        preview_script = preview_ctx.get_anime_preview(items, titles, config)
        # ... use preview_script
    # Workers are automatically cleaned up here
    ```

    Returns:
        PreviewContext: A context manager for preview operations
    """
    return PreviewContext()


class PreviewContext:
    """Context manager for preview operations with automatic cleanup."""

    def __init__(self):
        self._manager = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._manager:
            try:
                self._manager.shutdown_all(wait=False, timeout=3.0)
            except Exception as e:
                logger.warning(f"Failed to cleanup preview context: {e}")

    def get_anime_preview(
        self, items: List[MediaItem], titles: List[str], config: AppConfig
    ) -> str:
        """Get anime preview script with managed workers."""
        if not self._manager:
            self._manager = _get_preview_manager()
        return get_anime_preview(items, titles, config)

    def get_episode_preview(
        self, episodes: List[str], media_item: MediaItem, config: AppConfig
    ) -> str:
        """Get episode preview script with managed workers."""
        if not self._manager:
            self._manager = _get_preview_manager()
        return get_episode_preview(episodes, media_item, config)

    def get_dynamic_anime_preview(self, config: AppConfig) -> str:
        """Get dynamic anime preview script for search functionality."""
        if not self._manager:
            self._manager = _get_preview_manager()
        return get_dynamic_anime_preview(config)

    def get_review_preview(
        self, choice_map: Dict[str, MediaReview], config: AppConfig
    ) -> str:
        """Get review preview script with managed workers."""
        if not self._manager:
            self._manager = _get_preview_manager()
        return get_review_preview(choice_map, config)

    def get_character_preview(
        self, choice_map: Dict[str, Character], config: AppConfig
    ) -> str:
        """Get character preview script with managed workers."""
        if not self._manager:
            self._manager = _get_preview_manager()
        return get_character_preview(choice_map, config)

    def get_airing_schedule_preview(
        self,
        schedule_result: AiringScheduleResult,
        config: AppConfig,
        anime_title: str = "Anime",
    ) -> str:
        """Get airing schedule preview script with managed workers."""
        if not self._manager:
            self._manager = _get_preview_manager()
        return get_airing_schedule_preview(schedule_result, config, anime_title)

    def cancel_all_tasks(self) -> int:
        """Cancel all running preview tasks."""
        if not self._manager:
            return 0

        cancelled = 0
        if self._manager._preview_worker:
            cancelled += self._manager._preview_worker.cancel_all_tasks()
        if self._manager._episode_worker:
            cancelled += self._manager._episode_worker.cancel_all_tasks()
        if self._manager._review_worker:
            cancelled += self._manager._review_worker.cancel_all_tasks()
        if self._manager._character_worker:
            cancelled += self._manager._character_worker.cancel_all_tasks()
        if self._manager._airing_schedule_worker:
            cancelled += self._manager._airing_schedule_worker.cancel_all_tasks()
        return cancelled

    def get_status(self) -> dict:
        """Get status of workers in this context."""
        if self._manager:
            return self._manager.get_status()
        return {
            "preview_worker": None,
            "episode_worker": None,
            "review_worker": None,
            "character_worker": None,
            "airing_schedule_worker": None,
        }


def get_anime_preview(
    items: List[MediaItem], titles: List[str], config: AppConfig
) -> str:
    if config.general.selector == "rofi":
        return get_rofi_preview(items, titles, config)

    """
    Generate anime preview script and start background caching.

    Args:
        items: List of media items to preview
        titles: Corresponding titles for each media item
        config: Application configuration

    Returns:
        Preview script content for fzf
    """
    # Ensure cache directories exist on startup
    IMAGES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    INFO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    HEADER_COLOR = config.fzf.preview_header_color.split(",")
    SEPARATOR_COLOR = config.fzf.preview_separator_color.split(",")

    preview_script = TEMPLATE_PREVIEW_SCRIPT

    # Start the managed background caching
    try:
        preview_manager = _get_preview_manager()
        worker = preview_manager.get_preview_worker()
        worker.cache_anime_previews(items, titles, config)
        logger.debug("Started background caching for anime previews")
    except Exception as e:
        logger.error(f"Failed to start background caching: {e}")
        # Continue with script generation even if caching fails

    # Format the template with the dynamic values
    replacements = {
        "PREVIEW_MODE": config.general.preview,
        "IMAGE_CACHE_DIR": str(IMAGES_CACHE_DIR),
        "INFO_CACHE_DIR": str(INFO_CACHE_DIR),
        "IMAGE_RENDERER": config.general.image_renderer,
        # Color codes
        "HEADER_COLOR": ",".join(HEADER_COLOR),
        "SEPARATOR_COLOR": ",".join(SEPARATOR_COLOR),
        "PREFIX": "search-results",
        "SCALE_UP": str(config.general.preview_scale_up),
    }

    for key, value in replacements.items():
        preview_script = preview_script.replace(f"{{{key}}}", value)

    (PREVIEWS_CACHE_DIR / "search-results-preview-script.py").write_text(
        preview_script, encoding="utf-8"
    )

    preview_script_final = f"{sys.executable} {PREVIEWS_CACHE_DIR / 'search-results-preview-script.py'} {{}}"
    return preview_script_final


def get_episode_preview(
    episodes: List[str], media_item: MediaItem, config: AppConfig
) -> str:
    """
    Generate episode preview script and start background caching.

    Args:
        episodes: List of episode identifiers
        media_item: Media item containing episode data
        config: Application configuration

    Returns:
        Preview script content for fzf
    """
    if config.general.selector == "rofi":
        return get_rofi_episode_preview(episodes, media_item, config)
    IMAGES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    INFO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    HEADER_COLOR = config.fzf.preview_header_color.split(",")
    SEPARATOR_COLOR = config.fzf.preview_separator_color.split(",")

    preview_script = TEMPLATE_PREVIEW_SCRIPT

    # Start managed background caching for episodes
    try:
        preview_manager = _get_preview_manager()
        worker = preview_manager.get_episode_worker()
        worker.cache_episode_previews(episodes, media_item, config)
        logger.debug("Started background caching for episode previews")
    except Exception as e:
        logger.error(f"Failed to start episode background caching: {e}")
        # Continue with script generation even if caching fails

    # Prepare values to inject into the template
    path_sep = "\\" if PLATFORM == "win32" else "/"

    # Format the template with the dynamic values
    replacements = {
        "PREVIEW_MODE": config.general.preview,
        "IMAGE_CACHE_PATH": str(IMAGES_CACHE_DIR),
        "INFO_CACHE_PATH": str(INFO_CACHE_DIR),
        "PATH_SEP": path_sep,
        "IMAGE_RENDERER": config.general.image_renderer,
        # Color codes
        "C_TITLE": ansi.get_true_fg(HEADER_COLOR, bold=True),
        "C_KEY": ansi.get_true_fg(HEADER_COLOR, bold=True),
        "C_VALUE": ansi.get_true_fg(HEADER_COLOR, bold=True),
        "C_RULE": ansi.get_true_fg(SEPARATOR_COLOR, bold=True),
        "RESET": ansi.RESET,
        "PREFIX": f"{media_item.title.english}_Episode_",
        "SCALE_UP": " --scale-up" if config.general.preview_scale_up else "",
    }

    for key, value in replacements.items():
        preview_script = preview_script.replace(f"{{{key}}}", value)

    return preview_script


def get_dynamic_anime_preview(config: AppConfig) -> str:
    """
    Generate dynamic anime preview script for search functionality.

    This is different from regular anime preview because:
    1. We don't have media items upfront
    2. The preview needs to work with search results as they come in
    3. Preview is handled entirely in shell by parsing JSON results

    Args:
        config: Application configuration

    Returns:
        Preview script content for fzf dynamic search
    """
    # Ensure cache directories exist
    IMAGES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    INFO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    HEADER_COLOR = config.fzf.preview_header_color.split(",")
    SEPARATOR_COLOR = config.fzf.preview_separator_color.split(",")

    # Use the dynamic preview script template
    preview_script = DYNAMIC_PREVIEW_SCRIPT

    search_cache_dir = APP_CACHE_DIR / "search"
    search_results_file = search_cache_dir / "current_search_results.json"

    # Prepare values to inject into the template
    path_sep = "\\" if PLATFORM == "win32" else "/"

    # Format the template with the dynamic values
    replacements = {
        "PREVIEW_MODE": config.general.preview,
        "IMAGE_CACHE_PATH": str(IMAGES_CACHE_DIR),
        "INFO_CACHE_PATH": str(INFO_CACHE_DIR),
        "PATH_SEP": path_sep,
        "IMAGE_RENDERER": config.general.image_renderer,
        "SEARCH_RESULTS_FILE": str(search_results_file),
        # Color codes
        "C_TITLE": ansi.get_true_fg(HEADER_COLOR, bold=True),
        "C_KEY": ansi.get_true_fg(HEADER_COLOR, bold=True),
        "C_VALUE": ansi.get_true_fg(HEADER_COLOR, bold=True),
        "C_RULE": ansi.get_true_fg(SEPARATOR_COLOR, bold=True),
        "RESET": ansi.RESET,
        "SCALE_UP": " --scale-up" if config.general.preview_scale_up else "",
    }

    for key, value in replacements.items():
        preview_script = preview_script.replace(f"{{{key}}}", value)

    return preview_script


def _get_preview_manager() -> PreviewWorkerManager:
    """Get or create the global preview worker manager."""
    global _preview_manager
    if _preview_manager is None:
        _preview_manager = PreviewWorkerManager(
            IMAGES_CACHE_DIR, INFO_CACHE_DIR, REVIEWS_CACHE_DIR
        )
    return _preview_manager


def shutdown_preview_workers(wait: bool = True, timeout: Optional[float] = 5.0) -> None:
    """
    Shutdown all preview workers.

    Args:
        wait: Whether to wait for tasks to complete
        timeout: Maximum time to wait for shutdown
    """
    global _preview_manager
    if _preview_manager:
        _preview_manager.shutdown_all(wait=wait, timeout=timeout)
        _preview_manager = None


def get_preview_worker_status() -> dict:
    """Get status of all preview workers."""
    global _preview_manager
    if _preview_manager:
        return _preview_manager.get_status()
    return {"preview_worker": None, "episode_worker": None}


def get_review_preview(choice_map: Dict[str, MediaReview], config: AppConfig) -> str:
    """
    Generate the generic loader script for review previews and start background caching.
    """

    REVIEWS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    preview_manager = _get_preview_manager()
    worker = preview_manager.get_review_worker()
    worker.cache_review_previews(choice_map, config)
    logger.debug("Started background caching for review previews")

    # Use the generic loader script
    preview_script = TEMPLATE_REVIEW_PREVIEW_SCRIPT
    path_sep = "\\" if PLATFORM == "win32" else "/"

    # Inject the correct cache path and color codes
    replacements = {
        "PREVIEW_MODE": config.general.preview,
        "INFO_CACHE_DIR": str(REVIEWS_CACHE_DIR),
        "PATH_SEP": path_sep,
        "C_TITLE": ansi.get_true_fg(config.fzf.header_color.split(","), bold=True),
        "C_KEY": ansi.get_true_fg(config.fzf.header_color.split(","), bold=True),
        "C_VALUE": ansi.get_true_fg(config.fzf.header_color.split(","), bold=True),
        "C_RULE": ansi.get_true_fg(
            config.fzf.preview_separator_color.split(","), bold=True
        ),
        "RESET": ansi.RESET,
    }

    for key, value in replacements.items():
        preview_script = preview_script.replace(f"{{{key}}}", value)

    return preview_script


def get_character_preview(choice_map: Dict[str, Character], config: AppConfig) -> str:
    """
    Generate the generic loader script for character previews and start background caching.
    """

    INFO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    preview_manager = _get_preview_manager()
    worker = preview_manager.get_character_worker()
    worker.cache_character_previews(choice_map, config)
    logger.debug("Started background caching for character previews")

    # Use the generic loader script
    preview_script = TEMPLATE_CHARACTER_PREVIEW_SCRIPT
    path_sep = "\\" if PLATFORM == "win32" else "/"

    # Inject the correct cache path and color codes
    replacements = {
        "PREVIEW_MODE": config.general.preview,
        "INFO_CACHE_DIR": str(INFO_CACHE_DIR),
        "IMAGE_CACHE_DIR": str(IMAGES_CACHE_DIR),
        "PATH_SEP": path_sep,
        "C_TITLE": ansi.get_true_fg(config.fzf.header_color.split(","), bold=True),
        "C_KEY": ansi.get_true_fg(config.fzf.header_color.split(","), bold=True),
        "C_VALUE": ansi.get_true_fg(config.fzf.header_color.split(","), bold=True),
        "C_RULE": ansi.get_true_fg(
            config.fzf.preview_separator_color.split(","), bold=True
        ),
        "RESET": ansi.RESET,
    }

    for key, value in replacements.items():
        preview_script = preview_script.replace(f"{{{key}}}", value)

    return preview_script


def get_airing_schedule_preview(
    schedule_result: AiringScheduleResult, config: AppConfig, anime_title: str = "Anime"
) -> str:
    """
    Generate the generic loader script for airing schedule previews and start background caching.
    """

    INFO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    preview_manager = _get_preview_manager()
    worker = preview_manager.get_airing_schedule_worker()
    worker.cache_airing_schedule_preview(anime_title, schedule_result, config)
    logger.debug("Started background caching for airing schedule previews")

    # Use the generic loader script
    preview_script = TEMPLATE_AIRING_SCHEDULE_PREVIEW_SCRIPT
    path_sep = "\\" if PLATFORM == "win32" else "/"

    # Inject the correct cache path and color codes
    replacements = {
        "PREVIEW_MODE": config.general.preview,
        "INFO_CACHE_DIR": str(INFO_CACHE_DIR),
        "PATH_SEP": path_sep,
        "C_TITLE": ansi.get_true_fg(config.fzf.header_color.split(","), bold=True),
        "C_KEY": ansi.get_true_fg(config.fzf.header_color.split(","), bold=True),
        "C_VALUE": ansi.get_true_fg(config.fzf.header_color.split(","), bold=True),
        "C_RULE": ansi.get_true_fg(
            config.fzf.preview_separator_color.split(","), bold=True
        ),
        "RESET": ansi.RESET,
    }

    for key, value in replacements.items():
        preview_script = preview_script.replace(f"{{{key}}}", value)

    return preview_script
