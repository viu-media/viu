#!/usr/bin/env python3
#
# FZF Preview Script Template
#
# This script is a template. The placeholders in curly braces, like {NAME}
# are dynamically filled by python using .replace() during runtime.

import os
import shutil
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

# --- Template Variables (Injected by Python) ---
PREVIEW_MODE = "{PREVIEW_MODE}"
IMAGE_CACHE_DIR = Path("{IMAGE_CACHE_DIR}")
INFO_CACHE_DIR = Path("{INFO_CACHE_DIR}")
IMAGE_RENDERER = "{IMAGE_RENDERER}"
HEADER_COLOR = "{HEADER_COLOR}"
SEPARATOR_COLOR = "{SEPARATOR_COLOR}"
PREFIX = "{PREFIX}"
SCALE_UP = "{SCALE_UP}" == "True"

# --- Arguments ---
# sys.argv[1] is usually the raw line from FZF (the anime title/key)
TITLE = sys.argv[1] if len(sys.argv) > 1 else ""
KEY = """{KEY}"""
KEY = KEY + "-" if KEY else KEY

# Generate the hash to find the cached files
hash_id = f"{PREFIX}-{sha256((KEY + TITLE).encode('utf-8')).hexdigest()}"


def get_terminal_dimensions():
    """
    Determine the available dimensions (cols x lines) for the preview window.
    Prioritizes FZF environment variables.
    """
    fzf_cols = os.environ.get("FZF_PREVIEW_COLUMNS")
    fzf_lines = os.environ.get("FZF_PREVIEW_LINES")

    if fzf_cols and fzf_lines:
        return int(fzf_cols), int(fzf_lines)

    # Fallback to stty if FZF vars aren't set (unlikely in preview)
    try:
        rows, cols = (
            subprocess.check_output(
                ["stty", "size"], text=True, stderr=subprocess.DEVNULL
            )
            .strip()
            .split()
        )
        return int(cols), int(rows)
    except Exception:
        return 80, 24


def which(cmd):
    """Alias for shutil.which"""
    return shutil.which(cmd)


def render_kitty(file_path, width, height, scale_up):
    """Render using the Kitty Graphics Protocol (kitten/icat)."""
    # 1. Try 'kitten icat' (Modern)
    # 2. Try 'icat' (Legacy/Alias)
    # 3. Try 'kitty +kitten icat' (Fallback)

    cmd = []
    if which("kitten"):
        cmd = ["kitten", "icat"]
    elif which("icat"):
        cmd = ["icat"]
    elif which("kitty"):
        cmd = ["kitty", "+kitten", "icat"]

    if not cmd:
        return False

    # Build Arguments
    args = [
        "--clear",
        "--transfer-mode=memory",
        "--unicode-placeholder",
        "--stdin=no",
        f"--place={width}x{height}@0x0",
    ]

    if scale_up:
        args.append("--scale-up")

    args.append(file_path)

    subprocess.run(cmd + args, stdout=sys.stdout, stderr=sys.stderr)
    return True


