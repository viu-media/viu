import json
import logging
from typing import Dict, Optional

from ..constants import APP_DATA_DIR, ASSETS_DIR

logger = logging.getLogger(__name__)

# Cache for the normalizer data to avoid repeated file reads
_normalizer_cache: Optional[Dict[str, Dict[str, str]]] = None

USER_NORMALIZER_JSON = APP_DATA_DIR / "normalizer.json"

DEFAULT_NORMALIZER_JSON = ASSETS_DIR / "normalizer.json"


# will load one in the config dir if available and merge them
def _load_normalizer_data() -> Dict[str, Dict[str, str]]:
    """
    Load the normalizer.json file and cache it.

    Returns:
        Dictionary containing provider mappings from normalizer.json

    Raises:
        FileNotFoundError: If normalizer.json is not found
        json.JSONDecodeError: If normalizer.json is malformed
    """
    global _normalizer_cache

    if _normalizer_cache is not None:
        return _normalizer_cache

    default_normalizer = {}
    user_normalizer = {}
    with open(DEFAULT_NORMALIZER_JSON, "r", encoding="utf-8") as f:
        default_normalizer: dict = json.load(f)
    if USER_NORMALIZER_JSON.exists():
        with open(USER_NORMALIZER_JSON, "r", encoding="utf-8") as f:
            user_normalizer: dict = json.load(f)

    _normalizer_cache = default_normalizer
    for key in default_normalizer:
        if key in user_normalizer:
            _normalizer_cache[key].update(user_normalizer[key])

    return _normalizer_cache


def update_user_normalizer_json(
    provider_title: str, media_api_title: str, provider_name: str
):
    from .file import AtomicWriter

    logger.info(f"Updating user normalizer JSON at: {USER_NORMALIZER_JSON}")

    if not _normalizer_cache:
        raise RuntimeError(
            "Fatal _normalizer_cache missing this should not be the case : (. Please report"
        )
    _normalizer_cache[provider_name][provider_title] = media_api_title.lower()
    with AtomicWriter(USER_NORMALIZER_JSON) as f:
        json.dump(_normalizer_cache, f, indent=2)


def provider_title_to_media_api_title(provider_title: str, provider_name: str) -> str:
    """
    Convert a provider title to its equivalent media API title.

    This function takes a title from a specific provider (e.g., "1P" from allanime)
    and converts it to the standard media API title (e.g., "one piece").

    Args:
        provider_title: The title as it appears on the provider
        provider_name: The name of the provider (e.g., "allanime", "hianime", "animepahe")

    Returns:
        The normalized media API title, or the original title if no mapping exists

    Example:
        >>> provider_title_to_media_api_title("1P", "allanime")
        "one piece"
        >>> provider_title_to_media_api_title("My Star", "hianime")
        "Oshi no Ko"
        >>> provider_title_to_media_api_title("Unknown Title", "allanime")
        "Unknown Title"
    """
    try:
        normalizer_data = _load_normalizer_data()

        # Check if the provider exists in the normalizer data
        if provider_name not in normalizer_data:
            logger.debug("Provider '%s' not found in normalizer data", provider_name)
            return provider_title

        provider_mappings = normalizer_data[provider_name]

        # Return the mapped title if it exists, otherwise return the original
        normalized_title = provider_mappings.get(provider_title, provider_title)

        if normalized_title != provider_title:
            logger.debug(
                "Normalized provider title: '%s' -> '%s' (provider: %s)",
                provider_title,
                normalized_title,
                provider_name,
            )

        return normalized_title

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Failed to load normalizer data: %s", e)
        return provider_title


def media_api_title_to_provider_title(media_api_title: str, provider_name: str) -> str:
    """
    Convert a media API title to its equivalent provider title.

    This function takes a standard media API title and converts it to the title
    used by a specific provider. This is the reverse operation of
    provider_title_to_media_api_title().

    Args:
        media_api_title: The title as it appears in the media API (e.g., AniList)
        provider_name: The name of the provider (e.g., "allanime", "hianime", "animepahe")

    Returns:
        The provider-specific title, or the original title if no mapping exists

    Example:
        >>> media_api_title_to_provider_title("one piece", "allanime")
        "1P"
        >>> media_api_title_to_provider_title("Oshi no Ko", "hianime")
        "My Star"
        >>> media_api_title_to_provider_title("Unknown Title", "allanime")
        "Unknown Title"
    """
    try:
        normalizer_data = _load_normalizer_data()

        # Check if the provider exists in the normalizer data
        if provider_name not in normalizer_data:
            logger.debug("Provider '%s' not found in normalizer data", provider_name)
            return media_api_title

        provider_mappings = normalizer_data[provider_name]

        # Create a reverse mapping (media_api_title -> provider_title)
        reverse_mappings = {v: k for k, v in provider_mappings.items()}

        # Return the mapped title if it exists, otherwise return the original
        provider_title = reverse_mappings.get(media_api_title, media_api_title)

        if provider_title != media_api_title:
            logger.debug(
                "Converted media API title to provider title: '%s' -> '%s' (provider: %s)",
                media_api_title,
                provider_title,
                provider_name,
            )

        return provider_title

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Failed to load normalizer data: %s", e)
        return media_api_title


