"""
OER Ingestion Utilities

Helper modules for processing OpenStax content.
"""

from .xml_parser import CNXMLParser
from .chunker import TextChunker
from .vertex_ai_client import VertexAIEmbeddings, VertexVectorSearch

__all__ = ["CNXMLParser", "TextChunker", "VertexAIEmbeddings", "VertexVectorSearch"]
