#!/bin/bash
# Download OpenStax OER Content
# Downloads textbooks in CNXML format and associated images

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
RAW_DIR="$DATA_DIR/raw"

# Create directories
mkdir -p "$RAW_DIR"

echo "======================================"
echo "OpenStax Content Download"
echo "======================================"
echo ""

# OpenStax book URLs (CNXML format)
declare -A BOOKS=(
    ["physics-2e"]="https://archive.cnx.org/exports/405335a3-7cff-4df2-a9ad-29062a4af261@latest/college-physics-2e.complete.zip"
    ["chemistry-2e"]="https://archive.cnx.org/exports/7fccc9cf-9b71-44f6-800b-f9457fd64335@latest/chemistry-2e.complete.zip"
    ["biology-2e"]="https://archive.cnx.org/exports/8d50a0af-948b-4204-a71d-4826cba765b8@latest/biology-2e.complete.zip"
)

# Download each book
for book_id in "${!BOOKS[@]}"; do
    url="${BOOKS[$book_id]}"
    zip_file="$RAW_DIR/${book_id}.zip"
    extract_dir="$RAW_DIR/${book_id}"

    echo "Downloading: $book_id"
    echo "URL: $url"

    if [ -f "$zip_file" ]; then
        echo "  ✓ Already downloaded: $zip_file"
    else
        echo "  → Downloading..."
        curl -L -o "$zip_file" "$url"
        echo "  ✓ Downloaded: $zip_file"
    fi

    echo "  → Extracting..."
    rm -rf "$extract_dir"
    unzip -q "$zip_file" -d "$extract_dir"
    echo "  ✓ Extracted to: $extract_dir"
    echo ""
done

echo "======================================"
echo "Download Complete"
echo "======================================"
echo ""
echo "Downloaded books:"
for book_id in "${!BOOKS[@]}"; do
    extract_dir="$RAW_DIR/${book_id}"
    xml_file=$(find "$extract_dir" -name "*.cnxml" | head -1)
    if [ -n "$xml_file" ]; then
        echo "  ✓ $book_id ($(find "$extract_dir" -name "*.cnxml" | wc -l | tr -d ' ') CNXML files)"
    else
        echo "  ✗ $book_id (no CNXML files found)"
    fi
done
echo ""
echo "Next step: python 02_process_content.py"
