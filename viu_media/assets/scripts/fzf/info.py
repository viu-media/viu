import sys
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from rich.markdown import Markdown

console = Console(force_terminal=True, color_system="truecolor")

HEADER_COLOR = sys.argv[1]
SEPARATOR_COLOR = sys.argv[2]

console.print("{TITLE}", justify="center")

left = [
    (
        "Score",
        "Favorites",
        "Popularity",
        "Status",
    ),
    (
        "Episodes",
        "Next Episode",
        "Duration",
    ),
    (
        "Genres",
        "Format",
    ),
    (
        "List Status",
        "Progress",
    ),
    (
        "Start Date",
        "End Date",
    ),
    ("Studios",),
    ("Synonymns",),
    ("Tags",),
]
right = [
    (
        "{SCORE}",
        "{FAVOURITES}",
        "{POPULARITY}",
        "{STATUS}",
    ),
    (
        "{EPISODES}",
        "{NEXT_EPISODE}",
        "{DURATION}",
    ),
    (
        "{GENRES}",
        "{FORMAT}",
    ),
    (
        "{USER_STATUS}",
        "{USER_PROGRESS}",
    ),
    (
        "{START_DATE}",
        "{END_DATE}",
    ),
    ("{STUDIOS}",),
    ("{SYNONYMNS}",),
    ("{TAGS}",),
]


for L_grp, R_grp in zip(left, right):
    table = Table.grid(expand=True)
    table.add_column(justify="left", no_wrap=True)
    table.add_column(justify="right", overflow="fold")
    for L, R in zip(L_grp, R_grp):
        table.add_row(f"[bold rgb({HEADER_COLOR})]{L}: [/]", f"{R}")

    console.print(Rule(style=f"rgb({SEPARATOR_COLOR})"))
    console.print(table)

console.print(Rule(title="Description", style=f"rgb({SEPARATOR_COLOR})"))
console.print(Markdown("""{SYNOPSIS}"""))
