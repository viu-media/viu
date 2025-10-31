#!/bin/bash
#
# FZF Dynamic Preview Script Template
#
# This script handles previews for dynamic search results by parsing the JSON
# search results file and extracting info for the selected item.
# The placeholders in curly braces are dynamically filled by Python using .replace()

WIDTH=${FZF_PREVIEW_COLUMNS:-80}
IMAGE_RENDERER="{IMAGE_RENDERER}"
SEARCH_RESULTS_FILE="{SEARCH_RESULTS_FILE}"
IMAGE_CACHE_PATH="{IMAGE_CACHE_PATH}"
INFO_CACHE_PATH="{INFO_CACHE_PATH}"
PATH_SEP="{PATH_SEP}"

# Color codes injected by Python
C_TITLE="{C_TITLE}"
C_KEY="{C_KEY}"
C_VALUE="{C_VALUE}"
C_RULE="{C_RULE}"
RESET="{RESET}"

# Selected item from fzf
SELECTED_ITEM={}

generate_sha256() {
    local input="$1"
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

fzf_preview() {
    file=$1
    dim=${FZF_PREVIEW_COLUMNS}x${FZF_PREVIEW_LINES}
    if [ "$dim" = x ]; then
        dim=$(stty size </dev/tty | awk "{print \$2 \"x\" \$1}")
    fi
    if ! [ "$IMAGE_RENDERER" = "icat" ] && [ -z "$KITTY_WINDOW_ID" ] && [ "$((FZF_PREVIEW_TOP + FZF_PREVIEW_LINES))" -eq "$(stty size </dev/tty | awk "{print \$1}")" ]; then
        dim=${FZF_PREVIEW_COLUMNS}x$((FZF_PREVIEW_LINES - 1))
    fi

    if [ "$IMAGE_RENDERER" = "icat" ] && [ -z "$GHOSTTY_BIN_DIR" ]; then
        if command -v kitten >/dev/null 2>&1; then
            kitten icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\$d" | sed "$(printf "\$s/\$/\033[m/")"
        elif command -v icat >/dev/null 2>&1; then
            icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\$d" | sed "$(printf "\$s/\$/\033[m/")"
        else
            kitty icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\$d" | sed "$(printf "\$s/\$/\033[m/")"
        fi
    elif [ -n "$GHOSTTY_BIN_DIR" ]; then
        if command -v kitten >/dev/null 2>&1; then
            kitten icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\$d" | sed "$(printf "\$s/\$/\033[m/")"
        elif command -v icat >/dev/null 2>&1; then
            icat --clear --transfer-mode=memory --unicode-placeholder --stdin=no --place="$dim@0x0" "$file" | sed "\$d" | sed "$(printf "\$s/\$/\033[m/")"
        else
            chafa -s "$dim" "$file"
        fi
    elif command -v chafa >/dev/null 2>&1; then
        case "$PLATFORM" in
        android) chafa -s "$dim" "$file" ;;
        windows) chafa -f sixel -s "$dim" "$file" ;;
        *) chafa -s "$dim" "$file" ;;
        esac
        echo
    elif command -v imgcat >/dev/null; then
        imgcat -W "${dim%%x*}" -H "${dim##*x}" "$file"
    else
        echo please install a terminal image viewer
        echo either icat for kitty terminal and wezterm or imgcat or chafa
    fi
}

