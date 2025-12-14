import logging

from .constants import (
    DOWNLOAD_FILENAME_REGEX,
    DOWNLOAD_URL_REGEX,
    QUALITY_REGEX,
    VIDEO_INFO_CLEAN_REGEX,
    VIDEO_INFO_REGEX,
)

logger = logging.getLogger(__name__)


def extract_server_info(html_content: str, episode_title: str | None) -> dict | None:
    """
    Extracts server information from the VixCloud/AnimeUnity embed page.
    Handles extraction from both window.video object and download URL.
    """
    video_info = VIDEO_INFO_REGEX.search(html_content)
    download_url_match = DOWNLOAD_URL_REGEX.search(html_content)

    if not (download_url_match and video_info):
        return None

    info_str = VIDEO_INFO_CLEAN_REGEX.sub(r'"\1"', video_info.group(1))

    # Use eval context for JS constants
    ctx = {"null": None, "true": True, "false": False}
    try:
        info = eval(info_str, ctx)
    except Exception as e:
        logger.error(f"Failed to parse JS object: {e}")
        return None

    download_url = download_url_match.group(1)
    info["link"] = download_url

    # Extract metadata from download URL if missing in window.video
    if filename_match := DOWNLOAD_FILENAME_REGEX.search(download_url):
        info["name"] = filename_match.group(1)
    else:
        info["name"] = f"{episode_title or 'Unknown'}"

    if quality_match := QUALITY_REGEX.search(download_url):
        # "720p" -> 720
        info["quality"] = int(quality_match.group(1)[:-1])
    else:
        info["quality"] = 0  # Fallback

    return info