def normalize_title(
    title: str, provider_name: str, use_provider_mapping: bool = False
) -> str:
    """
    Normalize a title for search operations.

    This convenience function determines the appropriate normalization direction
    based on the use_provider_mapping parameter.

    Args:
        title: The title to normalize
        provider_name: The name of the provider
        use_provider_mapping: If True, convert media API title to provider title.
                             If False, convert provider title to media API title.

    Returns:
        The normalized title

    Example:
        >>> normalize_title_for_search("one piece", "allanime", use_provider_mapping=True)
        "1P"
        >>> normalize_title_for_search("1P", "allanime", use_provider_mapping=False)
        "one piece"
    """
    if use_provider_mapping:
        return media_api_title_to_provider_title(title, provider_name)
    else:
        return provider_title_to_media_api_title(title, provider_name)


def get_available_providers() -> list[str]:
    """
    Get a list of all available providers in the normalizer data.

    Returns:
        List of provider names that have mappings defined

    Example:
        >>> get_available_providers()
        ['allanime', 'hianime', 'animepahe']
    """
    try:
        normalizer_data = _load_normalizer_data()
        return list(normalizer_data.keys())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Failed to load normalizer data: %s", e)
        return []


def clear_cache() -> None:
    """
    Clear the internal cache for normalizer data.

    This is useful for testing or when the normalizer.json file has been updated
    and you want to reload the data.
    """
    global _normalizer_cache
    _normalizer_cache = None
    logger.debug("Cleared normalizer cache")


def get_provider_mappings(provider_name: str) -> Dict[str, str]:
    """
    Get all title mappings for a specific provider.

    Args:
        provider_name: The name of the provider

    Returns:
        Dictionary mapping provider titles to media API titles

    Example:
        >>> mappings = get_provider_mappings("allanime")
        >>> print(mappings["1P"])
        "one piece"
    """
    try:
        normalizer_data = _load_normalizer_data()
        return normalizer_data.get(provider_name, {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Failed to load normalizer data: %s", e)
        return {}


def has_mapping(title: str, provider_name: str, reverse: bool = False) -> bool:
    """
    Check if a mapping exists for the given title and provider.

    Args:
        title: The title to check
        provider_name: The name of the provider
        reverse: If True, check for media API -> provider mapping.
                If False, check for provider -> media API mapping.

    Returns:
        True if a mapping exists, False otherwise

    Example:
        >>> has_mapping("1P", "allanime", reverse=False)
        True
        >>> has_mapping("one piece", "allanime", reverse=True)
        True
        >>> has_mapping("Unknown Title", "allanime", reverse=False)
        False
    """
    try:
        normalizer_data = _load_normalizer_data()

        if provider_name not in normalizer_data:
            return False

        provider_mappings = normalizer_data[provider_name]

        if reverse:
            # Check if title exists as a value (media API title)
            return title in provider_mappings.values()
        else:
            # Check if title exists as a key (provider title)
            return title in provider_mappings

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Failed to load normalizer data: %s", e)
        return False


def add_runtime_mapping(
    provider_title: str, media_api_title: str, provider_name: str
) -> None:
    """
    Add a new mapping at runtime (not persisted to file).

    This is useful for adding mappings discovered during runtime that
    are not present in the normalizer.json file.

    Args:
        provider_title: The provider-specific title
        media_api_title: The media API title
        provider_name: The name of the provider

    Note:
        This mapping is only stored in memory and will be lost when
        the cache is cleared or the application restarts.

    Example:
        >>> add_runtime_mapping("Custom Title", "Normalized Title", "allanime")
        >>> provider_title_to_media_api_title("Custom Title", "allanime")
        "Normalized Title"
    """
    try:
        normalizer_data = _load_normalizer_data()

        # Initialize provider if it doesn't exist
        if provider_name not in normalizer_data:
            normalizer_data[provider_name] = {}

        # Add the mapping
        normalizer_data[provider_name][provider_title] = media_api_title

        logger.info(
            "Added runtime mapping: '%s' -> '%s' (provider: %s)",
            provider_title,
            media_api_title,
            provider_name,
        )

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Failed to add runtime mapping: %s", e)
