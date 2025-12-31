import importlib
import importlib.util
import logging
import pkgutil
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, List, Optional, Union

import click

from ...core.config import AppConfig
from ...core.constants import APP_DIR, USER_CONFIG
from .state import InternalDirective, MenuName, State

if TYPE_CHECKING:
    from ...libs.media_api.base import BaseApiClient
    from ...libs.provider.anime.base import BaseAnimeProvider
    from ...libs.selectors.base import BaseSelector
    from ..service.auth import AuthService
    from ..service.feedback import FeedbackService
    from ..service.github import GitHubContributionService
    from ..service.player import PlayerService
    from ..service.registry import MediaRegistryService
    from ..service.session import SessionsService
    from ..service.watch_history import WatchHistoryService

logger = logging.getLogger(__name__)


MENUS_DIR = APP_DIR / "cli" / "interactive" / "menu"


@dataclass
class Switch:
    "Forces menus to show selector and not just pass through,once viewed it auto sets back to false"

    _provider_results: bool = False
    _episodes: bool = False
    _servers: bool = False
    _dont_play: bool = False

    @property
    def show_provider_results_menu(self):
        if self._provider_results:
            self._provider_results = False
            return True
        return False

    def force_provider_results_menu(self):
        self._provider_results = True

    @property
    def dont_play(self):
        if self._dont_play:
            self._dont_play = False
            return True
        return False

    def force_dont_play(self):
        self._dont_play = True

    @property
    def show_episodes_menu(self):
        if self._episodes:
            self._episodes = False
            return True
        return False

    def force_episodes_menu(self):
        self._episodes = True

    @property
    def servers(self):
        if self._servers:
            self._servers = False
            return True
        return False

    def force_servers_menu(self):
        self._servers = True


@dataclass
class Context:
    config: "AppConfig"
    switch: Switch = field(default_factory=Switch)
    _provider: Optional["BaseAnimeProvider"] = None
    _selector: Optional["BaseSelector"] = None
    _media_api: Optional["BaseApiClient"] = None

    _feedback: Optional["FeedbackService"] = None
    _media_registry: Optional["MediaRegistryService"] = None
    _watch_history: Optional["WatchHistoryService"] = None
    _session: Optional["SessionsService"] = None
    _auth: Optional["AuthService"] = None
    _player: Optional["PlayerService"] = None
    _github: Optional["GitHubContributionService"] = None

    @property
    def provider(self) -> "BaseAnimeProvider":
        if not self._provider:
            from ...libs.provider.anime.provider import create_provider

            self._provider = create_provider(self.config.general.provider)
        return self._provider

    @property
    def selector(self) -> "BaseSelector":
        if not self._selector:
            from ...libs.selectors.selector import create_selector

            self._selector = create_selector(self.config)
        return self._selector

    @property
    def media_api(self) -> "BaseApiClient":
        if not self._media_api:
            import httpx

            from ...libs.media_api.api import create_api_client

            media_api = create_api_client(self.config.general.media_api, self.config)

            auth = self.auth
            if auth_profile := auth.get_auth():
                try:
                    p = media_api.authenticate(auth_profile.token)
                    if p:
                        logger.debug(f"Authenticated as {p.name}")
                    else:
                        logger.warning(
                            f"Failed to authenticate with {auth_profile.token}"
                        )
                except httpx.ConnectError as e:
                    logger.warning(f"It seems you are offline: {e}")

            else:
                logger.debug("Not authenticated")
            self._media_api = media_api

        return self._media_api

    @property
    def player(self) -> "PlayerService":
        if not self._player:
            from ..service.player import PlayerService

            self._player = PlayerService(
                self.config, self.provider, self.media_registry
            )
        return self._player

    @property
    def feedback(self) -> "FeedbackService":
        if not self._feedback:
            from ..service.feedback.service import FeedbackService

            self._feedback = FeedbackService(self.config)
        return self._feedback

    @property
    def media_registry(self) -> "MediaRegistryService":
        if not self._media_registry:
            from ..service.registry.service import MediaRegistryService

            self._media_registry = MediaRegistryService(
                self.config.general.media_api, self.config.media_registry
            )
        return self._media_registry

    @property
    def watch_history(self) -> "WatchHistoryService":
        if not self._watch_history:
            from ..service.watch_history.service import WatchHistoryService

            self._watch_history = WatchHistoryService(
                self.config, self.media_registry, self.media_api
            )
        return self._watch_history

    @property
    def session(self) -> "SessionsService":
        if not self._session:
            from ..service.session.service import SessionsService

            self._session = SessionsService(self.config.sessions)
        return self._session

    @property
    def auth(self) -> "AuthService":
        if not self._auth:
            from ..service.auth.service import AuthService

            self._auth = AuthService(self.config.general.media_api)
        return self._auth

    @property
    def github(self) -> "GitHubContributionService":
        if not self._github:
            from ..service.github.service import GitHubContributionService

            self._github = GitHubContributionService(
                selector=self.selector,
                feedback=self.feedback,
            )
        return self._github


