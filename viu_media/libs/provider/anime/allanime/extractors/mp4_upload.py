from ...types import EpisodeStream, Server
from ..constants import MP4_SERVER_JUICY_STREAM_REGEX
from ..utils import logger
from .base import BaseExtractor


class Mp4Extractor(BaseExtractor):
    @classmethod
    def extract(cls, url, client, episode_number, episode, source):
        response = client.get(url, timeout=10, follow_redirects=True)
        response.raise_for_status()

        embed_html = response.text.replace(" ", "").replace("\n", "")

        # NOTE: some of the video were deleted so the embed html will just be "Filewasdeleted"
        vid = MP4_SERVER_JUICY_STREAM_REGEX.search(embed_html)
        if not vid:
            if embed_html == "Filewasdeleted":
                logger.debug(
                    "Failed to extract stream url from mp4-uploads. Reason: Filewasdeleted"
                )
                return
            logger.debug(
                f"Failed to extract stream url from mp4-uploads. Reason: unknown. Embed html: {embed_html}"
            )
            return
        return Server(
            name="mp4-upload",
            links=[EpisodeStream(link=vid.group(1), quality="1080")],
            episode_title=episode["notes"],
            headers={"Referer": "https://www.mp4upload.com/"},
        )
