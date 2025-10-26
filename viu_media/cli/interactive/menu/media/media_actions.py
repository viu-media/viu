from typing import Callable, Dict, Literal, Optional

from .....libs.media_api.params import (
    MediaRecommendationParams,
    MediaRelationsParams,
    UpdateUserMediaListEntryParams,
)
from .....libs.media_api.types import (
    MediaItem,
    MediaStatus,
    UserMediaListStatus,
)
from .....libs.player.params import PlayerParams
from ...session import Context, session
from ...state import InternalDirective, MediaApiState, MenuName, State

MenuAction = Callable[[], State | InternalDirective]


@session.menu
def media_actions(ctx: Context, state: State) -> State | InternalDirective:
    from ....service.registry.service import DownloadStatus

    feedback = ctx.feedback

    icons = ctx.config.general.icons

    media_item = state.media_api.media_item

    if not media_item:
        feedback.error("Media item is not in state")
        return InternalDirective.BACK
    progress = _get_progress_string(ctx, state.media_api.media_item)

    # Check for downloaded episodes to conditionally show options
    record = ctx.media_registry.get_media_record(media_item.id)
    has_downloads = False
    if record:
        has_downloads = any(
            ep.download_status == DownloadStatus.COMPLETED
            and ep.file_path
            and ep.file_path.exists()
            for ep in record.media_episodes
        )

    options: Dict[str, MenuAction] = {
        f"{'▶️ ' if icons else ''}Stream {progress}": _stream(ctx, state),
        f"{'📽️ ' if icons else ''}Episodes": _stream(
            ctx, state, force_episodes_menu=True
        ),
    }

    if has_downloads:
        options[f"{'💾 ' if icons else ''}Stream (Downloads)"] = _stream_downloads(
            ctx, state
        )
        options[f"{'💿 ' if icons else ''}Episodes (Downloads)"] = _stream_downloads(
            ctx, state, force_episodes_menu=True
        )

    options.update(
        {
            f"{'📥 ' if icons else ''}Download": _download_episodes(ctx, state),
            f"{'📼 ' if icons else ''}Watch Trailer": _watch_trailer(ctx, state),
            f"{'🔗 ' if icons else ''}Recommendations": _view_recommendations(
                ctx, state
            ),
            f"{'🔄 ' if icons else ''}Related Anime": _view_relations(ctx, state),
            f"{'👥 ' if icons else ''}Characters": _view_characters(ctx, state),
            f"{'📅 ' if icons else ''}Airing Schedule": _view_airing_schedule(
                ctx, state
            ),
            f"{'📝 ' if icons else ''}View Reviews": _view_reviews(ctx, state),
            f"{'➕ ' if icons else ''}Add/Update List": _manage_user_media_list(
                ctx, state
            ),
            f"{'➕ ' if icons else ''}Add/Update List (Bulk)": _manage_user_media_list_in_bulk(
                ctx, state
            ),
            f"{'⭐ ' if icons else ''}Score Anime": _score_anime(ctx, state),
            f"{'ℹ️ ' if icons else ''}View Info": _view_info(ctx, state),
            f"{'📀 ' if icons else ''}Change Provider (Current: {ctx.config.general.provider.value.upper()})": _change_provider(
                ctx, state
            ),
            f"{'🔘 ' if icons else ''}Toggle Auto Select Anime (Current: {ctx.config.general.auto_select_anime_result})": _toggle_config_state(
                ctx, state, "AUTO_ANIME"
            ),
            f"{'🔘 ' if icons else ''}Toggle Auto Next Episode (Current: {ctx.config.stream.auto_next})": _toggle_config_state(
                ctx, state, "AUTO_EPISODE"
            ),
            f"{'🔘 ' if icons else ''}Toggle Continue From History (Current: {ctx.config.stream.continue_from_watch_history})": _toggle_config_state(
                ctx, state, "CONTINUE_FROM_HISTORY"
            ),
            f"{'🔘 ' if icons else ''}Toggle Translation Type  (Current: {ctx.config.stream.translation_type.upper()})": _toggle_config_state(
                ctx, state, "TRANSLATION_TYPE"
            ),
            f"{'🔙 ' if icons else ''}Back to Results": lambda: InternalDirective.BACK,
            f"{'❌ ' if icons else ''}Exit": lambda: InternalDirective.EXIT,
        }
    )

    choice = ctx.selector.choose(
        prompt="Select Action",
        choices=list(options.keys()),
    )

    if choice and choice in options:
        return options[choice]()

    return InternalDirective.BACK


