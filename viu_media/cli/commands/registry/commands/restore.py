"""
Registry restore command - restore registry from backup files
"""

import json
import shutil
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

import click

from .....core.config import AppConfig
from ....service.feedback import FeedbackService
from ....service.registry.service import MediaRegistryService


@click.command(help="Restore registry from a backup file")
@click.argument("backup_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--force", "-f", is_flag=True, help="Force restore even if current registry exists"
)
@click.option(
    "--backup-current",
    is_flag=True,
    help="Create backup of current registry before restoring",
)
@click.option(
    "--backup-current-tar-compression-fmt",
    type=click.Choice(["gz", "bz2", "xz"], case_sensitive=False),
    help="The compression format to use for the current registry backup (if enabled)",
)
@click.option("--verify", is_flag=True, help="Verify backup integrity before restoring")
@click.option(
    "--api",
    default="anilist",
    type=click.Choice(["anilist"], case_sensitive=False),
    help="Media API registry to restore to",
)
@click.pass_obj
def restore(
    config: AppConfig,
    backup_file: Path,
    force: bool,
    backup_current: bool,
    backup_current_compression_fmt: str,
    verify: bool,
    api: str,
):
    """
    Restore your media registry from a backup file.

    Can restore from tar or zip backups created by the backup command.
    Optionally creates a backup of the current registry before restoring.
    """
    feedback = FeedbackService(config)

    try:
        # Detect backup format
        backup_format = _detect_backup_format(backup_file)
        feedback.info("Backup Format", f"Detected {backup_format.upper()} format")

        # Verify backup if requested
        if verify:
            if not _verify_backup(backup_file, backup_format, feedback):
                feedback.error(
                    "Verification Failed",
                    "Backup file appears to be corrupted or invalid",
                )
                return
            feedback.success("Verification", "Backup file integrity verified")

        # Check if current registry exists
        registry_service = MediaRegistryService(api, config.media_registry)
        registry_exists = _check_registry_exists(registry_service)

        if registry_exists and not force:
            if not click.confirm(
                "Current registry exists. This will overwrite it. Continue with restore?"
            ):
                feedback.info("Restore Cancelled", "No changes were made")
                return

        # Create backup of current registry if requested
        if backup_current and registry_exists:
            _backup_current_registry(
                registry_service,
                api,
                feedback,
                backup_format=backup_format,
                compression_fmt=backup_current_compression_fmt,
            )

        # Show restore summary
        _show_restore_summary(backup_file, backup_format, feedback)

        # Perform restore
        _perform_restore(backup_file, backup_format, config, api, feedback)

        feedback.success(
            "Restore Complete", "Registry has been successfully restored from backup"
        )

        # Verify restored registry
        try:
            restored_service = MediaRegistryService(api, config.media_registry)
            stats = restored_service.get_registry_stats()
            feedback.info(
                "Restored Registry",
                f"Contains {stats.get('total_media', 0)} media entries",
            )
        except Exception as e:
            feedback.warning(
                "Verification Warning", f"Could not verify restored registry: {e}"
            )

    except Exception as e:
        feedback.error("Restore Error", f"Failed to restore registry: {e}")
        raise click.Abort()


def _detect_backup_format(backup_file: Path) -> str:
    """Detect backup file format."""
    suffixes = "".join(backup_file.suffixes).lower()
    if (
        ".tar" in suffixes
        or ".gz" in suffixes
        or ".tgz" in suffixes
        or ".bz2" in suffixes
        or ".xz" in suffixes
    ):
        return "tar"
    elif ".zip" in suffixes:
        return "zip"
    raise click.ClickException(f"Could not detect backup format for {backup_file}")


def _verify_backup(
    backup_file: Path, format_type: str, feedback: FeedbackService
) -> bool:
    """Verify backup file integrity."""
    try:
        metadata = {}
        has_registry = has_index = has_metadata = False
        if format_type == "tar":
            with tarfile.open(backup_file, "r:*") as tar:
                names = tar.getnames()
                for name in names:
                    if name == "registry/":
                        has_registry = True
                        continue
                    if name == "index/":
                        has_index = True
                        continue
                    if name == "backup_metadata.json":
                        has_metadata = True
                        continue
                if has_metadata:
                    metadata_member = tar.getmember("backup_metadata.json")
                    if metadata_file := tar.extractfile(metadata_member):
                        metadata = json.load(metadata_file)
        else:  # zip
            with zipfile.ZipFile(backup_file, "r") as zip_file:
                names = zip_file.namelist()
                for name in names:
                    if name == "registry/":
                        has_registry = True
                        continue
                    if name == "index/":
                        has_index = True
                        continue
                    if name == "backup_metadata.json":
                        has_metadata = True
                        continue
                if has_metadata:
                    with zip_file.open("backup_metadata.json") as metadata_file:
                        metadata = json.load(metadata_file)

        if has_metadata:
            feedback.info(
                "Backup Info", f"Created: {metadata.get('backup_timestamp', 'Unknown')}"
            )
            feedback.info(
                "Backup Info", f"Total Media: {metadata.get('total_media', 'Unknown')}"
            )

        return has_registry and has_index
    except (tarfile.ReadError, zipfile.BadZipFile, json.JSONDecodeError):
        return False
    except Exception as e:
        feedback.warning("Verification Warning", f"Could not fully verify backup: {e}")
        return False


