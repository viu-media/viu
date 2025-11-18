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


console.print("{TITLE}", justify="center")

left = [
    ("Duration", "Status"),
    ("Total Episodes", "Next Episode"),
    ("Progress", "List Status"),
    ("Start Date", "End Date"),
]
right = [
    ("{DURATION}", "{STATUS}"),
    ("{EPISODES}", "{NEXT_EPISODE}"),
    ("{USER_PROGRESS}", "{USER_STATUS}"),
    ("{START_DATE}", "{END_DATE}"),
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
