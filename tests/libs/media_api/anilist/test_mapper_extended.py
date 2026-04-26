from datetime import datetime
from typing import Any, cast

from viu_media.libs.media_api.anilist.mapper import (
    _to_generic_streaming_episodes,
    _to_generic_user_status,
    to_generic_airing_schedule_result,
    to_generic_characters_result,
    to_generic_notifications,
    to_generic_recommendations,
    to_generic_reviews_list,
    to_generic_search_result,
)
from viu_media.libs.media_api.types import UserMediaListStatus


def _build_media_item(media_id: int = 1) -> dict:
    return {
        "id": media_id,
        "idMal": None,
        "type": "ANIME",
        "title": {"english": f"Title {media_id}", "romaji": "Romaji", "native": "Native"},
        "status": "RELEASING",
        "format": "TV",
        "coverImage": {"large": "https://img/large.jpg", "medium": "https://img/med.jpg"},
        "bannerImage": None,
        "trailer": None,
        "description": "description",
        "episodes": 12,
        "duration": 24,
        "genres": ["Action"],
        "tags": [{"name": "CGI", "rank": 88}],
        "studios": {
            "nodes": [
                {
                    "name": "Studio One",
                    "favourites": 111,
                    "isAnimationStudio": True,
                }
            ]
        },
        "synonyms": ["Alt title"],
        "averageScore": 80,
        "popularity": 9000,
        "favourites": 77,
        "nextAiringEpisode": {"airingAt": 1700000000, "episode": 5, "timeUntilAiring": 123},
        "startDate": {"year": 2024, "month": 1, "day": 1},
        "endDate": {"year": 2024, "month": 3, "day": 1},
        "streamingEpisodes": [
            {"title": "Episode 10 - Main", "thumbnail": "thumb1"},
            {"title": "Episode 10.5 - Special", "thumbnail": "thumb2"},
        ],
        "mediaListEntry": {"id": 9, "status": "CURRENT", "progress": 2},
    }


def test_to_generic_streaming_episodes_renumbers_titles():
    episodes = [
        {"title": "Episode 10 - Main", "thumbnail": "thumb1"},
        {"title": "Episode 10.5 - Special", "thumbnail": "thumb2"},
    ]

    result = _to_generic_streaming_episodes(cast(Any, episodes))

    assert result["1"].title == "Episode 1 - Main"
    assert result["1.5"].title == "Episode 1.5 - Special"
    assert result["1"].thumbnail == "thumb1"


def test_to_generic_user_status_with_explicit_list_entry():
    media = {"mediaListEntry": {"status": "CURRENT"}}
    list_entry = {
        "progress": 12,
        "score": 9.0,
        "repeat": 1,
        "notes": "finished",
        "startDate": {"year": 2024, "month": 1, "day": 2},
        "completedAt": {"year": 2024, "month": 4, "day": 2},
        "createdAt": 1700000000,
    }

    result = _to_generic_user_status(cast(Any, media), cast(Any, list_entry))

    assert result is not None
    assert result.status == UserMediaListStatus.WATCHING
    assert result.progress == 12
    assert result.created_at == "1700000000"


def test_to_generic_user_status_uses_media_entry_when_list_entry_is_none():
    media = {"mediaListEntry": {"id": 55, "status": "CURRENT", "progress": 7}}

    result = _to_generic_user_status(cast(Any, media), None)

    assert result is not None
    assert result.id == 55
    assert result.status == UserMediaListStatus.WATCHING
    assert result.progress == 7


def test_to_generic_search_result_maps_page_and_media():
    payload = {
        "data": {
            "Page": {
                "media": [_build_media_item(1)],
                "pageInfo": {
                    "total": 1,
                    "currentPage": 1,
                    "hasNextPage": False,
                    "perPage": 10,
                },
            }
        }
    }

    result = to_generic_search_result(cast(Any, payload))

    assert result is not None
    assert result.page_info.total == 1
    assert len(result.media) == 1
    assert result.media[0].id == 1
    assert result.media[0].streaming_episodes["1"].title == "Episode 1 - Main"


def test_to_generic_recommendations_skips_invalid_recommendation_item():
    good_media = _build_media_item(2)
    bad_media = {"id": 999, "title": {"english": "broken", "romaji": "broken"}}
    payload = {
        "data": {
            "Page": {
                "recommendations": [
                    {"media": good_media},
                    {"media": bad_media},
                ]
            }
        }
    }

    result = to_generic_recommendations(payload)

    assert result is not None
    assert len(result) == 1
    assert result[0].id == 2


def test_to_generic_reviews_list_handles_invalid_and_empty_data():
    assert to_generic_reviews_list(cast(Any, {})) is None

    empty_reviews = {"data": {"Page": {"reviews": []}}}
    assert to_generic_reviews_list(cast(Any, empty_reviews)) == []


def test_to_generic_characters_result_maps_valid_payload():
    payload = {
        "data": {
            "Page": {
                "media": [
                    {
                        "characters": {
                            "nodes": [
                                {
                                    "id": 1,
                                    "name": {"full": "Naruto Uzumaki"},
                                    "image": {
                                        "medium": "https://img/char-med.jpg",
                                        "large": "https://img/char-large.jpg",
                                    },
                                    "description": "Main character",
                                    "gender": "Male",
                                    "age": "17",
                                    "bloodType": "B",
                                    "favourites": 100,
                                    "dateOfBirth": {
                                        "year": 2000,
                                        "month": 10,
                                        "day": 10,
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }

    result = to_generic_characters_result(payload)

    assert result is not None
    assert len(result.characters) == 1
    assert result.characters[0].name.full == "Naruto Uzumaki"
    assert result.characters[0].date_of_birth == datetime(2000, 10, 10)


def test_to_generic_characters_result_returns_none_on_malformed_data():
    payload = {"data": {"Page": {"media": []}}}

    result = to_generic_characters_result(payload)

    assert result is None


def test_to_generic_airing_schedule_result_handles_invalid_timestamps():
    payload = {
        "data": {
            "Page": {
                "media": [
                    {
                        "airingSchedule": {
                            "nodes": [
                                {"episode": 1, "airingAt": 1700000000, "timeUntilAiring": 10},
                                {"episode": 2, "airingAt": "invalid", "timeUntilAiring": 20},
                            ]
                        }
                    }
                ]
            }
        }
    }

    result = to_generic_airing_schedule_result(payload)

    assert result is not None
    assert len(result.schedule_items) == 2
    assert result.schedule_items[0].airing_at is not None
    assert result.schedule_items[1].airing_at is None


def test_to_generic_notifications_handles_empty_invalid_and_valid_payloads():
    assert to_generic_notifications(cast(Any, {})) is None

    empty_payload = {"data": {"Page": {"notifications": []}}}
    assert to_generic_notifications(cast(Any, empty_payload)) == []

    valid_payload = {
        "data": {
            "Page": {
                "notifications": [
                    {
                        "id": 44,
                        "type": "AIRING",
                        "episode": 7,
                        "contexts": ["Aired"],
                        "createdAt": 1700000000,
                        "media": {
                            "id": 12,
                            "idMal": None,
                            "title": {
                                "english": "Title",
                                "romaji": "Romaji",
                                "native": "Native",
                            },
                            "coverImage": {
                                "large": "https://img/cover.jpg",
                                "medium": "https://img/cover-med.jpg",
                            },
                        },
                    }
                ]
            }
        }
    }

    result = to_generic_notifications(cast(Any, valid_payload))

    assert result is not None
    assert len(result) == 1
    assert result[0].id == 44
    assert result[0].media.id == 12
