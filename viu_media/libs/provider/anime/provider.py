import importlib
import logging

from httpx import Client

from .base import BaseAnimeProvider
from .types import ProviderName

logger = logging.getLogger(__name__)

PROVIDERS_AVAILABLE = {
    "allanime": "provider.AllAnime",
    "animepahe": "provider.AnimePahe",
    "hianime": "provider.HiAnime",
    "nyaa": "provider.Nyaa",
    "yugen": "provider.Yugen",
    "animeunity": "provider.AnimeUnity",
}


class AnimeProviderFactory:
    """Factory for creating anime provider instances."""

    @staticmethod
    def create(provider_name: ProviderName) -> BaseAnimeProvider:
        """
        Dynamically creates an instance of the specified anime provider.

        This method imports the necessary provider module, instantiates its main class,
        and injects a pre-configured HTTP client.

        Args:
            provider_name: The name of the provider to create (e.g., 'allanime').

        Returns:
            An instance of a class that inherits from BaseProvider.

        Raises:
            ValueError: If the provider_name is not supported.
            ImportError: If the provider module or class cannot be found.
        """
        from ....core.utils.networking import random_user_agent

        # Correctly determine module and class name from the map
        import_path = PROVIDERS_AVAILABLE[provider_name.value.lower()]
        module_name, class_name = import_path.split(".", 1)

        # Construct the full package path for dynamic import
        package_path = f"viu_media.libs.provider.anime.{provider_name.value.lower()}"

        try:
            provider_module = importlib.import_module(f".{module_name}", package_path)
            provider_class = getattr(provider_module, class_name)
        except (ImportError, AttributeError) as e:
            logger.error(
                f"Failed to load provider '{provider_name.value.lower()}': {e}"
            )
            raise ImportError(
                f"Could not load provider '{provider_name.value.lower()}'. "
                "Check the module path and class name in PROVIDERS_AVAILABLE."
            ) from e

        # Each provider class requires an httpx.Client, which we set up here.
        client = Client(
            headers={"User-Agent": random_user_agent(), **provider_class.HEADERS}
        )

        return provider_class(client)


# Simple alias for ease of use, consistent with other factories in the codebase.
create_provider = AnimeProviderFactory.create
