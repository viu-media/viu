#!/bin/sh
#
# Episode Preview Info Script Template
# This script formats and displays episode information in the FZF preview pane.
# Some values are injected by python those with '{name}' syntax using .replace()

draw_rule

echo "{TITLE}" | fold -s -w "$WIDTH"

draw_rule

print_kv "Duration" "{DURATION}"
print_kv "Status" "{STATUS}"

draw_rule

print_kv "Total Episodes" "{EPISODES}"
print_kv "Next Episode" "{NEXT_EPISODE}"

draw_rule

print_kv "Progress" "{USER_PROGRESS}"
print_kv "List Status" "{USER_STATUS}"

draw_rule

print_kv "Start Date" "{START_DATE}"
print_kv "End Date" "{END_DATE}"

draw_rule
