from viu_media.libs.media_api.anilist.mapper import to_generic_user_profile
from viu_media.libs.media_api.anilist.types import AnilistViewerData
from viu_media.libs.media_api.types import UserProfile


def test_to_generic_user_profile_success():
    data: AnilistViewerData = {
        "data": {
            "Viewer": {
                "id": 123,
                "name": "testuser",
                "avatar": {"large": "https://example.com/avatar.png"},
                "bannerImage": "https://example.com/banner.png",
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
    data = {"data": None}
    profile = to_generic_user_profile(data)
    assert profile is None


def test_to_generic_user_profile_no_data_key():
    data = {"errors": [{"message": "Invalid token"}]}
    profile = to_generic_user_profile(data)
    assert profile is None


def test_to_generic_user_profile_no_viewer_key():
    data: AnilistViewerData = {"data": {"Page": {}}}
    profile = to_generic_user_profile(data)
    assert profile is None


def test_to_generic_user_profile_viewer_none():
    data: AnilistViewerData = {"data": {"Viewer": None}}
    profile = to_generic_user_profile(data)
    assert profile is None
