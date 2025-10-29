"""
CNXML Parser for OpenStax Content

Parses CNXML (Connexions XML) format and extracts structured content.
"""

import os
import re
from typing import List, Dict, Optional
from pathlib import Path

from lxml import etree
from bs4 import BeautifulSoup


class CNXMLParser:
    """
    Parser for OpenStax CNXML format.

    Extracts:
    - Chapters and sections
    - Text content (paragraphs, examples)
    - Figures and captions
    - Learning objectives
    - Metadata
    """

    def __init__(self):
        """Initialize parser with CNXML namespace."""
        self.ns = {
            'cnxml': 'http://cnx.rice.edu/cnxml',
            'md': 'http://cnx.rice.edu/mdml',
            'm': 'http://www.w3.org/1998/Math/MathML'
        }

    def parse_book(self, book_dir: str, subject: str) -> Dict:
        """
        Parse entire book from directory.

        Args:
            book_dir: Directory containing extracted CNXML files
            subject: Subject area (physics, chemistry, biology, cs)

        Returns:
            Structured book data with chapters and sections
        """
        book_dir = Path(book_dir)

        # Find collection.xml (table of contents)
        collection_file = book_dir / 'collection.xml'
        if not collection_file.exists():
            raise FileNotFoundError(f"collection.xml not found in {book_dir}")

        # Parse collection metadata
        tree = etree.parse(str(collection_file))
        root = tree.getroot()

        # Extract book metadata
        metadata = self._extract_metadata(root)

        # Extract chapter structure
        chapters = self._extract_chapters(root, book_dir, subject)

        return {
            'title': metadata.get('title', 'Unknown'),
            'author': metadata.get('author', 'OpenStax'),
            'license': 'CC BY 4.0',
            'subject': subject,
            'metadata': metadata,
            'chapters': chapters
        }

    def _extract_metadata(self, root: etree.Element) -> Dict:
        """Extract book metadata from collection.xml."""
        metadata = {}

        # Title
        title_elem = root.find('.//md:title', self.ns)
        if title_elem is not None:
            metadata['title'] = title_elem.text

        # Authors
        authors = []
        for person in root.findall('.//md:person', self.ns):
            name_elem = person.find('.//md:fullname', self.ns)
            if name_elem is not None:
                authors.append(name_elem.text)
        metadata['authors'] = authors

        # License
        license_elem = root.find('.//md:license', self.ns)
        if license_elem is not None:
            metadata['license_url'] = license_elem.get('url')

        return metadata

    def _extract_chapters(self, root: etree.Element, book_dir: Path, subject: str) -> List[Dict]:
        """Extract all chapters from collection.xml."""
        chapters = []

        # Find all modules (chapters/sections)
        for i, module in enumerate(root.findall('.//col:module',
                                                 {'col': 'http://cnx.rice.edu/collxml'})):
            document = module.get('document')
            if not document:
                continue

            # Find corresponding CNXML file
            module_file = book_dir / f'{document}.cnxml'
            if not module_file.exists():
                # Try alternate locations
                module_file = self._find_module_file(book_dir, document)
                if not module_file:
                    continue

            # Parse module content
            chapter_data = self._parse_module(module_file, subject, i)
            if chapter_data:
                chapters.append(chapter_data)

        return chapters

    def _find_module_file(self, book_dir: Path, document: str) -> Optional[Path]:
        """Find module file in subdirectories."""
        for cnxml_file in book_dir.rglob('*.cnxml'):
            if document in cnxml_file.stem:
                return cnxml_file
        return None

    def _parse_module(self, module_file: Path, subject: str, chapter_num: int) -> Optional[Dict]:
        """Parse individual module (chapter/section)."""
        try:
            tree = etree.parse(str(module_file))
            root = tree.getroot()

            # Extract title
            title_elem = root.find('.//cnxml:title', self.ns)
            title = title_elem.text if title_elem is not None else f"Chapter {chapter_num + 1}"

            # Extract content blocks
            content_blocks = self._extract_content_blocks(root)

            if not content_blocks:
                return None

            return {
                'id': f'chapter-{chapter_num + 1:02d}',
                'title': title,
                'subject': subject,
                'content_blocks': content_blocks
            }

        except Exception as e:
            print(f"Error parsing {module_file}: {e}")
            return None

    def _extract_content_blocks(self, root: etree.Element) -> List[Dict]:
        """Extract all content blocks (paragraphs, examples, etc.) from module."""
        blocks = []

        # Find content section
        content = root.find('.//cnxml:content', self.ns)
        if content is None:
            return blocks

        # Extract paragraphs
        for para in content.findall('.//cnxml:para', self.ns):
            text = self._extract_text(para)
            if text and len(text.strip()) > 50:  # Minimum length
                blocks.append({
                    'type': 'paragraph',
                    'text': text
                })

        # Extract examples
        for example in content.findall('.//cnxml:example', self.ns):
            title_elem = example.find('.//cnxml:title', self.ns)
            title = title_elem.text if title_elem is not None else "Example"

            text = self._extract_text(example)
            if text:
                blocks.append({
                    'type': 'example',
                    'title': title,
                    'text': text
                })

        # Extract figures
        for figure in content.findall('.//cnxml:figure', self.ns):
            caption_elem = figure.find('.//cnxml:caption', self.ns)
            caption = self._extract_text(caption_elem) if caption_elem is not None else ""

            if caption:
                blocks.append({
                    'type': 'figure',
                    'caption': caption
                })

        # Extract learning objectives (notes with class="learning-objectives")
        for note in content.findall('.//cnxml:note', self.ns):
            note_class = note.get('class', '')
            if 'learning-objective' in note_class.lower():
                text = self._extract_text(note)
                if text:
                    blocks.append({
                        'type': 'learning_objective',
                        'text': text
                    })

        return blocks

    def _extract_text(self, element: etree.Element) -> str:
        """
        Extract clean text from XML element.

        Handles:
        - Nested elements
        - Math equations (converts to LaTeX-like text)
        - Special formatting
        """
        if element is None:
            return ""

        # Convert to string and parse with BeautifulSoup for easier text extraction
        xml_string = etree.tostring(element, encoding='unicode')
        soup = BeautifulSoup(xml_string, 'lxml')

        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()

        # Handle math elements
        for math in soup.find_all(['math', 'm:math']):
            # Convert to placeholder text
            math.string = ' [MATH] '

        # Get text
        text = soup.get_text(separator=' ', strip=True)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text


def main():
    """Test parser with sample book."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python xml_parser.py <book_directory> <subject>")
        sys.exit(1)

    book_dir = sys.argv[1]
    subject = sys.argv[2]

    parser = CNXMLParser()
    book_data = parser.parse_book(book_dir, subject)

    print(f"Title: {book_data['title']}")
    print(f"Subject: {book_data['subject']}")
    print(f"Chapters: {len(book_data['chapters'])}")

    total_blocks = sum(len(ch['content_blocks']) for ch in book_data['chapters'])
    print(f"Total content blocks: {total_blocks}")


if __name__ == '__main__':
    main()