MenuFunction = Callable[[Context, State], Union[State, InternalDirective]]


@dataclass(frozen=True)
class Menu:
    name: MenuName
    execute: MenuFunction


class Session:
    _context: Context
    _history: List[State] = []
    _menus: dict[MenuName, Menu] = {}

    def _load_context(self, config: AppConfig):
        self._context = Context(config)
        logger.info("Application context reloaded.")

    def _edit_config(self):
        from ..config import ConfigLoader

        click.edit(filename=str(USER_CONFIG))
        logger.debug("Config changed; Reloading context")
        loader = ConfigLoader()
        config = loader.load()
        self._load_context(config)

    def run(
        self,
        config: AppConfig,
        resume: bool = False,
        history: Optional[List[State]] = None,
    ):
        self._load_context(config)
        if resume:
            if history := self._context.session.get_default_session_history():
                self._history = history
            else:
                logger.warning("Failed to continue from history. No sessions found")

        if history:
            self._history = history
        else:
            self._history.append(State(menu_name=MenuName.MAIN))

        try:
            self._run_main_loop()
        except Exception:
            self._context.session.create_crash_backup(self._history)
            raise
        finally:
            # Clean up preview workers when session ends
            self._cleanup_preview_workers()
        self._context.session.save_session(self._history)

    def _cleanup_preview_workers(self):
        """Clean up preview workers when session ends."""
        try:
            from ..utils.preview import shutdown_preview_workers

            shutdown_preview_workers(wait=False, timeout=5.0)
            logger.debug("Preview workers cleaned up successfully")
        except Exception as e:
            logger.warning(f"Failed to cleanup preview workers: {e}")

    def _run_main_loop(self):
        """Run the main session loop."""
        while self._history:
            current_state = self._history[-1]

            next_step = self._menus[current_state.menu_name].execute(
                self._context, current_state
            )

            if isinstance(next_step, InternalDirective):
                if next_step == InternalDirective.MAIN:
                    self._history = [self._history[0]]
                elif next_step == InternalDirective.RELOAD:
                    continue
                elif next_step == InternalDirective.CONFIG_EDIT:
                    self._edit_config()
                elif next_step == InternalDirective.BACK:
                    if len(self._history) > 1:
                        self._history.pop()
                elif next_step == InternalDirective.BACKX2:
                    if len(self._history) > 2:
                        self._history.pop()
                        self._history.pop()
                elif next_step == InternalDirective.BACKX3:
                    if len(self._history) > 3:
                        self._history.pop()
                        self._history.pop()
                        self._history.pop()
                elif next_step == InternalDirective.BACKX4:
                    if len(self._history) > 4:
                        self._history.pop()
                        self._history.pop()
                        self._history.pop()
                        self._history.pop()
                elif next_step == InternalDirective.EXIT:
                    break
            else:
                self._history.append(next_step)

    @property
    def menu(self) -> Callable[[MenuFunction], MenuFunction]:
        """A decorator to register a function as a menu."""

        def decorator(func: MenuFunction) -> MenuFunction:
            menu_name = MenuName(func.__name__.upper())
            if menu_name in self._menus:
                logger.warning(f"Menu '{menu_name}' is being redefined.")
            self._menus[menu_name] = Menu(name=menu_name, execute=func)
            return func

        return decorator

    def load_menus_from_folder(self, package: str):
        """Load menu modules from a subfolder.
        
        Uses pkgutil to discover modules for regular Python, and falls back
        to the package's __all__ list for PyInstaller frozen executables.
        """
        full_package_name = f"viu_media.cli.interactive.menu.{package}"
        logger.debug(f"Loading menus from package '{full_package_name}'...")

        try:
            # Import the parent package first
            parent_package = importlib.import_module(full_package_name)
        except ImportError as e:
            logger.error(f"Failed to import menu package '{full_package_name}': {e}")
            return

        # Try pkgutil first (works in regular Python)
        package_path = getattr(parent_package, "__path__", None)
        module_names = []
        
        if package_path:
            module_names = [
                name for _, name, ispkg in pkgutil.iter_modules(package_path)
                if not ispkg and not name.startswith("_")
            ]
        
        # Fallback to __all__ for PyInstaller frozen executables
        if not module_names:
            module_names = getattr(parent_package, "__all__", [])
            logger.debug(f"Using __all__ fallback with {len(module_names)} modules")

        for module_name in module_names:
            full_module_name = f"{full_package_name}.{module_name}"
            try:
                # Simply importing the module will execute it,
                # which runs the @session.menu decorators
                importlib.import_module(full_module_name)
            except Exception as e:
                logger.error(
                    f"Failed to load menu module '{full_module_name}': {e}"
                )


# Create a single, global instance of the Session to be imported by menu modules.
session = Session()
