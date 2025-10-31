#!/bin/sh
#
# Viu Preview Info Script Template
# This script formats and displays the textual information in the FZF preview pane.
# Some values are injected by python those with '{name}' syntax using .replace()

draw_rule

print_kv "Title" "{TITLE}"

draw_rule

# Emojis take up double the space
score_multiplier=1
if ! [ "{SCORE}" = "N/A" ]; then
	score_multiplier=2
fi
print_kv "Score" "{SCORE}" $score_multiplier

print_kv "Favourites" "{FAVOURITES}"
print_kv "Popularity" "{POPULARITY}"
print_kv "Status" "{STATUS}"

draw_rule

print_kv "Episodes" "{EPISODES}"
print_kv "Next Episode" "{NEXT_EPISODE}"
print_kv "Duration" "{DURATION}"

draw_rule

print_kv "Genres" "{GENRES}"
print_kv "Format" "{FORMAT}"

draw_rule

print_kv "List Status" "{USER_STATUS}"
print_kv "Progress" "{USER_PROGRESS}"

draw_rule

print_kv "Start Date" "{START_DATE}"
print_kv "End Date" "{END_DATE}"

draw_rule

print_kv "Studios" "{STUDIOS}"
print_kv "Synonymns" "{SYNONYMNS}"
print_kv "Tags" "{TAGS}"

draw_rule

# Synopsis
echo "{SYNOPSIS}" | fold -s -w "$WIDTH"
