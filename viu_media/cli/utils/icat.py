import shutil
import subprocess
import sys
import termios
import tty
from sys import exit

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def get_key():
    """Read a single keypress (including arrows)."""
    if sys.platform == "win32":
        raise NotImplementedError("icat is not supported on Windows.")

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch1 = sys.stdin.read(1)
        if ch1 == "\x1b":
            ch2 = sys.stdin.read(2)
            return ch1 + ch2
        return ch1
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def draw_banner_at(msg: str, row: int):
    """Move cursor to `row`, then render a centered, cyan-bordered panel."""
    sys.stdout.write(f"\x1b[{row};1H")
    text = Text(msg, justify="center")
    panel = Panel(Align(text, align="center"), border_style="cyan", padding=(1, 2))
    console.print(panel)


def icat_manga_viewer(image_links: list[str], window_title: str):
    ICAT = shutil.which("kitty")
    if not ICAT:
        console.print("[bold red]kitty (for icat) not found[/]")
        exit(1)

    idx, total = 0, len(image_links)
    title = f"{window_title}  ({total} images)"
    show_banner = True

    try:
        while True:
            console.clear()
            term_width, term_height = shutil.get_terminal_size((80, 24))
            panel_height = 0

            # Calculate space for image based on banner visibility
            if show_banner:
                msg_lines = 3  # Title + blank + controls
                panel_height = msg_lines + 4  # Padding and borders
                image_height = term_height - panel_height - 1
            else:
                image_height = term_height

            subprocess.run(
                [
                    ICAT,
                    "+kitten",
                    "icat",
                    "--clear",
                    "--scale-up",
                    "--place",
                    f"{term_width}x{image_height}@0x0",
                    "--z-index",
                    "-1",
                    image_links[idx],
                ],
                check=False,
            )

            if show_banner:
                controls = (
                    f"[{idx + 1}/{total}]  Prev: [h/←]   Next: [l/→]   "
                    f"Toggle Banner: [b]   Quit: [q/Ctrl-C]"
                )
                msg = f"{title}\n\n{controls}"
                start_row = term_height - panel_height
                draw_banner_at(msg, start_row)

            # key handling
            key = get_key()
            if key in ("l", "\x1b[C"):
                idx = (idx + 1) % total
            elif key in ("h", "\x1b[D"):
                idx = (idx - 1) % total
            elif key == "b":
                show_banner = not show_banner
            elif key in ("q", "\x03"):
                break

    except KeyboardInterrupt:
        pass
    finally:
        console.clear()
        console.print("Exited viewer.", style="bold")
