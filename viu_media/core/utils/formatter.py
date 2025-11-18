import re
from datetime import datetime
from typing import Dict, List, Optional, Union

from ...libs.media_api.types import AiringSchedule

COMMA_REGEX = re.compile(r"([0-9]{3})(?=\d)")
SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'


def format_media_duration(total_minutes: Optional[int]) -> str:
    """
    Converts a duration in minutes into a more human-readable format
    (e.g., "1 hour 30 minutes", "45 minutes", "2 hours").

    Args:
        total_minutes: The total duration in minutes (integer).

    Returns:
        A string representing the formatted duration.
    """
    if not total_minutes:
        return "N/A"

    if not isinstance(total_minutes, int) or total_minutes < 0:
        raise ValueError("Input must be a non-negative integer representing minutes.")

    if total_minutes == 0:
        return "0 minutes"

    hours = total_minutes // 60
    minutes = total_minutes % 60

    parts = []

    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")

    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

    # Join the parts with " and " if both hours and minutes are present
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    elif len(parts) == 1:
        return parts[0]
    else:
        # This case should ideally not be reached if total_minutes > 0
        return "0 minutes"  # Fallback for safety, though handled by initial check


def format_date(dt: Optional[datetime], format_str: str = "%A, %d %B %Y") -> str:
    """
    Formats a datetime object to a readable string.

    Default format: '2025-22 July'

    Params:
        dt (datetime): The datetime object to format.
        format_str (str): Optional custom format string (defaults to "%Y-%d %B").

    Returns:
        str: The formatted date.
    """
    if not dt:
        return "N/A"
    return dt.strftime(format_str)


def format_time(duration_in_secs: float) -> str:
    """Format duration in seconds to HH:MM:SS format."""
    h = int(duration_in_secs // 3600)
    m = int((duration_in_secs % 3600) // 60)
    s = int(duration_in_secs % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _htmlentity_transform(entity_with_semicolon):
    import contextlib
    import html.entities
    import html.parser

    """Transforms an HTML entity to a character."""
    entity = entity_with_semicolon[:-1]

    # Known non-numeric HTML entity
    if entity in html.entities.name2codepoint:
        return chr(html.entities.name2codepoint[entity])

    # TODO: HTML5 allows entities without a semicolon.
    # E.g. '&Eacuteric' should be decoded as 'Éric'.
    if entity_with_semicolon in html.entities.html5:
        return html.entities.html5[entity_with_semicolon]

    mobj = re.match(r"#(x[0-9a-fA-F]+|[0-9]+)", entity)
    if mobj is not None:
        numstr = mobj.group(1)
        if numstr.startswith("x"):
            base = 16
            numstr = f"0{numstr}"
        else:
            base = 10
        # See https://github.com/ytdl-org/youtube-dl/issues/7518
        with contextlib.suppress(ValueError):
            return chr(int(numstr, base))

    # Unknown entity in name, return its literal representation
    return f"&{entity};"


def unescapeHTML(s: str):
    if s is None:
        return None
    assert isinstance(s, str)

    return re.sub(r"&([^&;]+;)", lambda m: _htmlentity_transform(m.group(1)), s)


def escapeHTML(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def clean_html(html: Optional[str]):
    """Clean an HTML snippet into a readable string"""

    if html is None:  # Convenience for sanitizing descriptions etc.
        return html

    html = re.sub(r"\s+", " ", html)
    html = re.sub(r"(?u)\s?<\s?br\s?/?\s?>\s?", "\n", html)
    html = re.sub(r"(?u)<\s?/\s?p\s?>\s?<\s?p[^>]*>", "\n", html)
    # Strip html tags
    html = re.sub("<.*?>", "", html)
    # Replace html entities
    html = unescapeHTML(html)
    return html.strip()


def format_number_with_commas(number: Optional[int]) -> str:
    """Formats an integer with commas for thousands separation."""
    if number is None:
        return "N/A"
    return COMMA_REGEX.sub(r"\1,", str(number)[::-1])[::-1]


def format_airing_schedule(airing: Optional[AiringSchedule]) -> str:
    """Formats the next airing episode information into a readable string."""
    if not airing or not airing.airing_at:
        return "N/A"

    # Get a human-readable date and time
    air_date = airing.airing_at.strftime("%a, %b %d at %I:%M %p")
    return f"Ep {airing.episode} on {air_date}"


def format_list_with_commas(list_of_strs: List[str]) -> str:
    """Joins a list of genres into a single, comma-separated string."""
    return ", ".join(list_of_strs) if list_of_strs else "N/A"


def format_score_stars_full(score: Optional[float]) -> str:
    """Formats an AniList score (0-100) to a 0-10 scale using full stars."""
    if score is None:
        return "N/A"

    # Convert 0-100 to 0-10, then to a whole number of stars
    num_stars = min(round(score * 6 / 100), 6)
    return "⭐" * num_stars


def format_score(score: Optional[float]) -> str:
    """Formats an AniList score (0-100) to a 0-10 scale."""
    if score is None:
        return "N/A"
    return f"{score / 10.0:.1f} / 10"


def shell_safe(text: Optional[str]) -> str:
    """
    Escapes a string for safe inclusion in a shell script,
    specifically for use within double quotes. It escapes backticks,
    double quotes, and dollar signs.
    """
    if not text:
        return ""
    return text.replace("`", "\\`").replace('"', '\\"').replace("$", "\\$")


def extract_episode_number(title: str) -> Optional[float]:
    """
    Extracts the episode number (supports floats) from a title like:
    "Episode 2.5 - Some Title". Returns None if no match.
    """
    match = re.search(r"Episode\s+([0-9]+(?:\.[0-9]+)?)", title, re.IGNORECASE)
    if match:
        return round(float(match.group(1)), 3)
    return None


def strip_original_episode_prefix(title: str) -> str:
    """
    Removes the original 'Episode X' prefix from the title.
    """
    return re.sub(
        r"^Episode\s+[0-9]+(?:\.[0-9]+)?\s*[-:–]?\s*", "", title, flags=re.IGNORECASE
    )


def renumber_titles(titles: List[str]) -> Dict[str, Union[int, float, None]]:
    """
    Extracts and renumbers episode numbers from titles starting at 1.
    Preserves fractional spacing and leaves titles without episode numbers untouched.

    Returns a dict: {original_title: new_episode_number or None}
    """
    # Separate titles with and without numbers
    with_numbers = [(t, extract_episode_number(t)) for t in titles]
    with_numbers = [(t, n) for t, n in with_numbers if n is not None]
    without_numbers = [t for t in titles if extract_episode_number(t) is None]

    # Sort numerically
    with_numbers.sort(key=lambda x: x[1])

    renumbered = {}
    base_map = {}
    next_index = 1

    for title, orig_ep in with_numbers:
        int_part = int(orig_ep)
        is_whole = orig_ep == int_part

        if is_whole:
            base_map[int_part] = next_index
            renumbered_val = next_index
            next_index += 1
        else:
            base_val = base_map.get(int_part, next_index - 1)
            offset = round(orig_ep - int_part, 3)
            renumbered_val = round(base_val + offset, 3)

        renumbered[title] = renumbered_val

    # Add back the unnumbered titles with `None`
    for t in without_numbers:
        renumbered[t] = None

    return renumbered
