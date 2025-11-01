import logging
from contextlib import contextmanager
from typing import Optional

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from ....core.config import AppConfig

logger = logging.getLogger(__name__)

console = Console()


class FeedbackService:
    """Centralized manager for user feedback in interactive menus."""

    def __init__(self, config: AppConfig):
        self.app_config = config

    def success(self, message: str, details: Optional[str] = None) -> None:
        """Show a success message with optional details."""
        icon = "✅ " if self.app_config.general.icons else ""
        main_msg = f"[bold green]{icon}{message}[/bold green]"

        if self.app_config.general.selector == "rofi":
            try:
                from plyer import notification

                from ....core.constants import CLI_NAME, ICON_PATH

                notification.notify(  # type: ignore
                    title=f"{CLI_NAME} notification".title(),
                    message=message,
                    app_name=CLI_NAME,
                    app_icon=str(ICON_PATH),
                    timeout=self.app_config.general.desktop_notification_duration,
                )
                return
            except:  # noqa: E722
                logger.warning("Using rofi without plyer for notifications")
        if details:
            console.print(f"{main_msg}\n[dim]{details}[/dim]")
        else:
            console.print(main_msg)

    def error(self, message: str, details: Optional[str] = None) -> None:
        """Show an error message with optional details."""
        icon = "❌ " if self.app_config.general.icons else ""
        main_msg = f"[bold red]{icon}Error: {message}[/bold red]"

        if self.app_config.general.selector == "rofi":
            try:
                from plyer import notification

                from ....core.constants import CLI_NAME, ICON_PATH

                notification.notify(  # type: ignore
                    title=f"{CLI_NAME} notification".title(),
                    message=message,
                    app_name=CLI_NAME,
                    app_icon=str(ICON_PATH),
                    timeout=self.app_config.general.desktop_notification_duration,
                )
                return
            except:  # noqa: E722
                logger.warning("Using rofi without plyer for notifications")
        if details:
            console.print(f"{main_msg}\n[dim]{details}[/dim]")
        else:
            console.print(main_msg)
        click.pause("Enter to continue...")

    def warning(self, message: str, details: Optional[str] = None) -> None:
        """Show a warning message with optional details."""
        icon = "⚠️ " if self.app_config.general.icons else ""
        main_msg = f"[bold yellow]{icon}Warning: {message}[/bold yellow]"

        if self.app_config.general.selector == "rofi":
            try:
                from plyer import notification

                from ....core.constants import CLI_NAME, ICON_PATH

                notification.notify(  # type: ignore
                    title=f"{CLI_NAME} notification".title(),
                    message=message,
                    app_name=CLI_NAME,
                    app_icon=str(ICON_PATH),
                    timeout=self.app_config.general.desktop_notification_duration,
                )
                return
            except:  # noqa: E722
                logger.warning("Using rofi without plyer for notifications")
        if details:
            console.print(f"{main_msg}\n[dim]{details}[/dim]")
        else:
            console.print(main_msg)

    def info(self, message: str, details: Optional[str] = None) -> None:
        """Show an informational message with optional details."""
        icon = "" if self.app_config.general.icons else ""
        main_msg = f"[bold blue]{icon}{message}[/bold blue]"

        if self.app_config.general.selector == "rofi":
            try:
                from plyer import notification

                from ....core.constants import CLI_NAME, ICON_PATH

                notification.notify(  # type: ignore
                    title=f"{CLI_NAME} notification".title(),
                    message=message,
                    app_name=CLI_NAME,
                    app_icon=str(ICON_PATH),
                    timeout=self.app_config.general.desktop_notification_duration,
                )
                return
            except:  # noqa: E722
                logger.warning("Using rofi without plyer for notifications")
        if details:
            console.print(f"{main_msg}\n[dim]{details}[/dim]")
        else:
            console.print(main_msg)
        # time.sleep(5)

    @contextmanager
    def progress(
        self,
        message: str,
        total: Optional[float] = None,
        transient: bool = False,
        auto_add_task: bool = True,
        success_msg: Optional[str] = None,
        error_msg: Optional[str] = None,
    ):
        """Context manager for operations with loading indicator and result feedback."""
        with Progress(
            SpinnerColumn(self.app_config.general.preferred_spinner),
            TextColumn(f"[cyan]{message}..."),
            BarColumn(),
            TaskProgressColumn(),
            transient=transient,
            console=console,
        ) as progress:
            task_id = progress.add_task("", total=total)
            try:
                yield task_id, progress
                if success_msg:
                    self.success(success_msg)
            except Exception as e:
                error_details = str(e) if str(e) else None
                final_error_msg = error_msg or "Operation failed"
                self.error(final_error_msg, error_details)
                raise

    def pause_for_user(self, message: str = "Press Enter to continue") -> None:
        """Pause execution and wait for user input."""
        icon = "⏸️ " if self.app_config.general.icons else ""

        if self.app_config.general.selector == "rofi":
            try:
                from plyer import notification

                from ....core.constants import CLI_NAME, ICON_PATH

                notification.notify(  # type: ignore
                    title=f"{CLI_NAME} notification".title(),
                    message="No current way to display info in rofi, use fzf and the terminal instead",
                    app_name=CLI_NAME,
                    app_icon=str(ICON_PATH),
                    timeout=self.app_config.general.desktop_notification_duration,
                )
                return
            except:  # noqa: E722
                logger.warning("Using rofi without plyer for notifications")
        click.pause(f"{icon}{message}...")

    def clear_console(self):
        console.clear()
