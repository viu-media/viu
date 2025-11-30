import sys
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from rich.markdown import Markdown

console = Console(force_terminal=True, color_system="truecolor")

HEADER_COLOR = sys.argv[1]
SEPARATOR_COLOR = sys.argv[2]


def rule(title: str | None = None):
    console.print(Rule(style=f"rgb({SEPARATOR_COLOR})"))


console.print("{CHARACTER_NAME}", justify="center")

left = [
    ("Native Name", "Gender"),
    ("Age", "Blood Type"),
    ("Birthday", "Favourites"),
]
right = [
    ("{CHARACTER_NATIVE_NAME}", "{CHARACTER_GENDER}"),
    ("{CHARACTER_AGE}", "{CHARACTER_BLOOD_TYPE}"),
    ("{CHARACTER_BIRTHDAY}", "{CHARACTER_FAVOURITES}"),
]


for L_grp, R_grp in zip(left, right):
    table = Table.grid(expand=True)
    table.add_column(justify="left", no_wrap=True)
    table.add_column(justify="right", overflow="fold")
    for L, R in zip(L_grp, R_grp):
        table.add_row(f"[bold rgb({HEADER_COLOR})]{L} [/]", f"{R}")

    rule()
    console.print(table)


rule()
console.print(Markdown("""{CHARACTER_DESCRIPTION}"""))