print_kv() {
    local key="$1"
    local value="$2"
    local key_len=${#key}
    local value_len=${#value}
    local multiplier="${3:-1}"

    local padding_len=$((WIDTH - key_len - 2 - value_len * multiplier))

    if [ "$padding_len" -lt 1 ]; then
        padding_len=1
        value=$(echo $value| fold -s -w "$((WIDTH - key_len - 3))")
        printf "{C_KEY}%s:{RESET}%*s%s\\n" "$key" "$padding_len" "" " $value"
    else
        printf "{C_KEY}%s:{RESET}%*s%s\\n" "$key" "$padding_len" "" " $value"
    fi
}

draw_rule() {
    ll=2
    while [ $ll -le $FZF_PREVIEW_COLUMNS ];do
        echo -n -e "{C_RULE}─{RESET}"
        ((ll++))
    done
    echo
}

clean_html() {
    echo "$1" | sed 's/<[^>]*>//g' | sed 's/&lt;/</g' | sed 's/&gt;/>/g' | sed 's/&amp;/\&/g' | sed 's/&quot;/"/g' | sed "s/&#39;/'/g"
}

format_date() {
    local date_obj="$1"
    if [ "$date_obj" = "null" ] || [ -z "$date_obj" ]; then
        echo "N/A"
        return
    fi
    
    # Extract year, month, day from the date object
    if command -v jq >/dev/null 2>&1; then
        year=$(echo "$date_obj" | jq -r '.year // "N/A"' 2>/dev/null || echo "N/A")
        month=$(echo "$date_obj" | jq -r '.month // ""' 2>/dev/null || echo "")
        day=$(echo "$date_obj" | jq -r '.day // ""' 2>/dev/null || echo "")
    else
        year=$(echo "$date_obj" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('year', 'N/A'))" 2>/dev/null || echo "N/A")
        month=$(echo "$date_obj" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('month', ''))" 2>/dev/null || echo "")
        day=$(echo "$date_obj" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('day', ''))" 2>/dev/null || echo "")
    fi
    
    if [ "$year" = "N/A" ] || [ "$year" = "null" ]; then
        echo "N/A"
    elif [ -n "$month" ] && [ "$month" != "null" ] && [ -n "$day" ] && [ "$day" != "null" ]; then
        echo "$day/$month/$year"
    elif [ -n "$month" ] && [ "$month" != "null" ]; then
        echo "$month/$year"
    else
        echo "$year"
    fi
}

# If no selection or search results file doesn't exist, show placeholder
if [ -z "$SELECTED_ITEM" ] || [ ! -f "$SEARCH_RESULTS_FILE" ]; then
    echo "${C_TITLE}Dynamic Search Preview${RESET}"
    draw_rule
    echo "Type to search for anime..."
    echo "Results will appear here as you type."
    echo
    echo "DEBUG:"
    echo "SELECTED_ITEM='$SELECTED_ITEM'"
    echo "SEARCH_RESULTS_FILE='$SEARCH_RESULTS_FILE'"
    if [ -f "$SEARCH_RESULTS_FILE" ]; then
        echo "Search results file exists"
    else
        echo "Search results file missing"
    fi
    exit 0
fi
# Parse the search results JSON and find the matching item
if command -v jq >/dev/null 2>&1; then
    MEDIA_DATA=$(cat "$SEARCH_RESULTS_FILE" | jq --arg anime_title "$SELECTED_ITEM" '
        .data.Page.media[]? | 
        select((.title.english // .title.romaji // .title.native // "Unknown") == $anime_title )
    ' )
else
    # Fallback to Python for JSON parsing
    MEDIA_DATA=$(cat "$SEARCH_RESULTS_FILE" | python3 -c "
import json
import sys

try:
    data = json.load(sys.stdin)
    selected_item = '''$SELECTED_ITEM'''
    
    if 'data' not in data or 'Page' not in data['data'] or 'media' not in data['data']['Page']:
        sys.exit(1)
    
    media_list = data['data']['Page']['media']
    
    for media in media_list:
        title = media.get('title', {})
        english_title = title.get('english') or title.get('romaji') or title.get('native', 'Unknown')
        year = media.get('startDate', {}).get('year', 'Unknown') if media.get('startDate') else 'Unknown'
        status = media.get('status', 'Unknown')
        genres = ', '.join(media.get('genres', [])[:3]) or 'Unknown'
        display_format = f'{english_title} ({year}) [{status}] - {genres}'
        # Debug output for matching
        print(f"DEBUG: selected_item='{selected_item.strip()}' display_format='{display_format.strip()}'", file=sys.stderr)
        if selected_item.strip() == display_format.strip():
            json.dump(media, sys.stdout, indent=2)
            sys.exit(0)
    print(f"DEBUG: No match found for selected_item='{selected_item.strip()}'", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
fi

# If we couldn't find the media data, show error
if [ $? -ne 0 ] || [ -z "$MEDIA_DATA" ]; then
    echo "${C_TITLE}Preview Error${RESET}"
    draw_rule
    echo "Could not load preview data for:"
    echo "$SELECTED_ITEM"
    echo
    echo "DEBUG INFO:"
    echo "Search results file: $SEARCH_RESULTS_FILE"
    if [ -f "$SEARCH_RESULTS_FILE" ]; then
        echo "File exists, size: $(wc -c < "$SEARCH_RESULTS_FILE") bytes"
        echo "First few lines of search results:"
        head -3 "$SEARCH_RESULTS_FILE" 2>/dev/null || echo "Cannot read file"
    else
        echo "Search results file does not exist"
    fi
    exit 0
fi

# Extract information from the media data
if command -v jq >/dev/null 2>&1; then
    # Use jq for faster extraction
    TITLE=$(echo "$MEDIA_DATA" | jq -r '.title.english // .title.romaji // .title.native // "Unknown"' 2>/dev/null || echo "Unknown")
    STATUS=$(echo "$MEDIA_DATA" | jq -r '.status // "Unknown"' 2>/dev/null || echo "Unknown")
    FORMAT=$(echo "$MEDIA_DATA" | jq -r '.format // "Unknown"' 2>/dev/null || echo "Unknown")
    EPISODES=$(echo "$MEDIA_DATA" | jq -r '.episodes // "Unknown"' 2>/dev/null || echo "Unknown")
    DURATION=$(echo "$MEDIA_DATA" | jq -r 'if .duration then "\(.duration) min" else "Unknown" end' 2>/dev/null || echo "Unknown")
    SCORE=$(echo "$MEDIA_DATA" | jq -r 'if .averageScore then "\(.averageScore)/100" else "N/A" end' 2>/dev/null || echo "N/A")
    FAVOURITES=$(echo "$MEDIA_DATA" | jq -r '.favourites // 0' 2>/dev/null | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta' || echo "0")
    POPULARITY=$(echo "$MEDIA_DATA" | jq -r '.popularity // 0' 2>/dev/null | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta' || echo "0")
    GENRES=$(echo "$MEDIA_DATA" | jq -r '(.genres[:5] // []) | join(", ") | if . == "" then "Unknown" else . end' 2>/dev/null || echo "Unknown")
    DESCRIPTION=$(echo "$MEDIA_DATA" | jq -r '.description // "No description available."' 2>/dev/null || echo "No description available.")
    
    # Get start and end dates as JSON objects
    START_DATE_OBJ=$(echo "$MEDIA_DATA" | jq -c '.startDate' 2>/dev/null || echo "null")
    END_DATE_OBJ=$(echo "$MEDIA_DATA" | jq -c '.endDate' 2>/dev/null || echo "null")
    
    # Get cover image URL
    COVER_IMAGE=$(echo "$MEDIA_DATA" | jq -r '.coverImage.large // ""' 2>/dev/null || echo "")
else
    # Fallback to Python for extraction
    TITLE=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); title=data.get('title',{}); print(title.get('english') or title.get('romaji') or title.get('native', 'Unknown'))" 2>/dev/null || echo "Unknown")
    STATUS=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('status', 'Unknown'))" 2>/dev/null || echo "Unknown")
    FORMAT=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('format', 'Unknown'))" 2>/dev/null || echo "Unknown")
    EPISODES=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('episodes', 'Unknown'))" 2>/dev/null || echo "Unknown")
    DURATION=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); duration=data.get('duration'); print(f'{duration} min' if duration else 'Unknown')" 2>/dev/null || echo "Unknown")
    SCORE=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); score=data.get('averageScore'); print(f'{score}/100' if score else 'N/A')" 2>/dev/null || echo "N/A")
    FAVOURITES=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); print(f\"{data.get('favourites', 0):,}\")" 2>/dev/null || echo "0")
    POPULARITY=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); print(f\"{data.get('popularity', 0):,}\")" 2>/dev/null || echo "0")
    GENRES=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); print(', '.join(data.get('genres', [])[:5]))" 2>/dev/null || echo "Unknown")
    DESCRIPTION=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('description', 'No description available.'))" 2>/dev/null || echo "No description available.")
    
    # Get start and end dates
    START_DATE_OBJ=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); json.dump(data.get('startDate'), sys.stdout)" 2>/dev/null || echo "null")
    END_DATE_OBJ=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); json.dump(data.get('endDate'), sys.stdout)" 2>/dev/null || echo "null")
    
    # Get cover image URL
    COVER_IMAGE=$(echo "$MEDIA_DATA" | python3 -c "import json, sys; data=json.load(sys.stdin); cover=data.get('coverImage',{}); print(cover.get('large', ''))" 2>/dev/null || echo "")
