import logging
from pathlib import Path
from typing import Optional

import httpx
from viu_media.cli.service.registry import MediaRegistryService
from viu_media.cli.service.registry.models import DownloadStatus
from viu_media.core.config.model import AppConfig
from viu_media.core.constants import APP_CACHE_DIR
from viu_media.libs.media_api.base import BaseApiClient
from viu_media.libs.media_api.types import MediaItem, Notification

try:
    from plyer import notification as plyer_notification

    PLYER_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    plyer_notification = None  # type: ignore[assignment]
    PLYER_AVAILABLE = False

logger = logging.getLogger(__name__)

NOTIFICATION_ICONS_CACHE_DIR = APP_CACHE_DIR / "notification_icons"


class NotificationService:
    def __init__(
        self,
        app_config: AppConfig,
        media_api: BaseApiClient,
        registry_service: MediaRegistryService,
    ):
        self.media_api = media_api
        self.app_config = app_config
        self.registry = registry_service

    def _mark_seen(self, notification_id: int, media_id: int, episode: str | None):
        if self.registry and episode:
            try:
                self.registry.update_media_index_entry(
                    media_id, last_notified_episode=str(episode)
                )
            except Exception:
                logger.debug("Failed to update last_notified_episode in registry")

    def check_and_display_notifications(self):
        if not PLYER_AVAILABLE:
            logger.warning("plyer not installed. Cannot display desktop notifications.")
            return

        if not self.media_api.is_authenticated():
            logger.info("Not authenticated, skipping notification check.")
            return

        logger.info("Checking for new notifications...")
        notifications = self.media_api.get_notifications()

        if not notifications:
            logger.info("No new notifications found.")
            return

        # Filter out notifications already seen in this session or older than registry marker
        filtered: list[Notification] = []
        for n in notifications:
            if self._is_seen_in_registry(n.media.id, n.episode):
                continue
            filtered.append(n)

        if not filtered:
            logger.info("No unseen notifications found.")
            return

        for notif in filtered:
            if self.app_config.worker.auto_download_new_episode:
                if not self.registry.get_media_record(notif.media.id):
                    self.registry.get_or_create_record(notif.media)
                self.registry.update_episode_download_status(
                    media_id=notif.media.id,
                    episode_number=str(notif.episode),
                    status=DownloadStatus.QUEUED,
                )
            title = notif.media.title.english or notif.media.title.romaji
            message = f"Episode {notif.episode} of {title} has aired!"

            # Try to include an image (cover large/extra_large) if available
            app_icon: Optional[str] = None
            try:
                icon_path = self._get_or_fetch_icon(notif.media)
                app_icon = str(icon_path) if icon_path else None
            except Exception:
                app_icon = None

            try:
                # Guard: only call if available
                if not PLYER_AVAILABLE or plyer_notification is None:
                    raise RuntimeError("Notification backend unavailable")
                # Assert for type checkers and runtime safety
                assert plyer_notification is not None
                plyer_notification.notify(  # type: ignore
                    title="Viu: New Episode",
                    message=message,
                    app_name="Viu",
                    app_icon=app_icon,  # plyer supports file paths or URLs depending on platform
                    timeout=self.app_config.general.desktop_notification_duration,
                )
                logger.info(f"Displayed notification: {message}")
                self._mark_seen(
                    notif.id,
                    notif.media.id,
                    str(notif.episode) if notif.episode is not None else None,
                )
            except Exception as e:
                logger.error(f"Failed to display notification: {e}")

    def _is_seen_in_registry(self, media_id: int, episode: Optional[int]) -> bool:
        if episode is None:
            return False
        try:
            entry = self.registry.get_media_index_entry(media_id)
            if not entry or not entry.last_notified_episode:
                return False
            # Compare numerically
            try:
                last_ep = float(entry.last_notified_episode)
                return float(episode) <= last_ep
            except Exception:
                return False
        except Exception:
            return False

    def _get_or_fetch_icon(self, media_item: MediaItem) -> Optional[Path]:
        """Fetch and cache a small cover image for system notifications."""
        try:
            cover = media_item.cover_image
            url = None
            if cover:
                url = cover.extra_large or cover.large or cover.medium
            if not url:
                return None

            cache_dir = NOTIFICATION_ICONS_CACHE_DIR
            cache_dir.mkdir(parents=True, exist_ok=True)
            icon_path = cache_dir / f"{media_item.id}.png"
            if icon_path.exists() and icon_path.stat().st_size > 0:
                return icon_path

            # Directly download the image bytes without resizing
            with httpx.Client(follow_redirects=True, timeout=20) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.content
                if data:
                    icon_path.write_bytes(data)
                    return icon_path
        except Exception as e:
            logger.debug(f"Could not fetch icon for media {media_item.id}: {e}")
        return None
