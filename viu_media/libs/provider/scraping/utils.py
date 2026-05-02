"""
Encoding and utility functions for web scraping.

Provides various encoding utilities including base-N encoding
that was previously sourced from yt-dlp.
"""

import string
from typing import Optional


def encode_base_n(num: int, n: int, table: Optional[str] = None) -> str:
    """
    Encode a number in base-n representation.

    Args:
        num: The number to encode
        n: The base to use for encoding
        table: Custom character table (optional)

    Returns:
        String representation of the number in base-n

    Examples:
        >>> encode_base_n(255, 16)
        'ff'
        >>> encode_base_n(42, 36)
        '16'
    """
    if table is None:
        # Default table: 0-9, a-z
        table = string.digits + string.ascii_lowercase

    if not 2 <= n <= len(table):
        raise ValueError(f"Base must be between 2 and {len(table)}")

    if num == 0:
        return table[0]

    result = []
    is_negative = num < 0
    num = abs(num)

    while num > 0:
        result.append(table[num % n])
        num //= n

    if is_negative:
        result.append("-")

    return "".join(reversed(result))


def decode_base_n(encoded: str, n: int, table: Optional[str] = None) -> int:
    """
    Decode a base-n encoded string back to an integer.

    Args:
        encoded: The base-n encoded string
        n: The base used for encoding
        table: Custom character table (optional)

    Returns:
        The decoded integer

    Examples:
        >>> decode_base_n('ff', 16)
        255
        >>> decode_base_n('16', 36)
        42
    """
    if table is None:
        table = string.digits + string.ascii_lowercase

    if not 2 <= n <= len(table):
        raise ValueError(f"Base must be between 2 and {len(table)}")

    if not encoded:
        return 0

    is_negative = encoded.startswith("-")
    if is_negative:
        encoded = encoded[1:]

    result = 0
    for i, char in enumerate(reversed(encoded.lower())):
        if char not in table:
            raise ValueError(f"Invalid character '{char}' for base {n}")

        digit_value = table.index(char)
        if digit_value >= n:
            raise ValueError(f"Invalid digit '{char}' for base {n}")

        result += digit_value * (n**i)

    return -result if is_negative else result


def url_encode(text: str, safe: str = "") -> str:
    """
    URL encode a string.

    Args:
        text: Text to encode
        safe: Characters that should not be encoded

    Returns:
        URL encoded string
    """
    import urllib.parse

    return urllib.parse.quote(text, safe=safe)


def url_decode(text: str) -> str:
    """
    URL decode a string.

    Args:
        text: URL encoded text to decode

    Returns:
        Decoded string
    """
    import urllib.parse

    return urllib.parse.unquote(text)


def html_unescape(text: str) -> str:
    """
    Unescape HTML entities in text.

    Args:
        text: Text containing HTML entities

    Returns:
        Text with HTML entities unescaped

    Examples:
        >>> html_unescape('&quot;Hello&quot; &amp; &lt;World&gt;')
        '"Hello" & <World>'
    """
    import html

    return html.unescape(text)


def strip_tags(html_content: str) -> str:
    """
    Remove all HTML tags from content, leaving only text.

    Args:
        html_content: HTML content with tags

    Returns:
        Plain text with tags removed

    Examples:
        >>> strip_tags('<p>Hello <b>world</b>!</p>')
        'Hello world!'
    """
    import re

    return re.sub(r"<[^>]+>", "", html_content)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text by collapsing multiple spaces and removing leading/trailing whitespace.

    Args:
        text: Text to normalize

    Returns:
        Text with normalized whitespace

    Examples:
        >>> normalize_whitespace('  Hello    world  \\n\\t  ')
        'Hello world'
    """
    import re

    return re.sub(r"\s+", " ", text.strip())


def extract_domain(url: str) -> str:
    """
    Extract domain from a URL.

    Args:
        url: Full URL

    Returns:
        Domain portion of the URL

    Examples:
        >>> extract_domain('https://example.com/path?query=1')
        'example.com'
    """
    import urllib.parse

    parsed = urllib.parse.urlparse(url)
    return parsed.netloc


def join_url(base: str, path: str) -> str:
    """
    Join a base URL with a path.

    Args:
        base: Base URL
        path: Path to join

    Returns:
        Combined URL

    Examples:
        >>> join_url('https://example.com', '/api/data')
        'https://example.com/api/data'
    """
    import urllib.parse

    return urllib.parse.urljoin(base, path)


def parse_query_string(query: str) -> dict:
    """
    Parse a query string into a dictionary.

    Args:
        query: Query string (with or without leading '?')

    Returns:
        Dictionary of query parameters

    Examples:
        >>> parse_query_string('?name=John&age=30')
        {'name': ['John'], 'age': ['30']}
    """
    import urllib.parse

    if query.startswith("?"):
        query = query[1:]
    return urllib.parse.parse_qs(query)


def build_query_string(params: dict) -> str:
    """
    Build a query string from a dictionary of parameters.

    Args:
        params: Dictionary of parameters

    Returns:
        URL-encoded query string

    Examples:
        >>> build_query_string({'name': 'John', 'age': 30})
        'name=John&age=30'
    """
    import urllib.parse

    # Handle both single values and lists
    normalized_params = {}
    for key, value in params.items():
        if isinstance(value, (list, tuple)):
            normalized_params[key] = value
        else:
            normalized_params[key] = [str(value)]

    return urllib.parse.urlencode(normalized_params, doseq=True)
