#!/bin/sh
#
# FZF Airing Schedule Preview Script Template
#
# This script is a template. The placeholders in curly braces, like {NAME}
# are dynamically filled by python using .replace()

WIDTH=${FZF_PREVIEW_COLUMNS:-80} # Set a fallback width of 80
IMAGE_RENDERER="{IMAGE_RENDERER}"

generate_sha256() {
  local input

  # Check if input is passed as an argument or piped
  if [ -n "$1" ]; then
    input="$1"
  else
    input=$(cat)
  fi

  if command -v sha256sum &>/dev/null; then
    echo -n "$input" | sha256sum | awk '{print $1}'
  elif command -v shasum &>/dev/null; then
    echo -n "$input" | shasum -a 256 | awk '{print $1}'
  elif command -v sha256 &>/dev/null; then
    echo -n "$input" | sha256 | awk '{print $1}'
  elif command -v openssl &>/dev/null; then
    echo -n "$input" | openssl dgst -sha256 | awk '{print $2}'
  else
    echo -n "$input" | base64 | tr '/+' '_-' | tr -d '\n'
  fi
}


print_kv() {
    local key="$1"
    local value="$2"
    local key_len=${#key}
    local value_len=${#value}
    local multiplier="${3:-1}"

    # Correctly calculate padding by accounting for the key, the ": ", and the value.
    local padding_len=$((WIDTH - key_len - 2 - value_len * multiplier))

    # If the text is too long to fit, just add a single space for separation.
    if [ "$padding_len" -lt 1 ]; then
        padding_len=1
        value=$(echo $value| fold -s -w "$((WIDTH - key_len - 3))")
        printf "{C_KEY}%s:{RESET}%*s%s\\n" "$key" "$padding_len" "" " $value"
    else
        printf "{C_KEY}%s:{RESET}%*s%s\\n" "$key" "$padding_len" "" " $value"
    fi
}


draw_rule(){
    ll=2
    while [ $ll -le $FZF_PREVIEW_COLUMNS ];do
        echo -n -e "{C_RULE}─{RESET}"
        ((ll++))
    done
    echo
}

title={}
hash=$(generate_sha256 "$title")

if [ "{PREVIEW_MODE}" = "full" ] || [ "{PREVIEW_MODE}" = "text" ]; then
    info_file="{INFO_CACHE_DIR}{PATH_SEP}$hash"
    if [ -f "$info_file" ]; then
        source "$info_file"
    else
        echo "📅 Loading airing schedule..."
    fi
fi
