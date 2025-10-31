#!/bin/sh
#
# Viu Character Info Script Template
# This script formats and displays character details in the FZF preview pane.
# Python injects the actual data values into the placeholders.

draw_rule

print_kv "Character Name" "{CHARACTER_NAME}"

if [ -n "{CHARACTER_NATIVE_NAME}" ] && [ "{CHARACTER_NATIVE_NAME}" != "N/A" ]; then
    print_kv "Native Name" "{CHARACTER_NATIVE_NAME}"
fi

draw_rule

if [ -n "{CHARACTER_GENDER}" ] && [ "{CHARACTER_GENDER}" != "Unknown" ]; then
    print_kv "Gender" "{CHARACTER_GENDER}"
fi

if [ -n "{CHARACTER_AGE}" ] && [ "{CHARACTER_AGE}" != "Unknown" ]; then
    print_kv "Age" "{CHARACTER_AGE}"
fi

if [ -n "{CHARACTER_BLOOD_TYPE}" ] && [ "{CHARACTER_BLOOD_TYPE}" != "N/A" ]; then
    print_kv "Blood Type" "{CHARACTER_BLOOD_TYPE}"
fi

if [ -n "{CHARACTER_BIRTHDAY}" ] && [ "{CHARACTER_BIRTHDAY}" != "N/A" ]; then
    print_kv "Birthday" "{CHARACTER_BIRTHDAY}"
fi

if [ -n "{CHARACTER_FAVOURITES}" ] && [ "{CHARACTER_FAVOURITES}" != "0" ]; then
    print_kv "Favorites" "{CHARACTER_FAVOURITES}"
fi

draw_rule

echo "{CHARACTER_DESCRIPTION}" | fold -s -w "$WIDTH"

draw_rule
