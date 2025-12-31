#!/usr/bin/env python3
#
# FZF Dynamic Preview Script for Search Results
#
# This script handles previews for dynamic search by reading from the cached
# search results JSON and generating preview content on-the-fly.
# Template variables are injected by Python using .replace()

import json
import os
import shutil
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

# Import the utility functions
from _ansi_utils import (
    get_terminal_width,
    print_rule,
    print_table_row,
    strip_markdown,
    wrap_text,
)


# --- Template Variables (Injected by Python) ---
SEARCH_RESULTS_FILE = Path("{SEARCH_RESULTS_FILE}")
IMAGE_CACHE_DIR = Path("{IMAGE_CACHE_DIR}")
PREVIEW_MODE = "{PREVIEW_MODE}"
IMAGE_RENDERER = "{IMAGE_RENDERER}"
HEADER_COLOR = "{HEADER_COLOR}"
SEPARATOR_COLOR = "{SEPARATOR_COLOR}"
SCALE_UP = "{SCALE_UP}" == "True"

# --- Arguments ---
# sys.argv[1] is the selected anime title from fzf
SELECTED_TITLE = sys.argv[1] if len(sys.argv) > 1 else ""


def format_number(num):
    """Format number with thousand separators."""
    if num is None:
        return "N/A"
    return f"{num:,}"


def format_score_stars(score):
    """Format score as stars out of 6."""
    if score is None:
        return "N/A"
    # Convert 0-100 score to 0-6 stars
    stars = round(score / 100 * 6)
    return "⭐" * stars + f" ({score}/100)"


def format_date(date_obj):
    """Format date object to string."""
    if not date_obj or date_obj == "null":
        return "N/A"

    year = date_obj.get("year")
    month = date_obj.get("month")
    day = date_obj.get("day")

    if not year:
        return "N/A"
    if month and day:
        return f"{day}/{month}/{year}"
    if month:
        return f"{month}/{year}"
    return str(year)


