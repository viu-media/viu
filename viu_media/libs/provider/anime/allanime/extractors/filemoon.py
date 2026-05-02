from ...types import EpisodeStream, Server
from ..constants import API_BASE_URL, MP4_SERVER_JUICY_STREAM_REGEX
from ..types import AllAnimeEpisode, AllAnimeSource
from .base import BaseExtractor


# TODO: requires decoding obsfucated js (filemoon)
class FmHlsExtractor(BaseExtractor):
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

        embed_html = response.text.replace(" ", "").replace("\n", "")
        vid = MP4_SERVER_JUICY_STREAM_REGEX.search(embed_html)
        if not vid:
            raise Exception("")
        return Server(
            name="dropbox",
            links=[EpisodeStream(link=vid.group(1), quality="1080")],
            episode_title=episode["notes"],
            headers={"Referer": "https://www.mp4upload.com/"},
        )


# TODO: requires decoding obsfucated js (filemoon)
class OkExtractor(BaseExtractor):
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

        embed_html = response.text.replace(" ", "").replace("\n", "")
        vid = MP4_SERVER_JUICY_STREAM_REGEX.search(embed_html)
        if not vid:
            raise Exception("")
        return Server(
            name="dropbox",
            links=[EpisodeStream(link=vid.group(1), quality="1080")],
            episode_title=episode["notes"],
            headers={"Referer": "https://www.mp4upload.com/"},
        )
