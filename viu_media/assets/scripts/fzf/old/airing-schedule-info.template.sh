#!/bin/sh
#
# Viu Airing Schedule Info Script Template
# This script formats and displays airing schedule details in the FZF preview pane.
# Python injects the actual data values into the placeholders.

draw_rule

print_kv "Anime Title" "{ANIME_TITLE}"

draw_rule

print_kv "Total Episodes" "{TOTAL_EPISODES}"
print_kv "Upcoming Episodes" "{UPCOMING_EPISODES}"

draw_rule

echo "{C_KEY}Next Episodes:{RESET}"
echo
echo "{SCHEDULE_TABLE}" | fold -s -w "$WIDTH"

draw_rule