def get_media_from_results(title):
    """Find media item in search results by title."""
    if not SEARCH_RESULTS_FILE.exists():
        return None

    try:
        with open(SEARCH_RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        media_list = data.get("data", {}).get("Page", {}).get("media", [])

        for media in media_list:
            title_obj = media.get("title", {})
            eng = title_obj.get("english")
            rom = title_obj.get("romaji")
            nat = title_obj.get("native")

            if title in (eng, rom, nat):
                return media

        return None
    except Exception as e:
        print(f"Error reading search results: {e}", file=sys.stderr)
        return None


def download_image(url: str, output_path: Path) -> bool:
    """Download image from URL and save to file."""
    try:
        # Try using urllib (stdlib)
        from urllib import request

        req = request.Request(url, headers={"User-Agent": "viu/1.0"})
        with request.urlopen(req, timeout=5) as response:
            data = response.read()
            output_path.write_bytes(data)
            return True
    except Exception:
        # Silently fail - preview will just not show image
        return False


def which(cmd):
    """Check if command exists."""
    return shutil.which(cmd)


def get_terminal_dimensions():
    """Get terminal dimensions from FZF environment."""
    fzf_cols = os.environ.get("FZF_PREVIEW_COLUMNS")
    fzf_lines = os.environ.get("FZF_PREVIEW_LINES")

    if fzf_cols and fzf_lines:
        return int(fzf_cols), int(fzf_lines)

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


def render_kitty(file_path, width, height, scale_up):
    """Render using the Kitty Graphics Protocol (kitten/icat)."""
    cmd = []
    if which("kitten"):
        cmd = ["kitten", "icat"]
    elif which("icat"):
        cmd = ["icat"]
    elif which("kitty"):
        cmd = ["kitty", "+kitten", "icat"]

    if not cmd:
        return False

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
    """Render using Sixel."""
    if which("chafa"):
        subprocess.run(
            ["chafa", "-f", "sixel", "-s", f"{width}x{height}", file_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True

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

    if which("chafa"):
        subprocess.run(
            ["chafa", "-f", "iterm", "-s", f"{width}x{height}", file_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True
    return False


def render_timg(file_path, width, height):
    """Render using timg."""
    if which("timg"):
        subprocess.run(
            ["timg", f"-g{width}x{height}", "--upscale", file_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True
    return False


def render_chafa_auto(file_path, width, height):
    """Render using Chafa in auto mode."""
    if which("chafa"):
        subprocess.run(
            ["chafa", "-s", f"{width}x{height}", file_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return True
    return False


def fzf_image_preview(file_path: str):
    """Main dispatch function to choose the best renderer."""
    cols, lines = get_terminal_dimensions()
    width = cols
    height = lines

    # Check explicit configuration
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

    # Auto-detection / Fallback
    if os.environ.get("KITTY_WINDOW_ID") or os.environ.get("GHOSTTY_BIN_DIR"):
        if render_kitty(file_path, width, height, SCALE_UP):
            return

    if os.environ.get("TERM_PROGRAM") == "iTerm.app":
        if render_iterm(file_path, width, height):
            return

    # Try standard tools in order of quality/preference
    if render_kitty(file_path, width, height, SCALE_UP):
        return
    if render_sixel(file_path, width, height):
        return
    if render_timg(file_path, width, height):
        return
    if render_chafa_auto(file_path, width, height):
        return

    print("⚠️ No suitable image renderer found (icat, chafa, timg, img2sixel).")


def main():
    if not SELECTED_TITLE:
        print("No selection")
        return

    # Get the media data from cached search results
    media = get_media_from_results(SELECTED_TITLE)

    if not media:
        print("Loading preview...")
        return

    term_width = get_terminal_width()

    # Extract media information
    title_obj = media.get("title", {})
    title = (
        title_obj.get("english")
        or title_obj.get("romaji")
        or title_obj.get("native")
        or "Unknown"
    )

    # Show image if in image or full mode
    if PREVIEW_MODE in ("image", "full"):
        cover_image = media.get("coverImage", {}).get("large", "")
        if cover_image:
            # Ensure image cache directory exists
            IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

            # Generate hash matching the preview worker pattern
            # Use "anime-" prefix and hash of just the title (no KEY prefix for dynamic search)
            hash_id = f"anime-{sha256(SELECTED_TITLE.encode('utf-8')).hexdigest()}"
            image_file = IMAGE_CACHE_DIR / f"{hash_id}.png"

            # Download image if not cached
            if not image_file.exists():
                download_image(cover_image, image_file)

            # Try to render the image
            if image_file.exists():
                fzf_image_preview(str(image_file))
                print()  # Spacer
            else:
                print("🖼️  Loading image...")
                print()

    # Show text info if in text or full mode
    if PREVIEW_MODE in ("text", "full"):
        # Separator line
        r, g, b = map(int, SEPARATOR_COLOR.split(","))
        separator = f"\x1b[38;2;{r};{g};{b}m" + ("─" * term_width) + "\x1b[0m"
        print(separator, flush=True)

        # Title centered
        print(title.center(term_width))

        # Extract data
        status = media.get("status", "Unknown")
        format_type = media.get("format", "Unknown")
        episodes = media.get("episodes", "??")
        duration = media.get("duration")
        duration_str = f"{duration} min/ep" if duration else "Unknown"

        score = media.get("averageScore")
        score_str = format_score_stars(score)

        favourites = format_number(media.get("favourites", 0))
        popularity = format_number(media.get("popularity", 0))

        genres = ", ".join(media.get("genres", [])) or "Unknown"

        start_date = format_date(media.get("startDate"))
        end_date = format_date(media.get("endDate"))

        studios_list = media.get("studios", {}).get("nodes", [])
        # Studios are those with isAnimationStudio=true
        studios = ", ".join([s.get("name", "") for s in studios_list if s.get("name") and s.get("isAnimationStudio")]) or "N/A"
        # Producers are those with isAnimationStudio=false
        producers = ", ".join([s.get("name", "") for s in studios_list if s.get("name") and not s.get("isAnimationStudio")]) or "N/A"

        synonyms_list = media.get("synonyms", [])
        # Include romaji in synonyms if different from title
        romaji = title_obj.get("romaji")
        if romaji and romaji != title and romaji not in synonyms_list:
            synonyms_list = [romaji] + synonyms_list
        synonyms = ", ".join(synonyms_list) or "N/A"

        # Tags
        tags_list = media.get("tags", [])
        tags = ", ".join([t.get("name", "") for t in tags_list if t.get("name")]) or "N/A"

        # Next airing episode
        next_airing = media.get("nextAiringEpisode")
        if next_airing:
            next_ep = next_airing.get("episode", "?")
            airing_at = next_airing.get("airingAt")
            if airing_at:
                from datetime import datetime
                try:
                    dt = datetime.fromtimestamp(airing_at)
                    next_episode_str = f"Episode {next_ep} on {dt.strftime('%A, %d %B %Y at %H:%M')}"
                except (ValueError, OSError):
                    next_episode_str = f"Episode {next_ep}"
            else:
                next_episode_str = f"Episode {next_ep}"
        else:
            next_episode_str = "N/A"

        # User list status
        media_list_entry = media.get("mediaListEntry")
        if media_list_entry:
            user_status = media_list_entry.get("status", "NOT_ON_LIST")
            user_progress = f"Episode {media_list_entry.get('progress', 0)}"
        else:
            user_status = "NOT_ON_LIST"
            user_progress = "0"

        description = media.get("description", "No description available.")
        description = strip_markdown(description)

        # Print sections matching media_info.py structure exactly
        rows = [
            ("Score", score_str),
            ("Favorites", favourites),
            ("Popularity", popularity),
            ("Status", status),
        ]

        print_rule(SEPARATOR_COLOR)
        for key, value in rows:
            print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

        rows = [
            ("Episodes", str(episodes)),
            ("Duration", duration_str),
            ("Next Episode", next_episode_str),
        ]

        print_rule(SEPARATOR_COLOR)
        for key, value in rows:
            print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

        rows = [
            ("Genres", genres),
            ("Format", format_type),
        ]

        print_rule(SEPARATOR_COLOR)
        for key, value in rows:
            print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

        rows = [
            ("List Status", user_status),
            ("Progress", user_progress),
        ]

        print_rule(SEPARATOR_COLOR)
        for key, value in rows:
            print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

        rows = [
            ("Start Date", start_date),
            ("End Date", end_date),
        ]

        print_rule(SEPARATOR_COLOR)
        for key, value in rows:
            print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

        rows = [
            ("Studios", studios),
            ("Producers", producers),
        ]

        print_rule(SEPARATOR_COLOR)
        for key, value in rows:
            print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

        rows = [
            ("Synonyms", synonyms),
        ]

        print_rule(SEPARATOR_COLOR)
        for key, value in rows:
            print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

        rows = [
            ("Tags", tags),
        ]

        print_rule(SEPARATOR_COLOR)
        for key, value in rows:
            print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

        print_rule(SEPARATOR_COLOR)
        print(wrap_text(description, term_width))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Preview Error: {e}", file=sys.stderr)
