from typing import Callable, Dict, Literal, Union

from ...session import Context, session
from ...state import InternalDirective, MenuName, State

MenuAction = Callable[[], Union[State, InternalDirective]]


@session.menu
def player_controls(ctx: Context, state: State) -> Union[State, InternalDirective]:
    feedback = ctx.feedback
    feedback.clear_console()

    config = ctx.config
    selector = ctx.selector

    provider_anime = state.provider.anime
    media_item = state.media_api.media_item
    current_episode_num = state.provider.episode
    selected_server = state.provider.server
    server_map = state.provider.servers

    if (
        not provider_anime
        or not media_item
        or not current_episode_num
        or not selected_server
        or not server_map
    ):
        feedback.error("Player state is incomplete. Returning.")
        return InternalDirective.BACK

    available_episodes = getattr(
        provider_anime.episodes, config.stream.translation_type, []
    )
    current_index = available_episodes.index(current_episode_num)

    if config.stream.auto_next and current_index < len(available_episodes) - 1:
        feedback.info("Auto-playing next episode...")
        next_episode_num = available_episodes[current_index + 1]

        return State(
            menu_name=MenuName.SERVERS,
            media_api=state.media_api,
            provider=state.provider.model_copy(update={"episode_": next_episode_num}),
        )

    # --- Menu Options ---
    icons = config.general.icons
    options: Dict[str, Callable[[], Union[State, InternalDirective]]] = {}

    if current_index < len(available_episodes) - 1:
        options[f"{'⏭️ ' if icons else ''}Next Episode"] = _next_episode(ctx, state)
    if current_index:
        options[f"{'⏪ ' if icons else ''}Previous Episode"] = _previous_episode(
            ctx, state
        )

    options.update(
        {
            f"{'🔂 ' if icons else ''}Replay": _replay(ctx, state),
            f"{'💽 ' if icons else ''}Change Server": _change_server(ctx, state),
            f"{'📀 ' if icons else ''}Change Quality": _change_quality(ctx, state),
            f"{'🎞️ ' if icons else ''}Episode List": _episodes_list(ctx, state),
            f"{'🔘 ' if icons else ''}Toggle Auto Next Episode (Current: {ctx.config.stream.auto_next})": _toggle_config_state(
                ctx, state, "AUTO_EPISODE"
            ),
            f"{'🔘 ' if icons else ''}Toggle Translation Type  (Current: {ctx.config.stream.translation_type.upper()})": _toggle_config_state(
                ctx, state, "TRANSLATION_TYPE"
            ),
            f"{'🎥 ' if icons else ''}Media Actions Menu": lambda: InternalDirective.BACKX4,
            f"{'🏠 ' if icons else ''}Main Menu": lambda: InternalDirective.MAIN,
            f"{'❌ ' if icons else ''}Exit": lambda: InternalDirective.EXIT,
        }
    )

    choice = selector.choose(prompt="What's next?", choices=list(options.keys()))

    if choice and choice in options:
        return options[choice]()
    else:
        return InternalDirective.RELOAD


def _next_episode(ctx: Context, state: State) -> MenuAction:
    def action():
        feedback = ctx.feedback

        config = ctx.config

        provider_anime = state.provider.anime
        media_item = state.media_api.media_item
        current_episode_num = state.provider.episode
        selected_server = state.provider.server
        server_map = state.provider.servers

        if (
            not provider_anime
            or not media_item
            or not current_episode_num
            or not selected_server
            or not server_map
        ):
            feedback.error("Player state is incomplete. Returning.")
            return InternalDirective.BACK

        available_episodes = getattr(
            provider_anime.episodes, config.stream.translation_type, []
        )
        current_index = available_episodes.index(current_episode_num)

        if current_index < len(available_episodes) - 1:
            next_episode_num = available_episodes[current_index + 1]

            return State(
                menu_name=MenuName.SERVERS,
                media_api=state.media_api,
                provider=state.provider.model_copy(
                    update={"episode_": next_episode_num}
                ),
            )
        feedback.warning("This is the last available episode.")
        return InternalDirective.RELOAD

    return action


def _previous_episode(ctx: Context, state: State) -> MenuAction:
    def action():
        feedback = ctx.feedback

        config = ctx.config

        provider_anime = state.provider.anime
        current_episode_num = state.provider.episode

        if not provider_anime or not current_episode_num:
            feedback.error("Player state is incomplete. Returning.")
            return InternalDirective.BACK

        available_episodes = getattr(
            provider_anime.episodes, config.stream.translation_type, []
        )
        current_index = available_episodes.index(current_episode_num)

        if current_index:
            prev_episode_num = available_episodes[current_index - 1]

            return State(
                menu_name=MenuName.SERVERS,
                media_api=state.media_api,
                provider=state.provider.model_copy(
                    update={"episode_": prev_episode_num}
                ),
            )
        feedback.warning("This is the last available episode.")
        return InternalDirective.RELOAD

    return action


def _replay(ctx: Context, state: State) -> MenuAction:
    def action():
        return InternalDirective.BACK

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


def _change_server(ctx: Context, state: State) -> MenuAction:
    def action():
        from .....libs.provider.anime.types import ProviderServer

        feedback = ctx.feedback

        selector = ctx.selector

        provider_anime = state.provider.anime
        media_item = state.media_api.media_item
        current_episode_num = state.provider.episode
        selected_server = state.provider.server
        server_map = state.provider.servers

        if (
            not provider_anime
            or not media_item
            or not current_episode_num
            or not selected_server
            or not server_map
        ):
            feedback.error("Player state is incomplete. Returning.")
            return InternalDirective.BACK

        new_server_name = selector.choose(
            "Select a different server:", list(server_map.keys())
        )
        if new_server_name:
            ctx.config.stream.server = ProviderServer(new_server_name)
        return InternalDirective.RELOAD

    return action


def _episodes_list(ctx: Context, state: State) -> MenuAction:
    def action():
        ctx.switch.force_episodes_menu()
        return InternalDirective.BACKX2

    return action


def _change_quality(ctx: Context, state: State) -> MenuAction:
    def action():
        feedback = ctx.feedback

        selector = ctx.selector

        server_map = state.provider.servers

        if not server_map:
            feedback.error("Player state is incomplete. Returning.")
            return InternalDirective.BACK

        new_quality = selector.choose(
            "Select a different quality:",
            [link.quality for link in state.provider.server.links],
        )
        if new_quality:
            ctx.config.stream.quality = new_quality  # type:ignore
        return InternalDirective.RELOAD

    return action
