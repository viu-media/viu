from enum import Enum
from typing import Literal, TypedDict


class Server(Enum):
    SHAREPOINT = "sharepoint"
    DROPBOX = "dropbox"
    GOGOANIME = "gogoanime"
    WETRANSFER = "weTransfer"
    WIXMP = "wixmp"
    YT = "Yt"
    MP4_UPLOAD = "mp4-upload"


class AllAnimeEpisodesDetail(TypedDict):
    dub: list[str]
    sub: list[str]
    raw: list[str]


class AllAnimeEpisodes(TypedDict):
    dub: int
    sub: int
    raw: int


class AllAnimePageInfo(TypedDict):
    total: int


class AllAnimeShow(TypedDict):
    _id: str
    name: str
    availableEpisodesDetail: AllAnimeEpisodesDetail
    __typename: str


class AllAnimeSearchResult(TypedDict):
    _id: str
    name: str
    availableEpisodes: AllAnimeEpisodes
    __typename: str | None


class AllAnimeShows(TypedDict):
    pageInfo: AllAnimePageInfo
    edges: list[AllAnimeSearchResult]


class AllAnimeSearchResults(TypedDict):
    shows: AllAnimeShows


class AllAnimeSourceDownload(TypedDict):
    sourceName: str
    dowloadUrl: str


class AllAnimeSource(TypedDict):
    sourceName: Literal[
        "Sak",
        "S-mp4",
        "Luf-mp4",
        "Default",
        "Yt-mp4",
        "Kir",
        "Mp4",
        "Ak",
        "Vid-mp4",
        "Ok",
        "Ss-Hls",
        "Fm-Hls",
    ]
    sourceUrl: str
    priority: float
    sandbox: str
    type: str
    className: str
    streamerId: str
    downloads: AllAnimeSourceDownload


class AllAnimeEpisodeStream(TypedDict):
    link: str
    hls: bool
    resolutionStr: str
    fromCache: str


class AllAnimeEpisodeStreams(TypedDict):
    links: list[AllAnimeEpisodeStream]


class AllAnimeEpisode(TypedDict):
    episodeString: str
    sourceUrls: list[AllAnimeSource]
    notes: str | None


class AllAnimeStream:
    link: str
    mp4: bool
    hls: bool | None
    resolutionStr: str
    fromCache: str
    priority: int
    headers: dict | None


class AllAnimeStreams:
    links: list[AllAnimeStream]
