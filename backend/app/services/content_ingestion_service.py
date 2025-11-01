"""
OER Content Ingestion Service (Phase 4.3)

Ingests Open Educational Resources content, chunks it,
generates embeddings, and stores in vector database.
"""
import os
import logging
import hashlib
import json
import re
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import asyncio

from app.services.embeddings_service import get_embeddings_service
from app.models.content import ContentChunk, ContentSource

logger = logging.getLogger(__name__)


class ContentIngestionService:
    """
    Service for ingesting and processing OER content.

    Pipeline:
    1. Parse source content (JSON, XML, HTML)
    2. Chunk into semantic units
    3. Extract metadata and keywords
    4. Generate embeddings
    5. Store in PostgreSQL + Vector DB
    6. Index for fast retrieval
    """

    def __init__(self):
        """Initialize content ingestion service."""
        self.embeddings_service = get_embeddings_service()

        # Chunking configuration
        self.chunk_config = {
            "max_chunk_size": 500,  # words
            "min_chunk_size": 100,  # words
            "overlap": 50,  # words overlap between chunks
            "split_on": ["\\n\\n", "\\n", ". "],  # Split priority
        }

    async def ingest_openstax_content(
        self, source_title: str, subject: str, content_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ingest content from OpenStax textbook.

        Args:
            source_title: "College Physics 2e"
            subject: "physics"
            content_data: Parsed content dict with chapters/sections

        Returns:
            Dict with ingestion stats

        Example:
            >>> result = await service.ingest_openstax_content(
            ...     "College Physics 2e",
            ...     "physics",
            ...     parsed_content
            ... )
            >>> result["chunks_created"]
            1247
        """
        ingestion_id = self._generate_ingestion_id(source_title)
        logger.info(f"[{ingestion_id}] Starting ingestion: {source_title}")

        try:
            # Create source record
            source = self._create_source_record(
                source_title=source_title, subject=subject, content_data=content_data
            )

            # Extract and chunk content
            logger.info(f"[{ingestion_id}] Extracting and chunking content")
            chunks = self._process_chapters(
                content_data=content_data, source=source, subject=subject
            )

            logger.info(f"[{ingestion_id}] Created {len(chunks)} chunks")

            # Generate embeddings in batches
            logger.info(f"[{ingestion_id}] Generating embeddings")
            chunk_texts = [chunk["cleaned_text"] for chunk in chunks]
            embeddings = await self.embeddings_service.generate_embeddings_batch(
                texts=chunk_texts, batch_size=100
            )

            # Attach embeddings to chunks
            for chunk, embedding_data in zip(chunks, embeddings):
                chunk["embedding"] = embedding_data["embedding"]
                chunk["embedding_id"] = embedding_data["embedding_id"]

            # Store chunks in database
            logger.info(f"[{ingestion_id}] Storing chunks in database")
            stored_chunks = await self._store_chunks(chunks)

            # Update source status
            await self._update_source_status(
                source_id=source["source_id"],
                status="completed",
                chunks_count=len(stored_chunks),
            )

            logger.info(f"[{ingestion_id}] Ingestion complete")

            return {
                "status": "completed",
                "ingestion_id": ingestion_id,
                "source_id": source["source_id"],
                "source_title": source_title,
                "chunks_created": len(stored_chunks),
                "total_words": sum(chunk["word_count"] for chunk in chunks),
                "subjects": [subject],
                "completed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"[{ingestion_id}] Ingestion failed: {e}", exc_info=True)
            return {"status": "failed", "ingestion_id": ingestion_id, "error": str(e)}

    def _create_source_record(
        self, source_title: str, subject: str, content_data: Dict
    ) -> Dict:
        """Create source metadata record."""
        source_id = self._generate_source_id(source_title)

        return {
            "source_id": source_id,
            "title": source_title,
            "author": content_data.get("author", "OpenStax"),
            "subject": subject,
            "url": content_data.get("url", "https://openstax.org"),
            "license": content_data.get("license", "CC BY 4.0"),
            "source_version": content_data.get("version", "2e"),
            "total_chapters": len(content_data.get("chapters", [])),
            "created_at": datetime.utcnow(),
        }

    def _process_chapters(
        self, content_data: Dict, source: Dict, subject: str
    ) -> List[Dict]:
        """Process all chapters and create chunks."""
        all_chunks = []

        for chapter in content_data.get("chapters", []):
            chapter_number = chapter.get("number")
            chapter_title = chapter.get("title")

            for section in chapter.get("sections", []):
                section_number = section.get("number")
                section_title = section.get("title")
                section_text = section.get("content", "")

                # Chunk the section text
                chunks = self._chunk_text(
                    text=section_text,
                    chapter=f"Chapter {chapter_number}: {chapter_title}",
                    section=f"{section_number} {section_title}",
                    source=source,
                    subject=subject,
                    topic_ids=section.get("topic_ids", []),
                )

                all_chunks.extend(chunks)

        return all_chunks

    def _chunk_text(
        self,
        text: str,
        chapter: str,
        section: str,
        source: Dict,
        subject: str,
        topic_ids: List[str],
    ) -> List[Dict]:
        """
        Chunk text into semantic units.

        Strategy:
        - Target: 300-500 words per chunk
        - Split on paragraph boundaries
        - Maintain overlap for context
        - Preserve complete sentences
        """
        # Clean text
        cleaned_text = self._clean_text(text)

        # Split into sentences
        sentences = self._split_sentences(cleaned_text)

        chunks = []
        current_chunk = []
        current_word_count = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())

            # Check if adding this sentence exceeds max chunk size
            if (
                current_word_count + sentence_words
                > self.chunk_config["max_chunk_size"]
            ):
                # Save current chunk if it's big enough
                if current_word_count >= self.chunk_config["min_chunk_size"]:
                    chunk_dict = self._create_chunk_dict(
                        sentences=current_chunk,
                        chapter=chapter,
                        section=section,
                        source=source,
                        subject=subject,
                        topic_ids=topic_ids,
                    )
                    chunks.append(chunk_dict)

                    # Start new chunk with overlap
                    overlap_sentences = (
                        current_chunk[-2:] if len(current_chunk) >= 2 else []
                    )
                    current_chunk = overlap_sentences + [sentence]
                    current_word_count = sum(len(s.split()) for s in current_chunk)
                else:
                    # Chunk too small, add sentence
                    current_chunk.append(sentence)
                    current_word_count += sentence_words
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_word_count += sentence_words

        # Add final chunk
        if current_chunk and current_word_count >= self.chunk_config["min_chunk_size"]:
            chunk_dict = self._create_chunk_dict(
                sentences=current_chunk,
                chapter=chapter,
                section=section,
                source=source,
                subject=subject,
                topic_ids=topic_ids,
            )
            chunks.append(chunk_dict)

        return chunks

    def _create_chunk_dict(
        self,
        sentences: List[str],
        chapter: str,
        section: str,
        source: Dict,
        subject: str,
        topic_ids: List[str],
    ) -> Dict:
        """Create chunk dictionary with metadata."""
        text = " ".join(sentences)
        cleaned_text = self._clean_text(text)
        chunk_id = self._generate_chunk_id(cleaned_text)

        # Extract keywords
        keywords = self._extract_keywords(cleaned_text)

        # Extract concepts
        concepts = self._extract_concepts(cleaned_text, subject)

        return {
            "chunk_id": chunk_id,
            "source_title": source["title"],
            "source_author": source["author"],
            "source_url": source["url"],
            "source_license": source["license"],
            "subject": subject,
            "chapter": chapter,
            "section": section,
            "subsection": None,
            "topic_ids": topic_ids,
            "text": text,
            "cleaned_text": cleaned_text,
            "word_count": len(cleaned_text.split()),
            "keywords": keywords,
            "concepts": concepts,
            "created_at": datetime.utcnow(),
        }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters but keep punctuation
        text = re.sub(r"[^\w\s.,!?;:()\-\'\"]+", "", text)

        # Trim
        text = text.strip()

        return text

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitter (can be improved with spaCy/NLTK)
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # Filter empty
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract important keywords from text.

        Simple implementation: most common meaningful words.
        In production, would use TF-IDF or KeyBERT.
        """
        # Convert to lowercase
        text_lower = text.lower()

        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "they",
            "them",
            "their",
            "we",
            "us",
            "our",
            "you",
            "your",
        }

        # Extract words
        words = re.findall(r"\b[a-z]{3,}\b", text_lower)

        # Filter stop words
        words = [w for w in words if w not in stop_words]

        # Count frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # Return top keywords
        keywords = [word for word, freq in sorted_words[:max_keywords]]

        return keywords

    def _extract_concepts(self, text: str, subject: str) -> List[str]:
        """
        Extract key concepts from text.

        Uses subject-specific concept dictionaries.
        """
        # Subject-specific concept patterns
        concept_patterns = {
            "physics": [
                r"\b(force|energy|momentum|velocity|acceleration|friction|gravity)\b",
                r"\b(newton|law|motion|inertia|mass|weight)\b",
                r"\b(kinetic|potential|thermal|mechanical)\b",
            ],
            "chemistry": [
                r"\b(atom|molecule|element|compound|reaction|bond)\b",
                r"\b(acid|base|ph|solution|solvent|solute)\b",
                r"\b(oxidation|reduction|catalyst|equilibrium)\b",
            ],
            "math": [
                r"\b(equation|function|variable|constant|derivative)\b",
                r"\b(integral|limit|theorem|proof|formula)\b",
                r"\b(slope|intercept|quadratic|linear|polynomial)\b",
            ],
        }

        text_lower = text.lower()
        concepts = set()

        # Extract concepts using patterns
        for pattern in concept_patterns.get(subject, []):
            matches = re.findall(pattern, text_lower)
            concepts.update(matches)

        return list(concepts)[:15]  # Limit to 15 concepts

    async def _store_chunks(self, chunks: List[Dict]) -> List[str]:
        """
        Store chunks in database.

        In production, would use SQLAlchemy bulk insert.
        For now, returns chunk IDs.
        """
        # Mock storage - in production would insert to PostgreSQL
        chunk_ids = [chunk["chunk_id"] for chunk in chunks]

        logger.info(f"Stored {len(chunk_ids)} chunks (mock)")

        return chunk_ids

    async def _update_source_status(
        self, source_id: str, status: str, chunks_count: int
    ):
        """Update content source status."""
        # Mock update
        logger.info(f"Updated source {source_id}: {status}, {chunks_count} chunks")

    def _generate_ingestion_id(self, source_title: str) -> str:
        """Generate unique ingestion ID."""
        timestamp = datetime.utcnow().isoformat()
        content = f"{source_title}|{timestamp}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"ingest_{hash_val}"

    def _generate_source_id(self, source_title: str) -> str:
        """Generate unique source ID."""
        hash_val = hashlib.sha256(source_title.encode()).hexdigest()[:16]
        return f"source_{hash_val}"

    def _generate_chunk_id(self, text: str) -> str:
        """Generate unique chunk ID based on content."""
        hash_val = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"chunk_{hash_val}"


# Singleton instance
_content_ingestion_service_instance = None


def get_content_ingestion_service() -> ContentIngestionService:
    """Get singleton content ingestion service instance."""
    global _content_ingestion_service_instance
    if _content_ingestion_service_instance is None:
        _content_ingestion_service_instance = ContentIngestionService()
    return _content_ingestion_service_instance
