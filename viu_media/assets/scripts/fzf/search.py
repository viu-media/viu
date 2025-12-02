#!/usr/bin/env python3
#
# FZF Dynamic Search Script Template
#
# This script is a template for dynamic search functionality in fzf.
# The placeholders in curly braces, like {GRAPHQL_ENDPOINT} are dynamically
# filled by Python using .replace() during runtime.

import json
import sys
from pathlib import Path
from urllib import request
from urllib.error import URLError

# --- Template Variables (Injected by Python) ---
GRAPHQL_ENDPOINT = "{GRAPHQL_ENDPOINT}"
SEARCH_RESULTS_FILE = Path("{SEARCH_RESULTS_FILE}")
AUTH_HEADER = "{AUTH_HEADER}"

# The GraphQL query is injected as a properly escaped JSON string
GRAPHQL_QUERY = "{GRAPHQL_QUERY}"

# --- Get Query from fzf ---
# fzf passes the current query as the first argument when using --bind change:reload
QUERY = sys.argv[1] if len(sys.argv) > 1 else ""

# If query is empty, exit with empty results
if not QUERY.strip():
    print("")
    sys.exit(0)


def make_graphql_request(
    endpoint: str, query: str, variables: dict, auth_token: str = ""
) -> dict | None:
    """
    Make a GraphQL request to the specified endpoint.

    Args:
        endpoint: GraphQL API endpoint URL
        query: GraphQL query string
        variables: Query variables as a dictionary
        auth_token: Optional authorization token (Bearer token)

    Returns:
        Response JSON as a dictionary, or None if request fails
    """
    payload = {"query": query, "variables": variables}

    headers = {"Content-Type": "application/json", "User-Agent": "viu/1.0"}

    if auth_token:
        headers["Authorization"] = auth_token

    try:
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError, Exception) as e:
        print(f"❌ Request failed: {e}", file=sys.stderr)
        return None


def extract_title(media_item: dict) -> str:
    """
    Extract the best available title from a media item.

    Args:
        media_item: Media object from GraphQL response

    Returns:
        Title string (english > romaji > native > "Unknown")
    """
    title_obj = media_item.get("title", {})
    return (
        title_obj.get("english")
        or title_obj.get("romaji")
        or title_obj.get("native")
        or "Unknown"
    )


def main():
    # Ensure parent directory exists
    SEARCH_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Create GraphQL variables
    variables = {
        "query": QUERY,
        "type": "ANIME",
        "per_page": 50,
        "genre_not_in": ["Hentai"],
    }

    # Make the GraphQL request
    response = make_graphql_request(
        GRAPHQL_ENDPOINT, GRAPHQL_QUERY, variables, AUTH_HEADER
    )

    if response is None:
        print("❌ Search failed")
        sys.exit(1)

    # Save the raw response for later processing by dynamic_search.py
    try:
        with open(SEARCH_RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"❌ Failed to save results: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse and display results
    if "errors" in response:
        print(f"❌ Search error: {response['errors']}")
        sys.exit(1)

    # Navigate the response structure
    data = response.get("data", {})
    page = data.get("Page", {})
    media_list = page.get("media", [])

    if not media_list:
        print("❌ No results found")
        sys.exit(0)

    # Output titles for fzf (one per line)
    for media in media_list:
        title = extract_title(media)
        print(title)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
