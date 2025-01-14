from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable

    from ...libs.anilist.types import AnilistBaseMediaDataSchema
    from ...libs.anime_provider.types import Anime, EpisodeStream, SearchResult, Server


class FastAnimeRuntimeState(object):
    """A class that manages fastanime runtime during anilist command runtime"""

    provider_current_episode_stream_link: str
    provider_current_server: "Server"
    provider_current_server_name: str
    provider_available_episodes: list[str]
    provider_current_episode_number: str
    provider_server_episode_streams: list["EpisodeStream"]
    provider_anime_title: str
    provider_anime: "Anime"
    provider_anime_search_result: "SearchResult"
    progress_tracking: str = ""

    selected_anime_anilist: "AnilistBaseMediaDataSchema"
    selected_anime_id_anilist: int
    selected_anime_title_anilist: str
    selected_anime_media_action: str = "Stream"
    selected_anime_download_episodes: list[int]
    # current_anilist_data: "AnilistDataSchema | AnilistMediaList"
    anilist_results_data: "Any"
    current_page: int
    current_data_loader: "Callable"


def exit_app(exit_code=0, *args, **kwargs):
    import sys

    from rich.console import Console

    from ...constants import APP_NAME, ICON_PATH, USER_NAME

    console = Console()
    if not console.is_terminal:
        try:
            from plyer import notification
        except ImportError:
            print(
                "Plyer is not installed; install it for desktop notifications to be enabled"
            )
            exit(1)
        notification.notify(
            app_name=APP_NAME,
            app_icon=ICON_PATH,
            message=f"Have a good day {USER_NAME}",
            title="Shutting down",
        )  # pyright:ignore
    else:
        console.clear()
        console.print("Have a good day :smile:", USER_NAME)
    sys.exit(exit_code)
