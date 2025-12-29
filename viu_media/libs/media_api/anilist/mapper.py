import logging
from datetime import datetime
from typing import Dict, List, Optional

from ....core.utils.formatter import (
    renumber_titles,
    strip_original_episode_prefix,
)
from ..types import (
    AiringSchedule,
    AiringScheduleItem,
    AiringScheduleResult,
    Character,
    CharacterImage,
    CharacterName,
    CharacterSearchResult,
    MediaFormat,
    MediaGenre,
    MediaImage,
    MediaItem,
    MediaReview,
    MediaSearchResult,
    MediaStatus,
    MediaTag,
    MediaTagItem,
    MediaTitle,
    MediaTrailer,
    Notification,
    NotificationType,
    PageInfo,
    Reviewer,
    StreamingEpisode,
    Studio,
    UserListItem,
    UserMediaListStatus,
    MediaType,
    UserProfile,
)
from .types import (
    AnilistBaseMediaDataSchema,
    AnilistCurrentlyLoggedInUser,
    AnilistDataSchema,
    AnilistDateObject,
    AnilistImage,
    AnilistMediaList,
    AnilistMediaLists,
    AnilistMediaNextAiringEpisode,
    AnilistMediaTag,
    AnilistMediaTitle,
    AnilistMediaTrailer,
    AnilistNotification,
    AnilistNotifications,
    AnilistPageInfo,
    AnilistReview,
    AnilistReviews,
    AnilistStudioNodes,
    AnilistViewerData,
)
from .types import (
    StreamingEpisode as AnilistStreamingEpisode,
)

logger = logging.getLogger(__name__)

user_list_status_map = {
    "CURRENT": UserMediaListStatus.WATCHING,
    "PLANNING": UserMediaListStatus.PLANNING,
    "COMPLETED": UserMediaListStatus.COMPLETED,
    "PAUSED": UserMediaListStatus.PAUSED,
    "REPEATING": UserMediaListStatus.REPEATING,
    "DROPPED": UserMediaListStatus.DROPPED,
}
status_map = {
    "FINISHED": MediaStatus.FINISHED,
    "RELEASING": MediaStatus.RELEASING,
    "NOT_YET_RELEASED": MediaStatus.NOT_YET_RELEASED,
    "CANCELLED": MediaStatus.CANCELLED,
    "HIATUS": MediaStatus.HIATUS,
}


def _to_generic_date(date: AnilistDateObject) -> Optional[datetime]:
    if not date:
        return
    year = date["year"]
    month = date["month"]
    day = date["day"]
    if year:
        if not month:
            month = 1
        if not day:
            day = 1
        return datetime(year, month, day)


def _to_generic_media_title(anilist_title: AnilistMediaTitle) -> MediaTitle:
    """Maps an AniList title object to a generic MediaTitle."""
    romaji = anilist_title.get("romaji")
    english = anilist_title.get("english")
    native = anilist_title.get("native")
    return MediaTitle(
        romaji=romaji,
        english=(english or romaji or native or "NO_TITLE"),
        native=native,
    )


def _to_generic_media_image(anilist_image: AnilistImage) -> MediaImage:
    """Maps an AniList image object to a generic MediaImage."""
    return MediaImage(
        medium=anilist_image.get("medium"),
        large=anilist_image["large"],
        extra_large=anilist_image.get("extraLarge"),
    )


def _to_generic_media_trailer(
    anilist_trailer: Optional[AnilistMediaTrailer],
) -> Optional[MediaTrailer]:
    """Maps an AniList trailer object to a generic MediaTrailer."""
    if not anilist_trailer or not anilist_trailer.get("id"):
        return None
    return MediaTrailer(
        id=anilist_trailer["id"],
        site=anilist_trailer.get("site"),
        thumbnail_url=anilist_trailer.get("thumbnail"),
    )


def _to_generic_airing_schedule(
    anilist_schedule: Optional[AnilistMediaNextAiringEpisode],
) -> Optional[AiringSchedule]:
    """Maps an AniList nextAiringEpisode object to a generic AiringSchedule."""
    if anilist_schedule:
        return AiringSchedule(
            airing_at=datetime.fromtimestamp(anilist_schedule["airingAt"])
            if anilist_schedule.get("airingAt")
            else None,
            episode=anilist_schedule.get("episode", 0),
        )


def _to_generic_studios(anilist_studios: AnilistStudioNodes) -> List[Studio]:
    """Maps AniList studio nodes to a list of generic Studio objects."""
    if not anilist_studios or not anilist_studios.get("nodes"):
        return []
    return [
        Studio(
            name=s["name"],
            favourites=s["favourites"],
            is_animation_studio=s["isAnimationStudio"],
        )
        for s in anilist_studios["nodes"]
        if s  # Also check if individual studio object is not None
    ]