fi

# Format the dates
START_DATE=$(format_date "$START_DATE_OBJ")
END_DATE=$(format_date "$END_DATE_OBJ")

# Generate cache hash for this item (using selected item like regular preview)
CACHE_HASH=$(generate_sha256 "$SELECTED_ITEM")

# Try to show image if available
if [ "{PREVIEW_MODE}" = "full" ] || [ "{PREVIEW_MODE}" = "image" ]; then
    image_file="{IMAGE_CACHE_PATH}{PATH_SEP}${CACHE_HASH}.png"
    
    # If image not cached and we have a URL, try to download it quickly
    if [ ! -f "$image_file" ] && [ -n "$COVER_IMAGE" ]; then
        if command -v curl >/dev/null 2>&1; then
            # Quick download with timeout
            curl -s -m 3 -L "$COVER_IMAGE" -o "$image_file" 2>/dev/null || rm -f "$image_file" 2>/dev/null
        fi
    fi
    
    if [ -f "$image_file" ]; then
        fzf_preview "$image_file"
    else
        echo "🖼️  Loading image..."
    fi
    echo
fi

# Display text info if configured
if [ "{PREVIEW_MODE}" = "full" ] || [ "{PREVIEW_MODE}" = "text" ]; then
    draw_rule
    print_kv "Title" "$TITLE"
    draw_rule
    
    print_kv "Score" "$SCORE"
    print_kv "Favourites" "$FAVOURITES"
    print_kv "Popularity" "$POPULARITY"
    print_kv "Status" "$STATUS"
    
    draw_rule
    
    print_kv "Episodes" "$EPISODES"
    print_kv "Duration" "$DURATION"
    print_kv "Format" "$FORMAT"
    
    draw_rule
    
    print_kv "Genres" "$GENRES"
    print_kv "Start Date" "$START_DATE"
    print_kv "End Date" "$END_DATE"
    
    draw_rule
    
    # Clean and display description
    CLEAN_DESCRIPTION=$(clean_html "$DESCRIPTION")
    echo "$CLEAN_DESCRIPTION" | fold -s -w "$WIDTH"
fi
