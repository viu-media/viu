from ...types import EpisodeStream, Server
from ..constants import API_BASE_URL
from ..types import AllAnimeEpisode, AllAnimeSource
from .base import BaseExtractor


class SsHlsExtractor(BaseExtractor):
    @classmethod
    def extract(
        cls,
        url,
        client,
        episode_number: str,
        episode: AllAnimeEpisode,
        source: AllAnimeSource,
    ) -> Server:
        # TODO: requires some serious work i think : )
        response = client.get(
            url,
            timeout=10,
        )
        response.raise_for_status()
        streams = response.json()["links"]

        return Server(
            name="StreamSb",
            links=[
                EpisodeStream(link=link, quality="1080") for link in streams["links"]
            ],
            episode_title=episode["notes"],
            headers={"Referer": f"https://{API_BASE_URL}/"},
        )
