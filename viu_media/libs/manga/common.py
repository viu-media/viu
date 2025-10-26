import logging

from httpx import get

logger = logging.getLogger(__name__)


def fetch_manga_info_from_bal(anilist_id):
    try:
        url = f"https://raw.githubusercontent.com/bal-mackup/mal-backup/master/anilist/manga/{anilist_id}.json"
        response = get(url, timeout=11)
        if response.ok:
            return response.json()
    except Exception as e:
        logger.error(e)
