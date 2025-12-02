import sys
from _ansi_utils import print_rule, print_table_row, get_terminal_width

HEADER_COLOR = sys.argv[1]
SEPARATOR_COLOR = sys.argv[2]

# Get terminal dimensions
term_width = get_terminal_width()

# Print title centered
print("{TITLE}".center(term_width))

rows = [
    ("Duration", "{DURATION}"),
    ("Status", "{STATUS}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("Total Episodes", "{EPISODES}"),
    ("Next Episode", "{NEXT_EPISODE}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("Progress", "{USER_PROGRESS}"),
    ("List Status", "{USER_STATUS}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("Start Date", "{START_DATE}"),
    ("End Date", "{END_DATE}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

print_rule(SEPARATOR_COLOR)
