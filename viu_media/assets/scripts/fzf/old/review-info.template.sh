#!/bin/sh
#
# Viu Review Info Script Template
# This script formats and displays review details in the FZF preview pane.
# Python injects the actual data values into the placeholders.

draw_rule

print_kv "Review By" "{REVIEWER_NAME}"

draw_rule

print_kv "Summary" "{REVIEW_SUMMARY}"

draw_rule

echo "{REVIEW_BODY}" | fold -s -w "$WIDTH"

draw_rule
