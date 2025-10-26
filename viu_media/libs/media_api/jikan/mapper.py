from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..types import (
    MediaImage,
    MediaItem,
    MediaSearchResult,
    MediaStatus,
    MediaTitle,
    PageInfo,
    Studio,
)

if TYPE_CHECKING:
    # Jikan doesn't have a formal schema like GraphQL, so we work with dicts.
    pass

# Jikan uses specific strings for status, we can map them to our generic enum.
JIKAN_STATUS_MAP = {
    "Finished Airing": MediaStatus.FINISHED,
    "Currently Airing": MediaStatus.RELEASING,
    "Not yet aired": MediaStatus.NOT_YET_RELEASED,
}


def _to_generic_title(jikan_titles: list[dict]) -> MediaTitle:
    """Extracts titles from Jikan's list of title objects."""
    # Initialize with default values
    romaji = None
    english = None
    native = None

    # Jikan's default title is often the romaji one.
    # We prioritize specific types if available.
    for t in jikan_titles:
        type_ = t.get("type")
        title_ = t.get("title")
        if type_ == "Default":
            romaji = title_
        elif type_ == "English":
            english = title_
        elif type_ == "Japanese":
            native = title_

    return MediaTitle(
        romaji=romaji,
        english=english or romaji or native or "NOT AVAILABLE",
        native=native,
    )


def _to_generic_image(jikan_images: dict) -> MediaImage:
    """Maps Jikan's image structure."""
    if not jikan_images:
        return MediaImage(large="")  # Provide empty string as fallback
    # Jikan provides different image formats under a 'jpg' key.
    jpg_images = jikan_images.get("jpg", {})
    return MediaImage(
        large=jpg_images.get("large_image_url", ""),  # Fallback to empty string
        medium=jpg_images.get("image_url"),
    )


def _to_generic_media_item(data: dict) -> MediaItem:
    """Maps a single Jikan anime entry to our generic MediaItem."""

    # Jikan score is 0-10, our generic model is 0-10, so we can use it directly.
    # AniList was 0-100, so its mapper had to divide by 10.
    score = data.get("score")

    return MediaItem(
        id=data["mal_id"],
        id_mal=data["mal_id"],
        title=_to_generic_title(data.get("titles", [])),
        cover_image=_to_generic_image(data.get("images", {})),
        status=JIKAN_STATUS_MAP.get(data.get("status", ""), MediaStatus.UNKNOWN),
        episodes=data.get("episodes"),
        duration=data.get("duration"),
        average_score=score,
        popularity=data.get("popularity"),
        favourites=data.get("favorites"),
        description=data.get("synopsis"),
        genres=[g["name"] for g in data.get("genres", [])],
        studios=[
            Studio(id=s["mal_id"], name=s["name"]) for s in data.get("studios", [])
        ],
        # Jikan doesn't provide streaming episodes
        streaming_episodes={},
        # Jikan doesn't provide user list status in its search results.
        user_status=None,
    )


def to_generic_search_result(api_response: dict) -> Optional[MediaSearchResult]:
    """Top-level mapper for Jikan search results."""
    if not api_response or "data" not in api_response:
        return None

    media_items = [_to_generic_media_item(item) for item in api_response["data"]]

    pagination = api_response.get("pagination", {})
    page_info = PageInfo(
        total=pagination.get("items", {}).get("total", 0),
        current_page=pagination.get("current_page", 1),
        has_next_page=pagination.get("has_next_page", False),
        per_page=pagination.get("items", {}).get("per_page", 25),
    )

    return MediaSearchResult(page_info=page_info, media=media_items)
