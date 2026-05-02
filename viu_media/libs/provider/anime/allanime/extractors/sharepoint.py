from ...types import EpisodeStream, Server
from ..constants import API_BASE_URL
from ..types import AllAnimeEpisodeStreams
from .base import BaseExtractor


class Smp4Extractor(BaseExtractor):
    @classmethod
    def extract(cls, url, client, episode_number, episode, source):
        response = client.get(
            f"https://{API_BASE_URL}{url.replace('clock', 'clock.json')}",
            timeout=10,
        )
        response.raise_for_status()
        streams: AllAnimeEpisodeStreams = response.json()
        return Server(
            name="sharepoint",
            links=[
                EpisodeStream(
                    link=stream["link"],
                    quality="1080",
                    format=stream["resolutionStr"],
                )
                for stream in streams["links"]
            ],
            episode_title=episode["notes"],
            headers={"Referer": f"https://{API_BASE_URL}/"},
        )
