from .....libs.provider.anime.params import AnimeParams, SearchParams
from ...session import Context, session
from ...state import InternalDirective, State


@session.menu
def download_episodes(ctx: Context, state: State) -> State | InternalDirective:
    """Menu to select and download episodes synchronously."""
    from viu_media.cli.utils.search import find_best_match_title
    from .....core.utils.normalizer import normalize_title

    feedback = ctx.feedback
    selector = ctx.selector
    media_item = state.media_api.media_item
    config = ctx.config
    provider = ctx.provider

    if not media_item:
        feedback.error("No media item selected for download.")
        return InternalDirective.BACK

    media_title = media_item.title.english or media_item.title.romaji
    if not media_title:
        feedback.error("Cannot download: Media item has no title.")
        return InternalDirective.BACK

    # Step 1: Find the anime on the provider to get a full episode list
    with feedback.progress(
        f"Searching for '{media_title}' on {provider.__class__.__name__}..."
    ):
        provider_search_results = provider.search(
            SearchParams(
                query=normalize_title(media_title, config.general.provider.value, True)
            )
        )

    if not provider_search_results or not provider_search_results.results:
        feedback.warning(f"Could not find '{media_title}' on provider.")
        return InternalDirective.BACK

    provider_results_map = {res.title: res for res in provider_search_results.results}
    best_match_title = find_best_match_title(
        provider_results_map, config.general.provider, media_item
    )
    selected_provider_anime_ref = provider_results_map[best_match_title]

    with feedback.progress(f"Fetching episode list for '{best_match_title}'..."):
        full_provider_anime = provider.get(
            AnimeParams(id=selected_provider_anime_ref.id, query=media_title)
        )

    if not full_provider_anime:
        feedback.warning(f"Failed to fetch details for '{best_match_title}'.")
        return InternalDirective.BACK

    available_episodes = getattr(
        full_provider_anime.episodes, config.stream.translation_type, []
    )
    if not available_episodes:
        feedback.warning("No episodes found for download.")
        return InternalDirective.BACK

    # Step 2: Let user select episodes
    selected_episodes = selector.choose_multiple(
        "Select episodes to download (TAB to select, ENTER to confirm)",
        choices=available_episodes,
    )

    if not selected_episodes:
        feedback.info("No episodes selected for download.")
        return InternalDirective.BACK

    # Step 3: Download episodes synchronously using the session-scoped service
    feedback.info(
        f"Starting download of {len(selected_episodes)} episodes. This may take a while..."
    )
    ctx.download.download_episodes_sync(media_item, selected_episodes)

    feedback.success(f"Finished downloading {len(selected_episodes)} episodes.")

    # After downloading, return to the media actions menu
    return InternalDirective.BACK
