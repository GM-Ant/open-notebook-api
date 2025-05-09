#!/bin/bash
# Comprehensive example script for processing research papers with standard transformations

# Create a new research notebook
echo "Creating new research notebook..."
NOTEBOOK_ID=$(python open_notebook_cli.py create-notebook "AI Research" "Latest findings in AI and machine learning" --json | jq -r '.id')
echo "Created notebook: $NOTEBOOK_ID"

# Define a list of URL sources to process
URL_SOURCES=(
  "https://example.com/research/paper1"
  "https://example.com/research/paper2"
  "https://example.com/research/paper3"
)

# Add all sources with standard transformations and embedding
echo "Adding sources with transformations..."
for URL in "${URL_SOURCES[@]}"; do
  echo "Processing: $URL"
  SOURCE_ID=$(python open_notebook_cli.py add-url-source "$NOTEBOOK_ID" "$URL" --transform --json | jq -r '.id')
  echo "Added source: $SOURCE_ID"
done

# Create a summary note by combining all source insights
echo "Creating summary from all sources..."
SUMMARY=""

# Get all sources in the notebook
SOURCE_IDS=$(python open_notebook_cli.py list-sources "$NOTEBOOK_ID" --json | jq -r '.[].id')

# Collect summaries from each source
for SOURCE_ID in $SOURCE_IDS; do
  # Get the "Summary" insight from each source
  INSIGHT=$(python open_notebook_cli.py get-source "$SOURCE_ID" --show-insights --json | \
    jq -r '.insights[] | select(.insight_type=="Summary") | .content')
  
  # Add to combined summary
  SUMMARY="$SUMMARY\n\n$INSIGHT"
done

# Create a note with the combined summaries
python open_notebook_cli.py create-note "$NOTEBOOK_ID" "Combined Research Summary" "$SUMMARY" --type ai

echo "Workflow complete. All sources processed with standard transformations and summary created."