def _get_progress_string(ctx: Context, media_item: Optional[MediaItem]) -> str:
    if not media_item:
        return ""
    config = ctx.config

    progress = "0"

    if media_item.user_status:
        progress = str(media_item.user_status.progress or 0)

    episodes_total = str(media_item.episodes or "??")
    display_title = f"({progress} of {episodes_total})"

    # Add a visual indicator for new episodes if applicable
    if (
        media_item.status == MediaStatus.RELEASING
        and media_item.next_airing
        and media_item.user_status
        and media_item.user_status.status == UserMediaListStatus.WATCHING
    ):
        last_aired = media_item.next_airing.episode - 1
        unwatched = last_aired - (media_item.user_status.progress or 0)
        if unwatched > 0:
            icon = "🔹" if config.general.icons else "!"
            display_title += f" {icon}{unwatched} new{icon}"

    return display_title


def _stream(ctx: Context, state: State, force_episodes_menu=False) -> MenuAction:
    def action():
        if force_episodes_menu:
            ctx.switch.force_episodes_menu()
        return State(menu_name=MenuName.PROVIDER_SEARCH, media_api=state.media_api)

    return action


def _stream_downloads(
    ctx: Context, state: State, force_episodes_menu=False
) -> MenuAction:
    def action():
        if force_episodes_menu:
            ctx.switch.force_episodes_menu()
        return State(menu_name=MenuName.PLAY_DOWNLOADS, media_api=state.media_api)

    return action


def _download_episodes(ctx: Context, state: State) -> MenuAction:
    def action():
        return State(menu_name=MenuName.DOWNLOAD_EPISODES, media_api=state.media_api)

    return action


def _watch_trailer(ctx: Context, state: State) -> MenuAction:
    def action():
        feedback = ctx.feedback
        media_item = state.media_api.media_item

        if not media_item:
            return InternalDirective.RELOAD

        if not media_item.trailer or not media_item.trailer.id:
            feedback.warning(
                "No trailer available for this anime",
                "This anime doesn't have a trailer link in the database",
            )
        else:
            trailer_url = f"https://www.youtube.com/watch?v={media_item.trailer.id}"

            ctx.player.play(
                PlayerParams(url=trailer_url, query="", episode="", title="")
            )

        return InternalDirective.RELOAD

    return action


def _manage_user_media_list(ctx: Context, state: State) -> MenuAction:
    def action():
        feedback = ctx.feedback
        media_item = state.media_api.media_item

        if not media_item:
            return InternalDirective.RELOAD

        if not ctx.media_api.is_authenticated():
            feedback.warning(
                "You are not authenticated",
            )
            return InternalDirective.RELOAD

        status = ctx.selector.choose(
            "Select list status", choices=[t.value for t in UserMediaListStatus]
        )
        if status:
            # local
            ctx.media_registry.update_media_index_entry(
                media_id=media_item.id,
                media_item=media_item,
                status=UserMediaListStatus(status),
            )
            # remote
            if not ctx.media_api.update_list_entry(
                UpdateUserMediaListEntryParams(
                    media_item.id, status=UserMediaListStatus(status)
                )
            ):
                print(f"Failed to update {media_item.title.english}")
        return InternalDirective.RELOAD

    return action


def _manage_user_media_list_in_bulk(ctx: Context, state: State) -> MenuAction:
    def action():
        feedback = ctx.feedback
        search_result = state.media_api.search_result

        if not search_result:
            return InternalDirective.RELOAD

        if not ctx.media_api.is_authenticated():
            feedback.warning(
                "You are not authenticated",
            )
            return InternalDirective.RELOAD

        choice_map: Dict[str, MediaItem] = {
            item.title.english: item for item in search_result.values()
        }
        preview_command = None
        if ctx.config.general.preview != "none":
            from ....utils.preview import create_preview_context

            with create_preview_context() as preview_ctx:
                preview_command = preview_ctx.get_anime_preview(
                    list(choice_map.values()),
                    list(choice_map.keys()),
                    ctx.config,
                )
                selected_titles = ctx.selector.choose_multiple(
                    "Select anime to manage",
                    list(choice_map.keys()),
                    preview=preview_command,
                )
        else:
            selected_titles = ctx.selector.choose_multiple(
                "Select anime to download",
                list(choice_map.keys()),
            )
        if not selected_titles:
            feedback.warning("No anime selected. Aborting download.")
            return InternalDirective.RELOAD
        anime_to_update_status = [choice_map[title] for title in selected_titles]

        status = ctx.selector.choose(
            "Select list status", choices=[t.value for t in UserMediaListStatus]
        )
        if not status:
            feedback.warning("No status selected. Aborting bulk action.")
            return InternalDirective.RELOAD
        with feedback.progress(
            "Updating media list...", total=len(anime_to_update_status)
        ) as (task_id, progress):
            for media_item in anime_to_update_status:
                feedback.info(f"Updating media status for {media_item.title.english}")
                ctx.media_registry.update_media_index_entry(
                    media_id=media_item.id,
                    media_item=media_item,
                    status=UserMediaListStatus(status),
                )
                # remote

                if not ctx.media_api.update_list_entry(
                    UpdateUserMediaListEntryParams(
                        media_item.id, status=UserMediaListStatus(status)
                    )
                ):
                    print(f"Failed to update {media_item.title.english}")

                progress.update(task_id, advance=1)  # type: ignore
        return InternalDirective.RELOAD

    return action


