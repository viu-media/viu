#!/usr/bin/env python3
"""
Filter Parser for Dynamic Search

This module provides a parser for the special filter syntax used in dynamic search.
Filter syntax allows users to add filters inline with their search query.

SYNTAX:
    @filter:value       - Apply a filter with the given value
    @filter:value1,value2 - Apply multiple values (for array filters)
    @filter:!value      - Exclude/negate a filter value
    
SUPPORTED FILTERS:
    @genre:action,comedy        - Filter by genres
    @genre:!hentai              - Exclude genre
    @status:airing              - Filter by status (airing, finished, upcoming, cancelled, hiatus)
    @year:2024                  - Filter by season year
    @season:winter              - Filter by season (winter, spring, summer, fall)
    @format:tv,movie            - Filter by format (tv, movie, ova, ona, special, music)
    @sort:score                 - Sort by (score, popularity, trending, title, date)
    @score:>80                  - Minimum score
    @score:<50                  - Maximum score
    @popularity:>10000          - Minimum popularity
    @onlist                     - Only show anime on user's list
    @onlist:false               - Only show anime NOT on user's list

EXAMPLES:
    "naruto @genre:action @status:finished"
    "isekai @year:2024 @season:winter @sort:score"
    "@genre:action,adventure @status:airing"
    "romance @genre:!hentai @format:tv,movie"
"""

import re
from typing import Any, Dict, List, Optional, Tuple

# Mapping of user-friendly filter names to GraphQL variable names
FILTER_ALIASES = {
    # Status aliases
    "airing": "RELEASING",
    "releasing": "RELEASING",
    "finished": "FINISHED",
    "completed": "FINISHED",
    "upcoming": "NOT_YET_RELEASED",
    "not_yet_released": "NOT_YET_RELEASED",
    "unreleased": "NOT_YET_RELEASED",
    "cancelled": "CANCELLED",
    "canceled": "CANCELLED",
    "hiatus": "HIATUS",
    "paused": "HIATUS",
    # Format aliases
    "tv": "TV",
    "tv_short": "TV_SHORT",
    "tvshort": "TV_SHORT",
    "movie": "MOVIE",
    "film": "MOVIE",
    "ova": "OVA",
    "ona": "ONA",
    "special": "SPECIAL",
    "music": "MUSIC",
    # Season aliases
    "winter": "WINTER",
    "spring": "SPRING",
    "summer": "SUMMER",
    "fall": "FALL",
    "autumn": "FALL",
    # Sort aliases
    "score": "SCORE_DESC",
    "score_desc": "SCORE_DESC",
    "score_asc": "SCORE",
    "popularity": "POPULARITY_DESC",
    "popularity_desc": "POPULARITY_DESC",
    "popularity_asc": "POPULARITY",
    "trending": "TRENDING_DESC",
    "trending_desc": "TRENDING_DESC",
    "trending_asc": "TRENDING",
    "title": "TITLE_ROMAJI",
    "title_desc": "TITLE_ROMAJI_DESC",
    "date": "START_DATE_DESC",
    "date_desc": "START_DATE_DESC",
    "date_asc": "START_DATE",
    "newest": "START_DATE_DESC",
    "oldest": "START_DATE",
    "favourites": "FAVOURITES_DESC",
    "favorites": "FAVOURITES_DESC",
    "episodes": "EPISODES_DESC",
}

# Genre name normalization (lowercase -> proper case)
GENRE_NAMES = {
    "action": "Action",
    "adventure": "Adventure",
    "comedy": "Comedy",
    "drama": "Drama",
    "ecchi": "Ecchi",
    "fantasy": "Fantasy",
    "horror": "Horror",
    "mahou_shoujo": "Mahou Shoujo",
    "mahou": "Mahou Shoujo",
    "magical_girl": "Mahou Shoujo",
    "mecha": "Mecha",
    "music": "Music",
    "mystery": "Mystery",
    "psychological": "Psychological",
    "romance": "Romance",
    "sci-fi": "Sci-Fi",
    "scifi": "Sci-Fi",
    "sci_fi": "Sci-Fi",
    "slice_of_life": "Slice of Life",
    "sol": "Slice of Life",
    "sports": "Sports",
    "supernatural": "Supernatural",
    "thriller": "Thriller",
    "hentai": "Hentai",
}

# Filter pattern: @key:value or @key (boolean flags)
FILTER_PATTERN = re.compile(r"@(\w+)(?::([^\s]+))?", re.IGNORECASE)

# Comparison operators for numeric filters
COMPARISON_PATTERN = re.compile(r"^([<>]=?)?(\d+)$")


def normalize_value(value: str, value_type: str) -> str:
    """Normalize a filter value based on its type."""
    value_lower = value.lower().strip()
    
    if value_type == "genre":
        return GENRE_NAMES.get(value_lower, value.title())
    elif value_type in ("status", "format", "season", "sort"):
        return FILTER_ALIASES.get(value_lower, value.upper())
    
    return value


def parse_value_list(value_str: str) -> Tuple[List[str], List[str]]:
    """
    Parse a comma-separated value string, separating includes from excludes.
    
    Returns:
        Tuple of (include_values, exclude_values)
    """
    includes = []
    excludes = []
    
    for val in value_str.split(","):
        val = val.strip()
        if not val:
            continue
        if val.startswith("!"):
            excludes.append(val[1:])
        else:
            includes.append(val)
    
    return includes, excludes


