"""Local RAG layer for knowledge retrieval."""

from __future__ import annotations

from core.rag.chunker import ChunkingConfig, SourceDocument, TextChunk, TextChunker
from core.rag.indexer import IndexStats, KnowledgeIndexer
from core.rag.retriever import KnowledgeRetriever, RetrievedChunk
from core.rag.source_registry import KnowledgeSource, RAGConfig, RAGSettings, SourceRegistry

__all__ = [
    "ChunkingConfig",
    "IndexStats",
    "KnowledgeIndexer",
    "KnowledgeRetriever",
    "KnowledgeSource",
    "RAGConfig",
    "RAGSettings",
    "RetrievedChunk",
    "SourceDocument",
    "SourceRegistry",
    "TextChunk",
    "TextChunker",
]