def _change_provider(ctx: Context, state: State) -> MenuAction:
    def action():
        from .....libs.provider.anime.types import ProviderName

        new_provider = ctx.selector.choose(
            "Select Provider", [provider.value for provider in ProviderName]
        )
        ctx.config.general.provider = ProviderName(new_provider)
        # force a reset of the provider
        ctx._provider = None
        return InternalDirective.RELOAD

    return action


def _toggle_config_state(
    ctx: Context,
    state: State,
    config_state: Literal[
        "AUTO_ANIME", "AUTO_EPISODE", "CONTINUE_FROM_HISTORY", "TRANSLATION_TYPE"
    ],
) -> MenuAction:
    def action():
        match config_state:
            case "AUTO_ANIME":
                ctx.config.general.auto_select_anime_result = (
                    not ctx.config.general.auto_select_anime_result
                )
            case "AUTO_EPISODE":
                ctx.config.stream.auto_next = not ctx.config.stream.auto_next
            case "CONTINUE_FROM_HISTORY":
                ctx.config.stream.continue_from_watch_history = (
                    not ctx.config.stream.continue_from_watch_history
                )
            case "TRANSLATION_TYPE":
                ctx.config.stream.translation_type = (
                    "sub" if ctx.config.stream.translation_type == "dub" else "dub"
                )
        return InternalDirective.RELOAD

    return action


def _score_anime(ctx: Context, state: State) -> MenuAction:
    def action():
        feedback = ctx.feedback
        media_item = state.media_api.media_item

        if not media_item:
            return InternalDirective.RELOAD

        if not ctx.media_api.is_authenticated():
            return InternalDirective.RELOAD

        score_str = ctx.selector.ask("Enter score (0.0 - 10.0):")
        try:
            score = float(score_str) if score_str else 0.0
            if not 0.0 <= score <= 10.0:
                raise ValueError("Score out of range.")
            # local
            ctx.media_registry.update_media_index_entry(
                media_id=media_item.id, media_item=media_item, score=score
            )
            # remote
            ctx.media_api.update_list_entry(
                UpdateUserMediaListEntryParams(media_id=media_item.id, score=score)
            )
        except (ValueError, TypeError):
            feedback.error(
                "Invalid score entered", "Please enter a number between 0.0 and 10.0"
            )
        return InternalDirective.RELOAD

    return action


