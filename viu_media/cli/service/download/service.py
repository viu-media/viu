import logging
from pathlib import Path
from typing import TYPE_CHECKING, List

from viu_media.cli.utils.search import find_best_match_title

from ....core.config.model import AppConfig
from ....core.constants import APP_CACHE_DIR
from ....core.downloader import DownloadParams, create_downloader
from ....core.utils.concurrency import ManagedBackgroundWorker, thread_manager
from ....core.utils.normalizer import normalize_title
from ....libs.media_api.types import MediaItem
from ....libs.provider.anime.params import (
    AnimeParams,
    EpisodeStreamsParams,
    SearchParams,
)
from ..registry.models import DownloadStatus

if TYPE_CHECKING:
    from ....libs.media_api.api import BaseApiClient
    from ....libs.provider.anime.provider import BaseAnimeProvider
    from ..registry.service import MediaRegistryService


logger = logging.getLogger(__name__)
NOTIFICATION_ICONS_CACHE_DIR = APP_CACHE_DIR / "notification_icons"


class DownloadService:
    def __init__(
        self,
        config: AppConfig,
        registry_service: "MediaRegistryService",
        media_api_service: "BaseApiClient",
        provider_service: "BaseAnimeProvider",
    ):
        self.app_config = config
        self.registry = registry_service
        self.media_api = media_api_service
        self.provider = provider_service
        self.downloader = create_downloader(config.downloads)
        # Track in-flight downloads to avoid duplicate queueing
        self._inflight: set[tuple[int, str]] = set()

        self._worker = ManagedBackgroundWorker(
            max_workers=config.downloads.max_concurrent_downloads,
            name="DownloadWorker",
        )
        thread_manager.register_worker("download_worker", self._worker)

    def start(self):
        """Starts the download worker for background tasks."""
        if not self._worker.is_running():
            self._worker.start()
        # We can still resume background tasks on startup if any exist
        self.resume_unfinished_downloads()

    def stop(self):
        """Stops the download worker."""
        self._worker.shutdown(wait=False)

    def add_to_queue(self, media_item: MediaItem, episode_number: str) -> bool:
        """Mark an episode as queued in the registry (no immediate download)."""
        logger.info(
            f"Queueing episode '{episode_number}' for '{media_item.title.english}' (registry only)"
        )
        self.registry.get_or_create_record(media_item)
        return self.registry.update_episode_download_status(
            media_id=media_item.id,
            episode_number=episode_number,
            status=DownloadStatus.QUEUED,
        )

    def _submit_download(self, media_item: MediaItem, episode_number: str) -> bool:
        """Submit a download task to the worker if not already in-flight."""
        key = (media_item.id, str(episode_number))
        if key in self._inflight:
            return False
        if not self._worker.is_running():
            self._worker.start()
        self._inflight.add(key)
        self._worker.submit_function(
            self._execute_download_job, media_item, episode_number
        )
        return True

    def download_episodes_sync(self, media_item: MediaItem, episodes: List[str]):
        """
        Performs downloads SYNCHRONOUSLY and blocks until complete.
        This is for the direct `download` command.
        """
        for episode_number in episodes:
            title = (
                media_item.title.english
                or media_item.title.romaji
                or f"ID: {media_item.id}"
            )
            logger.info(
                f"Starting synchronous download for '{title}' Episode {episode_number}"
            )
            self._execute_download_job(media_item, episode_number)

    def resume_unfinished_downloads(self):
        """Finds and re-queues any downloads that were left in an unfinished state."""
        logger.info("Checking for unfinished downloads to resume...")
        # TODO: make the checking of unfinished downloads more efficient probably by modifying the registry to be aware of what actually changed and load that instead
        queued_jobs = self.registry.get_episodes_by_download_status(
            DownloadStatus.QUEUED
        )
        downloading_jobs = self.registry.get_episodes_by_download_status(
            DownloadStatus.DOWNLOADING
        )

        unfinished_jobs = queued_jobs + downloading_jobs
        if not unfinished_jobs:
            logger.info("No unfinished downloads found.")
            return

        logger.info(
            f"Found {len(unfinished_jobs)} unfinished downloads. Re-queueing..."
        )
        for media_id, episode_number in unfinished_jobs:
            if (media_id, str(episode_number)) in self._inflight:
                continue
            record = self.registry.get_media_record(media_id)
            if record and record.media_item:
                self._submit_download(record.media_item, episode_number)
            else:
                logger.error(
                    f"Could not find metadata for media ID {media_id}. Cannot resume. Please run 'viu registry sync'."
                )

    def retry_failed_downloads(self):
        """Finds and re-queues any downloads that were left in an unfinished state."""
        logger.info("Checking for unfinished downloads to resume...")
        # TODO: may need to improve this
        queued_jobs = self.registry.get_episodes_by_download_status(
            DownloadStatus.FAILED
        )

        unfinished_jobs = queued_jobs
        if not unfinished_jobs:
            logger.info("No unfinished downloads found.")
            return

        logger.info(
            f"Found {len(unfinished_jobs)} unfinished downloads. Re-queueing..."
        )
        for media_id, episode_number in unfinished_jobs:
            if (media_id, str(episode_number)) in self._inflight:
                continue

            record = self.registry.get_media_record(media_id)
            if record and record.media_item:
                for episode in record.media_episodes:
                    if episode_number != episode.episode_number:
                        continue
                    if (
                        episode.download_attempts
                        <= self.app_config.downloads.max_retry_attempts
                    ):
                        logger.info(
                            f"Retrying {episode_number} of {record.media_item.title.english}"
                        )
                        self._submit_download(record.media_item, episode_number)
                    else:
                        logger.info(
                            f"Max attempts reached for {episode_number} of {record.media_item.title.english}"
                        )

            else:
                logger.error(
                    f"Could not find metadata for media ID {media_id}. Cannot resume. Please run 'viu registry sync'."
                )

    def _execute_download_job(self, media_item: MediaItem, episode_number: str):
        """The core download logic, can be called by worker or synchronously."""
        self.registry.get_or_create_record(media_item)
        try:
            self.registry.update_episode_download_status(
                media_id=media_item.id,
                episode_number=episode_number,
                status=DownloadStatus.DOWNLOADING,
            )

            media_title = media_item.title.romaji or media_item.title.english

            # 1. Search the provider to get the provider-specific ID
            provider_search_results = self.provider.search(
                SearchParams(
                    query=normalize_title(
                        media_title, self.app_config.general.provider.value, True
                    ),
                    translation_type=self.app_config.stream.translation_type,
                )
            )

            if not provider_search_results or not provider_search_results.results:
                raise ValueError(
                    f"Could not find '{media_title}' on provider '{self.app_config.general.provider.value}'"
                )

            # 2. Find the best match using fuzzy logic (like auto-select)
            provider_results_map = {
                result.title: result for result in provider_search_results.results
            }
            best_match_title = find_best_match_title(
                provider_results_map, self.app_config.general.provider, media_item
            )
            provider_anime_ref = provider_results_map[best_match_title]

            # 3. Get full provider anime details (contains the correct episode list)
            provider_anime = self.provider.get(
                AnimeParams(id=provider_anime_ref.id, query=media_title)
            )
            if not provider_anime:
                raise ValueError(
                    f"Failed to get full details for '{best_match_title}' from provider."
                )

            # 4. Get stream links using the now-validated provider_anime ID
            streams_iterator = self.provider.episode_streams(
                EpisodeStreamsParams(
                    anime_id=provider_anime.id,
                    query=media_title,
                    episode=episode_number,
                    translation_type=self.app_config.stream.translation_type,
                )
            )
            if not streams_iterator:
                raise ValueError("Provider returned no stream iterator.")

            server = next(streams_iterator, None)
            if not server or not server.links:
                raise ValueError(f"No stream links found for Episode {episode_number}")

            if server.name != self.app_config.downloads.server.value:
                while True:
                    try:
                        _server = next(streams_iterator)
                        if _server.name == self.app_config.downloads.server.value:
                            server = _server
                            break
                    except StopIteration:
                        break

            stream_link = server.links[0]
            episode_title = f"{media_item.title.english}; Episode {episode_number}"
            if media_item.streaming_episodes and media_item.streaming_episodes.get(
                episode_number
            ):
                episode_title = media_item.streaming_episodes[episode_number].title
            # 5. Perform the download
            download_params = DownloadParams(
                url=stream_link.link,
                anime_title=media_item.title.english,
                episode_title=episode_title,
                silent=False,
                headers=server.headers,
                subtitles=[sub.url for sub in server.subtitles],
                merge=self.app_config.downloads.merge_subtitles,
                clean=self.app_config.downloads.cleanup_after_merge,
                no_check_certificate=self.app_config.downloads.no_check_certificate,
            )

            result = self.downloader.download(download_params)

            # 6. Update registry based on result
            if result.success and result.video_path:
                file_size = (
                    result.video_path.stat().st_size
                    if result.video_path.exists()
                    else None
                )
                self.registry.update_episode_download_status(
                    media_id=media_item.id,
                    episode_number=episode_number,
                    status=DownloadStatus.COMPLETED,
                    file_path=result.merged_path or result.video_path,
                    file_size=file_size,
                    quality=stream_link.quality,
                    provider_name=self.app_config.general.provider.value,
                    server_name=server.name,
                    subtitle_paths=result.subtitle_paths,
                )
                message = f"Successfully downloaded Episode {episode_number} of '{media_title}'"
                try:
                    from plyer import notification

                    icon_path = self._get_or_fetch_icon(media_item)
                    app_icon = str(icon_path) if icon_path else None

                    notification.notify(  # type: ignore
                        title="Viu: New Episode",
                        message=message,
                        app_name="Viu",
                        app_icon=app_icon,
                        timeout=self.app_config.general.desktop_notification_duration,
                    )
                except:  # noqa: E722
                    pass
                logger.info(message)
            else:
                raise ValueError(result.error_message or "Unknown download error")

        except Exception as e:
            message = f"Download failed for '{media_item.title.english}' Ep {episode_number}: {e}"
            try:
                from plyer import notification

                icon_path = self._get_or_fetch_icon(media_item)
                app_icon = str(icon_path) if icon_path else None

                notification.notify(  # type: ignore
                    title="Viu: New Episode",
                    message=message,
                    app_name="Viu",
                    app_icon=app_icon,
                    timeout=self.app_config.general.desktop_notification_duration,
                )
            except:  # noqa: E722
                pass
            logger.error(
                message,
                exc_info=True,
            )
            self.registry.update_episode_download_status(
                media_id=media_item.id,
                episode_number=episode_number,
                status=DownloadStatus.FAILED,
                error_message=str(e),
            )
        finally:
            # Remove from in-flight tracking regardless of outcome
            try:
                self._inflight.discard((media_item.id, str(episode_number)))
            except Exception:
                pass

    def _get_or_fetch_icon(self, media_item: MediaItem) -> Path | None:
        """Fetch and cache a small cover image for system notifications."""
        import httpx

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
