#!/usr/bin/env python3
#
# FZF Preview Script Template
#
# This script is a template. The placeholders in curly braces, like {NAME}
#  are dynamically filled by python using .replace()

from pathlib import Path
from hashlib import sha256
import subprocess
import os
import shutil
import sys
from rich.console import Console
from rich.rule import Rule

# dynamically filled variables
PREVIEW_MODE = "{PREVIEW_MODE}"
IMAGE_CACHE_DIR = Path("{IMAGE_CACHE_DIR}")
INFO_CACHE_DIR = Path("{INFO_CACHE_DIR}")
IMAGE_RENDERER = "{IMAGE_RENDERER}"
HEADER_COLOR = "{HEADER_COLOR}"
SEPARATOR_COLOR = "{SEPARATOR_COLOR}"
PREFIX = "{PREFIX}"
SCALE_UP = "{SCALE_UP}" == "True"

# fzf passes the title with quotes, so we need to trim them
TITLE = sys.argv[1]

hash = f"{PREFIX}-{sha256(TITLE.encode('utf-8')).hexdigest()}"


def fzf_image_preview(file_path: str):
    # Environment variables from fzf
    FZF_PREVIEW_COLUMNS = os.environ.get("FZF_PREVIEW_COLUMNS")
    FZF_PREVIEW_LINES = os.environ.get("FZF_PREVIEW_LINES")
    FZF_PREVIEW_TOP = os.environ.get("FZF_PREVIEW_TOP")
    KITTY_WINDOW_ID = os.environ.get("KITTY_WINDOW_ID")
    GHOSTTY_BIN_DIR = os.environ.get("GHOSTTY_BIN_DIR")
    PLATFORM = os.environ.get("PLATFORM")

    # Compute terminal dimensions
    dim = (
        f"{FZF_PREVIEW_COLUMNS}x{FZF_PREVIEW_LINES}"
        if FZF_PREVIEW_COLUMNS and FZF_PREVIEW_LINES
        else "x"
    )

    if dim == "x":
        try:
            rows, cols = (
                subprocess.check_output(
                    ["stty", "size"], text=True, stderr=subprocess.DEVNULL
                )
                .strip()
                .split()
            )
            dim = f"{cols}x{rows}"
        except Exception:
            dim = "80x24"

    # Adjust dimension if icat not used and preview area fills bottom of screen
    if (
        IMAGE_RENDERER != "icat"
        and not KITTY_WINDOW_ID
        and FZF_PREVIEW_TOP
        and FZF_PREVIEW_LINES
    ):
        try:
            term_rows = int(
                subprocess.check_output(["stty", "size"], text=True).split()[0]
            )
            if int(FZF_PREVIEW_TOP) + int(FZF_PREVIEW_LINES) == term_rows:
                dim = f"{FZF_PREVIEW_COLUMNS}x{int(FZF_PREVIEW_LINES) - 1}"
        except Exception:
            pass

    # Helper to run commands
    def run(cmd):
        subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)

    def command_exists(cmd):
        return shutil.which(cmd) is not None

    # ICAT / KITTY path
    if IMAGE_RENDERER == "icat" and not GHOSTTY_BIN_DIR:
        icat_cmd = None
        if command_exists("kitten"):
            icat_cmd = ["kitten", "icat"]
        elif command_exists("icat"):
            icat_cmd = ["icat"]
        elif command_exists("kitty"):
            icat_cmd = ["kitty", "icat"]

        if icat_cmd:
            run(
                icat_cmd
                + [
                    "--clear",
                    "--transfer-mode=memory",
                    "--unicode-placeholder",
                    "--stdin=no",
                    f"--place={dim}@0x0",
                    file_path,
                ]
            )
        else:
            print("No icat-compatible viewer found (kitten/icat/kitty)")

    elif GHOSTTY_BIN_DIR:
        try:
            cols = int(FZF_PREVIEW_COLUMNS or "80") - 1
            lines = FZF_PREVIEW_LINES or "24"
            dim = f"{cols}x{lines}"
        except Exception:
            pass

        if command_exists("kitten"):
            run(
                [
                    "kitten",
                    "icat",
                    "--clear",
                    "--transfer-mode=memory",
                    "--unicode-placeholder",
                    "--stdin=no",
                    f"--place={dim}@0x0",
                    file_path,
                ]
            )
        elif command_exists("icat"):
            run(
                [
                    "icat",
                    "--clear",
                    "--transfer-mode=memory",
                    "--unicode-placeholder",
                    "--stdin=no",
                    f"--place={dim}@0x0",
                    file_path,
                ]
            )
        elif command_exists("chafa"):
            run(["chafa", "-s", dim, file_path])

    elif command_exists("chafa"):
        # Platform specific rendering
        if PLATFORM == "android":
            run(["chafa", "-s", dim, file_path])
        elif PLATFORM == "windows":
            run(["chafa", "-f", "sixel", "-s", dim, file_path])
        else:
            run(["chafa", "-s", dim, file_path])
        print()

    elif command_exists("imgcat"):
        width, height = dim.split("x")
        run(["imgcat", "-W", width, "-H", height, file_path])

    else:
        print(
            "⚠️ Please install a terminal image viewer (icat, kitten, imgcat, or chafa)."
        )


console = Console(force_terminal=True, color_system="truecolor")
if PREVIEW_MODE == "image" or PREVIEW_MODE == "full":
    preview_image_path = IMAGE_CACHE_DIR / f"{hash}.png"
    if preview_image_path.exists():
        fzf_image_preview(str(preview_image_path))
        print()
    else:
        print("🖼️  Loading image...")

console.print(Rule(style=f"rgb({SEPARATOR_COLOR})"))
if PREVIEW_MODE == "info" or PREVIEW_MODE == "full":
    preview_info_path = INFO_CACHE_DIR / f"{hash}.py"
    if preview_info_path.exists():
        subprocess.run(
            [sys.executable, str(preview_info_path), HEADER_COLOR, SEPARATOR_COLOR]
        )
    else:
        console.print("📝 Loading details...")
