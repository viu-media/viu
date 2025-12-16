import json
import logging
import sys
from pathlib import Path

from .....core.constants import APP_CACHE_DIR, SCRIPTS_DIR
from .....libs.media_api.params import MediaSearchParams
from ...session import Context, session
from ...state import InternalDirective, MediaApiState, MenuName, State

logger = logging.getLogger(__name__)

SEARCH_CACHE_DIR = APP_CACHE_DIR / "previews" / "dynamic-search"
SEARCH_RESULTS_FILE = SEARCH_CACHE_DIR / "current_search_results.json"
FZF_SCRIPTS_DIR = SCRIPTS_DIR / "fzf"
SEARCH_TEMPLATE_SCRIPT = (FZF_SCRIPTS_DIR / "search.py").read_text(encoding="utf-8")


@session.menu
def dynamic_search(ctx: Context, state: State) -> State | InternalDirective:
    """Dynamic search menu that provides real-time search results."""
    feedback = ctx.feedback
    feedback.clear_console()

    # Ensure cache directory exists
    SEARCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Read the GraphQL search query
    from .....libs.media_api.anilist import gql

    search_query = gql.SEARCH_MEDIA.read_text(encoding="utf-8")
    # Escape the GraphQL query as a JSON string literal for Python script
    search_query_json = json.dumps(search_query).replace('"', "")

    # Prepare the search script
    auth_header = ""
    profile = ctx.auth.get_auth()
    if ctx.media_api.is_authenticated() and profile:
        auth_header = f"Bearer {profile.token}"

    search_command = SEARCH_TEMPLATE_SCRIPT

    replacements = {
        "GRAPHQL_ENDPOINT": "https://graphql.anilist.co",
        "GRAPHQL_QUERY": search_query_json,
        "SEARCH_RESULTS_FILE": SEARCH_RESULTS_FILE.as_posix(),
        "AUTH_HEADER": auth_header,
    }

    for key, value in replacements.items():
        search_command = search_command.replace(f"{{{key}}}", str(value))

    # Write the filled template to a cache file
    search_script_file = SEARCH_CACHE_DIR / "search.py"
    search_script_file.write_text(search_command, encoding="utf-8")

    # Make the search script executable by calling it with python3
    # fzf will pass the query as {q} which becomes the first argument
    search_command_final = (
        f"{Path(sys.executable).as_posix()} {search_script_file.as_posix()} {{q}}"
    )

    try:
        # Prepare preview functionality
        preview_command = None
        if ctx.config.general.preview != "none":
            from ....utils.preview import create_preview_context

            with create_preview_context() as preview_ctx:
                preview_command = preview_ctx.get_dynamic_anime_preview(ctx.config)

                choice = ctx.selector.search(
                    prompt="Search Anime",
                    search_command=search_command_final,
                    preview=preview_command,
                )
        else:
            choice = ctx.selector.search(
                prompt="Search Anime",
                search_command=search_command_final,
            )
    except NotImplementedError:
        feedback.error("Dynamic search is not supported by your current selector")
        feedback.info("Please use the regular search option or switch to fzf selector")
        return InternalDirective.MAIN

    if not choice:
        return InternalDirective.MAIN

    # Read the cached search results
    if not SEARCH_RESULTS_FILE.exists():
        logger.error("Search results file not found")
        return InternalDirective.MAIN

    with open(SEARCH_RESULTS_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Transform the raw data into MediaSearchResult
    search_result = ctx.media_api.transform_raw_search_data(raw_data)

    if not search_result or not search_result.media:
        feedback.info("No results found")
        return InternalDirective.MAIN

    # Find the selected media item by matching the choice with the displayed format
    selected_media = None
    for media_item in search_result.media:
        if (
            media_item.title.english == choice.strip()
            or media_item.title.romaji == choice.strip()
        ):
            selected_media = media_item
            break

    if not selected_media:
        logger.error(f"Could not find selected media for choice: {choice}")
        return InternalDirective.MAIN

    # Navigate to media actions with the selected item
    return State(
        menu_name=MenuName.MEDIA_ACTIONS,
        media_api=MediaApiState(
            search_result={media.id: media for media in search_result.media},
            media_id=selected_media.id,
            search_params=MediaSearchParams(),
            page_info=search_result.page_info,
        ),
    )
