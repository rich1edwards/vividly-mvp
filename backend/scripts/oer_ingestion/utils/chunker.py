"""
Text Chunking Utility

Splits content into 500-word chunks with overlap for embedding generation.
"""

import re
from typing import List, Dict
import tiktoken


class TextChunker:
    """
    Splits text into chunks suitable for embedding generation.

    Parameters:
    - Target chunk size: 500 words
    - Minimum: 300 words
    - Maximum: 800 words
    - Overlap: 50 words
    """

    def __init__(
        self,
        target_size: int = 500,
        min_size: int = 300,
        max_size: int = 800,
        overlap: int = 50,
    ):
        """
        Initialize chunker.

        Args:
            target_size: Target chunk size in words
            min_size: Minimum chunk size
            max_size: Maximum chunk size
            overlap: Overlap between chunks in words
        """
        self.target_size = target_size
        self.min_size = min_size
        self.max_size = max_size
        self.overlap = overlap

        # Initialize tokenizer for accurate token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def chunk_book(self, book_data: Dict) -> List[Dict]:
        """
        Chunk entire book into embeddings-ready chunks.

        Args:
            book_data: Parsed book data from CNXMLParser

        Returns:
            List of chunks with metadata
        """
        chunks = []
        chunk_counter = 0

        for chapter in book_data["chapters"]:
            chapter_chunks = self._chunk_chapter(
                chapter, book_data["title"], book_data["subject"], chunk_counter
            )
            chunks.extend(chapter_chunks)
            chunk_counter += len(chapter_chunks)

        return chunks

    def _chunk_chapter(
        self, chapter: Dict, book_title: str, subject: str, start_index: int
    ) -> List[Dict]:
        """Chunk a single chapter."""
        chunks = []

        # Combine all content blocks into sequential text
        text_segments = []
        for block in chapter["content_blocks"]:
            if block["type"] == "paragraph":
                text_segments.append(block["text"])
            elif block["type"] == "example":
                text_segments.append(f"{block['title']}: {block['text']}")
            elif block["type"] == "learning_objective":
                text_segments.append(f"Learning Objective: {block['text']}")
            elif block["type"] == "figure":
                text_segments.append(f"Figure: {block['caption']}")

        # Join into full chapter text
        full_text = " ".join(text_segments)

        # Split into words
        words = self._tokenize_words(full_text)

        # Create chunks
        i = 0
        chunk_num = 0
        while i < len(words):
            # Extract chunk
            end_idx = min(i + self.target_size, len(words))
            chunk_words = words[i:end_idx]

            # Extend to sentence boundary if possible
            chunk_words = self._extend_to_sentence_boundary(chunk_words, words, end_idx)

            chunk_text = " ".join(chunk_words)
            word_count = len(chunk_words)

            # Skip chunks that are too small (unless it's the last chunk)
            if word_count < self.min_size and end_idx < len(words):
                i += self.target_size
                continue

            # Create chunk metadata
            chunk_id = f"{subject}-{chapter['id']}-{chunk_num:03d}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "word_count": word_count,
                    "token_count": self._count_tokens(chunk_text),
                    "metadata": {
                        "source_title": book_title,
                        "chapter_id": chapter["id"],
                        "chapter_title": chapter["title"],
                        "subject": subject,
                        "chunk_index": start_index + chunk_num,
                    },
                }
            )

            chunk_num += 1

            # Move to next chunk with overlap
            i += self.target_size - self.overlap

        return chunks

    def _tokenize_words(self, text: str) -> List[str]:
        """
        Split text into words.

        Args:
            text: Input text

        Returns:
            List of words
        """
        # Split on whitespace and punctuation boundaries
        words = re.findall(r"\S+", text)
        return words

    def _extend_to_sentence_boundary(
        self, chunk_words: List[str], all_words: List[str], end_idx: int
    ) -> List[str]:
        """
        Extend chunk to nearest sentence boundary.

        Looks for sentence-ending punctuation (.!?) within next 50 words.

        Args:
            chunk_words: Current chunk words
            all_words: All words in text
            end_idx: Current end index

        Returns:
            Extended chunk words
        """
        # Sentence ending punctuation
        sentence_enders = {".", "!", "?"}

        # Look ahead up to 50 words for sentence boundary
        lookahead = 50
        for i in range(len(chunk_words) - 1, -1, -1):
            word = chunk_words[i]
            if any(word.endswith(ender) for ender in sentence_enders):
                # Found sentence boundary, truncate here
                return chunk_words[: i + 1]

        # No boundary found in current chunk, look ahead
        for i in range(end_idx, min(end_idx + lookahead, len(all_words))):
            word = all_words[i]
            chunk_words.append(word)
            if any(word.endswith(ender) for ender in sentence_enders):
                return chunk_words

        # No boundary found, return as is (but cap at max_size)
        if len(chunk_words) > self.max_size:
            return chunk_words[: self.max_size]

        return chunk_words

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Input text

        Returns:
            Token count
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: estimate 1.3 tokens per word
            words = self._tokenize_words(text)
            return int(len(words) * 1.3)

    def get_chunk_statistics(self, chunks: List[Dict]) -> Dict:
        """
        Get statistics about chunks.

        Args:
            chunks: List of chunks

        Returns:
            Statistics dict
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_word_count": 0,
                "avg_token_count": 0,
                "min_word_count": 0,
                "max_word_count": 0,
            }

        word_counts = [c["word_count"] for c in chunks]
        token_counts = [c["token_count"] for c in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_word_count": sum(word_counts) / len(word_counts),
            "avg_token_count": sum(token_counts) / len(token_counts),
            "min_word_count": min(word_counts),
            "max_word_count": max(word_counts),
            "total_words": sum(word_counts),
            "total_tokens": sum(token_counts),
        }


def main():
    """Test chunker with sample text."""
    sample_text = (
        """
    Newton's third law of motion states that for every action, there is an equal
    and opposite reaction. This law is fundamental to understanding how forces work
    in the physical world. When you push against a wall, the wall pushes back with
    an equal force. When a rocket expels gas backward, the gas pushes the rocket
    forward. These are examples of action-reaction pairs.
    """
        * 50
    )  # Repeat to create larger text

    chunker = TextChunker()

    # Create mock book data
    book_data = {
        "title": "Test Book",
        "subject": "physics",
        "chapters": [
            {
                "id": "chapter-01",
                "title": "Test Chapter",
                "content_blocks": [{"type": "paragraph", "text": sample_text}],
            }
        ],
    }

    chunks = chunker.chunk_book(book_data)
    stats = chunker.get_chunk_statistics(chunks)

    print(f"Chunks created: {stats['total_chunks']}")
    print(f"Avg word count: {stats['avg_word_count']:.1f}")
    print(f"Avg token count: {stats['avg_token_count']:.1f}")
    print(f"Word count range: {stats['min_word_count']} - {stats['max_word_count']}")


if __name__ == "__main__":
    main()
