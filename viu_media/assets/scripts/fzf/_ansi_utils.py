"""
ANSI utilities for FZF preview scripts.

Lightweight stdlib-only utilities to replace Rich dependency in preview scripts.
Provides RGB color formatting, table rendering, and markdown stripping.
"""

import os
import re
import shutil
import textwrap
import unicodedata


def get_terminal_width() -> int:
    """
    Get terminal width, prioritizing FZF preview environment variables.

    Returns:
        Terminal width in columns
    """
    fzf_cols = os.environ.get("FZF_PREVIEW_COLUMNS")
    if fzf_cols:
        return int(fzf_cols)
    return shutil.get_terminal_size((80, 24)).columns


def display_width(text: str) -> int:
    """
    Calculate the actual display width of text, accounting for wide characters.

    Args:
        text: Text to measure

    Returns:
        Display width in terminal columns
    """
    width = 0
    for char in text:
        # East Asian Width property: 'F' (Fullwidth) and 'W' (Wide) take 2 columns
        if unicodedata.east_asian_width(char) in ("F", "W"):
            width += 2
        else:
            width += 1
    return width


def rgb_color(r: int, g: int, b: int, text: str, bold: bool = False) -> str:
    """
    Format text with RGB color using ANSI escape codes.

    Args:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
        text: Text to colorize
        bold: Whether to make text bold

    Returns:
        ANSI-escaped colored text
    """
    color_code = f"\x1b[38;2;{r};{g};{b}m"
    bold_code = "\x1b[1m" if bold else ""
    reset = "\x1b[0m"
    return f"{color_code}{bold_code}{text}{reset}"


def parse_color(color_csv: str) -> tuple[int, int, int]:
    """
    Parse RGB color from comma-separated string.

    Args:
        color_csv: Color as 'R,G,B' string

    Returns:
        Tuple of (r, g, b) integers
    """
    parts = color_csv.split(",")
    return int(parts[0]), int(parts[1]), int(parts[2])


def print_rule(sep_color: str) -> None:
    """
    Print a horizontal rule line.

    Args:
        sep_color: Color as 'R,G,B' string
    """
    width = get_terminal_width()
    r, g, b = parse_color(sep_color)
    print(rgb_color(r, g, b, "─" * width))


def print_table_row(
    key: str, value: str, header_color: str, key_width: int, value_width: int
) -> None:
    """
    Print a two-column table row with left-aligned key and right-aligned value.

    Args:
        key: Left column text (header/key)
        value: Right column text (value)
        header_color: Color for key as 'R,G,B' string
        key_width: Width for key column
        value_width: Width for value column
    """
    r, g, b = parse_color(header_color)
    key_styled = rgb_color(r, g, b, key, bold=True)

    # Get actual terminal width
    term_width = get_terminal_width()

    # Calculate display widths accounting for wide characters
    key_display_width = display_width(key)

    # Calculate actual value width based on terminal and key display width
    actual_value_width = max(20, term_width - key_display_width - 2)

    # Wrap value if it's too long (use character count, not display width for wrapping)
    value_lines = textwrap.wrap(str(value), width=actual_value_width) if value else [""]

    if not value_lines:
        value_lines = [""]

    # Print first line with properly aligned value
    first_line = value_lines[0]
    first_line_display_width = display_width(first_line)

    # Use manual spacing to right-align based on display width
    spacing = term_width - key_display_width - first_line_display_width - 2
    if spacing > 0:
        print(f"{key_styled}  {' ' * spacing}{first_line}")
    else:
        print(f"{key_styled}  {first_line}")

    # Print remaining wrapped lines (left-aligned, indented)
    for line in value_lines[1:]:
        print(f"{' ' * (key_display_width + 2)}{line}")


def strip_markdown(text: str) -> str:
    """
    Strip markdown formatting from text.

    Removes:
    - Headers (# ## ###)
    - Bold (**text** or __text__)
    - Italic (*text* or _text_)
    - Links ([text](url))
    - Code blocks (```code```)
    - Inline code (`code`)

    Args:
        text: Markdown-formatted text

    Returns:
        Plain text with markdown removed
    """
    if not text:
        return ""

    # Remove code blocks first
    text = re.sub(r"```[\s\S]*?```", "", text)

    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Remove headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove bold (** or __)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)

    # Remove italic (* or _)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)

    # Remove links, keep text
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

    # Remove images
    text = re.sub(r"!\[.*?\]\(.+?\)", "", text)

    return text.strip()


def wrap_text(text: str, width: int | None = None) -> str:
    """
    Wrap text to terminal width.

    Args:
        text: Text to wrap
        width: Width to wrap to (defaults to terminal width)

    Returns:
        Wrapped text
    """
    if width is None:
        width = get_terminal_width()

    return textwrap.fill(text, width=width)