def render_sixel(file_path, width, height):
    """
    Render using Sixel.
    Prioritizes 'chafa' for Sixel as it handles text-cell sizing better than img2sixel.
    """

    # Option A: Chafa (Best for Sixel sizing)
    if which("chafa"):
        # Chafa automatically detects Sixel support if terminal reports it,
        # but we force it here if specifically requested via logic flow.
        subprocess.run(
            ["chafa", "-f", "sixel", "-s", f"{width}x{height}", file_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True

    # Option B: img2sixel (Libsixel)
    # Note: img2sixel uses pixels, not cells. We estimate 1 cell ~= 10px width, 20px height
    if which("img2sixel"):
        pixel_width = width * 10
        pixel_height = height * 20
        subprocess.run(
            [
                "img2sixel",
                f"--width={pixel_width}",
                f"--height={pixel_height}",
                file_path,
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True

    return False


def render_iterm(file_path, width, height):
    """Render using iTerm2 Inline Image Protocol."""
    if which("imgcat"):
        subprocess.run(
            ["imgcat", "-W", str(width), "-H", str(height), file_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True

    # Chafa also supports iTerm
    if which("chafa"):
        subprocess.run(
            ["chafa", "-f", "iterm", "-s", f"{width}x{height}", file_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True
    return False


def render_timg(file_path, width, height):
    """Render using timg (supports half-blocks, quarter-blocks, sixel, kitty, etc)."""
    if which("timg"):
        subprocess.run(
            ["timg", f"-g{width}x{height}", "--upscale", file_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True
    return False


def render_chafa_auto(file_path, width, height):
    """
    Render using Chafa in auto mode.
    It supports Sixel, Kitty, iTerm, and various unicode block modes.
    """
    if which("chafa"):
        subprocess.run(
            ["chafa", "-s", f"{width}x{height}", file_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True
    return False


def fzf_image_preview(file_path: str):
    """
    Main dispatch function to choose the best renderer.
    """
    cols, lines = get_terminal_dimensions()

    # Heuristic: Reserve 1 line for prompt/status if needed, though FZF handles this.
    # Some renderers behave better with a tiny bit of padding.
    width = cols
    height = lines

    # --- 1. Check Explicit Configuration ---

    if IMAGE_RENDERER == "icat" or IMAGE_RENDERER == "system-kitty":
        if render_kitty(file_path, width, height, SCALE_UP):
            return

    elif IMAGE_RENDERER == "sixel" or IMAGE_RENDERER == "system-sixels":
        if render_sixel(file_path, width, height):
            return

    elif IMAGE_RENDERER == "imgcat":
        if render_iterm(file_path, width, height):
            return

    elif IMAGE_RENDERER == "timg":
        if render_timg(file_path, width, height):
            return

    elif IMAGE_RENDERER == "chafa":
        if render_chafa_auto(file_path, width, height):
            return

    # --- 2. Auto-Detection / Fallback Strategy ---

    # If explicit failed or set to 'auto'/'system-default', try detecting environment

    # Ghostty / Kitty Environment
    if os.environ.get("KITTY_WINDOW_ID") or os.environ.get("GHOSTTY_BIN_DIR"):
        if render_kitty(file_path, width, height, SCALE_UP):
            return

    # iTerm Environment
    if os.environ.get("TERM_PROGRAM") == "iTerm.app":
        if render_iterm(file_path, width, height):
            return

    # Try standard tools in order of quality/preference
    if render_kitty(file_path, width, height, SCALE_UP):
        return  # Try kitty just in case
    if render_sixel(file_path, width, height):
        return
    if render_timg(file_path, width, height):
        return
    if render_chafa_auto(file_path, width, height):
        return

    print("⚠️ No suitable image renderer found (icat, chafa, timg, img2sixel).")


def fzf_text_info_render():
    """Renders the text-based info via the cached python script."""
    # Get terminal dimensions from FZF environment or fallback
    cols, lines = get_terminal_dimensions()

    # Print simple separator line with proper width
    r, g, b = map(int, SEPARATOR_COLOR.split(","))
    separator = f"\x1b[38;2;{r};{g};{b}m" + ("─" * cols) + "\x1b[0m"
    print(separator, flush=True)

    if PREVIEW_MODE == "text" or PREVIEW_MODE == "full":
        preview_info_path = INFO_CACHE_DIR / f"{hash_id}.py"
        if preview_info_path.exists():
            subprocess.run(
                [sys.executable, str(preview_info_path), HEADER_COLOR, SEPARATOR_COLOR]
            )
        else:
            # Print dim text
            print("\x1b[2m📝 Loading details...\x1b[0m")


def main():
    # 1. Image Preview
    if (PREVIEW_MODE == "image" or PREVIEW_MODE == "full") and (
        PREFIX not in ("character", "review", "airing-schedule")
    ):
        preview_image_path = IMAGE_CACHE_DIR / f"{hash_id}.png"
        if preview_image_path.exists():
            fzf_image_preview(str(preview_image_path))
            print()  # Spacer
        else:
            print("🖼️  Loading image...")

    # 2. Text Info Preview
    fzf_text_info_render()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Preview Error: {e}")