def _view_info(ctx: Context, state: State) -> MenuAction:
    def action():
        media_item = state.media_api.media_item

        if not media_item:
            return InternalDirective.RELOAD

        import re

        from rich import box
        from rich.columns import Columns
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        from ....utils import image

        console = Console()
        console.clear()

        # Display cover image if available
        if cover_image := media_item.cover_image:
            image.render(cover_image.large)

        # Create main title
        main_title = (
            media_item.title.english or media_item.title.romaji or "Unknown Title"
        )
        title_text = Text(main_title, style="bold cyan")

        # Create info table
        info_table = Table(show_header=False, box=box.SIMPLE, pad_edge=False)
        info_table.add_column("Field", style="bold yellow", min_width=15)
        info_table.add_column("Value", style="white")

        # Add basic information
        info_table.add_row("English Title", media_item.title.english or "N/A")
        info_table.add_row("Romaji Title", media_item.title.romaji or "N/A")
        info_table.add_row("Native Title", media_item.title.native or "N/A")

        if media_item.synonymns:
            synonyms = ", ".join(media_item.synonymns[:3])  # Show first 3 synonyms
            if len(media_item.synonymns) > 3:
                synonyms += f" (+{len(media_item.synonymns) - 3} more)"
            info_table.add_row("Synonyms", synonyms)

        info_table.add_row("Type", media_item.type.value if media_item.type else "N/A")
        info_table.add_row(
            "Format", media_item.format.value if media_item.format else "N/A"
        )
        info_table.add_row(
            "Status", media_item.status.value if media_item.status else "N/A"
        )
        info_table.add_row(
            "Episodes", str(media_item.episodes) if media_item.episodes else "Unknown"
        )
        info_table.add_row(
            "Duration",
            f"{media_item.duration} min" if media_item.duration else "Unknown",
        )

        # Add dates
        if media_item.start_date:
            start_date = media_item.start_date.strftime("%Y-%m-%d")
            info_table.add_row("Start Date", start_date)
        if media_item.end_date:
            end_date = media_item.end_date.strftime("%Y-%m-%d")
            info_table.add_row("End Date", end_date)

        # Add scores and popularity
        if media_item.average_score:
            info_table.add_row("Average Score", f"{media_item.average_score}/100")
        if media_item.popularity:
            info_table.add_row("Popularity", f"#{media_item.popularity:,}")
        if media_item.favourites:
            info_table.add_row("Favorites", f"{media_item.favourites:,}")

        # Add MAL ID if available
        if media_item.id_mal:
            info_table.add_row("MyAnimeList ID", str(media_item.id_mal))

        # Create genres panel
        if media_item.genres:
            genres_text = ", ".join([genre.value for genre in media_item.genres])
            genres_panel = Panel(
                Text(genres_text, style="green"),
                title="[bold]Genres[/bold]",
                border_style="green",
                box=box.ROUNDED,
            )
        else:
            genres_panel = Panel(
                Text("No genres available", style="dim"),
                title="[bold]Genres[/bold]",
                border_style="green",
                box=box.ROUNDED,
            )

        # Create tags panel (show top tags)
        if media_item.tags:
            top_tags = sorted(media_item.tags, key=lambda x: x.rank or 0, reverse=True)[
                :10
            ]
            tags_text = ", ".join([tag.name.value for tag in top_tags])
            tags_panel = Panel(
                Text(tags_text, style="yellow"),
                title="[bold]Tags[/bold]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        else:
            tags_panel = Panel(
                Text("No tags available", style="dim"),
                title="[bold]Tags[/bold]",
                border_style="yellow",
                box=box.ROUNDED,
            )

        # Create studios panel
        if media_item.studios:
            studios_text = ", ".join(
                [studio.name for studio in media_item.studios if studio.name]
            )
            studios_panel = Panel(
                Text(studios_text, style="blue"),
                title="[bold]Studios[/bold]",
                border_style="blue",
                box=box.ROUNDED,
            )
        else:
            studios_panel = Panel(
                Text("No studio information", style="dim"),
                title="[bold]Studios[/bold]",
                border_style="blue",
                box=box.ROUNDED,
            )

        # Create description panel
        description = media_item.description or "No description available"
        # Clean HTML tags from description
        clean_description = re.sub(r"<[^>]+>", "", description)
        # Replace common HTML entities
        clean_description = (
            clean_description.replace("&quot;", '"')
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )

        description_panel = Panel(
            Text(clean_description, style="white"),
            title="[bold]Description[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )

        # Create user status panel if available
        if media_item.user_status:
            user_info_table = Table(show_header=False, box=box.SIMPLE)
            user_info_table.add_column("Field", style="bold magenta")
            user_info_table.add_column("Value", style="white")

            if media_item.user_status.status:
                user_info_table.add_row(
                    "Status", media_item.user_status.status.value.title()
                )
            if media_item.user_status.progress is not None:
                progress = (
                    f"{media_item.user_status.progress}/{media_item.episodes or '?'}"
                )
                user_info_table.add_row("Progress", progress)
            if media_item.user_status.score:
                user_info_table.add_row(
                    "Your Score", f"{media_item.user_status.score}/10"
                )
            if media_item.user_status.repeat:
                user_info_table.add_row(
                    "Rewatched", f"{media_item.user_status.repeat} times"
                )

            user_panel = Panel(
                user_info_table,
                title="[bold]Your List Status[/bold]",
                border_style="magenta",
                box=box.ROUNDED,
            )
        else:
            user_panel = None

        # Create next airing panel if available
        if media_item.next_airing:
            airing_info_table = Table(show_header=False, box=box.SIMPLE)
            airing_info_table.add_column("Field", style="bold red")
            airing_info_table.add_column("Value", style="white")

            airing_info_table.add_row(
                "Next Episode", str(media_item.next_airing.episode)
            )

            if media_item.next_airing.airing_at:
                air_date = media_item.next_airing.airing_at.strftime("%Y-%m-%d %H:%M")
                airing_info_table.add_row("Air Date", air_date)

            airing_panel = Panel(
                airing_info_table,
                title="[bold]Next Airing[/bold]",
                border_style="red",
                box=box.ROUNDED,
            )
        else:
            airing_panel = None

        # Create main info panel
        info_panel = Panel(
            info_table,
            title="[bold]Basic Information[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )

        # Display everything
        console.print(Panel(title_text, box=box.DOUBLE, border_style="bright_cyan"))
        console.print()

        # Create columns for better layout
        panels_row1 = [info_panel, genres_panel]
        if user_panel:
            panels_row1.append(user_panel)

        console.print(Columns(panels_row1, equal=True, expand=True))
        console.print()

        panels_row2 = [tags_panel, studios_panel]
        if airing_panel:
            panels_row2.append(airing_panel)

        console.print(Columns(panels_row2, equal=True, expand=True))
        console.print()

        console.print(description_panel)

        ctx.selector.ask("Press Enter to continue...")
        return InternalDirective.RELOAD

    return action


def _view_recommendations(ctx: Context, state: State) -> MenuAction:
    def action():
        feedback = ctx.feedback
        media_item = state.media_api.media_item

        if not media_item:
            feedback.error("Media item is not in state")
            return InternalDirective.RELOAD

        loading_message = "Fetching recommendations..."
        recommendations = None

        with feedback.progress(loading_message):
            recommendations = ctx.media_api.get_recommendation_for(
                MediaRecommendationParams(id=media_item.id, page=1)
            )

        if not recommendations:
            feedback.warning(
                "No recommendations found",
                "This anime doesn't have any recommendations available",
            )
            return InternalDirective.RELOAD

        # Convert list of MediaItem to search result format
        search_result = {item.id: item for item in recommendations}

        # Create a fake page info since recommendations don't have pagination
        from .....libs.media_api.types import PageInfo

        page_info = PageInfo(
            total=len(recommendations),
            current_page=1,
            has_next_page=False,
            per_page=len(recommendations),
        )

        return State(
            menu_name=MenuName.RESULTS,
            media_api=MediaApiState(
                search_result=search_result,
                page_info=page_info,
                search_params=None,  # No search params for recommendations
            ),
        )

    return action


def _view_relations(ctx: Context, state: State) -> MenuAction:
    def action():
        feedback = ctx.feedback
        media_item = state.media_api.media_item

        if not media_item:
            feedback.error("Media item is not in state")
            return InternalDirective.RELOAD

        loading_message = "Fetching related anime..."
        relations = None

        with feedback.progress(loading_message):
            relations = ctx.media_api.get_related_anime_for(
                MediaRelationsParams(id=media_item.id)
            )

        if not relations:
            feedback.warning(
                "No related anime found",
                "This anime doesn't have any related anime available",
            )
            return InternalDirective.RELOAD

        # Convert list of MediaItem to search result format
        search_result = {item.id: item for item in relations}

        # Create a fake page info since relations don't have pagination
        from .....libs.media_api.types import PageInfo

        page_info = PageInfo(
            total=len(relations),
            current_page=1,
            has_next_page=False,
            per_page=len(relations),
        )

        return State(
            menu_name=MenuName.RESULTS,
            media_api=MediaApiState(
                search_result=search_result,
                page_info=page_info,
                search_params=None,  # No search params for relations
            ),
        )

    return action


def _view_characters(ctx: Context, state: State) -> MenuAction:
    """Action to transition to the character selection menu."""

    def action() -> State | InternalDirective:
        return State(menu_name=MenuName.MEDIA_CHARACTERS, media_api=state.media_api)

    return action


def _view_airing_schedule(ctx: Context, state: State) -> MenuAction:
    """Action to transition to the airing schedule menu."""

    def action() -> State | InternalDirective:
        return State(
            menu_name=MenuName.MEDIA_AIRING_SCHEDULE, media_api=state.media_api
        )

    return action


def _view_reviews(ctx: Context, state: State) -> MenuAction:
    """Action to transition to the review selection menu."""

    def action() -> State | InternalDirective:
        return State(menu_name=MenuName.MEDIA_REVIEW, media_api=state.media_api)

    return action