def _to_generic_tags(anilist_tags: list[AnilistMediaTag]) -> List[MediaTagItem]:
    """Maps a list of AniList tags to generic MediaTag objects."""
    if not anilist_tags:
        return []
    return [
        MediaTagItem(name=MediaTag(t["name"]), rank=t.get("rank"))
        for t in anilist_tags
        if t and t.get("name")
    ]


def _to_generic_streaming_episodes(
    anilist_episodes: list[AnilistStreamingEpisode],
) -> Dict[str, StreamingEpisode]:
    """Maps a list of AniList streaming episodes to generic StreamingEpisode objects,
    renumbering them fresh if they contain episode numbers."""

    titles = [ep["title"] for ep in anilist_episodes if "title" in ep and ep["title"]]
    renumber_map = renumber_titles(titles)

    result = {}
    for ep in anilist_episodes:
        title = ep.get("title")
        if not title:
            continue

        renumbered_ep = renumber_map.get(title)
        display_title = (
            f"Episode {renumbered_ep} - {strip_original_episode_prefix(title)}"
            if renumbered_ep is not None
            else title
        )

        result[str(renumbered_ep)] = StreamingEpisode(
            title=display_title,
            thumbnail=ep.get("thumbnail"),
        )

    return result


def _to_generic_user_status(
    anilist_media: AnilistBaseMediaDataSchema,
    anilist_list_entry: Optional[AnilistMediaList],
) -> Optional[UserListItem]:
    """Maps an AniList mediaListEntry to a generic UserListStatus."""
    # FIX: investigate the inconsistency between mediaList entry status `and the main status
    if anilist_list_entry:
        return UserListItem(
            status=user_list_status_map[anilist_media["mediaListEntry"]["status"]],  # type:ignore
            progress=anilist_list_entry["progress"],
            score=anilist_list_entry["score"],
            repeat=anilist_list_entry["repeat"],
            notes=anilist_list_entry["notes"],
            start_date=_to_generic_date(anilist_list_entry.get("startDate")),
            completed_at=_to_generic_date(anilist_list_entry.get("completedAt")),
            # TODO: should this be a datetime if so what is the raw values type
            created_at=str(anilist_list_entry["createdAt"]),
        )
    else:
        if not anilist_media["mediaListEntry"]:
            return

        return UserListItem(
            id=anilist_media["mediaListEntry"]["id"],
            status=user_list_status_map[anilist_media["mediaListEntry"]["status"]]
            if anilist_media["mediaListEntry"]["status"]
            else None,
            progress=anilist_media["mediaListEntry"]["progress"],
        )


def _to_generic_media_item(
    data: AnilistBaseMediaDataSchema, media_list: AnilistMediaList | None = None
) -> MediaItem:
    """Maps a single AniList media schema to a generic MediaItem."""
    return MediaItem(
        id=data["id"],
        id_mal=data.get("idMal"),
        type=data.get("type", "ANIME"),
        title=_to_generic_media_title(data["title"]),
        status=status_map[data["status"]],
        format=MediaFormat(data["format"]) if data["format"] else None,
        cover_image=_to_generic_media_image(data["coverImage"]),
        banner_image=data.get("bannerImage"),
        trailer=_to_generic_media_trailer(data["trailer"]),
        description=data.get("description"),
        episodes=data.get("episodes"),
        duration=data.get("duration"),
        genres=[MediaGenre(genre) for genre in data["genres"]],
        tags=_to_generic_tags(data.get("tags")),
        studios=_to_generic_studios(data.get("studios")),
        synonymns=data.get("synonyms", []),
        average_score=data.get("averageScore"),
        popularity=data.get("popularity"),
        favourites=data.get("favourites"),
        next_airing=_to_generic_airing_schedule(data.get("nextAiringEpisode")),
        start_date=_to_generic_date(data["startDate"]),
        end_date=_to_generic_date(data["endDate"]),
        streaming_episodes=_to_generic_streaming_episodes(
            data.get("streamingEpisodes", [])
        ),
        user_status=_to_generic_user_status(data, media_list),
    )


def _to_generic_page_info(data: AnilistPageInfo) -> PageInfo:
    """Maps an AniList page info object to a generic PageInfo."""
    return PageInfo(
        total=data.get("total", 0),
        current_page=data.get("currentPage", 1),
        has_next_page=data.get("hasNextPage", False),
        per_page=data.get("perPage", 0),
    )


