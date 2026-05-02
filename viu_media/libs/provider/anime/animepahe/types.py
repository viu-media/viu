from enum import Enum
from typing import Literal, TypedDict


class Server(Enum):
    KWIK = "Kwik"


class AnimePaheSearchResult(TypedDict):
    id: str
    title: str
    type: str
    episodes: int
    status: str
    season: str
    year: int
    score: int
    poster: str
    session: str


class AnimePaheSearchPage(TypedDict):
    total: int
    per_page: int
    current_page: int
    last_page: int
    _from: int
    to: int
    data: list[AnimePaheSearchResult]


class Episode(TypedDict):
    id: str
    anime_id: int
    episode: float
    episode2: int
    edition: str
    title: str
    snapshot: str  # episode image
    disc: str
    audio: Literal["eng", "jpn"]
    duration: str  # time 00:00:00
    session: str
    filler: int
    created_at: str


class AnimePaheAnimePage(TypedDict):
    total: int
    per_page: int
    current_page: int
    last_page: int
    next_page_url: str | None
    prev_page_url: str | None
    _from: int
    to: int
    data: list[Episode]


class AnimePaheEpisodeInfo(TypedDict):
    title: str
    episode: float
    id: str
    translation_type: Literal["eng", "jpn"]
    duration: str
    poster: str


class AvailableEpisodesDetail(TypedDict):
    sub: list[str]
    dub: list[str]
    raw: list[str]


class AnimePaheAnime(TypedDict):
    id: str
    title: str
    year: int
    season: str
    poster: str
    score: int
    availableEpisodesDetail: AvailableEpisodesDetail
    episodesInfo: list[AnimePaheEpisodeInfo]


class PageInfo(TypedDict):
    total: int
    perPage: int
    currentPage: int


class AnimePaheSearchResults(TypedDict):
    pageInfo: PageInfo
    results: list[AnimePaheSearchResult]


class AnimePaheStreamLink(TypedDict):
    quality: str
    translation_type: Literal["sub", "dub"]
    link: str


class AnimePaheServer(TypedDict):
    server: Literal["kwik"]
    links: list[AnimePaheStreamLink]
    episode_title: str
    subtitles: list
    headers: dict