def parse_comparison(value: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Parse a comparison value like ">80" or "<50".
    
    Returns:
        Tuple of (operator, number) or (None, None) if invalid
    """
    match = COMPARISON_PATTERN.match(value)
    if match:
        operator = match.group(1) or ">"  # Default to greater than
        number = int(match.group(2))
        return operator, number
    return None, None


def parse_filters(query: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse a search query and extract filter directives.
    
    Args:
        query: The full search query including filter syntax
        
    Returns:
        Tuple of (clean_query, filters_dict)
        - clean_query: The query with filter syntax removed
        - filters_dict: Dictionary of GraphQL variables to apply
    """
    filters: Dict[str, Any] = {}
    
    # Find all filter matches
    matches = list(FILTER_PATTERN.finditer(query))
    
    for match in matches:
        filter_name = match.group(1).lower()
        filter_value = match.group(2)  # May be None for boolean flags
        
        # Handle different filter types
        if filter_name == "genre":
            if filter_value:
                includes, excludes = parse_value_list(filter_value)
                if includes:
                    normalized = [normalize_value(v, "genre") for v in includes]
                    filters.setdefault("genre_in", []).extend(normalized)
                if excludes:
                    normalized = [normalize_value(v, "genre") for v in excludes]
                    filters.setdefault("genre_not_in", []).extend(normalized)
        
        elif filter_name == "status":
            if filter_value:
                includes, excludes = parse_value_list(filter_value)
                if includes:
                    normalized = [normalize_value(v, "status") for v in includes]
                    filters.setdefault("status_in", []).extend(normalized)
                if excludes:
                    normalized = [normalize_value(v, "status") for v in excludes]
                    filters.setdefault("status_not_in", []).extend(normalized)
        
        elif filter_name == "format":
            if filter_value:
                includes, _ = parse_value_list(filter_value)
                if includes:
                    normalized = [normalize_value(v, "format") for v in includes]
                    filters.setdefault("format_in", []).extend(normalized)
        
        elif filter_name == "year":
            if filter_value:
                try:
                    filters["seasonYear"] = int(filter_value)
                except ValueError:
                    pass  # Invalid year, skip
        
        elif filter_name == "season":
            if filter_value:
                filters["season"] = normalize_value(filter_value, "season")
        
        elif filter_name == "sort":
            if filter_value:
                sort_val = normalize_value(filter_value, "sort")
                filters["sort"] = [sort_val]
        
        elif filter_name == "score":
            if filter_value:
                op, num = parse_comparison(filter_value)
                if num is not None:
                    if op in (">", ">="):
                        filters["averageScore_greater"] = num
                    elif op in ("<", "<="):
                        filters["averageScore_lesser"] = num
        
        elif filter_name == "popularity":
            if filter_value:
                op, num = parse_comparison(filter_value)
                if num is not None:
                    if op in (">", ">="):
                        filters["popularity_greater"] = num
                    elif op in ("<", "<="):
                        filters["popularity_lesser"] = num
        
        elif filter_name == "onlist":
            if filter_value is None or filter_value.lower() in ("true", "yes", "1"):
                filters["on_list"] = True
            elif filter_value.lower() in ("false", "no", "0"):
                filters["on_list"] = False
        
        elif filter_name == "tag":
            if filter_value:
                includes, excludes = parse_value_list(filter_value)
                if includes:
                    # Tags use title case typically
                    normalized = [v.replace("_", " ").title() for v in includes]
                    filters.setdefault("tag_in", []).extend(normalized)
                if excludes:
                    normalized = [v.replace("_", " ").title() for v in excludes]
                    filters.setdefault("tag_not_in", []).extend(normalized)
    
    # Remove filter syntax from query to get clean search text
    clean_query = FILTER_PATTERN.sub("", query).strip()
    # Clean up multiple spaces
    clean_query = re.sub(r"\s+", " ", clean_query).strip()
    
    return clean_query, filters


def get_help_text() -> str:
    """Return a help string describing the filter syntax."""
    return """
╭─────────────────── Filter Syntax Help ───────────────────╮
│                                                          │
│  @genre:action,comedy     Filter by genres               │
│  @genre:!hentai           Exclude genre                  │
│  @status:airing           Status: airing, finished,      │
│                           upcoming, cancelled, hiatus    │
│  @year:2024               Filter by year                 │
│  @season:winter           winter, spring, summer, fall   │
│  @format:tv,movie         tv, movie, ova, ona, special   │
│  @sort:score              score, popularity, trending,   │
│                           date, title, newest, oldest    │
│  @score:>80               Minimum score                  │
│  @score:<50               Maximum score                  │
│  @popularity:>10000       Minimum popularity             │
│  @onlist                  Only on your list              │
│  @onlist:false            Not on your list               │
│  @tag:isekai,reincarnation Filter by tags                │
│                                                          │
│  Examples:                                               │
│    naruto @genre:action @status:finished                 │
│    @genre:action,adventure @year:2024 @sort:score        │
│    isekai @season:winter @year:2024                      │
│                                                          │
╰──────────────────────────────────────────────────────────╯
""".strip()


if __name__ == "__main__":
    # Test the parser
    import json
    import sys
    
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
        clean, filters = parse_filters(test_query)
        print(f"Original: {test_query}")
        print(f"Clean query: {clean}")
        print(f"Filters: {json.dumps(filters, indent=2)}")
    else:
        print(get_help_text())
