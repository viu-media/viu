from ...types import EpisodeStream, Server
from ..constants import API_BASE_URL
from ..types import AllAnimeEpisode, AllAnimeSource
from .base import BaseExtractor


class SakExtractor(BaseExtractor):
    @classmethod
    def extract(
        cls,
        url,
        client,
        episode_number: str,
        episode: AllAnimeEpisode,
        source: AllAnimeSource,
    ) -> Server:
        response = client.get(
            f"https://{API_BASE_URL}{url.replace('clock', 'clock.json')}",
            timeout=10,
        )
        response.raise_for_status()
        streams = response.json()

        return Server(
            name="dropbox",
            links=[
                EpisodeStream(link=link, quality="1080") for link in streams["links"]
            ],
            episode_title=episode["notes"],
            headers={"Referer": f"https://{API_BASE_URL}/"},
        )
