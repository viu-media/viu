from typing import Union

from httpx import Response

from ..types import (
    Anime,
    AnimeEpisodes,
    MediaTranslationType,
    PageInfo,
    SearchResult,
    SearchResults,
)
from .types import AllAnimeSearchResults, AllAnimeShow


def generate_list(count: Union[int, str]) -> list[str]:
    return list(map(str, range(int(count))))


translation_type_map = {
    "sub": MediaTranslationType.SUB,
    "dub": MediaTranslationType.DUB,
    "raw": MediaTranslationType.RAW,
}


def map_to_search_results(response: Response) -> SearchResults:
    search_results: AllAnimeSearchResults = response.json()["data"]
    return SearchResults(
        page_info=PageInfo(total=search_results["shows"]["pageInfo"]["total"]),
        results=[
            SearchResult(
                id=result["_id"],
                title=result["name"],
                media_type=result["__typename"],
                episodes=AnimeEpisodes(
                    sub=generate_list(result["availableEpisodes"]["sub"]),
                    dub=generate_list(result["availableEpisodes"]["dub"]),
                    raw=generate_list(result["availableEpisodes"]["raw"]),
                ),
            )
            for result in search_results["shows"]["edges"]
        ],
    )


def map_to_anime_result(response: Response) -> Anime:
    anime: AllAnimeShow = response.json()["data"]["show"]
    return Anime(
        id=anime["_id"],
        title=anime["name"],
        episodes=AnimeEpisodes(
            sub=sorted(anime["availableEpisodesDetail"]["sub"], key=float),
            dub=sorted(anime["availableEpisodesDetail"]["dub"], key=float),
            raw=sorted(anime["availableEpisodesDetail"]["raw"], key=float),
        ),
        type=anime.get("__typename"),
    )
