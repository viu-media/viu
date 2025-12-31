import logging
import shutil
import subprocess
import sys
import textwrap

from ....core.config import RofiConfig
from ....core.utils import detect
from ..base import BaseSelector

logger = logging.getLogger(__name__)


class RofiSelector(BaseSelector):
    def __init__(self, config: RofiConfig):
        self.config = config
        self.executable = shutil.which("rofi")
        if not self.executable:
            raise FileNotFoundError("rofi executable not found in PATH.")

    def choose(self, prompt, choices, *, preview=None, header=None):
        if preview and detect.is_bash_script(preview):
            preview = None
        rofi_input = preview if preview else "\n".join(choices)

        theme = self.config.theme_preview if preview else self.config.theme_main
        theme = theme if choices else self.config.theme_input
        theme = self.config.theme_confirm if "Yes" in choices else theme
        args = [
            self.executable,
            "-no-config",
            "-theme",
            theme,
            "-p",
            prompt,
            "-i",
            "-dmenu",
        ]
        if preview:
            args.append("-show-icons")
        result = subprocess.run(
            args,
            input=rofi_input,
            stdout=subprocess.PIPE,
            text=True,
            env=detect.get_clean_env()
        )

        if result.returncode == 0:
            choice = result.stdout.strip()
            return choice
        else:
            # HACK: force exit if no input
            try:
                from plyer import notification

                from ....core.constants import (
                    CLI_NAME,
                    CLI_NAME_LOWER,
                    ICON_PATH,
                )

                notification.notify(  # type: ignore
                    title=f"{CLI_NAME} notification".title(),
                    message=f"Nothing was selected {CLI_NAME_LOWER} is shutting down",
                    app_name=CLI_NAME,
                    app_icon=str(ICON_PATH),
                    timeout=2 * 60,
                )
            except:  # noqa: E722
                logger.warning("Using rofi without plyer for notifications")
            sys.exit(1)

    def confirm(self, prompt, *, default=False):
        choices = ["Yes", "No"]
        default_choice = "Yes" if default else "No"

        result = self.choose(
            "\n".join(textwrap.wrap(prompt, width=30)),
            choices,
            header=f"Default: {default_choice}",
        )
        return result == "Yes"

    def ask(self, prompt, *, default=None):
        return self.choose("\n".join(textwrap.wrap(prompt, width=30)), [])

    def choose_multiple(
        self, prompt: str, choices: list[str], preview: str | None = None
    ) -> list[str]:
        if preview and detect.is_bash_script(preview):
            preview = None
        rofi_input = preview or "\n".join(choices)
        args = [
            self.executable,
            "-no-config",
            "-theme",
            self.config.theme_main if not preview else self.config.theme_preview,
            "-multi-select",
            "-p",
            prompt,
            "-i",
            "-dmenu",
        ]
        result = subprocess.run(
            args,
            input=rofi_input,
            stdout=subprocess.PIPE,
            text=True,
            env=detect.get_clean_env()
        )

        if result.returncode == 0:
            selections = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
            return selections

        try:
            from plyer import notification

            from ....core.constants import (
                CLI_NAME,
                CLI_NAME_LOWER,
                ICON_PATH,
            )

            notification.notify(  # type: ignore
                title=f"{CLI_NAME} notification".title(),
                message=f"Nothing was selected {CLI_NAME_LOWER} is shutting down",
                app_name=CLI_NAME,
                app_icon=str(ICON_PATH),
                timeout=2 * 60,
            )
        except:  # noqa: E722
            logger.warning("Using rofi without plyer for notifications")
        # HACK: force exit if no input
        sys.exit(1)


if __name__ == "__main__":
    config = RofiConfig()
    selector = RofiSelector(config)
    choice = selector.ask("Hello dev :)")
    print(choice)
    choice = selector.confirm("Hello dev :)")
    print(choice)
    choice = selector.choose_multiple("What comes first", ["a", "b"])
    print(choice)
    choice = selector.choose("What comes first", ["a", "b"])
    print(choice)
