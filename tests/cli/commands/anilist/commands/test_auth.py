from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from viu_media.cli.commands.anilist.commands.auth import auth


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.user.interactive = True
    return config


@pytest.fixture
def mock_auth_service():
    with patch("viu_media.cli.service.auth.AuthService") as mock:
        yield mock


@pytest.fixture
def mock_feedback_service():
    with patch("viu_media.cli.service.feedback.FeedbackService") as mock:
        yield mock


@pytest.fixture
def mock_selector():
    with patch("viu_media.libs.selectors.selector.create_selector") as mock:
        yield mock


@pytest.fixture
def mock_api_client():
    with patch("viu_media.libs.media_api.api.create_api_client") as mock:
        yield mock


@pytest.fixture
def mock_webbrowser():
    with patch("viu_media.cli.commands.anilist.commands.auth.webbrowser") as mock:
        yield mock


def test_auth_with_token_argument(
    runner,
    mock_config,
    mock_auth_service,
    mock_feedback_service,
    mock_selector,
    mock_api_client,
):
    """Test 'viu anilist auth <token>'."""
    api_client_instance = mock_api_client.return_value
    profile_mock = MagicMock()
    profile_mock.name = "testuser"
    api_client_instance.authenticate.return_value = profile_mock

    auth_service_instance = mock_auth_service.return_value
    auth_service_instance.get_auth.return_value = None

    result = runner.invoke(auth, ["test_token"], obj=mock_config)

    assert result.exit_code == 0
    mock_api_client.assert_called_with("anilist", mock_config)
    api_client_instance.authenticate.assert_called_with("test_token")
    auth_service_instance.save_user_profile.assert_called_with(
        profile_mock, "test_token"
    )
    feedback_instance = mock_feedback_service.return_value
    feedback_instance.info.assert_called_with("Successfully logged in as testuser! ✨")


def test_auth_with_token_file(
    runner,
    mock_config,
    mock_auth_service,
    mock_feedback_service,
    mock_selector,
    mock_api_client,
    tmp_path,
):
    """Test 'viu anilist auth <path/to/token.txt>'."""
    token_file = tmp_path / "token.txt"
    token_file.write_text("file_token")

    api_client_instance = mock_api_client.return_value
    profile_mock = MagicMock()
    profile_mock.name = "testuser"
    api_client_instance.authenticate.return_value = profile_mock

    auth_service_instance = mock_auth_service.return_value
    auth_service_instance.get_auth.return_value = None

    result = runner.invoke(auth, [str(token_file)], obj=mock_config)

    assert result.exit_code == 0
    mock_api_client.assert_called_with("anilist", mock_config)
    api_client_instance.authenticate.assert_called_with("file_token")
    auth_service_instance.save_user_profile.assert_called_with(
        profile_mock, "file_token"
    )
    feedback_instance = mock_feedback_service.return_value
    feedback_instance.info.assert_called_with("Successfully logged in as testuser! ✨")


def test_auth_with_empty_token_file(
    runner,
    mock_config,
    mock_auth_service,
    mock_feedback_service,
    mock_selector,
    mock_api_client,
    tmp_path,
):
    """Test 'viu anilist auth' with an empty token file."""
    token_file = tmp_path / "token.txt"
    token_file.write_text("")

    auth_service_instance = mock_auth_service.return_value
    auth_service_instance.get_auth.return_value = None

    result = runner.invoke(auth, [str(token_file)], obj=mock_config)

    assert result.exit_code == 0
    feedback_instance = mock_feedback_service.return_value
    feedback_instance.error.assert_called_with(f"Token file is empty: {token_file}")


def test_auth_interactive(
    runner,
    mock_config,
    mock_auth_service,
    mock_feedback_service,
    mock_selector,
    mock_api_client,
    mock_webbrowser,
):
    """Test 'viu anilist auth' interactive mode."""
    mock_webbrowser.open.return_value = True

    selector_instance = mock_selector.return_value
    selector_instance.ask.return_value = "interactive_token"

    api_client_instance = mock_api_client.return_value
    profile_mock = MagicMock()
    profile_mock.name = "testuser"
    api_client_instance.authenticate.return_value = profile_mock

    auth_service_instance = mock_auth_service.return_value
    auth_service_instance.get_auth.return_value = None

    result = runner.invoke(auth, [], obj=mock_config)

    assert result.exit_code == 0
    selector_instance.ask.assert_called_with("Enter your AniList Access Token")
    api_client_instance.authenticate.assert_called_with("interactive_token")
    auth_service_instance.save_user_profile.assert_called_with(
        profile_mock, "interactive_token"
    )
    feedback_instance = mock_feedback_service.return_value
    feedback_instance.info.assert_called_with("Successfully logged in as testuser! ✨")


