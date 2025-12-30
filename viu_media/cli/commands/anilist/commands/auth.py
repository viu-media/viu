import webbrowser
from pathlib import Path
import click

from .....core.config.model import AppConfig


def _get_token(feedback, selector, token_input: str | None) -> str | None:
    """
    Retrieves the authentication token from a file path, a direct string, or an interactive prompt.
    """
    if token_input:
        path = Path(token_input)
        if path.is_file():
            try:
                token = path.read_text().strip()
                if not token:
                    feedback.error(f"Token file is empty: {path}")
                    return None
                return token
            except Exception as e:
                feedback.error(f"Error reading token from file: {e}")
                return None
        return token_input

    from .....core.constants import ANILIST_AUTH

    open_success = webbrowser.open(ANILIST_AUTH, new=2)
    if open_success:
        feedback.info("Your browser has been opened to obtain an AniList token.")
        feedback.info(
            f"Or you can visit the site manually [magenta][link={ANILIST_AUTH}]here[/link][/magenta]."
        )
    else:
        feedback.warning(
            f"Failed to open the browser. Please visit the site manually [magenta][link={ANILIST_AUTH}]here[/link][/magenta]."
        )
    feedback.info(
        "After authorizing, copy the token from the address bar and paste it below."
    )
    return selector.ask("Enter your AniList Access Token")


@click.command(help="Login to your AniList account to enable progress tracking.")
@click.option("--status", "-s", is_flag=True, help="Check current login status.")
@click.option("--logout", "-l", is_flag=True, help="Log out and erase credentials.")
@click.argument("token_input", required=False, type=str)
@click.pass_obj
def auth(config: AppConfig, status: bool, logout: bool, token_input: str | None):
    """
    Handles user authentication and credential management.

    This command allows you to log in to your AniList account to enable
    progress tracking and other features.

    You can provide your authentication token in three ways:
    1. Interactively: Run the command without arguments to open a browser
       and be prompted to paste the token.
    2. As an argument: Pass the token string directly to the command.
       $ viu anilist auth "your_token_here"
    3. As a file: Pass the path to a text file containing the token.
       $ viu anilist auth /path/to/token.txt
    """
    from .....libs.media_api.api import create_api_client
    from ....service.auth import AuthService
    from ....service.feedback import FeedbackService

    auth_service = AuthService("anilist")
    feedback = FeedbackService(config)

    if status:
        user_data = auth_service.get_auth()
        if user_data:
            feedback.info(f"Logged in as: {user_data.user_profile}")
        else:
            feedback.error("Not logged in.")
        return

    from .....libs.selectors.selector import create_selector

    selector = create_selector(config)
    feedback.clear_console()

    if logout:
        if selector.confirm("Are you sure you want to log out and erase your token?"):
            auth_service.clear_user_profile()
            feedback.info("You have been logged out.")
        return

    if auth_profile := auth_service.get_auth():
        if not selector.confirm(
            f"You are already logged in as {auth_profile.user_profile.name}.Would you like to relogin"
        ):
            return
    token = _get_token(feedback, selector, token_input)

    if not token:
        if not token_input:
            feedback.error("Login cancelled.")
        return

    api_client = create_api_client("anilist", config)
    # Use the API client to validate the token and get profile info
    profile = api_client.authenticate(token.strip())

    if profile:
        # If successful, use the manager to save the credentials
        auth_service.save_user_profile(profile, token)
        feedback.info(f"Successfully logged in as {profile.name}! ✨")
    else:
        feedback.error("Login failed. The token may be invalid or expired.")