def to_generic_search_result(
    data: AnilistDataSchema, user_media_list: List[AnilistMediaList] | None = None
) -> Optional[MediaSearchResult]:
    """
    Top-level mapper to convert a raw AniList search/list API response
    into a generic MediaSearchResult object.
    """
    page_data = data["data"]["Page"]

    raw_media_list = page_data["media"]
    if user_media_list:
        media_items: List[MediaItem] = [
            _to_generic_media_item(item, user_media_list_item)
            for item, user_media_list_item in zip(raw_media_list, user_media_list)
        ]
        page_info = _to_generic_page_info(page_data["pageInfo"])
    else:
        media_items: List[MediaItem] = [
            _to_generic_media_item(item) for item in raw_media_list
        ]
        page_info = _to_generic_page_info(page_data["pageInfo"])

    return MediaSearchResult(page_info=page_info, media=media_items)


def to_generic_user_list_result(data: AnilistMediaLists) -> Optional[MediaSearchResult]:
    """
    Mapper for user list queries where media data is nested inside a 'mediaList' key.
    """
    page_data = data["data"]["Page"]

    # Extract media objects from the 'mediaList' array
    media_list_items = page_data["mediaList"]
    raw_media_list = [item["media"] for item in media_list_items]

    # Now that we have a standard list of media, we can reuse the main search result mapper
    return to_generic_search_result(
        {
            "data": {
                "Page": {
                    "media": raw_media_list,
                    "pageInfo": page_data["pageInfo"],
                },
            }
        },
        media_list_items,
    )


def to_generic_user_profile(data: AnilistViewerData) -> Optional[UserProfile]:
    """Maps a raw AniList viewer response to a generic UserProfile."""

    data_node = data.get("data")
    if not data_node:
        return None

    viewer_data: Optional[AnilistCurrentlyLoggedInUser] = data_node.get("Viewer")

    if not viewer_data:
        return None

    return UserProfile(
        id=viewer_data["id"],
        name=viewer_data["name"],
        avatar_url=viewer_data["avatar"]["large"],
        banner_url=viewer_data["bannerImage"],
    )


# TODO: complete this
def to_generic_relations(data: dict) -> Optional[List[MediaItem]]:
    """Maps the 'relations' part of an API response."""
    nodes = data["data"].get("Media", {}).get("relations", {}).get("nodes", [])
    return [_to_generic_media_item(node) for node in nodes if node]


def to_generic_recommendations(data: dict) -> Optional[List[MediaItem]]:
    """Maps the 'recommendations' part of an API response."""
    if not data or not data.get("data"):
        return None

    page_data = data.get("data", {}).get("Page", {})
    if not page_data:
        return None

    recommendations = page_data.get("recommendations", [])
    if not recommendations:
        return None

    result = []
    for rec in recommendations:
        if rec and rec.get("media"):
            try:
                media_item = _to_generic_media_item(rec["media"])
                result.append(media_item)
            except Exception as e:
                logger.warning(f"Failed to map recommendation media item: {e}")
                continue

    return result if result else None


def _to_generic_reviewer(anilist_user: AnilistCurrentlyLoggedInUser) -> Reviewer:
    """Maps an AniList user object to a generic Reviewer."""
    return Reviewer(
        name=anilist_user["name"],
        avatar_url=anilist_user["avatar"]["large"]
        if anilist_user.get("avatar")
        else None,
    )


def _to_generic_review(anilist_review: AnilistReview) -> MediaReview:
    """Maps a single AniList review to a generic Review."""
    return MediaReview(
        summary=anilist_review.get("summary"),
        body=anilist_review.get("body", "No review body provided.") or "",
        user=_to_generic_reviewer(anilist_review["user"]),
    )


def to_generic_reviews_list(data: AnilistReviews) -> Optional[List[MediaReview]]:
    """Top-level mapper for a list of reviews."""
    if not data or "data" not in data:
        return None

    page_data = data["data"].get("Page", {})
    if not page_data:
        return None

    raw_reviews = page_data.get("reviews", [])
    if not raw_reviews:
        return []

    return [_to_generic_review(review) for review in raw_reviews if review]


def _to_generic_character_name(anilist_name: Optional[Dict]) -> CharacterName:
    """Maps an AniList character name object to a generic CharacterName."""
    if not anilist_name:
        return CharacterName()

    return CharacterName(
        first=anilist_name.get("first"),
        middle=anilist_name.get("middle"),
        last=anilist_name.get("last"),
        full=anilist_name.get("full"),
        native=anilist_name.get("native"),
    )


def _to_generic_character_image(
    anilist_image: Optional[Dict],
) -> Optional[CharacterImage]:
    """Maps an AniList character image object to a generic CharacterImage."""
    if not anilist_image:
        return None

    return CharacterImage(
        medium=anilist_image.get("medium"),
        large=anilist_image.get("large"),
    )


