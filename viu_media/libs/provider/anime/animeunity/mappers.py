from typing import Literal

from ..types import (
    Anime,
    AnimeEpisodeInfo,
    AnimeEpisodes,
    EpisodeStream,
    MediaTranslationType,
    PageInfo,
    SearchResult,
    SearchResults,
    Server,
)
from .constants import AVAILABLE_VIDEO_QUALITY


def map_to_search_results(
    data: dict, translation_type: Literal["sub", "dub"]
) -> SearchResults:
    results = []
    for result in data:
        mapped_result = map_to_search_result(result, translation_type)
        if mapped_result:
            results.append(mapped_result)

    return SearchResults(
        page_info=PageInfo(),
        results=results,
    )


def map_to_search_result(
    data: dict, translation_type: Literal["sub", "dub"] | None
) -> SearchResult | None:
    if translation_type and data["dub"] != 1 if translation_type == "dub" else 0:
        return None
    return SearchResult(
        id=str(data["id"]),
        title=get_titles(data)[0] if get_titles(data) else "Unknown",
        episodes=AnimeEpisodes(
            sub=(
                list(map(str, range(1, get_episodes_count(data) + 1)))
                if data["dub"] == 0
                else []
            ),
            dub=(
                list(map(str, range(1, get_episodes_count(data) + 1)))
                if data["dub"] == 1
                else []
            ),
        ),
        other_titles=get_titles(data),
        score=data["score"],
        poster=data["imageurl"],
        year=data["date"],
    )


def map_to_anime_result(data: list, search_result: SearchResult) -> Anime:
    return Anime(
        id=search_result.id,
        title=search_result.title,
        episodes=AnimeEpisodes(
            sub=[
                episode["number"]
                for episode in data
                if len(search_result.episodes.sub) > 0
            ],
            dub=[
                episode["number"]
                for episode in data
                if len(search_result.episodes.dub) > 0
            ],
        ),
        episodes_info=[
            AnimeEpisodeInfo(
                id=str(episode["id"]),
                episode=episode["number"],
                title=f"{search_result.title} - Ep {episode['number']}",
            )
            for episode in data
        ],
        type=search_result.media_type,
        poster=search_result.poster,
        year=search_result.year,
    )


def map_to_server(
    episode: AnimeEpisodeInfo, info: dict, translation_type: Literal["sub", "dub"]
) -> Server:
    return Server(
        name="vixcloud",
        links=[
            EpisodeStream(
                link=info["link"].replace(str(info["quality"]), quality),
                title=info["name"],
                quality=quality,  # type: ignore
                translation_type=MediaTranslationType(translation_type),
                mp4=True,
            )
            for quality in sorted(
                list(set(AVAILABLE_VIDEO_QUALITY + [str(info["quality"])])),
                key=lambda x: int(x),
                reverse=True,
            )
            if int(quality) <= info["quality"]
        ],
        episode_title=episode.title,
    )


def get_titles(data: dict) -> list[str]:
    """
    Return the most appropriate title from the record.
    """
    titles = []
    if data.get("title_eng"):
        titles.append(data["title_eng"])
    if data.get("title"):
        titles.append(data["title"])
    if data.get("title_it"):
        titles.append(data["title_it"])
    return titles


def get_episodes_count(record: dict) -> int:
    """
    Return the number of episodes from the record.
    """
    if (count := record.get("real_episodes_count", 0)) > 0:
        return count
    return record.get("episodes_count", 0)
