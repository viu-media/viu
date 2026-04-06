import re

from .....core.constants import GRAPHQL_DIR

SERVERS_AVAILABLE = [
    "sharepoint",
    "dropbox",
    "gogoanime",
    "weTransfer",
    "wixmp",
    "Yt",
    "mp4-upload",
]
API_BASE_URL = "allanime.day"
API_GRAPHQL_REFERER = "https://allanime.to/"
API_GRAPHQL_ENDPOINT = f"https://api.{API_BASE_URL}/api/"
API_GRAPHQL_HEADERS= {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": f"{API_GRAPHQL_REFERER}",
}

# search constants
DEFAULT_COUNTRY_OF_ORIGIN = "all"
DEFAULT_NSFW = True
DEFAULT_UNKNOWN = True
DEFAULT_PER_PAGE = 40
DEFAULT_PAGE = 1

# regex stuff
MP4_SERVER_JUICY_STREAM_REGEX = re.compile(
    r"video/mp4\",src:\"(https?://.*/video\.mp4)\""
)

# graphql files
_GQL_QUERIES = GRAPHQL_DIR / "allanime" / "queries"
SEARCH_GQL = _GQL_QUERIES / "search.gql"
ANIME_GQL = _GQL_QUERIES / "anime.gql"
EPISODE_GQL = _GQL_QUERIES / "episodes.gql"