def test_auth_status_logged_in(
    runner, mock_config, mock_auth_service, mock_feedback_service
):
    """Test 'viu anilist auth --status' when logged in."""
    auth_service_instance = mock_auth_service.return_value
    user_data_mock = MagicMock()
    user_data_mock.user_profile = "testuser"
    auth_service_instance.get_auth.return_value = user_data_mock

    result = runner.invoke(auth, ["--status"], obj=mock_config)

    assert result.exit_code == 0
    feedback_instance = mock_feedback_service.return_value
    feedback_instance.info.assert_called_with("Logged in as: testuser")


def test_auth_status_logged_out(
    runner, mock_config, mock_auth_service, mock_feedback_service
):
    """Test 'viu anilist auth --status' when logged out."""
    auth_service_instance = mock_auth_service.return_value
    auth_service_instance.get_auth.return_value = None

    result = runner.invoke(auth, ["--status"], obj=mock_config)

    assert result.exit_code == 0
    feedback_instance = mock_feedback_service.return_value
    feedback_instance.error.assert_called_with("Not logged in.")


def test_auth_logout(
    runner, mock_config, mock_auth_service, mock_feedback_service, mock_selector
):
    """Test 'viu anilist auth --logout'."""
    selector_instance = mock_selector.return_value
    selector_instance.confirm.return_value = True

    result = runner.invoke(auth, ["--logout"], obj=mock_config)

    assert result.exit_code == 0
    auth_service_instance = mock_auth_service.return_value
    auth_service_instance.clear_user_profile.assert_called_once()
    feedback_instance = mock_feedback_service.return_value
    feedback_instance.info.assert_called_with("You have been logged out.")


def test_auth_logout_cancel(
    runner, mock_config, mock_auth_service, mock_feedback_service, mock_selector
):
    """Test 'viu anilist auth --logout' when user cancels."""
    selector_instance = mock_selector.return_value
    selector_instance.confirm.return_value = False

    result = runner.invoke(auth, ["--logout"], obj=mock_config)

    assert result.exit_code == 0
    auth_service_instance = mock_auth_service.return_value
    auth_service_instance.clear_user_profile.assert_not_called()


def test_auth_already_logged_in_relogin_yes(
    runner,
    mock_config,
    mock_auth_service,
    mock_feedback_service,
    mock_selector,
    mock_api_client,
):
    """Test 'viu anilist auth' when already logged in and user chooses to relogin."""
    auth_service_instance = mock_auth_service.return_value
    auth_profile_mock = MagicMock()
    auth_profile_mock.user_profile.name = "testuser"
    auth_service_instance.get_auth.return_value = auth_profile_mock

    selector_instance = mock_selector.return_value
    selector_instance.confirm.return_value = True
    selector_instance.ask.return_value = "new_token"

    api_client_instance = mock_api_client.return_value
    new_profile_mock = MagicMock()
    new_profile_mock.name = "newuser"
    api_client_instance.authenticate.return_value = new_profile_mock

    result = runner.invoke(auth, [], obj=mock_config)

    assert result.exit_code == 0
    selector_instance.confirm.assert_called_with(
        "You are already logged in as testuser. Would you like to relogin"
    )
    auth_service_instance.save_user_profile.assert_called_with(
        new_profile_mock, "new_token"
    )
    feedback_instance = mock_feedback_service.return_value
    feedback_instance.info.assert_called_with("Successfully logged in as newuser! ✨")


def test_auth_already_logged_in_relogin_no(
    runner, mock_config, mock_auth_service, mock_feedback_service, mock_selector
):
    """Test 'viu anilist auth' when already logged in and user chooses not to relogin."""
    auth_service_instance = mock_auth_service.return_value
    auth_profile_mock = MagicMock()
    auth_profile_mock.user_profile.name = "testuser"
    auth_service_instance.get_auth.return_value = auth_profile_mock

    selector_instance = mock_selector.return_value
    selector_instance.confirm.return_value = False

    result = runner.invoke(auth, [], obj=mock_config)

    assert result.exit_code == 0
    auth_service_instance.save_user_profile.assert_not_called()
    feedback_instance = mock_feedback_service.return_value
    feedback_instance.info.assert_not_called()
