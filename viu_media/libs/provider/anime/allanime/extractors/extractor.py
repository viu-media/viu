from httpx import Client

from ...types import Server
from ..types import AllAnimeEpisode, AllAnimeSource
from ..utils import debug_extractor, logger, one_digit_symmetric_xor
from .ak import AkExtractor
from .dropbox import SakExtractor
from .filemoon import FmHlsExtractor, OkExtractor
from .gogoanime import Lufmp4Extractor
from .mp4_upload import Mp4Extractor
from .sharepoint import Smp4Extractor
from .streamsb import SsHlsExtractor
from .vid_mp4 import VidMp4Extractor
from .we_transfer import KirExtractor
from .wixmp import DefaultExtractor
from .yt_mp4 import YtExtractor

AVAILABLE_SOURCES = {
    "Sak": SakExtractor,
    "S-mp4": Smp4Extractor,
    "Luf-Mp4": Lufmp4Extractor,
    "Default": DefaultExtractor,
    "Yt-mp4": YtExtractor,
    "Kir": KirExtractor,
    "Mp4": Mp4Extractor,
}
OTHER_SOURCES = {
    "Ak": AkExtractor,
    "Vid-mp4": VidMp4Extractor,
    "Ok": OkExtractor,
    "Ss-Hls": SsHlsExtractor,
    "Fm-Hls": FmHlsExtractor,
}


@debug_extractor
def extract_server(
    client: Client,
    episode_number: str,
    episode: AllAnimeEpisode,
    source: AllAnimeSource,
) -> Server | None:
    url = source.get("sourceUrl")
    if not url:
        logger.debug(f"Url not found in source: {source}")
        return

    if url.startswith("--"):
        url = one_digit_symmetric_xor(56, url[2:])

        logger.debug(f"Decrypting url for source: {source['sourceName']}")
    if source["sourceName"] in OTHER_SOURCES:
        logger.debug(f"Found  {source['sourceName']} but ignoring")
        return

    if source["sourceName"] not in AVAILABLE_SOURCES:
        logger.debug(
            f"Found  {source['sourceName']} but did not expect it, its time to scrape lol"
        )
        return
    logger.debug(f"Found  {source['sourceName']}")

    return AVAILABLE_SOURCES[source["sourceName"]].extract(
        url, client, episode_number, episode, source
    )