def _to_generic_character(anilist_character: Dict) -> Optional[Character]:
    """Maps an AniList character object to a generic Character."""
    if not anilist_character:
        return None

    # Parse date of birth if available
    date_of_birth = None
    if dob := anilist_character.get("dateOfBirth"):
        try:
            year = dob.get("year")
            month = dob.get("month")
            day = dob.get("day")
            if year and month and day:
                date_of_birth = datetime(year, month, day)
        except (ValueError, TypeError):
            pass

    return Character(
        id=anilist_character.get("id"),
        name=_to_generic_character_name(anilist_character.get("name")),
        image=_to_generic_character_image(anilist_character.get("image")),
        description=anilist_character.get("description"),
        gender=anilist_character.get("gender"),
        age=anilist_character.get("age"),
        blood_type=anilist_character.get("bloodType"),
        favourites=anilist_character.get("favourites"),
        date_of_birth=date_of_birth,
    )


def to_generic_characters_result(data: Dict) -> Optional[CharacterSearchResult]:
    """Maps AniList character data to a generic CharacterSearchResult."""
    if not data or "data" not in data:
        logger.error("Invalid character data structure")
        return None

    try:
        page_data = data["data"]["Page"]["media"][0]
        characters_data = page_data["characters"]["nodes"]

        characters = []
        for char_data in characters_data:
            if character := _to_generic_character(char_data):
                characters.append(character)

        return CharacterSearchResult(
            characters=characters,
            page_info=None,  # Characters don't typically have pagination
        )
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error parsing character data: {e}")
        return None


def _to_generic_airing_schedule_item(
    anilist_episode: Dict,
) -> Optional[AiringScheduleItem]:
    """Maps an AniList airing schedule episode to a generic AiringScheduleItem."""
    if not anilist_episode:
        return None

    airing_at = None
    if airing_timestamp := anilist_episode.get("airingAt"):
        try:
            airing_at = datetime.fromtimestamp(airing_timestamp)
        except (ValueError, TypeError):
            pass

    return AiringScheduleItem(
        episode=anilist_episode.get("episode", 0),
        airing_at=airing_at,
        time_until_airing=anilist_episode.get("timeUntilAiring"),
    )


def to_generic_airing_schedule_result(data: Dict) -> Optional[AiringScheduleResult]:
    """Maps AniList airing schedule data to a generic AiringScheduleResult."""
    if not data or "data" not in data:
        logger.error("Invalid airing schedule data structure")
        return None

    try:
        page_data = data["data"]["Page"]["media"][0]
        schedule_data = page_data["airingSchedule"]["nodes"]

        schedule_items = []
        for episode_data in schedule_data:
            if item := _to_generic_airing_schedule_item(episode_data):
                schedule_items.append(item)

        return AiringScheduleResult(
            schedule_items=schedule_items,
            page_info=None,  # Schedule doesn't typically have pagination
        )
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error parsing airing schedule data: {e}")
        return None


def _to_generic_media_item_from_notification_partial(
    data: AnilistBaseMediaDataSchema,
) -> MediaItem:
    """
    A specialized mapper for the partial MediaItem object received in notifications.
    It provides default values for fields not present in the notification's media payload.
    """
    return MediaItem(
        id=data["id"],
        id_mal=data.get("idMal"),
        title=_to_generic_media_title(data["title"]),
        cover_image=_to_generic_media_image(data["coverImage"]),
        # Provide default/empty values for fields not in notification payload
        type=MediaType.ANIME,
        status=MediaStatus.RELEASING,  # Assume releasing for airing notifications
        format=None,
        description=None,
        episodes=None,
        duration=None,
        genres=[],
        tags=[],
        studios=[],
        synonymns=[],
        average_score=None,
        popularity=None,
        favourites=None,
        streaming_episodes={},
        user_status=None,
    )


def _to_generic_notification(anilist_notification: AnilistNotification) -> Notification:
    """Maps a single AniList notification to a generic Notification object."""
    return Notification(
        id=anilist_notification["id"],
        type=NotificationType(anilist_notification["type"]),
        episode=anilist_notification.get("episode"),
        contexts=anilist_notification.get("contexts", []),
        created_at=datetime.fromtimestamp(anilist_notification["createdAt"]),
        media=_to_generic_media_item_from_notification_partial(
            anilist_notification["media"]
        ),
    )


def to_generic_notifications(
    data: AnilistNotifications,
) -> Optional[List[Notification]]:
    """Top-level mapper for a list of notifications."""
    if not data or "data" not in data:
        return None

    page_data = data["data"].get("Page", {})
    if not page_data:
        return None

    raw_notifications = page_data.get("notifications", [])
    if not raw_notifications:
        return []

    return [
        _to_generic_notification(notification)
        for notification in raw_notifications
        if notification
    ]
