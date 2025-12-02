import sys
from _ansi_utils import (
    print_rule,
    print_table_row,
    strip_markdown,
    wrap_text,
    get_terminal_width,
)

HEADER_COLOR = sys.argv[1]
SEPARATOR_COLOR = sys.argv[2]

# Get terminal dimensions
term_width = get_terminal_width()

# Print title centered
print("{CHARACTER_NAME}".center(term_width))

rows = [
    ("Native Name", "{CHARACTER_NATIVE_NAME}"),
    ("Gender", "{CHARACTER_GENDER}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("Age", "{CHARACTER_AGE}"),
    ("Blood Type", "{CHARACTER_BLOOD_TYPE}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("Birthday", "{CHARACTER_BIRTHDAY}"),
    ("Favourites", "{CHARACTER_FAVOURITES}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

print_rule(SEPARATOR_COLOR)
print(wrap_text(strip_markdown("""{CHARACTER_DESCRIPTION}"""), term_width))
