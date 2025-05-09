#!/bin/bash
# Example script to apply standard transformations to all existing sources in a notebook.

# Check if notebook ID is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <notebook_id>"
  echo "Example: $0 notebook:your_notebook_id_here"
  exit 1
fi

NOTEBOOK_ID=$1

echo "Applying standard transformations to all sources in notebook: $NOTEBOOK_ID"

# Get all source IDs in the notebook
SOURCE_IDS=$(python open_notebook_cli.py list-sources "$NOTEBOOK_ID" --json | jq -r '.[].id')

if [ -z "$SOURCE_IDS" ]; then
  echo "No sources found in notebook $NOTEBOOK_ID."
  exit 0
fi

# Loop through each source and apply the --transform flag
for SOURCE_ID in $SOURCE_IDS; do
  echo "Processing source: $SOURCE_ID"
  python open_notebook_cli.py apply-transformation "$SOURCE_ID" --transform
  if [ $? -eq 0 ]; then
    echo "Successfully applied standard transformations to $SOURCE_ID."
  else
    echo "Failed to apply transformations to $SOURCE_ID."
  fi
done

echo "Finished applying standard transformations to all sources in $NOTEBOOK_ID."
echo "Use 'get-source <source_id> --show-insights' to view the results for each source."
