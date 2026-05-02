import logging
from functools import lru_cache
from typing import Iterator, Optional
from urllib.parse import urlparse

from ..base import BaseAnimeProvider
from ..params import AnimeParams, EpisodeStreamsParams, SearchParams
from ..types import Anime, AnimeEpisodeInfo, SearchResult, SearchResults, Server
from ..utils.debug import debug_provider
from .constants import (
    ANIMEPAHE_BASE,
    ANIMEPAHE_ENDPOINT,
    CDN_PROVIDER,
    JUICY_STREAM_REGEX,
    REQUEST_HEADERS,
    SERVER_HEADERS,
    STREAM_HEADERS,
)
from .extractor import process_animepahe_embed_page
from .mappers import map_to_anime_result, map_to_search_results, map_to_server
from .types import AnimePaheAnimePage, AnimePaheSearchPage

logger = logging.getLogger(__name__)


class AnimePahe(BaseAnimeProvider):
    HEADERS = REQUEST_HEADERS

    @debug_provider
    def search(self, params: SearchParams) -> SearchResults | None:
        return self._search(params)

    @lru_cache()
    def _search(self, params: SearchParams) -> SearchResults | None:
        url_params = {"m": "search", "q": params.query}
        response = self.client.get(ANIMEPAHE_ENDPOINT, params=url_params)
        response.raise_for_status()
        data: AnimePaheSearchPage = response.json()
        if not data.get("data"):
            return
        return map_to_search_results(data)

    @debug_provider
    def get(self, params: AnimeParams) -> Anime | None:
        return self._get_anime(params)

    @lru_cache()
    def _get_anime(self, params: AnimeParams) -> Anime | None:
        page = 1
        standardized_episode_number = 0

        search_result = self._get_search_result(params)
        if not search_result:
            logger.error(f"No search result found for ID {params.id}")
            return None

        anime: Optional[AnimePaheAnimePage] = None

        has_next_page = True
        while has_next_page:
            logger.debug(f"Loading page: {page}")
            _anime_page = self._anime_page_loader(
                m="release",
                id=params.id,
                sort="episode_asc",
                page=page,
            )

            has_next_page = True if _anime_page["next_page_url"] else False
            page += 1
            if not anime:
                anime = _anime_page
            else:
                anime["data"].extend(_anime_page["data"])

        if anime:
            for episode in anime.get("data", []):
                if episode["episode"] % 1 == 0:
                    standardized_episode_number += 1
                    episode.update({"episode": standardized_episode_number})
                else:
                    standardized_episode_number += episode["episode"] % 1
                    episode.update({"episode": standardized_episode_number})
                    standardized_episode_number = int(standardized_episode_number)

            return map_to_anime_result(search_result, anime)

    @lru_cache()
    def _get_search_result(self, params: AnimeParams) -> Optional[SearchResult]:
        search_results = self._search(SearchParams(query=params.query))
        if not search_results or not search_results.results:
            logger.error(f"No search results found for ID {params.id}")
            return None
        for search_result in search_results.results:
            if search_result.id == params.id:
                return search_result

    @lru_cache()
    def _anime_page_loader(self, m, id, sort, page) -> AnimePaheAnimePage:
        url_params = {
            "m": m,
            "id": id,
            "sort": sort,
            "page": page,
        }
        response = self.client.get(ANIMEPAHE_ENDPOINT, params=url_params)
        response.raise_for_status()
        return response.json()

    @debug_provider
    def episode_streams(self, params: EpisodeStreamsParams) -> Iterator[Server] | None:
        from ...scraping.html_parser import (
            extract_attributes,
            get_element_by_id,
            get_elements_html_by_class,
        )

        episode = self._get_episode_info(params)
        if not episode:
            logger.error(
                f"Episode {params.episode} doesn't exist for anime {params.anime_id}"
            )
            return

        url = f"{ANIMEPAHE_BASE}/play/{params.anime_id}/{episode.session_id}"
        response = self.client.get(url, follow_redirects=True)
        response.raise_for_status()

        c = get_element_by_id("resolutionMenu", response.text)
        if not c:
            logger.error("Resolution menu not found in the response")
            return
        resolutionMenuItems = get_elements_html_by_class("dropdown-item", c)
        res_dicts = [extract_attributes(item) for item in resolutionMenuItems]
        quality = None
        translation_type = None
        stream_links = []
        stream_host = None

        # TODO: better document the scraping process
        for res_dict in res_dicts:
            # the actual attributes are data attributes in the original html 'prefixed with data-'
            embed_url = res_dict["src"]
            logger.debug(f"Found embed url: {embed_url}")
            data_audio = "dub" if res_dict["audio"] == "eng" else "sub"

            if data_audio != params.translation_type:
                logger.debug(f"Found {data_audio} but wanted {params.translation_type}")
                continue

            if not embed_url:
                logger.warning("embed url not found please report to the developers")
                continue

            embed_response = self.client.get(
                embed_url,
                headers={
                    "User-Agent": self.client.headers["User-Agent"],
                    **SERVER_HEADERS,
                },
            )
            embed_response.raise_for_status()
            embed_page = embed_response.text
            logger.debug("Processing embed page for JS decoding")

            decoded_js = process_animepahe_embed_page(embed_page)
            if not decoded_js:
                logger.error("failed to decode embed page")
                continue
            logger.debug(f"Decoded JS: {decoded_js[:100]}...")
            juicy_stream = JUICY_STREAM_REGEX.search(decoded_js)
            if not juicy_stream:
                logger.error("failed to find juicy stream")
                continue
            logger.debug(f"Found juicy stream: {juicy_stream.group(1)}")
            juicy_stream = juicy_stream.group(1)
            stream_host = urlparse(juicy_stream).hostname
            quality = res_dict["resolution"]
            logger.debug(f"Found quality: {quality}")
            translation_type = data_audio
            stream_links.append((quality, juicy_stream))

        if translation_type and stream_links:
            headers = {
                "User-Agent": self.client.headers["User-Agent"],
                "Host": stream_host or CDN_PROVIDER,
                **STREAM_HEADERS,
            }
            yield map_to_server(
                episode, translation_type, stream_links, headers=headers
            )

    @lru_cache()
    def _get_episode_info(
        self, params: EpisodeStreamsParams
    ) -> Optional[AnimeEpisodeInfo]:
        anime_info = self._get_anime(
            AnimeParams(id=params.anime_id, query=params.query)
        )
        if not anime_info:
            logger.error(f"No anime info for {params.anime_id}")
            return
        if not anime_info.episodes_info:
            logger.error(f"No episodes info for {params.anime_id}")
            return
        for episode in anime_info.episodes_info:
            if episode.episode == params.episode:
                return episode


if __name__ == "__main__":
    from ..utils.debug import test_anime_provider

    test_anime_provider(AnimePahe)
