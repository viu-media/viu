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
from .types import (
    AnimePaheAnimePage,
    AnimePaheSearchPage,
)

translation_type_map = {
    "sub": MediaTranslationType.SUB,
    "dub": MediaTranslationType.DUB,
    "raw": MediaTranslationType.RAW,
}


def map_to_search_results(data: AnimePaheSearchPage) -> SearchResults:
    results = []
    for result in data["data"]:
        results.append(
            SearchResult(
                id=result["session"],
                title=result["title"],
                episodes=AnimeEpisodes(
                    sub=list(map(str, range(1, result["episodes"] + 1))),
                    dub=list(map(str, range(1, result["episodes"] + 1))),
                    raw=list(map(str, range(1, result["episodes"] + 1))),
                ),
                media_type=result["type"],
                score=result["score"],
                status=result["status"],
                season=result["season"],
                poster=result["poster"],
                year=str(result["year"]),
            )
        )

    return SearchResults(
        page_info=PageInfo(
            total=data["total"],
            per_page=data["per_page"],
            current_page=data["current_page"],
        ),
        results=results,
    )


def map_to_anime_result(
    search_result: SearchResult, anime: AnimePaheAnimePage
) -> Anime:
    episodes_info = []
    episodes = []
    anime["data"] = sorted(anime["data"], key=lambda k: float(k["episode"]))
    for ep_info in anime["data"]:
        episodes.append(str(ep_info["episode"]))
        episodes_info.append(
            AnimeEpisodeInfo(
                id=str(ep_info["id"]),
                session_id=ep_info["session"],
                episode=str(ep_info["episode"]),
                title=ep_info["title"],
                poster=ep_info["snapshot"],
                duration=str(ep_info["duration"]),
            )
        )

    return Anime(
        id=search_result.id,
        title=search_result.title,
        episodes=AnimeEpisodes(
            sub=episodes,
            dub=episodes,
        ),
        year=str(search_result.year),
        poster=search_result.poster,
        episodes_info=episodes_info,
    )


def map_to_server(
    episode: AnimeEpisodeInfo,
    translation_type: str,
    stream_links: list[tuple[str, str]],
    headers: dict[str, str],
) -> Server:
    links = [
        EpisodeStream(
            link=link[1],
            quality=link[0] if link[0] in ["360", "480", "720", "1080"] else "1080",  # type:ignore
            translation_type=translation_type_map[translation_type],
        )
        for link in stream_links
    ]
    return Server(
        name="kwik", links=links, episode_title=episode.title, headers=headers
    )
