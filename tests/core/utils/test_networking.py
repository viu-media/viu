from unittest.mock import patch

import httpx

from viu_media.core.utils.networking import get_remote_filename, random_user_agent


def _make_response(url: str, headers: dict[str, str] | None = None) -> httpx.Response:
    request = httpx.Request("GET", url)
    return httpx.Response(200, headers=headers, request=request)


def test_random_user_agent_uses_selected_chrome_version():
    with patch("viu_media.core.utils.networking.random.choice", return_value="97.0.4692.20"):
        user_agent = random_user_agent()

    assert "Chrome/97.0.4692.20" in user_agent
    assert user_agent.startswith("Mozilla/5.0")


def test_get_remote_filename_prefers_filename_star_header():
    response = _make_response(
        "https://example.com/download",
        {"Content-Disposition": "attachment; filename*=UTF-8''my%20anime%20file.mkv"},
    )

    filename = get_remote_filename(response)

    assert filename == "my anime file.mkv"


def test_get_remote_filename_uses_regular_filename_header():
    response = _make_response(
        "https://example.com/download",
        {"Content-Disposition": 'attachment; filename="episode-01.mp4"'},
    )

    filename = get_remote_filename(response)

    assert filename == "episode-01.mp4"


def test_get_remote_filename_falls_back_to_url_path():
    response = _make_response("https://example.com/files/ep%2001.mp4?token=abc")

    filename = get_remote_filename(response)

    assert filename == "ep 01.mp4"


def test_get_remote_filename_returns_none_when_no_candidate_found():
    response = _make_response("https://example.com/")

    filename = get_remote_filename(response)

    assert filename is None
