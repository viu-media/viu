import sys
import shutil
from _ansi_utils import print_rule, print_table_row, strip_markdown, wrap_text

HEADER_COLOR = sys.argv[1]
SEPARATOR_COLOR = sys.argv[2]

# Get terminal dimensions
term_width = shutil.get_terminal_size((80, 24)).columns

# Print title centered
print("{REVIEWER_NAME}".center(term_width))

rows = [
    ("Summary", "{REVIEW_SUMMARY}"),
]

print_rule(SEPARATOR_COLOR)
for key, value in rows:
    print_table_row(key, value, HEADER_COLOR, 15, term_width - 20)

print_rule(SEPARATOR_COLOR)
print(wrap_text(strip_markdown("""{REVIEW_BODY}"""), term_width))
