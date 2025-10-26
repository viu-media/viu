"""Update command for Viu CLI."""

from typing import TYPE_CHECKING

import click
from rich import print

from ..utils.update import check_for_updates, print_release_json, update_app

if TYPE_CHECKING:
    from ...core.config import AppConfig


@click.command(
    help="Update Viu to the latest version",
    short_help="Update Viu",
    epilog="""
\b
\b\bExamples:
  # Check for updates and update if available
  viu update
\b
  # Force update even if already up to date
  viu update --force
\b
  # Only check for updates without updating
  viu update --check-only
\b
  # Show release notes for the latest version
  viu update --release-notes
""",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force update even if already up to date",
)
@click.option(
    "--check-only",
    "-c",
    is_flag=True,
    help="Only check for updates without updating",
)
@click.option(
    "--release-notes",
    "-r",
    is_flag=True,
    help="Show release notes for the latest version",
)
@click.pass_context
@click.pass_obj
def update(
    config: "AppConfig",
    ctx: click.Context,
    force: bool,
    check_only: bool,
    release_notes: bool,
) -> None:
    """
    Update Viu to the latest version.

    This command checks for available updates and optionally updates
    the application to the latest version from the configured sources
    (pip, uv, pipx, git, or nix depending on installation method).

    Args:
        config: The application configuration object
        ctx: The click context containing CLI options
        force: Whether to force update even if already up to date
        check_only: Whether to only check for updates without updating
        release_notes: Whether to show release notes for the latest version
    """
    if release_notes:
        print("[cyan]Fetching latest release notes...[/]")
        is_latest, release_json = check_for_updates()

        if not release_json:
            print(
                "[yellow]Could not fetch release information. Please check your internet connection.[/]"
            )
        else:
            print_release_json(release_json)

        return

    elif check_only:
        print("[cyan]Checking for updates...[/]")
        is_latest, release_json = check_for_updates()

        if not release_json:
            print(
                "[yellow]Could not check for updates. Please check your internet connection.[/]"
            )

        if is_latest:
            print("[green]Viu is up to date![/]")
            print(f"[dim]Current version: {release_json.get('tag_name', 'unknown')}[/]")
        else:
            latest_version = release_json.get("tag_name", "unknown")
            print(f"[yellow]Update available: {latest_version}[/]")
            print("[dim]Run 'viu update' to update[/]")
    else:
        print("[cyan]Checking for updates and updating if necessary...[/]")
        success, release_json = update_app(force=force)

        if not release_json:
            print(
                "[red]Could not check for updates. Please check your internet connection.[/]"
            )
        if success:
            latest_version = release_json.get("tag_name", "unknown")
            print(f"[green]Successfully updated to version {latest_version}![/]")
        else:
            if force:
                print("[red]Update failed. Please check the error messages above.[/]")
