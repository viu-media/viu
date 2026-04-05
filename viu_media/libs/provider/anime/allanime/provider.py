import logging
from typing import TYPE_CHECKING

from .....core.utils.graphql import execute_graphql
from ..base import BaseAnimeProvider
from ..utils.debug import debug_provider
from .constants import (
    ANIME_GQL,
    API_GRAPHQL_ENDPOINT,
    API_GRAPHQL_REFERER,
    EPISODE_GQL,
    SEARCH_GQL,
)
from .mappers import (
    map_to_anime_result,
    map_to_search_results,
)

if TYPE_CHECKING:
    from .types import AllAnimeEpisode
logger = logging.getLogger(__name__)


class AllAnime(BaseAnimeProvider):
    HEADERS = {"Referer": API_GRAPHQL_REFERER}

    @debug_provider
    def search(self, params):
        response = execute_graphql(
            API_GRAPHQL_ENDPOINT,
            self.client,
            SEARCH_GQL,
            variables={
                "search": {
                    "allowAdult": params.allow_nsfw,
                    "allowUnknown": params.allow_unknown,
                    "query": params.query,
                },
                "limit": params.page_limit,
                "page": params.current_page,
                "translationtype": params.translation_type,
                "countryorigin": params.country_of_origin,
            },
        )
        return map_to_search_results(response)

    @debug_provider
    def get(self, params):
        response = execute_graphql(
            API_GRAPHQL_ENDPOINT,
            self.client,
            ANIME_GQL,
            variables={"showId": params.id},
        )
        return map_to_anime_result(response)

    @debug_provider
    def episode_streams(self, params):
        from .extractors import extract_server

        episode_response = execute_graphql(
            API_GRAPHQL_ENDPOINT,
            self.client,
            EPISODE_GQL,
            variables={
                "showId": params.anime_id,
                "translationType": params.translation_type,
                "episodeString": params.episode,
            },
        )
        episode: AllAnimeEpisode = episode_response.json()["data"]["episode"]
        for source in episode["sourceUrls"]:
            if server := extract_server(self.client, params.episode, episode, source):
                yield server


if __name__ == "__main__":
    from ..utils.debug import test_anime_provider

    test_anime_provider(AllAnime)
