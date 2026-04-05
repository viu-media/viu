import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from httpx import Client, Response

from .networking import TIMEOUT

if TYPE_CHECKING:
    from httpx import Client

logger = logging.getLogger(__name__)


def load_graphql_from_file(file: Path) -> str:
    """
    Reads and returns the content of a .gql file.

    Args:
        file: The Path object pointing to the .gql file.

    Returns:
        The string content of the file.
    """
    try:
        return file.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"GraphQL file not found at: {file}")
        raise


def execute_graphql_query_with_get_request(
    url: str, httpx_client: Client, graphql_file: Path, variables: dict
) -> Response:
    query = load_graphql_from_file(graphql_file)
    params = {"query": query, "variables": json.dumps(variables)}
    response = httpx_client.get(url, params=params, timeout=TIMEOUT)
    return response


def execute_graphql(
    url: str, httpx_client: Client, graphql_file: Path, variables: dict
) -> Response:
    query = load_graphql_from_file(graphql_file)
    json_body = {"query": query, "variables": variables}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://allanime.to",
    }
    response = httpx_client.post(url, json=json_body, headers=headers, timeout=TIMEOUT)
    return response
