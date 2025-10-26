import logging

from ...common.mini_anilist import search_for_manga_with_anilist
from ..base_provider import MangaProvider
from ..common import fetch_manga_info_from_bal

logger = logging.getLogger(__name__)


class MangaDexApi(MangaProvider):
    def search_for_manga(self, title: str, *args):
        try:
            search_results = search_for_manga_with_anilist(title)
            return search_results
        except Exception as e:
            logger.error(f"[MANGADEX-ERROR]: {e}")

    def get_manga(self, anilist_manga_id: str):
        bal_data = fetch_manga_info_from_bal(anilist_manga_id)
        if not bal_data:
            return
        manga_id, MangaDexManga = next(iter(bal_data["Sites"]["Mangadex"].items()))
        return {
            "id": manga_id,
            "title": MangaDexManga["title"],
            "poster": MangaDexManga["image"],
            "availableChapters": [],
        }

    def get_chapter_thumbnails(self, manga_id, chapter):
        chapter_info_url = f"https://api.mangadex.org/chapter?manga={manga_id}&translatedLanguage[]=en&chapter={chapter}&includeEmptyPages=0"
        chapter_info_response = self.session.get(chapter_info_url)
        if not chapter_info_response.ok:
            return
        chapter_info = next(iter(chapter_info_response.json()["data"]))
        chapters_thumbnails_url = (
            f"https://api.mangadex.org/at-home/server/{chapter_info['id']}"
        )
        chapter_thumbnails_response = self.session.get(chapters_thumbnails_url)
        if not chapter_thumbnails_response.ok:
            return
        chapter_thumbnails_info = chapter_thumbnails_response.json()
        base_url = chapter_thumbnails_info["baseUrl"]
        hash = chapter_thumbnails_info["chapter"]["hash"]
        return {
            "thumbnails": [
                f"{base_url}/data/{hash}/{chapter_thumbnail}"
                for chapter_thumbnail in chapter_thumbnails_info["chapter"]["data"]
            ],
            "title": chapter_info["attributes"]["title"],
        }
