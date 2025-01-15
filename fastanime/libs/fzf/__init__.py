import logging
import os
import shutil
import subprocess
import sys
from typing import Callable, List

from click import clear
from rich import print

logger = logging.getLogger(__name__)


FZF_DEFAULT_OPTS = """ 
    --color=fg:#d0d0d0,fg+:#d0d0d0,bg:#121212,bg+:#262626
    --color=hl:#5f87af,hl+:#5fd7ff,info:#afaf87,marker:#87ff00
    --color=prompt:#d7005f,spinner:#af5fff,pointer:#af5fff,header:#87afaf
    --color=border:#262626,label:#aeaeae,query:#d9d9d9
    --border="rounded" --border-label="" --preview-window="border-rounded" --prompt="> "
    --marker=">" --pointer="◆" --separator="─" --scrollbar="│"
"""

HEADER = """

███████╗░█████╗░░██████╗████████╗░█████╗░███╗░░██╗██╗███╗░░░███╗███████╗
██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔══██╗████╗░██║██║████╗░████║██╔════╝
█████╗░░███████║╚█████╗░░░░██║░░░███████║██╔██╗██║██║██╔████╔██║█████╗░░
██╔══╝░░██╔══██║░╚═══██╗░░░██║░░░██╔══██║██║╚████║██║██║╚██╔╝██║██╔══╝░░
██║░░░░░██║░░██║██████╔╝░░░██║░░░██║░░██║██║░╚███║██║██║░╚═╝░██║███████╗
╚═╝░░░░░╚═╝░░╚═╝╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝╚═╝░░╚══╝╚═╝╚═╝░░░░░╚═╝╚══════╝

"""


class FZF:
    """an abstraction over the fzf commandline utility

    Attributes:
        FZF_EXECUTABLE: [TODO:attribute]
        default_options: [TODO:attribute]
        stdout: [TODO:attribute]
    """

    # if not os.getenv("FZF_DEFAULT_OPTS"):
    #     os.environ["FZF_DEFAULT_OPTS"] = FZF_DEFAULT_OPTS
    FZF_EXECUTABLE = shutil.which("fzf")
    default_options = [
        "--cycle",
        "--info=hidden",
        "--layout=reverse",
        "--height=100%",
        "--bind=right:accept,ctrl-/:toggle-preview,ctrl-space:toggle-wrap+toggle-preview-wrap",
        "--no-margin",
        "+m",
        "-i",
        "--exact",
        "--tabstop=1",
        "--preview-window=left,35%,wrap",
        "--wrap",
    ]

    def _with_filter(self, command: str, work: Callable) -> List[str]:
        """ported from the fzf docs demo

        Args:
            command: [TODO:description]
            work: [TODO:description]

        Returns:
            [TODO:return]
        """
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                shell=True,
            )
        except subprocess.SubprocessError as e:
            print(f"Failed to start subprocess: {e}", file=sys.stderr)
            return []

        original_stdout = sys.stdout
        sys.stdout = process.stdin

        try:
            work()
            if process.stdin:
                process.stdin.close()
        except Exception as e:
            print(f"Exception during work execution: {e}", file=sys.stderr)
        finally:
            sys.stdout = original_stdout

        output = []
        if process.stdout:
            output = process.stdout.read().splitlines()
            process.stdout.close()

        return output

    def _run_fzf(self, commands: list[str], _fzf_input) -> str:
        """core abstraction

        Args:
            _fzf_input ([TODO:parameter]): [TODO:description]
            commands: [TODO:description]

        Raises:
            Exception: [TODO:throw]

        Returns:
            [TODO:return]
        """
        fzf_input = "\n".join(_fzf_input)

        if not self.FZF_EXECUTABLE:
            raise Exception("fzf executable not found")

        result = subprocess.run(
            [self.FZF_EXECUTABLE, *commands],
            input=fzf_input,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            text=True,
            encoding="utf-8",
        )
        if not result or result.returncode != 0 or not result.stdout:
            print("sth went wrong:confused:")
            input("press enter to try again...")
            clear()
            return self._run_fzf(commands, _fzf_input)
        clear()

        return result.stdout.strip()

    def run(
        self,
        fzf_input: list[str],
        prompt: str,
        header: str = HEADER,
        preview: str | None = None,
        expect: str | None = None,
        validator: Callable | None = None,
        preselect: int | None = None,
    ) -> str:
        """a helper method that wraps common use cases over the fzf utility

        Args:
            fzf_input: [TODO:description]
            prompt: [TODO:description]
            header: [TODO:description]
            preview: [TODO:description]
            expect: [TODO:description]
            validator: [TODO:description]

        Returns:
            [TODO:return]
        """
        _HEADER_COLOR = os.environ.get("FASTANIME_HEADER_COLOR", "215,0,95").split(",")
        header = os.environ.get("FASTANIME_HEADER_ASCII_ART", HEADER)
        header = "\n".join(
            [
                f"\033[38;2;{_HEADER_COLOR[0]};{_HEADER_COLOR[1]};{_HEADER_COLOR[2]};m{line}\033[0m"
                for line in header.split("\n")
            ]
        )
        _commands = [
            *self.default_options,
            "--header",
            header,
            "--header-first",
            "--prompt",
            f"{prompt.title()}: ",
        ]  # pyright:ignore

        if preview:
            _commands.append(f"--preview={preview}")
        if expect:
            _commands.append(f"--expect={expect}")
        if preselect:
            _commands.append("--sync")
            _commands.append(f"--bind=start:pos({preselect + 1})")

        result = self._run_fzf(_commands, fzf_input)  # pyright:ignore
        if not result:
            print("Please enter a value")
            input("Enter to do it right")
            return self.run(fzf_input, prompt, header, preview, expect, validator)
        elif validator:
            success, info = validator(result)
            if not success:
                print(info)
                input("Enter to try again")
                return self.run(fzf_input, prompt, header, preview, expect, validator)
        # os.environ["FZF_DEFAULT_OPTS"] = ""
        return result


fzf = FZF()

if __name__ == "__main__":
    action = fzf.run([*os.listdir(), "exit"], "Prompt: ", "Header", preview="bat {}")
    print(action)
