#!/usr/bin/env python3
#
# FZF Preview Script Template
#
# This script is a template. The placeholders in curly braces, like {NAME}
#  are dynamically filled by python using .replace()

from pathlib import Path
from hashlib import sha256
import subprocess
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

console = Console(force_terminal=True, color_system="truecolor")
if PREVIEW_MODE == "image" or PREVIEW_MODE == "full":
    preview_image_path = IMAGE_CACHE_DIR / f"{hash}.png"
    if preview_image_path.exists():
        print("rendering image")
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
