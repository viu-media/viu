import logging
import os
import shutil
import subprocess

from rich.prompt import Prompt

from ....core.config import FzfConfig
from ....core.exceptions import ViuError
from ..base import BaseSelector

logger = logging.getLogger(__name__)


class FzfSelector(BaseSelector):
    def __init__(self, config: FzfConfig):
        self.config = config
        self.executable = shutil.which("fzf")
        if not self.executable:
            raise ViuError("Please install fzf to use the fzf selector")

        os.environ["FZF_DEFAULT_OPTS"] = self.config.opts

        self.header_color = config.header_color.split(",")
        self.header = "\n".join(
            [
                f"\033[38;2;{self.header_color[0]};{self.header_color[1]};{self.header_color[2]};m{line}\033[0m"
                for line in config.header_ascii_art.replace("\t", "").split("\n")
            ]
        )

    def choose(self, prompt, choices, *, preview=None, header=None):
        fzf_input = "\n".join(choices)

        commands = [
            self.executable,
            "--prompt",
            f"{prompt.title()}: ",
            "--header",
            self.header,
            "--header-first",
        ]
        if preview:
            commands.extend(["--preview", preview])

        result = subprocess.run(
            commands,
            input=fzf_input,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def choose_multiple(self, prompt, choices, preview=None):
        """Enhanced multi-selection using fzf's --multi flag."""
        fzf_input = "\n".join(choices)

        commands = [
            self.executable,
            "--multi",
            "--prompt",
            f"{prompt.title()}: ",
            "--header",
            f"{self.header}\nPress TAB to select multiple items, ENTER to confirm",
            "--header-first",
        ]
        if preview:
            commands.extend(["--preview", preview])

        result = subprocess.run(
            commands,
            input=fzf_input,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            return []

        # Split the output by newlines and filter out empty strings
        selections = [
            line.strip() for line in result.stdout.strip().split("\n") if line.strip()
        ]
        return selections

    def confirm(self, prompt, *, default=False):
        choices = ["Yes", "No"]
        default_choice = "Yes" if default else "No"
        result = self.choose(prompt, choices, header=f"Default: {default_choice}")
        return result == "Yes"

    def ask(self, prompt, *, default=None):
        # cleaner to use rich
        return Prompt.ask(prompt, default=default)
        # -- not going to be used --
        commands = [
            self.executable,
            "--prompt",
            f"{prompt.title()}: ",
            "--header",
            self.header,
            "--header-first",
            "--print-query",
        ]

        result = subprocess.run(
            commands,
            input="",
            stdout=subprocess.PIPE,
            text=True,
            check=False,
        )
        # The output contains the selection (if any) and the query on the last line
        lines = result.stdout.strip().splitlines()
        return lines[-1] if lines else (default or "")

    def search(self, prompt, search_command, *, preview=None, header=None):
        """Enhanced search using fzf's --reload flag for dynamic search."""
        commands = [
            self.executable,
            "--prompt",
            f"{prompt.title()}: ",
            "--header",
            self.header,
            "--header-first",
            "--bind",
            f"change:reload({search_command})",
            "--ansi",
        ]

        if preview:
            commands.extend(["--preview", preview])

        result = subprocess.run(
            commands,
            input="",
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()


if __name__ == "__main__":
    config = FzfConfig()
    selector = FzfSelector(config)
    choice = selector.ask("Hello dev :)")
    print(choice)
    choice = selector.confirm("Hello dev :)")
    print(choice)
    choice = selector.choose_multiple("What comes first", ["a", "b"])
    print(choice)
    choice = selector.choose("What comes first", ["a", "b"])
    print(choice)
