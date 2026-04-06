from unittest.mock import patch

import pytest
from httpx import Client

from viu_media.core.config import AnilistConfig
from viu_media.libs.media_api.anilist.api import AniListApi
from viu_media.libs.media_api.params import MediaSearchParams, UpdateUserMediaListEntryParams
from viu_media.libs.media_api.types import MediaGenre, MediaStatus, UserMediaListStatus


class FakeResponse:
    def __init__(self, payload, text=""):
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


@pytest.fixture
def api_client():
    api = AniListApi(AnilistConfig(per_page=7), Client())
    try:
        yield api
    finally:
        api.http_client.close()


def test_authenticate_sets_profile_and_authorization_header(api_client):
    viewer_payload = {
        "data": {
            "Viewer": {
                "id": 1,
                "name": "ash",
                "avatar": {"large": "https://img/avatar.jpg"},
                "bannerImage": "https://img/banner.jpg",
            }
        }
    }

    with patch(
        "viu_media.libs.media_api.anilist.api.execute_graphql",
        return_value=FakeResponse(viewer_payload),
    ):
        profile = api_client.authenticate("token-123")

    assert profile is not None
    assert profile.name == "ash"
    assert api_client.http_client.headers["Authorization"] == "Bearer token-123"
    assert api_client.is_authenticated() is True


def test_authenticate_clears_token_when_profile_fetch_fails(api_client):
    with patch.object(api_client, "get_viewer_profile", return_value=None):
        profile = api_client.authenticate("bad-token")

    assert profile is None
    assert api_client.token is None
    assert "Authorization" not in api_client.http_client.headers
    assert api_client.is_authenticated() is False


def test_get_viewer_profile_without_token_returns_none(api_client):
    with patch("viu_media.libs.media_api.anilist.api.execute_graphql") as mock_execute:
        profile = api_client.get_viewer_profile()

    assert profile is None
    mock_execute.assert_not_called()


def test_search_media_builds_expected_graphql_variables(api_client):
    params = MediaSearchParams(
        query="naruto",
        page=2,
        status=MediaStatus.RELEASING,
        genre_in=[MediaGenre.ACTION],
    )

    with (
        patch("viu_media.libs.media_api.anilist.api.execute_graphql") as mock_execute,
        patch(
            "viu_media.libs.media_api.anilist.api.mapper.to_generic_search_result",
            return_value="mapped",
        ),
    ):
        mock_execute.return_value = FakeResponse({"data": {"Page": {}}})
        result = api_client.search_media(params)

    assert result == "mapped"
    called_variables = mock_execute.call_args.args[3]
    assert called_variables["query"] == "naruto"
    assert called_variables["page"] == 2
    assert called_variables["status"] == "RELEASING"
    assert called_variables["genre_in"] == ["Action"]
    assert called_variables["genre_not_in"] == ["Hentai"]
    assert called_variables["type"] == "ANIME"
    assert called_variables["per_page"] == 7


def test_update_list_entry_requires_authentication(api_client):
    params = UpdateUserMediaListEntryParams(media_id=99)

    with patch("viu_media.libs.media_api.anilist.api.execute_graphql") as mock_execute:
        result = api_client.update_list_entry(params)

    assert result is False
    mock_execute.assert_not_called()


def test_update_list_entry_maps_score_and_progress_and_returns_true(api_client):
    api_client.token = "token"
    params = UpdateUserMediaListEntryParams(
        media_id=10,
        status=UserMediaListStatus.WATCHING,
        progress="3.0",
        score=8.5,
    )

    with patch(
        "viu_media.libs.media_api.anilist.api.execute_graphql",
        return_value=FakeResponse({"data": {"SaveMediaListEntry": {"id": 10}}}),
    ) as mock_execute:
        result = api_client.update_list_entry(params)

    assert result is True
    called_variables = mock_execute.call_args.args[3]
    assert called_variables == {
        "mediaId": 10,
        "status": "CURRENT",
        "progress": 3,
        "scoreRaw": 85,
    }


def test_update_list_entry_returns_false_on_api_errors(api_client):
    api_client.token = "token"
    params = UpdateUserMediaListEntryParams(media_id=10)

    with patch(
        "viu_media.libs.media_api.anilist.api.execute_graphql",
        return_value=FakeResponse({"errors": [{"message": "boom"}]}),
    ):
        result = api_client.update_list_entry(params)

    assert result is False


def test_delete_list_entry_requires_authentication(api_client):
    with patch("viu_media.libs.media_api.anilist.api.execute_graphql") as mock_execute:
        result = api_client.delete_list_entry(11)

    assert result is False
    mock_execute.assert_not_called()


def test_delete_list_entry_returns_false_when_item_not_found(api_client):
    api_client.token = "token"
    with patch(
        "viu_media.libs.media_api.anilist.api.execute_graphql",
        return_value=FakeResponse({"data": {"MediaList": None}}),
    ) as mock_execute:
        result = api_client.delete_list_entry(11)

    assert result is False
    assert mock_execute.call_count == 1


def test_delete_list_entry_deletes_when_list_item_exists(api_client):
    api_client.token = "token"
    responses = [
        FakeResponse({"data": {"MediaList": {"id": 321}}}),
        FakeResponse({"data": {"DeleteMediaListEntry": {"deleted": True}}}),
    ]

    with patch(
        "viu_media.libs.media_api.anilist.api.execute_graphql",
        side_effect=responses,
    ) as mock_execute:
        result = api_client.delete_list_entry(22)

    assert result is True
    assert mock_execute.call_count == 2
    first_vars = mock_execute.call_args_list[0].args[3]
    second_vars = mock_execute.call_args_list[1].args[3]
    assert first_vars == {"mediaId": 22}
    assert second_vars == {"id": 321}
