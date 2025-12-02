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
print("{TITLE}".center(term_width))

# Define table data
rows = [
    ("Score", "{SCORE}"),
    ("Favorites", "{FAVOURITES}"),
    ("Popularity", "{POPULARITY}"),
    ("Status", "{STATUS}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("Episodes", "{EPISODES}"),
    ("Duration", "{DURATION}"),
    ("Next Episode", "{NEXT_EPISODE}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("Genres", "{GENRES}"),
    ("Format", "{FORMAT}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("List Status", "{USER_STATUS}"),
    ("Progress", "{USER_PROGRESS}"),
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

rows = [
    ("Studios", "{STUDIOS}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("Synonyms", "{SYNONYMNS}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

rows = [
    ("Tags", "{TAGS}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

print_rule(SEPARATOR_COLOR)
print(wrap_text(strip_markdown("""{SYNOPSIS}"""), term_width))
