#!/bin/bash

# Set variables
CLI_URL="https://github.com/tailwindlabs/tailwindcss/releases/download/v4.0.0/tailwindcss-linux-x64"
CLI_FILE="tailwindcss"

# Download the standalone CLI if not already present
if [ ! -f "$CLI_FILE" ]; then
    echo "Downloading Tailwind CSS v4 standalone CLI..."
    curl -sLO "$CLI_URL"
    chmod +x "$CLI_FILE"
else
    echo "Tailwind CLI already exists."
fi
