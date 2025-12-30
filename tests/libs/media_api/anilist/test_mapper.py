from typing import Any

from viu_media.libs.media_api.anilist.mapper import to_generic_user_profile
from viu_media.libs.media_api.anilist.types import AnilistViewerData
from viu_media.libs.media_api.types import UserProfile


def test_to_generic_user_profile_success():
    data: AnilistViewerData = {
        "data": {
            "Viewer": {
                "id": 123,
                "name": "testuser",
                "avatar": {
                    "large": "https://example.com/avatar.png",
                    "medium": "https://example.com/avatar_medium.png",
                    "extraLarge": "https://example.com/avatar_extraLarge.png",
                    "small": "https://example.com/avatar_small.png",
                },
                "bannerImage": "https://example.com/banner.png",
                "token": "test_token",
            }
        }
    }
    profile = to_generic_user_profile(data)
    assert isinstance(profile, UserProfile)
    assert profile.id == 123
    assert profile.name == "testuser"
    assert profile.avatar_url == "https://example.com/avatar.png"
    assert profile.banner_url == "https://example.com/banner.png"


def test_to_generic_user_profile_data_none():
    data: Any = {"data": None}
    profile = to_generic_user_profile(data)
    assert profile is None


def test_to_generic_user_profile_no_data_key():
    data: Any = {"errors": [{"message": "Invalid token"}]}
    profile = to_generic_user_profile(data)
    assert profile is None


def test_to_generic_user_profile_no_viewer_key():
    data: Any = {"data": {"Page": {}}}
    profile = to_generic_user_profile(data)
    assert profile is None


def test_to_generic_user_profile_viewer_none():
    data: Any = {"data": {"Viewer": None}}
    profile = to_generic_user_profile(data)
    assert profile is None
