#!/bin/bash
# Download OpenStax OER Content (PDF Format)
# Downloads textbooks in PDF format from CloudFront CDN

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
RAW_DIR="$DATA_DIR/raw_pdf"

# Create directories
mkdir -p "$RAW_DIR"

echo "======================================"
echo "OpenStax PDF Content Download"
echo "======================================"
echo ""
echo "Note: Downloading PDFs from CloudFront CDN"
echo "      (archive.cnx.org CNXML source is offline)"
echo ""

# OpenStax PDF URLs (CloudFront CDN)
# Format: "book_id|url"
BOOKS=(
    "physics_2e|https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/College_Physics_2e-WEB.pdf"
    "chemistry_2e|https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/Chemistry2e-WEB.pdf"
    "biology_2e|https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/Biology2e-WEB.pdf"
    "precalculus_2e|https://d3bxy9euw4e147.cloudfront.net/oscms-prodcms/media/documents/Precalculus_2e-WEB.pdf"
)

# Download each book
for book_entry in "${BOOKS[@]}"; do
    book_id="${book_entry%%|*}"
    url="${book_entry##*|}"
    pdf_file="$RAW_DIR/${book_id}.pdf"

    echo "Downloading: $book_id"
    echo "URL: $url"

    if [ -f "$pdf_file" ]; then
        echo "  ✓ Already downloaded: $pdf_file"
    else
        echo "  → Downloading..."
        curl -L -o "$pdf_file" "$url"

        if [ -f "$pdf_file" ]; then
            file_size_mb=$(du -m "$pdf_file" | cut -f1)
            echo "  ✓ Downloaded: $pdf_file (${file_size_mb} MB)"
        else
            echo "  ✗ Download failed: $pdf_file"
        fi
    fi
    echo ""
done

echo "======================================"
echo "Download Complete"
echo "======================================"
echo ""
echo "Downloaded books:"
for book_entry in "${BOOKS[@]}"; do
    book_id="${book_entry%%|*}"
    pdf_file="$RAW_DIR/${book_id}.pdf"
    if [ -f "$pdf_file" ]; then
        file_size_mb=$(du -m "$pdf_file" | cut -f1)
        echo "  ✓ $book_id (${file_size_mb} MB)"
    else
        echo "  ✗ $book_id (download failed)"
    fi
done
echo ""
echo "Next step: python 02_process_pdf.py"
