"""An abstraction over all providers offering added features with a simple and well typed api

[TODO:description]
"""

import importlib
import logging
from typing import TYPE_CHECKING

from .libs.manga_provider import manga_sources

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


class MangaProvider:
    """Class that manages all anime sources adding some extra functionality to them.
    Attributes:
        PROVIDERS: [TODO:attribute]
        provider: [TODO:attribute]
        provider: [TODO:attribute]
        dynamic: [TODO:attribute]
        retries: [TODO:attribute]
        manga_provider: [TODO:attribute]
    """

    PROVIDERS = list(manga_sources.keys())
    provider = PROVIDERS[0]

    def __init__(self, provider="mangadex", dynamic=False, retries=0) -> None:
        self.provider = provider
        self.dynamic = dynamic
        self.retries = retries
        self.lazyload_provider(self.provider)

    def lazyload_provider(self, provider):
        """updates the current provider being used"""
        _, anime_provider_cls_name = manga_sources[provider].split(".", 1)
        package = f"viu_media.libs.manga_provider.{provider}"
        provider_api = importlib.import_module(".api", package)
        manga_provider = getattr(provider_api, anime_provider_cls_name)
        self.manga_provider = manga_provider()

    def search_for_manga(
        self,
        user_query,
        nsfw=True,
        unknown=True,
    ):
        """core abstraction over all providers search functionality

        Args:
            user_query ([TODO:parameter]): [TODO:description]
            translation_type ([TODO:parameter]): [TODO:description]
            nsfw ([TODO:parameter]): [TODO:description]
            manga_provider ([TODO:parameter]): [TODO:description]
            anilist_obj: [TODO:description]

        Returns:
            [TODO:return]
        """
        manga_provider = self.manga_provider
        try:
            results = manga_provider.search_for_manga(user_query, nsfw, unknown)
        except Exception as e:
            logger.error(e)
            results = None
        return results

    def get_manga(
        self,
        anime_id: str,
    ):
        """core abstraction over getting info of an anime from all providers

        Args:
            anime_id: [TODO:description]
            anilist_obj: [TODO:description]

        Returns:
            [TODO:return]
        """
        manga_provider = self.manga_provider
        try:
            results = manga_provider.get_manga(anime_id)
        except Exception as e:
            logger.error(e)
            results = None
        return results

    def get_chapter_thumbnails(
        self,
        manga_id: str,
        chapter: str,
    ):
        manga_provider = self.manga_provider
        try:
            results = manga_provider.get_chapter_thumbnails(manga_id, chapter)
        except Exception as e:
            logger.error(e)
            results = None
        return results  # pyright:ignore
