from __future__ import annotations

import os
import random
import threading
from typing import TYPE_CHECKING

from click import clear
from InquirerPy import inquirer
from InquirerPy.validator import EmptyInputValidator
from rich import print
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from yt_dlp.utils import sanitize_filename

from ...anilist import AniList
from ...constants import USER_CONFIG_PATH
from ...libs.discord import discord
from ...libs.fzf import fzf
from ...libs.rofi import Rofi
from ...Utility.data import anime_normalizer
from ...Utility.utils import anime_title_percentage_match
from ..utils.mpv import run_mpv
from ..utils.tools import exit_app
from ..utils.utils import (
    filter_by_quality,
    fuzzy_inquirer,
    move_preferred_subtitle_lang_to_top,
)
from .utils import aniskip

if TYPE_CHECKING:
    from ...libs.anilist.types import AnilistBaseMediaDataSchema
    from ...libs.anime_provider.types import Anime, SearchResult, Server
    from ..config import Config
    from ..utils.tools import FastAnimeRuntimeState


def calculate_percentage_completion(start_time, end_time):
    """helper function used to calculate the difference between two timestamps in seconds

    Args:
        start_time ([TODO:parameter]): [TODO:description]
        end_time ([TODO:parameter]): [TODO:description]

    Returns:
        [TODO:return]
    """

    try:
        start = start_time.split(":")
        end = end_time.split(":")
        start_secs = int(start[0]) * 3600 + int(start[1]) * 60 + int(start[2])
        end_secs = int(end[0]) * 3600 + int(end[1]) * 60 + int(end[2])
        return start_secs / end_secs * 100
    except Exception:
        return 0

def discord_updater(show,episode,switch):
    discord.discord_connect(show,episode,switch)

