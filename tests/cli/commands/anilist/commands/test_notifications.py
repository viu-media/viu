from contextlib import nullcontext
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from viu_media.cli.commands.anilist.commands.notifications import notifications


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config():
    return SimpleNamespace(general=SimpleNamespace(media_api="anilist"))


def test_notifications_requires_authentication(runner, mock_config):
    with (
        patch("viu_media.cli.service.feedback.FeedbackService") as mock_feedback,
        patch("viu_media.libs.media_api.api.create_api_client") as mock_create_api,
        patch("viu_media.cli.service.auth.AuthService") as mock_auth,
    ):
        feedback_instance = mock_feedback.return_value
        feedback_instance.progress.return_value = nullcontext()

        auth_instance = mock_auth.return_value
        auth_instance.get_auth.return_value = None

        api_client = mock_create_api.return_value
        api_client.is_authenticated.return_value = False

        result = runner.invoke(notifications, [], obj=mock_config)

    assert result.exit_code == 0
    feedback_instance.error.assert_called_with(
        "Authentication Required", "Please log in with 'viu anilist auth'."
    )


def test_notifications_shows_all_caught_up_message(runner, mock_config):
    with (
        patch("viu_media.cli.service.feedback.FeedbackService") as mock_feedback,
        patch("viu_media.libs.media_api.api.create_api_client") as mock_create_api,
        patch("viu_media.cli.service.auth.AuthService") as mock_auth,
    ):
        feedback_instance = mock_feedback.return_value
        feedback_instance.progress.return_value = nullcontext()

        auth_instance = mock_auth.return_value
        auth_instance.get_auth.return_value = SimpleNamespace(token="token")

        api_client = mock_create_api.return_value
        api_client.is_authenticated.return_value = True
        api_client.get_notifications.return_value = []

        result = runner.invoke(notifications, [], obj=mock_config)

    assert result.exit_code == 0
    api_client.authenticate.assert_called_once_with("token")
    feedback_instance.success.assert_called_with(
        "All caught up!", "You have no new notifications."
    )


def test_notifications_prints_table_and_mark_read_info(runner, mock_config):
    notification_item = SimpleNamespace(
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        media=SimpleNamespace(title=SimpleNamespace(english="Blue Lock", romaji=None)),
        episode=12,
    )

    with (
        patch("viu_media.cli.service.feedback.FeedbackService") as mock_feedback,
        patch("viu_media.libs.media_api.api.create_api_client") as mock_create_api,
        patch("viu_media.cli.service.auth.AuthService") as mock_auth,
        patch("viu_media.cli.commands.anilist.commands.notifications.Console") as mock_console,
    ):
        feedback_instance = mock_feedback.return_value
        feedback_instance.progress.return_value = nullcontext()

        auth_instance = mock_auth.return_value
        auth_instance.get_auth.return_value = SimpleNamespace(token="token")

        api_client = mock_create_api.return_value
        api_client.is_authenticated.return_value = True
        api_client.get_notifications.return_value = [notification_item]

        console_instance = mock_console.return_value

        result = runner.invoke(notifications, [], obj=mock_config)

    assert result.exit_code == 0
    console_instance.print.assert_called_once()
    feedback_instance.info.assert_called_once_with(
        "Notifications have been marked as read on AniList.",
    )
