#!/usr/bin/env python3
#
# FZF Dynamic Search Script Template
#
# This script is a template for dynamic search functionality in fzf.
# The placeholders in curly braces, like {GRAPHQL_ENDPOINT} are dynamically
# filled by Python using .replace() during runtime.
#
# FILTER SYNTAX:
#   @genre:action,comedy     Filter by genres
#   @genre:!hentai           Exclude genre
#   @status:airing           Status: airing, finished, upcoming, cancelled, hiatus
#   @year:2024               Filter by year
#   @season:winter           winter, spring, summer, fall
#   @format:tv,movie         tv, movie, ova, ona, special
#   @sort:score              score, popularity, trending, date, title
#   @score:>80 / @score:<50  Min/max score
#   @onlist / @onlist:false  Filter by list status
#   @tag:isekai              Filter by tags

import json
import sys
from pathlib import Path
from urllib import request
from urllib.error import URLError

# Import the filter parser
from _filter_parser import parse_filters

# --- Template Variables (Injected by Python) ---
GRAPHQL_ENDPOINT = "{GRAPHQL_ENDPOINT}"
SEARCH_RESULTS_FILE = Path("{SEARCH_RESULTS_FILE}")
AUTH_HEADER = "{AUTH_HEADER}"

# The GraphQL query is injected as a properly escaped JSON string
GRAPHQL_QUERY = "{GRAPHQL_QUERY}"

# --- Get Query from fzf ---
# fzf passes the current query as the first argument when using --bind change:reload
RAW_QUERY = sys.argv[1] if len(sys.argv) > 1 else ""

# Parse the query to extract filters and clean search text
QUERY, PARSED_FILTERS = parse_filters(RAW_QUERY)

# If query is empty and no filters, show help hint
if not RAW_QUERY.strip():
    print("💡 Tip: Use @genre:action @status:airing for filters (type @help for syntax)")
    sys.exit(0)

# Show filter help if requested
if RAW_QUERY.strip().lower() in ("@help", "@?", "@h"):
    from _filter_parser import get_help_text
    print(get_help_text())
    sys.exit(0)

# If we only have filters (no search text), that's valid - we'll search with filters only
# But if we have neither query nor filters, we already showed the help hint above


def make_graphql_request(
    endpoint: str, query: str, variables: dict, auth_token: str = ""
) -> tuple[dict | None, str | None]:
    """
    Make a GraphQL request to the specified endpoint.

    Args:
        endpoint: GraphQL API endpoint URL
        query: GraphQL query string
        variables: Query variables as a dictionary
        auth_token: Optional authorization token (Bearer token)

    Returns:
        Tuple of (Response JSON, error message) - one will be None
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
            return json.loads(response.read().decode("utf-8")), None
    except URLError as e:
        return None, f"Network error: {e.reason}"
    except json.JSONDecodeError as e:
        return None, f"Invalid response: {e}"
    except Exception as e:
        return None, f"Request error: {e}"


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

    # Base GraphQL variables
    variables = {
        "type": "ANIME",
        "per_page": 50,
        "genre_not_in": ["Hentai"],  # Default exclusion
    }
    
    # Add search query if provided
    if QUERY:
        variables["query"] = QUERY
    
    # Apply parsed filters from the filter syntax
    for key, value in PARSED_FILTERS.items():
        # Handle array merging for _in and _not_in fields
        if key.endswith("_in") or key.endswith("_not_in"):
            if key in variables:
                # Merge arrays, avoiding duplicates
                existing = set(variables[key])
                existing.update(value)
                variables[key] = list(existing)
            else:
                variables[key] = value
        else:
            variables[key] = value

    # Make the GraphQL request
    response, error = make_graphql_request(
        GRAPHQL_ENDPOINT, GRAPHQL_QUERY, variables, AUTH_HEADER
    )

    if error:
        print(f"❌ {error}")
        # Also show what we tried to search for debugging
        print(f"   Query: {QUERY or '(none)'}")
        print(f"   Filters: {json.dumps(PARSED_FILTERS) if PARSED_FILTERS else '(none)'}")
        sys.exit(1)

    if response is None:
        print("❌ Search failed: No response received")
        sys.exit(1)

    # Check for GraphQL errors first (these come in the response body)
    if "errors" in response:
        errors = response["errors"]
        if errors:
            # Extract error messages
            error_msgs = [e.get("message", str(e)) for e in errors]
            print(f"❌ API Error: {'; '.join(error_msgs)}")
            # Show variables for debugging
            print(f"   Filters used: {json.dumps(PARSED_FILTERS, indent=2) if PARSED_FILTERS else '(none)'}")
            sys.exit(1)

    # Save the raw response for later processing by dynamic_search.py
    try:
        with open(SEARCH_RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"❌ Failed to save results: {e}")
        sys.exit(1)

    # Navigate the response structure
    data = response.get("data", {})
    page = data.get("Page", {})
    media_list = page.get("media", [])

    if not media_list:
        print("🔍 No results found")
        if PARSED_FILTERS:
            print(f"   Try adjusting your filters")
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
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        sys.exit(1)