def _check_registry_exists(registry_service: MediaRegistryService) -> bool:
    """Check if a registry already exists."""
    # TODO: Improve this check to be more robust
    return registry_service.media_registry_dir.exists() and any(
        registry_service.media_registry_dir.iterdir()
    )


def _backup_current_registry(
    registry_service: MediaRegistryService,
    api: str,
    feedback: FeedbackService,
    backup_format: str,
    compression_fmt: str,
):
    """Create backup of current registry before restoring."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if backup_format == "tar":
        from .backup import _create_tar_backup

        backup_path = Path(f"viu_registry_pre_restore_{api}_{timestamp}.tar.gz")

        try:
            _create_tar_backup(
                registry_service, backup_path, True, False, feedback, api
            )
            feedback.success("Current Registry Backed Up", f"Saved to {backup_path}")
        except Exception as e:
            feedback.warning(
                "Backup Warning", f"Failed to backup current registry: {e}"
            )
    else:
        from .backup import _create_zip_backup

        backup_path = Path(f"viu_registry_pre_restore_{api}_{timestamp}.zip")

        _create_zip_backup(registry_service, backup_path, True, feedback, api)


def _show_restore_summary(
    backup_file: Path, format_type: str, feedback: FeedbackService
):
    """Show summary of what will be restored."""
    try:
        file_count = media_files = 0
        if format_type == "tar":
            with tarfile.open(backup_file, "r:*") as tar:
                members = tar.getmembers()
                file_count = len([m for m in members if m.isfile()])
                media_files = len(
                    [
                        m
                        for m in members
                        if m.name.startswith("registry/") and m.name.endswith(".json")
                    ]
                )
        else:  # zip
            import zipfile

            with zipfile.ZipFile(backup_file, "r") as zip_file:
                info_list = zip_file.infolist()
                file_count = len([info for info in info_list if not info.is_dir()])
                media_files = len(
                    [
                        info
                        for info in info_list
                        if info.filename.startswith("registry/")
                        and info.filename.endswith(".json")
                    ]
                )

        feedback.info(
            "Restore Preview",
            f"Backup contains {file_count} files, including {media_files} media entries.",
        )
    except Exception as e:
        feedback.warning("Preview Error", f"Could not analyze backup: {e}")


def _perform_restore(
    backup_file: Path,
    format_type: str,
    config: AppConfig,
    api: str,
    feedback: FeedbackService,
):
    """Perform the actual restore operation."""
    temp_dir = Path(
        config.media_registry.media_dir.parent
        / f"restore_temp_{datetime.now().timestamp()}"
    )
    temp_dir.mkdir(exist_ok=True, parents=True)

    try:
        with feedback.progress("Restoring from backup...") as (task_id, progress):
            # 1. Extract backup
            progress.update(task_id, description="Extracting backup...")
            if format_type == "tar":
                with tarfile.open(backup_file, "r:*") as tar:
                    tar.extractall(temp_dir)
            else:
                import zipfile

                with zipfile.ZipFile(backup_file, "r") as zip_file:
                    zip_file.extractall(temp_dir)
            feedback.info("Extraction", "Backup extracted to temporary directory")

            # 2. Prepare paths
            registry_dir = config.media_registry.media_dir / api
            index_dir = config.media_registry.index_dir
            cache_dir = config.media_registry.media_dir.parent / "cache"

            # 3. Clean existing data
            progress.update(task_id, description="Cleaning existing registry...")
            if registry_dir.exists():
                shutil.rmtree(registry_dir)
            if index_dir.exists():
                shutil.rmtree(index_dir)
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
            feedback.info("Cleanup", "Removed existing registry, index, and cache data")

            # 4. Move extracted files
            progress.update(task_id, description="Moving new files into place...")
            if (extracted_registry := temp_dir / "registry" / api).exists():
                shutil.move(str(extracted_registry), str(registry_dir))
            if (extracted_index := temp_dir / "index").exists():
                shutil.move(str(extracted_index), str(index_dir))
            if (extracted_cache := temp_dir / "cache").exists():
                shutil.move(str(extracted_cache), str(cache_dir))

            progress.update(task_id, description="Finalizing...")

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            feedback.info("Cleanup", "Temporary files removed")