def media_player_controls(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    """Menu that that offers media player controls

    Args:
        config: [TODO:description]
        fastanime_runtime_state: [TODO:description]
    """
    # user config
    config.translation_type.lower()

    # internal config
    current_episode_number: str = (
        fastanime_runtime_state.provider_current_episode_number
    )
    available_episodes: list = sorted(
        fastanime_runtime_state.provider_available_episodes, key=float
    )
    server_episode_streams: list = (
        fastanime_runtime_state.provider_server_episode_streams
    )
    current_episode_stream_link: str = (
        fastanime_runtime_state.provider_current_episode_stream_link
    )
    provider_anime_title: str = fastanime_runtime_state.provider_anime_title
    anime_id_anilist: int = fastanime_runtime_state.selected_anime_id_anilist

    def _servers():
        """Go to servers menu"""
        config.server = ""

        provider_anime_episode_servers_menu(config, fastanime_runtime_state)

    def _replay():
        """replay the current media"""
        selected_server: "Server" = fastanime_runtime_state.provider_current_server
        print(
            "[bold magenta]Now Replaying:[/]",
            provider_anime_title,
            "[bold magenta] Episode: [/]",
            current_episode_number,
        )

        if (
            config.watch_history[str(anime_id_anilist)]["episode_no"]
            == current_episode_number
        ):
            start_time = config.watch_history[str(anime_id_anilist)][
                "episode_stopped_at"
            ]
            print("[green]Continuing from:[/] ", start_time)
        else:
            start_time = "0"
        custom_args = []
        if config.skip:
            if args := aniskip(
                fastanime_runtime_state.selected_anime_anilist["idMal"],
                current_episode_number,
            ):
                custom_args.extend(args)
        subtitles = move_preferred_subtitle_lang_to_top(
            selected_server["subtitles"], config.sub_lang
        )
        episode_title = selected_server["episode_title"]
        if config.normalize_titles:
            import re

            for episode_detail in fastanime_runtime_state.selected_anime_anilist[
                "streamingEpisodes"
            ]:
                if re.match(
                    f"Episode {current_episode_number} ", episode_detail["title"]
                ):
                    episode_title = episode_detail["title"]
                    break
        if config.sync_play:
            from ..utils.syncplay import SyncPlayer

            stop_time, total_time = SyncPlayer(
                current_episode_stream_link,
                episode_title,
                headers=selected_server["headers"],
                subtitles=subtitles,
            )
        elif config.use_python_mpv:
            from ..utils.player import player

            player.create_player(
                current_episode_stream_link,
                config.anime_provider,
                fastanime_runtime_state,
                config,
                episode_title,
                start_time,
                headers=selected_server["headers"],
                subtitles=subtitles,
            )
            stop_time = player.last_stop_time
            total_time = player.last_total_time
        else:
            stop_time, total_time = run_mpv(
                current_episode_stream_link,
                episode_title,
                start_time=start_time,
                custom_args=custom_args,
                headers=selected_server["headers"],
                subtitles=subtitles,
                player=config.player,
            )

        # either update the watch history to the next episode or current depending on progress
        if stop_time == "0" or total_time == "0":
            episode = str(int(current_episode_number) + 1)
        else:
            percentage_completion_of_episode = calculate_percentage_completion(
                stop_time, total_time
            )
            if percentage_completion_of_episode < config.episode_complete_at:
                episode = current_episode_number
            else:
                episode = str(int(current_episode_number) + 1)
                stop_time = "0"
                total_time = "0"

        clear()
        config.media_list_track(
            anime_id_anilist,
            episode_no=episode,
            episode_stopped_at=stop_time,
            episode_total_length=total_time,
            progress_tracking=fastanime_runtime_state.progress_tracking,
        )
        media_player_controls(config, fastanime_runtime_state)

    def _next_episode():
        """watch the next episode"""
        # ensures you dont accidentally erase your progress for an in complete episode
        stop_time = config.watch_history.get(str(anime_id_anilist), {}).get(
            "episode_stopped_at", "0"
        )

        total_time = config.watch_history.get(str(anime_id_anilist), {}).get(
            "episode_total_length", "0"
        )

        # compute if the episode is actually completed
        if stop_time == "0" or total_time == "0":
            percentage_completion_of_episode = 0
        else:
            percentage_completion_of_episode = calculate_percentage_completion(
                stop_time, total_time
            )
        if percentage_completion_of_episode < config.episode_complete_at:
            if config.auto_next:
                if config.use_rofi:
                    if not Rofi.confirm(
                        "Are you sure you wish to continue to the next episode you haven't completed the current episode?"
                    ):
                        media_actions_menu(config, fastanime_runtime_state)
                        return
                else:
                    if not Confirm.ask(
                        "Are you sure you wish to continue to the next episode you haven't completed the current episode?",
                        default=False,
                    ):
                        media_actions_menu(config, fastanime_runtime_state)
                        return
            elif not config.use_rofi:
                if not Confirm.ask(
                    "Are you sure you wish to continue to the next episode, your progress for the current episodes will be erased?",
                    default=True,
                ):
                    media_actions_menu(config, fastanime_runtime_state)
                    return

        # all checks have passed lets go to the next episode
        next_episode = available_episodes.index(current_episode_number) + 1
        if next_episode >= len(available_episodes):
            next_episode = len(available_episodes) - 1

        # updateinternal config
        fastanime_runtime_state.provider_current_episode_number = available_episodes[
            next_episode
        ]

        # update user config
        config.media_list_track(
            anime_id_anilist,
            episode_no=available_episodes[next_episode],
            progress_tracking=fastanime_runtime_state.progress_tracking,
        )

        # call interface
        provider_anime_episode_servers_menu(config, fastanime_runtime_state)

    def _episodes():
        """Go to episodes menu"""
        # reset watch_history
        config.continue_from_history = False

        # call interface
        provider_anime_episodes_menu(config, fastanime_runtime_state)

    def _previous_episode():
        """Watch previous episode"""
        prev_episode = available_episodes.index(current_episode_number) - 1
        if prev_episode <= 0:
            prev_episode = 0
        # fastanime_runtime_state.episode_title = episode["title"]
        fastanime_runtime_state.provider_current_episode_number = available_episodes[
            prev_episode
        ]

        # update user config
        config.media_list_track(
            anime_id_anilist,
            episode_no=available_episodes[prev_episode],
            progress_tracking=fastanime_runtime_state.progress_tracking,
        )

        # call interface
        provider_anime_episode_servers_menu(config, fastanime_runtime_state)

    def _change_quality():
        """Change the quality of the media"""
        # extract the actual link urls
        options = [link["quality"] for link in server_episode_streams]

        # prompt for new quality
        if config.use_fzf:
            quality = fzf.run(
                options, prompt="Select Quality", header="Quality Options"
            )
        elif config.use_rofi:
            quality = Rofi.run(options, "Select Quality")
        else:
            quality = fuzzy_inquirer(
                options,
                "Select Quality",
            )
        config.quality = quality  # set quality
        media_player_controls(config, fastanime_runtime_state)

    def _change_translation_type():
        """change translation type"""
        # prompt for new translation type
        options = ["sub", "dub"]
        if config.use_fzf:
            translation_type = fzf.run(
                options, prompt="Select Translation Type", header="Lang Options"
            ).lower()
        elif config.use_rofi:
            translation_type = Rofi.run(options, "Select Translation Type")
        else:
            translation_type = fuzzy_inquirer(
                options,
                "Select Translation Type",
            ).lower()

        # update internal config
        config.translation_type = translation_type.lower()

        # reload to controls
        media_player_controls(config, fastanime_runtime_state)

    icons = config.icons
    options = {
        f"{'🔂 ' if icons else ''}Replay": _replay,
        f"{'⏭  ' if icons else ''}Next Episode": _next_episode,
        f"{'⏮  ' if icons else ''}Previous Episode": _previous_episode,
        f"{'🗃️ ' if icons else ''}Episodes": _episodes,
        f"{'📀 ' if icons else ''}Change Quality": _change_quality,
        f"{'🎧 ' if icons else ''}Change Translation Type": _change_translation_type,
        f"{'💽 ' if icons else ''}Servers": _servers,
        f"{'📱 ' if icons else ''}Main Menu": lambda: fastanime_main_menu(
            config, fastanime_runtime_state
        ),
        f"{'📜 ' if icons else ''}Media Actions Menu": lambda: media_actions_menu(
            config, fastanime_runtime_state
        ),
        f"{'🔎 ' if icons else ''}Anilist Results Menu": lambda: anilist_results_menu(
            config, fastanime_runtime_state
        ),
        f"{'❌ ' if icons else ''}Exit": exit_app,
    }

    if config.auto_next:
        print("Auto selecting next episode")
        _next_episode()
        return

    choices = list(options.keys())
    if config.use_fzf:
        action = fzf.run(
            choices,
            prompt="Select Action",
        )
    elif config.use_rofi:
        action = Rofi.run(choices, "Select Action")
    else:
        action = fuzzy_inquirer(choices, "Select Action")
    options[action]()


def provider_anime_episode_servers_menu(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    """Menu that enables selection of a server either manually or automatically based on user config then plays the stream link of the quality the user prefers

    Args:
        config: [TODO:description]
        fastanime_runtime_state: [TODO:description]

    Returns:
        [TODO:return]
    """
    # user config
    quality: str = config.quality
    translation_type = config.translation_type
    anime_provider = config.anime_provider

    # runtime configuration
    current_episode_number: str = (
        fastanime_runtime_state.provider_current_episode_number
    )
    provider_anime_title: str = fastanime_runtime_state.provider_anime_title
    anime_id_anilist: int = fastanime_runtime_state.selected_anime_id_anilist
    provider_anime: "Anime" = fastanime_runtime_state.provider_anime

    server_name = ""
    # get streams for episode from provider
    with Progress() as progress:
        progress.add_task("Fetching Episode Streams...", total=None)
        episode_streams_generator = anime_provider.get_episode_streams(
            provider_anime["id"],
            current_episode_number,
            translation_type,
        )
    if not episode_streams_generator:
        if not config.use_rofi:
            print("Failed to fetch :cry:")
            input("Enter to retry...")
        else:
            if not Rofi.confirm("Sth went wrong!!Enter to continue..."):
                exit(1)
        media_actions_menu(config, fastanime_runtime_state)
        return

    if config.server == "top":
        # no need to get all servers if top just works
        with Progress() as progress:
            progress.add_task("Fetching top server...", total=None)
            selected_server = next(episode_streams_generator, None)
        if not selected_server:
            if config.use_rofi:
                if Rofi.confirm("Sth went wrong enter to continue"):
                    media_actions_menu(config, fastanime_runtime_state)
                else:
                    exit_app(1)
            else:
                print("Sth went wrong")
                input("Enter to continue...")
                media_actions_menu(config, fastanime_runtime_state)
            return
    else:
        with Progress() as progress:
            progress.add_task("Fetching servers...", total=None)
            episode_streams_dict = {
                episode_stream["server"]: episode_stream
                for episode_stream in episode_streams_generator
            }

        if not episode_streams_dict:
            if config.use_rofi:
                if Rofi.confirm("Sth went wrong enter to continue"):
                    media_actions_menu(config, fastanime_runtime_state)
                else:
                    exit_app(1)
            else:
                print("Sth went wrong")
                input("Enter to continue...")
                media_actions_menu(config, fastanime_runtime_state)
            return
        # check if user server exists and is actually a valid serrver then sets it
        if config.server and config.server in episode_streams_dict.keys():
            server_name = config.server

        # prompt for preferred server if not automatically set using config
        if not server_name:
            choices = [*episode_streams_dict.keys(), "top", "Back"]
            if config.use_fzf:
                server_name = fzf.run(
                    choices,
                    prompt="Select Server",
                    header="Servers",
                )
            elif config.use_rofi:
                server_name = Rofi.run(choices, "Select Server")
            else:
                server_name = fuzzy_inquirer(
                    choices,
                    "Select Server",
                )
        if server_name == "Back":
            # set continue_from_history to false in order for episodes menu to be shown or continue from history if true will prevent this from happening
            config.continue_from_history = False

            provider_anime_episodes_menu(config, fastanime_runtime_state)
            return
        elif server_name == "top" and episode_streams_dict.keys():
            selected_server = episode_streams_dict[list(episode_streams_dict.keys())[0]]
        else:
            if server_name == "top" or server_name == "back":
                if config.use_rofi:
                    if not Rofi.confirm("No severs available..."):
                        exit_app()
                    else:
                        media_actions_menu(config, fastanime_runtime_state)
                        return
                else:
                    print("Failed to set server")
                    input("Enter to continue")
                    media_actions_menu(config, fastanime_runtime_state)
                    return
            selected_server = episode_streams_dict[server_name]

    # get the stream of the preferred quality
    provider_server_episode_streams = selected_server["links"]
    provider_server_episode_stream = filter_by_quality(
        quality, provider_server_episode_streams
    )
    if not provider_server_episode_stream:
        print("Quality not found")
        input("Enter to continue...")
        media_actions_menu(config, fastanime_runtime_state)
        return

    current_stream_link = provider_server_episode_stream["link"]

    # update internal config
    fastanime_runtime_state.provider_server_episode_streams = (
        provider_server_episode_streams
    )
    fastanime_runtime_state.provider_current_episode_stream_link = current_stream_link
    fastanime_runtime_state.provider_current_server = selected_server
    fastanime_runtime_state.provider_current_server_name = server_name

    # play video
    print(
        "[bold magenta]Now playing:[/]",
        provider_anime_title,
        "[bold magenta] Episode: [/]",
        current_episode_number,
    )
    # update discord activity for user
    switch = threading.Event()
    if config.discord:
        discord_proc = threading.Thread(target=discord_updater, args=(provider_anime_title,current_episode_number,switch))
        discord_proc.start()

    # try to get the timestamp you left off from if available
    start_time = config.watch_history.get(str(anime_id_anilist), {}).get(
        "episode_stopped_at", "0"
    )
    episode_in_history = config.watch_history.get(str(anime_id_anilist), {}).get(
        "episode_no", ""
    )
    if start_time != "0" and episode_in_history == current_episode_number:
        print("[green]Continuing from:[/] ", start_time)
    else:
        start_time = "0"
    custom_args = []
    if config.skip:
        if args := aniskip(
            fastanime_runtime_state.selected_anime_anilist["idMal"],
            current_episode_number,
        ):
            custom_args.extend(args)
    subtitles = move_preferred_subtitle_lang_to_top(
        selected_server["subtitles"], config.sub_lang
    )
    episode_title = selected_server["episode_title"]
    if config.normalize_titles:
        import re

        for episode_detail in fastanime_runtime_state.selected_anime_anilist[
            "streamingEpisodes"
        ]:
            if re.match(f"Episode {current_episode_number} ", episode_detail["title"]):
                episode_title = episode_detail["title"]
                break

    if config.recent:
        config.update_recent(
            [
                fastanime_runtime_state.selected_anime_anilist,
                *config.user_data["recent_anime"],
            ]
        )
        print("Updating recent anime...")
    if config.sync_play:
        from ..utils.syncplay import SyncPlayer

        stop_time, total_time = SyncPlayer(
            current_stream_link,
            episode_title,
            headers=selected_server["headers"],
            subtitles=subtitles,
        )
    elif config.use_python_mpv:
        from ..utils.player import player

        if start_time == "0" and episode_in_history != current_episode_number:
            start_time = "0"
        player.create_player(
            current_stream_link,
            anime_provider,
            fastanime_runtime_state,
            config,
            episode_title,
            start_time,
            headers=selected_server["headers"],
            subtitles=subtitles,
        )

        stop_time = player.last_stop_time
        total_time = player.last_total_time
        current_episode_number = fastanime_runtime_state.provider_current_episode_number
    else:
        if not episode_in_history == current_episode_number:
            start_time = "0"
        stop_time, total_time = run_mpv(
            current_stream_link,
            episode_title,
            start_time=start_time,
            custom_args=custom_args,
            headers=selected_server["headers"],
            subtitles=subtitles,
            player=config.player,
        )
    print("Finished at: ", stop_time)

    # stop discord activity updater
    if config.discord:
        switch.set()

    # update_watch_history
    # this will try to update the episode to be the next episode if delta has reached a specific threshhold
    # this update will only apply locally
    # the remote(anilist) is only updated when its certain you are going to open the player
    if stop_time == "0" or total_time == "0":
        # increment the episodes
        # next_episode = available_episodes.index(current_episode_number) + 1
        # if next_episode >= len(available_episodes):
        #     next_episode = len(available_episodes) - 1
        # episode = available_episodes[next_episode]
        pass
    else:
        percentage_completion_of_episode = calculate_percentage_completion(
            stop_time, total_time
        )
        if percentage_completion_of_episode > config.episode_complete_at:
            # -- update anilist progress if user --
            remote_progress = (
                fastanime_runtime_state.selected_anime_anilist["mediaListEntry"] or {}
            ).get("progress")
            disable_anilist_update = False
            if remote_progress:
                if (
                    float(remote_progress) > float(current_episode_number)
                    and config.force_forward_tracking
                ):
                    disable_anilist_update = True
            if (
                fastanime_runtime_state.progress_tracking == "track"
                and config.user
                and not disable_anilist_update
                and current_episode_number
            ):
                AniList.update_anime_list(
                    {
                        "mediaId": anime_id_anilist,
                        "progress": int(float(current_episode_number)),
                    }
                )

            # increment the episodes
            # next_episode = available_episodes.index(current_episode_number) + 1
            # if next_episode >= len(available_episodes):
            #     next_episode = len(available_episodes) - 1
            # episode = available_episodes[next_episode]
            # stop_time = "0"
            # total_time = "0"

    config.media_list_track(
        anime_id_anilist,
        episode_no=current_episode_number,
        episode_stopped_at=stop_time,
        episode_total_length=total_time,
        progress_tracking=fastanime_runtime_state.progress_tracking,
    )

    # switch to controls
    clear()

    media_player_controls(config, fastanime_runtime_state)


def provider_anime_episodes_menu(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    """A menu that handles selection of episode either manually or automatically based on either local episode progress or remote(anilist) progress

    Args:
        config: [TODO:description]
        fastanime_runtime_state: [TODO:description]
    """
    # user config
    translation_type: str = config.translation_type.lower()
    continue_from_history: bool = config.continue_from_history
    user_watch_history: dict = config.watch_history

    # runtime configuration
    anime_id_anilist: int = fastanime_runtime_state.selected_anime_id_anilist
    anime_title: str = fastanime_runtime_state.provider_anime_title
    provider_anime: "Anime" = fastanime_runtime_state.provider_anime
    selected_anime_anilist: "AnilistBaseMediaDataSchema" = (
        fastanime_runtime_state.selected_anime_anilist
    )

    # prompt for episode number
    available_episodes = sorted(
        provider_anime["availableEpisodesDetail"][translation_type], key=float
    )
    current_episode_number = ""

    # auto select episode if continue from history otherwise prompt episode number
    if continue_from_history:
        # the user watch history thats locally available
        # will be preferred over remote
        if (
            user_watch_history.get(str(anime_id_anilist), {}).get("episode_no")
            in available_episodes
        ):
            if (
                config.preferred_history == "local"
                or not selected_anime_anilist["mediaListEntry"]
            ):
                current_episode_number = user_watch_history[str(anime_id_anilist)][
                    "episode_no"
                ]

                stop_time = user_watch_history.get(str(anime_id_anilist), {}).get(
                    "episode_stopped_at", "0"
                )
                total_time = user_watch_history.get(str(anime_id_anilist), {}).get(
                    "episode_total_length", "0"
                )
                if stop_time != "0" and total_time != "0":
                    percentage_completion_of_episode = calculate_percentage_completion(
                        stop_time, total_time
                    )
                    if percentage_completion_of_episode > config.episode_complete_at:
                        # increment the episodes
                        next_episode = (
                            available_episodes.index(current_episode_number) + 1
                        )
                        if next_episode >= len(available_episodes):
                            next_episode = len(available_episodes) - 1
                        episode = available_episodes[next_episode]
                        stop_time = "0"
                        total_time = "0"
                        current_episode_number = episode

            else:
                current_episode_number = str(
                    (selected_anime_anilist["mediaListEntry"] or {"progress": 0}).get(
                        "progress"
                    )
                )
            print(
                f"[bold cyan]Continuing from Episode:[/] [bold]{current_episode_number}[/]"
            )

        # try to get the episode from anilist if present
        elif selected_anime_anilist["mediaListEntry"]:
            current_episode_number = str(
                (selected_anime_anilist["mediaListEntry"] or {"progress": 0}).get(
                    "progress"
                )
            )
            if current_episode_number not in available_episodes:
                current_episode_number = ""
            print(
                f"[bold cyan]Continuing from Episode:[/] [bold]{current_episode_number}[/]"
            )
        # reset to none if not found
        else:
            current_episode_number = ""

    # prompt for episode number if not set
    if not current_episode_number or current_episode_number not in available_episodes:
        choices = [*available_episodes, "Back"]
        preview = None
        if config.preview:
            from .utils import get_fzf_episode_preview

            e = fastanime_runtime_state.selected_anime_anilist["episodes"]
            if e:
                eps = range(0, e + 1)
            else:
                eps = available_episodes
            preview = get_fzf_episode_preview(
                fastanime_runtime_state.selected_anime_anilist, eps
            )
        if config.use_fzf:
            current_episode_number = fzf.run(
                choices, prompt="Select Episode", header=anime_title, preview=preview
            )
        elif config.use_rofi:
            current_episode_number = Rofi.run(choices, "Select Episode")
        else:
            current_episode_number = fuzzy_inquirer(
                choices,
                "Select Episode",
            )

    if current_episode_number == "Back":
        media_actions_menu(config, fastanime_runtime_state)
        return
    #
    # # try to get the start time and if not found default to "0"
    # start_time = user_watch_history.get(str(anime_id_anilist), {}).get(
    #     "start_time", "0"
    # )
    # config.update_watch_history(
    #     anime_id_anilist, current_episode_number, start_time=start_time
    # )

    # update runtime data
    fastanime_runtime_state.provider_available_episodes = available_episodes
    fastanime_runtime_state.provider_current_episode_number = current_episode_number

    # next interface
    provider_anime_episode_servers_menu(config, fastanime_runtime_state)


def fetch_anime_episode(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    selected_anime: "SearchResult" = (
        fastanime_runtime_state.provider_anime_search_result
    )
    anime_provider = config.anime_provider
    with Progress() as progress:
        progress.add_task("Fetching Anime Info...", total=None)
        provider_anime = anime_provider.get_anime(
            selected_anime["id"],
        )
    if not provider_anime:
        print(
            "Sth went wrong :cry: this could mean the provider is down or your internet"
        )
        if not config.use_rofi:
            input("Enter to continue...")
        else:
            if not Rofi.confirm("Sth went wrong!!Enter to continue..."):
                exit(1)
        return media_actions_menu(config, fastanime_runtime_state)

    fastanime_runtime_state.provider_anime = provider_anime
    if fastanime_runtime_state.selected_anime_media_action == "Stream":
        provider_anime_episodes_menu(config, fastanime_runtime_state)
    elif fastanime_runtime_state.selected_anime_media_action == "Download":
        download_options_menu(config, fastanime_runtime_state)


#
#   ---- ANIME DOWNLOAD MENU ----
#


def download_options_menu(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    options = ["Download all", "Download selected", "Back"]
    download_option: str = ""
    if config.use_fzf:
        download_option = fzf.run(
            options,
            "Enter your preferred download option for the current anime",
        )
    elif config.use_rofi:
        download_option = Rofi.run(
            options,
            "Enter your preferred download option for the current anime",
        )
    else:
        download_option = fuzzy_inquirer(
            options,
            "Enter your preferred download option for the current anime",
        )

    selected_episodes: list[str] = []
    if download_option == "Download all":

        # User config
        translation_type: str = config.translation_type.lower()

        selected_episodes = sorted(
            fastanime_runtime_state.provider_anime["availableEpisodesDetail"][
                translation_type
            ],
            key=float,
        )

    elif download_option == "Download selected":
        selected_episodes = select_multiple_episodes(config, fastanime_runtime_state)

        if selected_episodes == []:
            download_options_menu(config, fastanime_runtime_state)
            return

    elif download_option == "Back":
        media_actions_menu(config, fastanime_runtime_state)
        return

    else:
        print("Invalid option")
        download_options_menu(config, fastanime_runtime_state)
        return


def select_multiple_episodes(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    """A menu that handles selection of episodes. Can be used to select multiple episodes

    Args:
        config: [TODO:description]
        fastanime_runtime_state: [TODO:description]
    """
    # user config
    translation_type: str = config.translation_type.lower()

    # runtime configuration
    anime_title: str = fastanime_runtime_state.provider_anime_title
    provider_anime: "Anime" = fastanime_runtime_state.provider_anime

    available_episodes = sorted(
        provider_anime["availableEpisodesDetail"][translation_type], key=float
    )

    selected_episodes: list[str] = (
        []
    )  # Use str instead of int to deal with special/recap episodes
    selected_entry: str = ""

    choices = [
        "Select till top",
        *list(map(lambda x: f"[ ] {x}", available_episodes)),  # Convert to [ ] <num>
        "Select till end",
        "Select all in between",
        "Download",
        "Back",
    ]

    preview = None
    # if config.preview:
    #     from .utils import get_fzf_episode_preview
    #
    #     e = fastanime_runtime_state.selected_anime_anilist["episodes"]
    #     if e:
    #         eps = range(0, e + 1)
    #     else:
    #         eps = available_episodes
    #
    #     preview = get_fzf_episode_preview(
    #         fastanime_runtime_state.selected_anime_anilist, eps
    #     )
    #     # eps = [f"[ ] {ep}" for ep in eps]

    preselect_index = 1

    while selected_entry != "Download":

        if config.use_fzf:
            selected_entry = fzf.run(
                choices,
                prompt="Select Episode",
                header=anime_title,
                preview=preview,
                preselect=preselect_index,
            )
        elif config.use_rofi:
            selected_entry = Rofi.run(
                choices, "Select Episode", preselect=preselect_index
            )
        else:
            selected_entry = fuzzy_inquirer(
                choices,
                "Select Episode",
            )

        if selected_entry == "Back":
            return []

        elif selected_entry == "Select till top" and selected_episodes != []:
            # Select all episodes from the top to the first selected episode
            for i in range(1, int(choices.index(f"[*] {selected_episodes[0]}"))):
                selected_episodes.append(choices[i][4:])
            preselect_index = choices.index("Select till top")

        elif selected_entry == "Select till end" and selected_episodes != []:
            # Select all episodes from the last selected episode to the end
            for i in range(
                choices.index(f"[*] {selected_episodes[-1]}") + 1,
                choices.index(selected_entry),
            ):
                selected_episodes.append(choices[i][4:])
            preselect_index = choices.index("Select till end")

        elif selected_entry == "Select all in between" and selected_episodes != []:
            # Select all episodes in between the first and last selected episodes
            for i in range(
                choices.index(f"[*] {selected_episodes[0]}") + 1,
                choices.index(f"[*] {selected_episodes[-1]}"),
            ):
                selected_episodes.append(choices[i][4:])
            preselect_index = choices.index("Select all in between")
        elif selected_entry.startswith("[ ] "):
            selected_episodes.append(selected_entry[4:])
            preselect_index = choices.index(selected_entry) + 1

        elif selected_entry.startswith("[*] "):
            selected_episodes.remove(selected_entry[4:])
            preselect_index = choices.index(selected_entry) + 1

        # Remake the choices list
        selected_episodes = list(set(selected_episodes))  # Remove duplicates
        selected_episodes.sort(key=float)
        for i in range(1, len(available_episodes)):
            if choices[i][4:] in selected_episodes:
                choices[i] = f"[*] {choices[i][4:]}"
            else:
                choices[i] = f"[ ] {choices[i][4:]}"

    return selected_episodes


#
#   ---- ANIME PROVIDER SEARCH RESULTS MENU ----
#


def set_prefered_progress_tracking(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState", update=False
):
    if (
        fastanime_runtime_state.progress_tracking == ""
        or update
        or fastanime_runtime_state.progress_tracking == "prompt"
    ):
        if config.default_media_list_tracking == "track":
            fastanime_runtime_state.progress_tracking = "track"
        elif config.default_media_list_tracking == "disabled":
            fastanime_runtime_state.progress_tracking = "disabled"
        else:
            options = ["disabled", "track"]
            if config.use_fzf:
                fastanime_runtime_state.progress_tracking = fzf.run(
                    options,
                    "Enter your preferred progress tracking for the current anime",
                )
            elif config.use_rofi:
                fastanime_runtime_state.progress_tracking = Rofi.run(
                    options,
                    "Enter your preferred progress tracking for the current anime",
                )
            else:
                fastanime_runtime_state.progress_tracking = fuzzy_inquirer(
                    options,
                    "Enter your preferred progress tracking for the current anime",
                )


def anime_provider_search_results_menu(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    """A menu that handles searching and selecting provider results; either manually or through fuzzy matching

    Args:
        config: [TODO:description]
        fastanime_runtime_state: [TODO:description]
    """
    # user config
    translation_type = config.translation_type.lower()

    # runtime data
    selected_anime_title = fastanime_runtime_state.selected_anime_title_anilist

    selected_anime_anilist: "AnilistBaseMediaDataSchema" = (
        fastanime_runtime_state.selected_anime_anilist
    )
    anime_provider = config.anime_provider

    # search and get the requested title from provider
    with Progress() as progress:
        progress.add_task("Fetching Search Results...", total=None)
        provider_search_results = anime_provider.search_for_anime(
            selected_anime_title,
            translation_type,
        )
    if not provider_search_results:
        print(
            "Sth went wrong :cry: while fetching this could mean you have poor internet connection or the provider is down"
        )
        if not config.use_rofi:
            input("Enter to continue...")
        else:
            if not Rofi.confirm("Sth went wrong!!Enter to continue..."):
                exit(1)
        return media_actions_menu(config, fastanime_runtime_state)

    provider_search_results = {
        anime["title"]: anime for anime in provider_search_results["results"]
    }
    _title = None
    if _title := next(
        (
            original
            for original, normalized in anime_normalizer.items()
            if normalized.lower() == selected_anime_title.lower()
        ),
        None,
    ):
        _title = _title

    if config.auto_select:
        provider_anime_title = max(
            provider_search_results.keys(),
            key=lambda title: anime_title_percentage_match(
                title, selected_anime_anilist
            ),
        )
        print(f"[cyan]Auto selecting[/]: {provider_anime_title}")
    else:
        choices = [*provider_search_results.keys(), "Back"]
        if config.use_fzf:
            provider_anime_title = fzf.run(
                choices,
                prompt="Select Search Result",
                header="Anime Search Results",
            )

        elif config.use_rofi:
            provider_anime_title = Rofi.run(choices, "Select Search Result")
        else:
            provider_anime_title = fuzzy_inquirer(
                choices,
                "Select Search Result",
            )
        if provider_anime_title == "Back":
            media_actions_menu(config, fastanime_runtime_state)
            return

    # update runtime data
    fastanime_runtime_state.provider_anime_title = (
        anime_normalizer.get(provider_anime_title) or provider_anime_title
    )
    fastanime_runtime_state.provider_anime_search_result = provider_search_results[
        provider_anime_title
    ]

    fastanime_runtime_state.progress_tracking = config.watch_history.get(
        str(fastanime_runtime_state.selected_anime_id_anilist), {}
    ).get("progress_tracking", "prompt")
    if fastanime_runtime_state.selected_anime_media_action == "Stream":
        set_prefered_progress_tracking(config, fastanime_runtime_state)
        fetch_anime_episode(config, fastanime_runtime_state)
    elif fastanime_runtime_state.selected_anime_media_action == "Download":
        fetch_anime_episode(config, fastanime_runtime_state)
    else:
        print("Unknown media action")
        if not config.use_rofi:
            input("Enter to continue...")
        else:
            if not Rofi.confirm("Unknown media action!!Enter to continue..."):
                exit(1)
        media_actions_menu(config, fastanime_runtime_state)


#
#  ---- ANILIST MEDIA ACTIONS MENU ----
#
def media_actions_menu(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    """The menu responsible for handling all media actions such as watching a trailer or streaming it

    Args:
        config: [TODO:description]
        fastanime_runtime_state: [TODO:description]
    """
    selected_anime_anilist: "AnilistBaseMediaDataSchema" = (
        fastanime_runtime_state.selected_anime_anilist
    )
    selected_anime_title_anilist: str = (
        fastanime_runtime_state.selected_anime_title_anilist
    )

    # the progress of the episode based on what  anilist has not locally
    progress = (selected_anime_anilist["mediaListEntry"] or {"progress": 0}).get(
        "progress", 0
    )
    episodes_total = selected_anime_anilist["episodes"] or "Inf"

    def _watch_trailer(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """Helper function to watch trailers with

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        if trailer := selected_anime_anilist.get("trailer"):
            trailer_url = "https://youtube.com/watch?v=" + trailer["id"]
            print("[bold magenta]Watching Trailer of:[/]", selected_anime_title_anilist)
            run_mpv(
                trailer_url,
                ytdl_format=config.format,
                player=config.player,
            )
            media_actions_menu(config, fastanime_runtime_state)
        else:
            if not config.use_rofi:
                print("no trailer available :confused")
                input("Enter to continue...")
            else:
                if not Rofi.confirm("No trailler found!!Enter to continue"):
                    exit(0)
            media_actions_menu(config, fastanime_runtime_state)

    def _add_to_list(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """Helper function to update an anime's media_list_type

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        if not config.user:
            print("You aint logged in")
            input("Enter to continue")
            media_actions_menu(config, fastanime_runtime_state)
            return

        anime_lists = {
            "Watching": "CURRENT",
            "Paused": "PAUSED",
            "Planning": "PLANNING",
            "Dropped": "DROPPED",
            "Rewatching": "REPEATING",
            "Completed": "COMPLETED",
        }
        choices = list(anime_lists.keys())
        if config.use_fzf:
            anime_list = fzf.run(
                choices,
                "Choose the list you want to add to",
                "Add your animelist",
            )
        elif config.use_rofi:
            anime_list = Rofi.run(choices, "Choose list you want to add to")
        else:
            anime_list = fuzzy_inquirer(
                choices,
                "Choose the list you want to add to",
            )
        result = AniList.update_anime_list(
            {"status": anime_lists[anime_list], "mediaId": selected_anime_anilist["id"]}
        )
        if not result[0]:
            print("Failed to update", result)
        else:
            print(
                f"Successfully added {selected_anime_title_anilist} to your {anime_list} list :smile:"
            )
        if not config.use_rofi:
            input("Enter to continue...")
        media_actions_menu(config, fastanime_runtime_state)

    def _score_anime(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """Helper function to score anime on anilist from terminal or rofi

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        if not config.user:
            print("You aint logged in")
            input("Enter to continue")
            media_actions_menu(config, fastanime_runtime_state)
            return
        if config.use_rofi:
            score = Rofi.ask("Enter Score", is_int=True)
            score = max(100, min(0, score))
        else:
            score = inquirer.number(  # pyright:ignore
                message="Enter the score:",
                min_allowed=0,
                max_allowed=100,
                validate=EmptyInputValidator(),
            ).execute()

        result = AniList.update_anime_list(
            {"scoreRaw": score, "mediaId": selected_anime_anilist["id"]}
        )
        if not result[0]:
            print("Failed to update", result)
        else:
            print(f"Successfully scored {selected_anime_title_anilist}; score: {score}")
        if not config.use_rofi:
            input("Enter to continue...")
        media_actions_menu(config, fastanime_runtime_state)

    # FIX: For some reason this fails to delete
    def _remove_from_list(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """Remove an anime from  your media list

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        if Confirm.ask(
            f"Are you sure you want to procede, the folowing action will permanently remove {selected_anime_title_anilist} from your list and your progress will be erased",
            default=False,
        ):
            success, data = AniList.delete_medialist_entry(selected_anime_anilist["id"])
            if not success or not data:
                print("Failed to delete", data)
            elif not data.get("deleted"):
                print("Failed to delete", data)
            else:
                print("Successfully deleted :cry:", selected_anime_title_anilist)
        else:
            print(selected_anime_title_anilist, ":relieved:")
        if not config.use_rofi:
            input("Enter to continue...")
        media_actions_menu(config, fastanime_runtime_state)

    def _change_translation_type(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """Change the translation type to use

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        # prompt for new translation type
        options = ["Sub", "Dub"]
        if config.use_fzf:
            translation_type = fzf.run(
                options, prompt="Select Translation Type", header="Language Options"
            )
        elif config.use_rofi:
            translation_type = Rofi.run(options, "Select Translation Type")
        else:
            translation_type = fuzzy_inquirer(
                options,
                "Select translation type",
            )

        # update internal config
        config.translation_type = translation_type.lower()

        media_actions_menu(config, fastanime_runtime_state)

    def _change_player(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """Change the translation type to use

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        # prompt for new translation type
        options = ["syncplay", "mpv-mod", "default"]
        if config.use_fzf:
            player = fzf.run(
                options,
                prompt="Select Player",
            )
        elif config.use_rofi:
            player = Rofi.run(options, "Select Player")
        else:
            player = fuzzy_inquirer(
                options,
                "Select Player",
            )

        # update internal config
        if player == "syncplay":
            config.sync_play = True
            config.use_python_mpv = False
        else:
            config.sync_play = False
            if player == "mpv-mod":
                config.use_python_mpv = True
            else:
                config.use_python_mpv = False
        media_actions_menu(config, fastanime_runtime_state)

    def _view_info(config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"):
        """helper function to view info of an anime from terminal

        Args:
            config ([TODO:parameter]): [TODO:description]
            fastanime_runtime_state ([TODO:parameter]): [TODO:description]
        """
        from rich.console import Console
        from rich.prompt import Confirm
        from yt_dlp.utils import clean_html

        from ...Utility import anilist_data_helper
        from ..utils.print_img import print_img

        clear()
        console = Console()

        print_img(selected_anime_anilist["coverImage"]["large"])
        console.print(
            "[bold cyan]Title(jp): ", selected_anime_anilist["title"]["romaji"]
        )
        console.print(
            "[bold cyan]Title(eng): ", selected_anime_anilist["title"]["english"]
        )
        console.print("[bold cyan]Popularity: ", selected_anime_anilist["popularity"])
        console.print("[bold cyan]Favourites: ", selected_anime_anilist["favourites"])
        console.print("[bold cyan]Status: ", selected_anime_anilist["status"])
        console.print(
            "[bold cyan]Start Date: ",
            anilist_data_helper.format_anilist_date_object(
                selected_anime_anilist["startDate"]
            ),
        )
        console.print(
            "[bold cyan]End Date: ",
            anilist_data_helper.format_anilist_date_object(
                selected_anime_anilist["endDate"]
            ),
        )
        # console.print("[bold cyan]Season: ", selected_anime["season"])
        console.print("[bold cyan]Episodes: ", selected_anime_anilist["episodes"])
        console.print(
            "[bold cyan]Tags: ",
            anilist_data_helper.format_list_data_with_comma(
                [tag["name"] for tag in selected_anime_anilist["tags"]]
            ),
        )
        console.print(
            "[bold cyan]Genres: ",
            anilist_data_helper.format_list_data_with_comma(
                selected_anime_anilist["genres"]
            ),
        )
        if selected_anime_anilist["nextAiringEpisode"]:
            console.print(
                "[bold cyan]Next Episode: ",
                anilist_data_helper.extract_next_airing_episode(
                    selected_anime_anilist["nextAiringEpisode"]
                ),
            )
        console.print(
            "[bold underline cyan]Description\n[/]",
            clean_html(str(selected_anime_anilist["description"])),
        )
        if Confirm.ask("Enter to continue...", default=True):
            media_actions_menu(config, fastanime_runtime_state)
        return

    def _toggle_auto_select(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """helper function to toggle auto select anime title using fuzzy matching

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        config.auto_select = not config.auto_select
        media_actions_menu(config, fastanime_runtime_state)

    def _toggle_continue_from_history(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """helper function to toggle continue from history

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        config.continue_from_history = not config.continue_from_history
        media_actions_menu(config, fastanime_runtime_state)

    def _toggle_auto_next(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """helper function to toggle auto next

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        config.auto_next = not config.auto_next
        media_actions_menu(config, fastanime_runtime_state)

    def _change_provider(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """Helper function to change provider to use

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        from ...libs.anime_provider import anime_sources

        options = list(anime_sources.keys())
        if config.use_fzf:
            provider = fzf.run(
                options, prompt="Select Translation Type", header="Language Options"
            )
        elif config.use_rofi:
            provider = Rofi.run(options, "Select Translation Type")
        else:
            provider = fuzzy_inquirer(
                options,
                "Select translation type",
            )

        config.provider = provider
        config.anime_provider.provider = provider
        config.anime_provider.lazyload_provider(provider)

        media_actions_menu(config, fastanime_runtime_state)

    def _stream_anime(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """helper function to go to the next menu respecting your config

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """

        fastanime_runtime_state.selected_anime_media_action = "Stream"
        anime_provider_search_results_menu(config, fastanime_runtime_state)

    def _select_episode_to_stream(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """Convinience function to disable continue from history and show the episodes menu

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        config.continue_from_history = False
        fastanime_runtime_state.selected_anime_media_action = "Stream"
        anime_provider_search_results_menu(config, fastanime_runtime_state)

    def _set_progress_tracking(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        set_prefered_progress_tracking(config, fastanime_runtime_state, update=True)
        media_actions_menu(config, fastanime_runtime_state)

    def _relations(config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"):
        """Helper function to get anime recommendations
        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        relations = AniList.get_related_anime_for(
            fastanime_runtime_state.selected_anime_id_anilist
        )
        if not relations[0]:
            print("No recommendations found", relations[1])
            input("Enter to continue...")
            media_actions_menu(config, fastanime_runtime_state)
            return

        relations = relations[1]["data"]["Page"]["relations"]  # pyright:ignore
        fastanime_runtime_state.anilist_results_data = {
            "data": {"Page": {"media": relations["nodes"]}}  # pyright:ignore
        }
        anilist_results_menu(config, fastanime_runtime_state)

    def _recommendations(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """Helper function to get anime recommendations
        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """
        recommendations = AniList.get_recommended_anime_for(
            fastanime_runtime_state.selected_anime_id_anilist
        )
        if not recommendations[0]:
            print("No recommendations found", recommendations[1])
            input("Enter to continue...")
            media_actions_menu(config, fastanime_runtime_state)
            return

        fastanime_runtime_state.anilist_results_data = {
            "data": {
                "Page": {
                    "media": [
                        media["media"]
                        for media in recommendations[1]["data"]["Page"][
                            "recommendations"  # pyright:ignore
                        ]
                    ]
                }
            }
        }
        anilist_results_menu(config, fastanime_runtime_state)

    def _download_anime(
        config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
    ):
        """helper function to go to the next menu containing download options respecting your config

        Args:
            config: [TODO:description]
            fastanime_runtime_state: [TODO:description]
        """

        fastanime_runtime_state.selected_anime_media_action = "Download"

        anime_provider_search_results_menu(config, fastanime_runtime_state)

    icons = config.icons
    options = {
        f"{'📽️ ' if icons else ''}Stream ({progress}/{episodes_total})": _stream_anime,
        f"{'📽️ ' if icons else ''}Episodes": _select_episode_to_stream,
        f"{'  ' if icons else ''}Download": _download_anime,
        f"{'📼 ' if icons else ''}Watch Trailer": _watch_trailer,
        f"{'✨ ' if icons else ''}Score Anime": _score_anime,
        f"{'✨ ' if icons else ''}Progress Tracking": _set_progress_tracking,
        f"{'📥 ' if icons else ''}Add to List": _add_to_list,
        f"{'📤 ' if icons else ''}Remove from List": _remove_from_list,
        f"{'📖 ' if icons else ''}Recommendations": _recommendations,
        f"{'📖 ' if icons else ''}Relations": _relations,
        f"{'📖 ' if icons else ''}View Info": _view_info,
        f"{'🎧 ' if icons else ''}Change Translation Type": _change_translation_type,
        f"{'💽 ' if icons else ''}Change Provider": _change_provider,
        f"{'💽 ' if icons else ''}Change Player": _change_player,
        f"{'🔘 ' if icons else ''}Toggle auto select anime": _toggle_auto_select,  #  WARN: problematic if you choose an anime that doesnt match id
        f"{'💠 ' if icons else ''}Toggle auto next episode": _toggle_auto_next,
        f"{'🔘 ' if icons else ''}Toggle continue from history": _toggle_continue_from_history,
        f"{'🔙 ' if icons else ''}Back": anilist_results_menu,
        f"{'❌ ' if icons else ''}Exit": lambda *_: exit_app(),
    }
    choices = list(options.keys())
    if config.use_fzf:
        action = fzf.run(choices, prompt="Select Action", header="Anime Menu")
    elif config.use_rofi:
        action = Rofi.run(choices, "Select Action")
    else:
        action = fuzzy_inquirer(
            choices,
            "Select Action",
        )
    options[action](config, fastanime_runtime_state)


#
#   ---- ANILIST RESULTS MENU ----
#
def anilist_results_menu(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    """The menu that handles and displays the results of an anilist action enabling using to select anime of choice

    Args:
        config: [TODO:description]
        fastanime_runtime_state: [TODO:description]
    """
    search_results = fastanime_runtime_state.anilist_results_data["data"]["Page"][
        "media"
    ]

    anime_data = {}
    for anime in search_results:
        anime: "AnilistBaseMediaDataSchema"

        # determine the progress of watching the anime based on whats in anilist data !! NOT LOCALLY
        progress = (anime["mediaListEntry"] or {"progress": 0}).get("progress", 0)

        # if the max episodes is none set it to inf meaning currently not determinable or infinity
        episodes_total = anime["episodes"] or "Inf"

        # set the actual title and ensure its a string since even after this it may be none
        title = str(
            anime["title"][config.preferred_language] or anime["title"]["romaji"]
        )
        # this process is mostly need inoder for the preview to work correctly
        title = sanitize_filename(f"{title} ({progress} of {episodes_total})")

        # Check if the anime is currently airing and has new/unwatched episodes
        if (
            anime["status"] == "RELEASING"
            and anime["nextAiringEpisode"]
            and progress > 0
            and (anime["mediaListEntry"] or {}).get("status", "") == "CURRENT"
        ):
            last_aired_episode = anime["nextAiringEpisode"]["episode"] - 1
            if last_aired_episode - progress > 0:
                title += f" 🔹{last_aired_episode - progress} new episode(s)🔹"

        # add the anime to the anime data dict setting the key to the title
        # this dict is used for promting the title and maps directly to the anime object of interest containing the actual data
        anime_data[title] = anime

    # prompt for the anime of choice
    choices = [*anime_data.keys(), "Next Page", "Previous Page", "Back"]
    if config.use_fzf:
        if config.preview:
            from .utils import get_fzf_anime_preview

            preview = get_fzf_anime_preview(search_results, anime_data.keys())
            selected_anime_title = fzf.run(
                choices,
                prompt="Select Anime",
                header="Search Results",
                preview=preview,
            )
        else:
            selected_anime_title = fzf.run(
                choices,
                prompt="Select Anime",
                header="Search Results",
            )
    elif config.use_rofi:
        if config.preview:
            from .utils import IMAGES_CACHE_DIR, get_rofi_icons

            get_rofi_icons(search_results, anime_data.keys())
            choices = []
            for title in anime_data.keys():
                icon_path = os.path.join(IMAGES_CACHE_DIR, title)
                choices.append(f"{title}\0icon\x1f{icon_path}.png")
            choices.append("Back")
            selected_anime_title = Rofi.run_with_icons(choices, "Select Anime")
        else:
            selected_anime_title = Rofi.run(choices, "Select Anime")
    else:
        selected_anime_title = fuzzy_inquirer(
            choices,
            "Select Anime",
        )
    if selected_anime_title == "Back":
        fastanime_main_menu(config, fastanime_runtime_state)
        return
    if selected_anime_title == "Next Page":
        fastanime_runtime_state.current_page = page = (
            fastanime_runtime_state.current_page + 1
        )
        success, data = fastanime_runtime_state.current_data_loader(
            config=config, page=page
        )
        if success:
            fastanime_runtime_state.anilist_results_data = data

            anilist_results_menu(config, fastanime_runtime_state)
        else:
            print("Failed to get next page")
            print(data)
            input("Enter to continue...")
            anilist_results_menu(config, fastanime_runtime_state)

        return
    if selected_anime_title == "Previous Page":
        fastanime_runtime_state.current_page = page = (
            (fastanime_runtime_state.current_page - 1)
            if fastanime_runtime_state.current_page > 1
            else 1
        )
        success, data = fastanime_runtime_state.current_data_loader(
            config=config, page=page
        )
        if success:
            fastanime_runtime_state.anilist_results_data = data

            anilist_results_menu(config, fastanime_runtime_state)
        else:
            print("Failed to get previous page")
            print(data)
            input("Enter to continue...")
            anilist_results_menu(config, fastanime_runtime_state)
        return

    selected_anime: "AnilistBaseMediaDataSchema" = anime_data[selected_anime_title]
    fastanime_runtime_state.selected_anime_anilist = selected_anime
    fastanime_runtime_state.selected_anime_title_anilist = (
        selected_anime["title"]["romaji"] or selected_anime["title"]["english"]
    )
    fastanime_runtime_state.selected_anime_id_anilist = selected_anime["id"]

    media_actions_menu(config, fastanime_runtime_state)


#
# ---- FASTANIME MAIN MENU ----
#
def _handle_animelist(
    config: "Config",
    fastanime_runtime_state: "FastAnimeRuntimeState",
    list_type: str,
    page=1,
):
    """A helper function that handles user media lists

    Args:
        fastanime_runtime_state ([TODO:parameter]): [TODO:description]
        config: [TODO:description]
        list_type: [TODO:description]

    Returns:
        [TODO:return]
    """
    if not config.user:
        if not config.use_rofi:
            print("You haven't logged in please run: fastanime anilist login")
            input("Enter to continue...")
        else:
            if not Rofi.confirm("You haven't logged in!!Enter to continue"):
                exit(1)
        fastanime_main_menu(config, fastanime_runtime_state)
        return
    # determine the watch list to get
    match list_type:
        case "Watching":
            status = "CURRENT"
        case "Planned":
            status = "PLANNING"
        case "Completed":
            status = "COMPLETED"
        case "Dropped":
            status = "DROPPED"
        case "Paused":
            status = "PAUSED"
        case "Rewatching":
            status = "REPEATING"
        case _:
            return

    # get the media list
    anime_list = AniList.get_anime_list(status, page=page)
    # handle null
    if not anime_list:
        print("Sth went wrong", anime_list)
        if not config.use_rofi:
            input("Enter to continue")
        else:
            if not Rofi.confirm("Sth went wrong!!Enter to continue..."):
                exit(1)
        fastanime_main_menu(config, fastanime_runtime_state)
        return
    # handle failure
    if not anime_list[0] or not anime_list[1]:
        print("Sth went wrong", anime_list)
        if not config.use_rofi:
            input("Enter to continue")
        else:
            if not Rofi.confirm("Sth went wrong!!Enter to continue..."):
                exit(1)
        # recall anilist menu
        fastanime_main_menu(config, fastanime_runtime_state)
        return
    # injecting the data is the simplest way since the ui expects a field called media that should have media type
    media = [
        mediaListItem["media"]
        for mediaListItem in anime_list[1]["data"]["Page"]["mediaList"]
    ]
    anime_list[1]["data"]["Page"]["media"] = media  # pyright:ignore
    return anime_list


def _anilist_search(config: "Config", page=1):
    """A function that enables seaching of an anime

    Returns:
        [TODO:return]
    """
    # TODO: Add filters and other search features
    if config.use_rofi:
        search_term = str(Rofi.ask("Search for"))
    else:
        search_term = Prompt.ask("[cyan]Search for[/]")

    return AniList.search(query=search_term, page=page)


def _anilist_random(config: "Config", page=1):
    """A function that generates random anilist ids enabling random discovery of anime

    Returns:
        [TODO:return]
    """
    random_anime = range(1, 15000)
    random_anime = random.sample(random_anime, k=50)

    return AniList.search(id_in=list(random_anime))


def _watch_history(config: "Config", page=1):
    """Function that lets you see all the anime that has locally been saved to your watch history

    Returns:
        [TODO:return]
    """
    watch_history = list(map(int, config.watch_history.keys()))
    return AniList.search(id_in=watch_history, sort="TRENDING_DESC", page=page)


def _recent(config: "Config", page=1):
    return (
        True,
        {"data": {"Page": {"media": config.user_data["recent_anime"]}}},
    )


# WARNING: Will probably be depracated
def _anime_list(config: "Config", page=1):
    anime_list = config.anime_list
    return AniList.search(id_in=anime_list, pages=page)


def fastanime_main_menu(
    config: "Config", fastanime_runtime_state: "FastAnimeRuntimeState"
):
    """The main entry point to the anilist command

    Args:
        config: An object containing cconfiguration data
        fastanime_runtime_state: A query dict used to store data during navigation of the ui # initially this was very messy
    """

    def _edit_config(*args, **kwargs):
        """Helper function to edit your config when the ui is still running"""

        from click import edit

        edit(filename=USER_CONFIG_PATH)
        if config.use_rofi:
            config.load_config()
            config.use_rofi = True
            config.use_fzf = False
        else:
            config.load_config()

        config.set_fastanime_config_environs()

        config.anime_provider.provider = config.provider
        config.anime_provider.lazyload_provider(config.provider)

        fastanime_main_menu(config, fastanime_runtime_state)

    icons = config.icons
    # each option maps to anilist data that is described by the option name
    options = {
        f"{'🔥 ' if icons else ''}Trending": AniList.get_trending,
        f"{'🎞️ ' if icons else ''}Recent": _recent,
        f"{'📺 ' if icons else ''}Watching": lambda config, media_list_type="Watching", page=1: _handle_animelist(
            config, fastanime_runtime_state, media_list_type, page=page
        ),
        f"{'⏸  ' if icons else ''}Paused": lambda config, media_list_type="Paused", page=1: _handle_animelist(
            config, fastanime_runtime_state, media_list_type, page=page
        ),
        f"{'🚮 ' if icons else ''}Dropped": lambda config, media_list_type="Dropped", page=1: _handle_animelist(
            config, fastanime_runtime_state, media_list_type, page=page
        ),
        f"{'📑 ' if icons else ''}Planned": lambda config, media_list_type="Planned", page=1: _handle_animelist(
            config, fastanime_runtime_state, media_list_type, page=page
        ),
        f"{'✅ ' if icons else ''}Completed": lambda config, media_list_type="Completed", page=1: _handle_animelist(
            config, fastanime_runtime_state, media_list_type, page=page
        ),
        f"{'🔁 ' if icons else ''}Rewatching": lambda config, media_list_type="Rewatching", page=1: _handle_animelist(
            config, fastanime_runtime_state, media_list_type, page=page
        ),
        f"{'🔔 ' if icons else ''}Recently Updated Anime": AniList.get_most_recently_updated,
        f"{'🔎 ' if icons else ''}Search": _anilist_search,
        f"{'🎞️ ' if icons else ''}Watch History": _watch_history,
        # "AnimeList": _anime_list💯,
        f"{'🎲 ' if icons else ''}Random Anime": _anilist_random,
        f"{'🌟 ' if icons else ''}Most Popular Anime": AniList.get_most_popular,
        f"{'💖 ' if icons else ''}Most Favourite Anime": AniList.get_most_favourite,
        f"{'✨ ' if icons else ''}Most Scored Anime": AniList.get_most_scored,
        f"{'🎬 ' if icons else ''}Upcoming Anime": AniList.get_upcoming_anime,
        f"{'📝 ' if icons else ''}Edit Config": _edit_config,
        f"{'❌ ' if icons else ''}Exit": exit_app,
    }

    # Load main menu order if set in config file
    if config.menu_order:
        menu_order_list = config.menu_order.split(",")
        lookup = {key.split(" ", 1)[-1]: key for key in options}
        ordered_dict = {
            lookup[key]: options[lookup[key]]
            for key in menu_order_list
            if key in lookup
        }
        options = ordered_dict

    # prompt user to select an action
    choices = list(options.keys())
    if config.use_fzf:
        action = fzf.run(
            choices,
            prompt="Select Action",
            header="Anilist Menu",
        )
    elif config.use_rofi:
        action = Rofi.run(choices, "Select Action")
    else:
        action = fuzzy_inquirer(
            choices,
            "Select Action",
        )
    fastanime_runtime_state.current_data_loader = options[action]
    fastanime_runtime_state.current_page = 1
    anilist_data = options[action](config=config)
    # anilist data is a (bool,data)
    # the bool indicated success
    if anilist_data[0]:
        fastanime_runtime_state.anilist_results_data = anilist_data[1]
        anilist_results_menu(config, fastanime_runtime_state)

    else:
        print(anilist_data[1])
        if not config.use_rofi:
            input("Enter to continue...")
        else:
            if not Rofi.confirm("Sth went wrong!!Enter to continue..."):
                exit(1)
        # recall the anilist function for the user to reattempt their choice
        fastanime_main_menu(config, fastanime_runtime_state)
