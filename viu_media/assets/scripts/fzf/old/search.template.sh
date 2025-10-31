#!/bin/bash
#
# FZF Dynamic Search Script Template
#
# This script is a template for dynamic search functionality in fzf.
# The placeholders in curly braces, like {QUERY} are dynamically filled by Python using .replace()

# Configuration variables (injected by Python)
GRAPHQL_ENDPOINT="{GRAPHQL_ENDPOINT}"
CACHE_DIR="{CACHE_DIR}"
SEARCH_RESULTS_FILE="{SEARCH_RESULTS_FILE}"
AUTH_HEADER="{AUTH_HEADER}"

# Get the current query from fzf
QUERY="{{q}}"

# If query is empty, exit with empty results
if [ -z "$QUERY" ]; then
    echo ""
    exit 0
fi

# Create GraphQL variables
VARIABLES=$(cat <<EOF
{
    "query": "$QUERY",
    "type": "ANIME",
    "per_page": 50,
    "genre_not_in": ["Hentai"]
}
EOF
)

# The GraphQL query is injected here as a properly escaped string
GRAPHQL_QUERY='{GRAPHQL_QUERY}'

# Create the GraphQL request payload
PAYLOAD=$(cat <<EOF
{
    "query": $GRAPHQL_QUERY,
    "variables": $VARIABLES
}
EOF
)

# Make the GraphQL request and save raw results
if [ -n "$AUTH_HEADER" ]; then
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: $AUTH_HEADER" \
        -d "$PAYLOAD" \
        "$GRAPHQL_ENDPOINT")
else
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" \
        "$GRAPHQL_ENDPOINT")
fi

# Check if the request was successful
if [ $? -ne 0 ] || [ -z "$RESPONSE" ]; then
    echo "❌ Search failed"
    exit 1
fi

# Save the raw response for later processing
echo "$RESPONSE" > "$SEARCH_RESULTS_FILE"

# Parse and display results
if command -v jq >/dev/null 2>&1; then
    # Use jq for faster and more reliable JSON parsing
    echo "$RESPONSE" | jq -r '
        if .errors then
            "❌ Search error: " + (.errors | tostring)
        elif (.data.Page.media // []) | length == 0 then
            "❌ No results found"
        else
            .data.Page.media[] | (.title.english // .title.romaji // .title.native // "Unknown")
        end
    ' 2>/dev/null || echo "❌ Parse error"
else
    # Fallback to Python for JSON parsing
    echo "$RESPONSE" | python3 -c "
import json
import sys

try:
    data = json.load(sys.stdin)
    
    if 'errors' in data:
        print('❌ Search error: ' + str(data['errors']))
        sys.exit(1)
    
    if 'data' not in data or 'Page' not in data['data'] or 'media' not in data['data']['Page']:
        print('❌ No results found')
        sys.exit(0)
    
    media_list = data['data']['Page']['media']
    
    if not media_list:
        print('❌ No results found')
        sys.exit(0)
    
    for media in media_list:
        title = media.get('title', {})
        english_title = title.get('english') or title.get('romaji') or title.get('native', 'Unknown')
        year = media.get('startDate', {}).get('year', 'Unknown') if media.get('startDate') else 'Unknown'
        status = media.get('status', 'Unknown')
        genres = ', '.join(media.get('genres', [])[:3]) or 'Unknown'
        
        # Format: Title (Year) [Status] - Genres
        print(f'{english_title} ({year}) [{status}] - {genres}')
        
except Exception as e:
    print(f'❌ Parse error: {str(e)}')
    sys.exit(1)
"
fi
