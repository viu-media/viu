"""
Registry backup command - create full backups of the registry
"""

import json
import tarfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import click

from .....core.config import AppConfig
from ....service.feedback import FeedbackService
from ....service.registry.service import MediaRegistryService

if TYPE_CHECKING:
    pass


@click.command(help="Create a full backup of the registry")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output backup file path (auto-generated if not specified)",
)
@click.option("--compress", "-c", is_flag=True, help="Compress the backup archive")
@click.option("--include-cache", is_flag=True, help="Include cache files in backup")
@click.option(
    "--format",
    "backup_format",
    type=click.Choice(["tar", "zip"], case_sensitive=False),
    default="tar",
    help="Backup archive format",
)
@click.option(
    "--api",
    default="anilist",
    type=click.Choice(["anilist"], case_sensitive=False),
    help="Media API registry to backup",
)
@click.pass_obj
def backup(
    config: AppConfig,
    output: str | None,
    compress: bool,
    include_cache: bool,
    backup_format: str,
    api: str,
):
    """
    Create a complete backup of your media registry.

    Includes all media records, index files, and optionally cache data.
    Backups can be compressed and are suitable for restoration.
    """
    feedback = FeedbackService(config)

    try:
        registry_service = MediaRegistryService(api, config.media_registry)

        # Generate output filename if not specified
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = (
                "tar.gz" if compress and backup_format == "tar" else backup_format
            )
            if backup_format == "zip":
                extension = "zip"
            output = f"viu_registry_backup_{api}_{timestamp}.{extension}"

        output_path = Path(output)

        # Get backup statistics before starting
        stats = registry_service.get_registry_stats()
        total_media = stats.get("total_media", 0)

        feedback.info("Starting Backup", f"Backing up {total_media} media entries...")

        # Create backup based on format
        if backup_format.lower() == "tar":
            _create_tar_backup(
                registry_service, output_path, compress, include_cache, feedback, api
            )
        elif backup_format.lower() == "zip":
            _create_zip_backup(
                registry_service, output_path, include_cache, feedback, api
            )

        # Get final backup size
        backup_size = _format_file_size(output_path)

        feedback.success(
            "Backup Complete", f"Registry backed up to {output_path} ({backup_size})"
        )

        # Show backup contents summary
        _show_backup_summary(output_path, backup_format, feedback)

    except Exception as e:
        feedback.error("Backup Error", f"Failed to create backup: {e}")
        raise click.Abort()


def _create_tar_backup(
    registry_service: MediaRegistryService,
    output_path: Path,
    compress: bool,
    include_cache: bool,
    feedback: FeedbackService,
    api: str,
):
    """Create a tar-based backup."""
    # TODO: Add support for bz2/xz compression if needed
    mode = "w:gz" if compress else "w"

    with tarfile.open(output_path, mode) as tar:
        # Add registry directory
        registry_dir = registry_service.config.media_dir / api
        if registry_dir.exists():
            tar.add(registry_dir, arcname=f"registry/{api}")
            feedback.info("Added to backup", f"Registry data ({api})")

        # Add index directory
        index_dir = registry_service.config.index_dir
        if index_dir.exists():
            tar.add(index_dir, arcname="index")
            feedback.info("Added to backup", "Registry index")

        # Add cache if requested
        if include_cache:
            cache_dir = registry_service.config.media_dir.parent / "cache"
            if cache_dir.exists():
                tar.add(cache_dir, arcname="cache")
                feedback.info("Added to backup", "Cache data")

        # Add metadata file directly into the archive without creating a temp file
        try:
            metadata = _create_backup_metadata(registry_service, api, include_cache)
            metadata_bytes = json.dumps(metadata, indent=2, default=str).encode("utf-8")

            tarinfo = tarfile.TarInfo(name="backup_metadata.json")
            tarinfo.size = len(metadata_bytes)
            tarinfo.mtime = int(datetime.now().timestamp())

            with BytesIO(metadata_bytes) as bio:
                tar.addfile(tarinfo, bio)
        except Exception as e:
            feedback.warning("Metadata Error", f"Failed to add metadata: {e}")


def _create_zip_backup(
    registry_service: MediaRegistryService,
    output_path: Path,
    include_cache: bool,
    feedback: FeedbackService,
    api: str,
):
    """Create a zip-based backup."""
    import zipfile

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add registry directory
        registry_dir = registry_service.config.media_dir / api
        if registry_dir.exists():
            for file_path in registry_dir.rglob("*"):
                if file_path.is_file():
                    arcname = f"registry/{api}/{file_path.relative_to(registry_dir)}"
                    zip_file.write(file_path, arcname)
            feedback.info("Added to backup", f"Registry data ({api})")

        # Add index directory
        index_dir = registry_service.config.index_dir
        if index_dir.exists():
            for file_path in index_dir.rglob("*"):
                if file_path.is_file():
                    arcname = f"index/{file_path.relative_to(index_dir)}"
                    zip_file.write(file_path, arcname)
            feedback.info("Added to backup", "Registry index")

        # Add cache if requested
        if include_cache:
            cache_dir = registry_service.config.media_dir.parent / "cache"
            if cache_dir.exists():
                for file_path in cache_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = f"cache/{file_path.relative_to(cache_dir)}"
                        zip_file.write(file_path, arcname)
                feedback.info("Added to backup", "Cache data")

        # Add metadata
        try:
            metadata = _create_backup_metadata(registry_service, api, include_cache)
            metadata_json = json.dumps(metadata, indent=2, default=str)
            zip_file.writestr("backup_metadata.json", metadata_json)
        except Exception as e:
            feedback.warning("Metadata Error", f"Failed to add metadata: {e}")


def _create_backup_metadata(
    registry_service: MediaRegistryService, api: str, include_cache: bool
) -> dict:
    """Create backup metadata."""
    from .....core.constants import __version__

    stats = registry_service.get_registry_stats()

    return {
        "backup_timestamp": datetime.now().isoformat(),
        "viu_version": __version__,
        "registry_version": stats.get("version"),
        "api": api,
        "total_media": stats.get("total_media", 0),
        "include_cache": include_cache,
        "registry_stats": stats,
        "backup_type": "full",
    }


def _show_backup_summary(
    backup_path: Path, format_type: str, feedback: FeedbackService
):
    """Show summary of backup contents."""
    try:
        if format_type.lower() == "tar":
            with tarfile.open(backup_path, "r:*") as tar:
                members = tar.getmembers()
                file_count = len([m for m in members if m.isfile()])
                dir_count = len([m for m in members if m.isdir()])
        else:  # zip
            import zipfile

            with zipfile.ZipFile(backup_path, "r") as zip_file:
                info_list = zip_file.infolist()
                file_count = len([info for info in info_list if not info.is_dir()])
                dir_count = len([info for info in info_list if info.is_dir()])

        feedback.info("Backup Contents", f"{file_count} files, {dir_count} directories")

    except Exception as e:
        feedback.warning("Summary Error", f"Could not analyze backup contents: {e}")


def _format_file_size(file_path: Path) -> str:
    """Format file size in human-readable format."""
    try:
        size_bytes: float = float(file_path.stat().st_size)
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while size_bytes >= 1024.0 and i < len(size_name) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_name[i]}"
    except FileNotFoundError:
        return "Unknown size"
