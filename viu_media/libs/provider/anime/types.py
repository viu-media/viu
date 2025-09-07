from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict

# from .allanime.types import Server as AllAnimeServer
# from .animepahe.types import Server as AnimePaheServer


# ENUMS
class ProviderName(Enum):
    ALLANIME = "allanime"
    ANIMEPAHE = "animepahe"
    ANIMEUNITY = "animeunity"


class ProviderServer(Enum):
    TOP = "TOP"

    # AllAnimeServer values
    SHAREPOINT = "sharepoint"
    DROPBOX = "dropbox"
    GOGOANIME = "gogoanime"
    WETRANSFER = "weTransfer"
    WIXMP = "wixmp"
    YT = "Yt"
    MP4_UPLOAD = "mp4-upload"

    # AnimePaheServer values
    KWIK = "kwik"

    # AnimeUnityServer values
    VIXCLOUD = "vixcloud"


class MediaTranslationType(Enum):
    SUB = "sub"
    DUB = "dub"
    RAW = "raw"


# MODELS
class BaseAnimeProviderModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class PageInfo(BaseAnimeProviderModel):
    total: Optional[int] = None
    per_page: Optional[int] = None
    current_page: Optional[int] = None


class AnimeEpisodes(BaseAnimeProviderModel):
    sub: List[str]
    dub: List[str] = []
    raw: List[str] = []


class SearchResult(BaseAnimeProviderModel):
    id: str
    title: str
    episodes: AnimeEpisodes
    other_titles: List[str] = []
    media_type: Optional[str] = None
    score: Optional[float] = None
    status: Optional[str] = None
    season: Optional[str] = None
    poster: Optional[str] = None
    year: Optional[str] = None


class SearchResults(BaseAnimeProviderModel):
    page_info: PageInfo
    results: List[SearchResult]


class AnimeEpisodeInfo(BaseAnimeProviderModel):
    id: str
    episode: str
    session_id: Optional[str] = None
    title: Optional[str] = None
    poster: Optional[str] = None
    duration: Optional[str] = None


class Anime(BaseAnimeProviderModel):
    id: str
    title: str
    episodes: AnimeEpisodes
    type: Optional[str] = None
    episodes_info: List[AnimeEpisodeInfo] | None = None
    poster: Optional[str] = None
    year: Optional[str] = None


class EpisodeStream(BaseAnimeProviderModel):
    # episode: str
    link: str
    title: Optional[str] = None
    quality: Literal["360", "480", "720", "1080"] = "720"
    translation_type: MediaTranslationType = MediaTranslationType.SUB
    format: Optional[str] = None
    hls: Optional[bool] = None
    mp4: Optional[bool] = None
    priority: Optional[int] = None


class Subtitle(BaseAnimeProviderModel):
    url: str
    language: Optional[str] = None


class Server(BaseAnimeProviderModel):
    name: str
    links: List[EpisodeStream]
    episode_title: Optional[str] = None
    headers: dict[str, str] = dict()
    subtitles: List[Subtitle] = []
    audio: List[str] = []
