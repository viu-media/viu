from abc import ABC, abstractmethod

from httpx import Client

from ...types import Server
from ..types import AllAnimeEpisode, AllAnimeSource


class BaseExtractor(ABC):
    @classmethod
    @abstractmethod
    def extract(
        cls,
        url: str,
        client: Client,
        episode_number: str,
        episode: AllAnimeEpisode,
        source: AllAnimeSource,
    ) -> Server | None:
        pass
