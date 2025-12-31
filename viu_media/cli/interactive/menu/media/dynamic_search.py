import json
import logging
import shutil
from pathlib import Path

from .....core.constants import APP_CACHE_DIR, SCRIPTS_DIR
from .....core.utils.detect import get_python_executable
from .....libs.media_api.params import MediaSearchParams
from ...session import Context, session
from ...state import InternalDirective, MediaApiState, MenuName, State

logger = logging.getLogger(__name__)

SEARCH_CACHE_DIR = APP_CACHE_DIR / "previews" / "dynamic-search"
SEARCH_RESULTS_FILE = SEARCH_CACHE_DIR / "current_search_results.json"
LAST_QUERY_FILE = SEARCH_CACHE_DIR / "last_query.txt"
RESTORE_MODE_FILE = SEARCH_CACHE_DIR / ".restore_mode"
FZF_SCRIPTS_DIR = SCRIPTS_DIR / "fzf"
SEARCH_TEMPLATE_SCRIPT = (FZF_SCRIPTS_DIR / "search.py").read_text(encoding="utf-8")
FILTER_PARSER_SCRIPT = FZF_SCRIPTS_DIR / "_filter_parser.py"


def _load_cached_titles() -> list[str]:
    """Load titles from cached search results for display in fzf."""
    if not SEARCH_RESULTS_FILE.exists():
        return []
    
    try:
        with open(SEARCH_RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        media_list = data.get("data", {}).get("Page", {}).get("media", [])
        titles = []
        for media in media_list:
            title_obj = media.get("title", {})
            title = (
                title_obj.get("english")
                or title_obj.get("romaji")
                or title_obj.get("native")
                or "Unknown"
            )
            titles.append(title)
        return titles
    except (IOError, json.JSONDecodeError):
        return []


@session.menu
def dynamic_search(ctx: Context, state: State) -> State | InternalDirective:
    """Dynamic search menu that provides real-time search results."""
    feedback = ctx.feedback
    feedback.clear_console()

    # Ensure cache directory exists
    SEARCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Check if we're in restore mode (coming back from media_actions)
    restore_mode = RESTORE_MODE_FILE.exists()
    if restore_mode:
        # Clear the restore flag
        RESTORE_MODE_FILE.unlink(missing_ok=True)

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
        "LAST_QUERY_FILE": LAST_QUERY_FILE.as_posix(),
        "AUTH_HEADER": auth_header,
    }

    for key, value in replacements.items():
        search_command = search_command.replace(f"{{{key}}}", str(value))

    # Write the filled template to a cache file
    search_script_file = SEARCH_CACHE_DIR / "search.py"
    search_script_file.write_text(search_command, encoding="utf-8")

    # Copy the filter parser module to the cache directory
    # This is required for the search script to import it
    filter_parser_dest = SEARCH_CACHE_DIR / "_filter_parser.py"
    if FILTER_PARSER_SCRIPT.exists():
        shutil.copy2(FILTER_PARSER_SCRIPT, filter_parser_dest)

    # Make the search script executable by calling it with python3
    # fzf will pass the query as {q} which becomes the first argument
    search_command_final = (
        f"{Path(get_python_executable()).as_posix()} {search_script_file.as_posix()} {{q}}"
    )

    # Header hint for filter syntax
    filter_hint = "💡 Filters: @genre:action @status:airing @year:2024 @sort:score (type @help for more)"

    # Only load previous query if we're in restore mode (coming back from media_actions)
    initial_query = None
    cached_results = None
    if restore_mode:
        # Load previous query
        if LAST_QUERY_FILE.exists():
            try:
                initial_query = LAST_QUERY_FILE.read_text(encoding="utf-8").strip()
            except IOError:
                pass
        # Load cached results to display immediately without network request
        cached_results = _load_cached_titles()

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
                    header=filter_hint,
                    initial_query=initial_query,
                    initial_results=cached_results,
                )
        else:
            choice = ctx.selector.search(
                prompt="Search Anime",
                search_command=search_command_final,
                header=filter_hint,
                initial_query=initial_query,
                initial_results=cached_results,
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

    # Set restore mode flag so we can restore state when user goes back
    RESTORE_MODE_FILE.touch()

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
