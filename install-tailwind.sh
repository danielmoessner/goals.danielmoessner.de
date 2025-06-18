#!/bin/bash

CLI_URL="https://github.com/tailwindlabs/tailwindcss/releases/download/v4.1.10/tailwindcss-macos-arm64"
CLI_FILE="tailwindcss"

echo "Downloading Tailwind CSS v4 standalone CLI..."
curl -sL "$CLI_URL" -o "./$CLI_FILE"
chmod +x "$CLI_FILE"
