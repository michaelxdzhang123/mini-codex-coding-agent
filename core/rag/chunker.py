from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class ChunkingConfig:
    """Configuration for text chunking."""

    chunk_size: int = 800
    chunk_overlap: int = 120

    def validate(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")


@dataclass(slots=True)
class SourceDocument:
    """A loaded knowledge document before chunking."""

    source_name: str
    path: Path
    content: str
    file_type: str


@dataclass(slots=True)
class TextChunk:
    """A single chunk ready for embedding/indexing."""

    chunk_id: str
    source_name: str
    source_path: str
    text: str
    chunk_index: int
    file_type: str
    metadata: dict[str, str | int]


class TextChunker:
    """
    Responsible for turning raw text documents into chunks.

    This class should stay simple in v1:
    - no semantic chunking yet
    - no language-specific parsing yet
    - plain sliding window strategy is enough
    """

    def __init__(self, config: ChunkingConfig) -> None:
        self.config = config
        self.config.validate()

    def chunk_document(self, document: SourceDocument) -> list[TextChunk]:
        """
        Chunk one source document into multiple TextChunk objects.
        """
        return list(
            self._chunk_text(
                text=document.content,
                source_name=document.source_name,
                source_path=str(document.path),
                file_type=document.file_type,
            )
        )

    def _chunk_text(
        self,
        text: str,
        source_name: str,
        source_path: str,
        file_type: str,
    ) -> Iterable[TextChunk]:
        """
        Sliding-window chunking.

        This implementation is intentionally basic.
        Codex can later improve:
        - paragraph-aware chunking
        - markdown-aware chunking
        - code/comment-aware chunking
        """
        normalized = self._normalize_text(text)
        if not normalized:
            return []

        size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        step = size - overlap

        chunks: list[TextChunk] = []
        start = 0
        chunk_index = 0

        while start < len(normalized):
            end = min(start + size, len(normalized))
            chunk_text = normalized[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_id=f"{source_name}:{source_path}:{chunk_index}",
                        source_name=source_name,
                        source_path=source_path,
                        text=chunk_text,
                        chunk_index=chunk_index,
                        file_type=file_type,
                        metadata={
                            "source_name": source_name,
                            "source_path": source_path,
                            "chunk_index": chunk_index,
                            "file_type": file_type,
                        },
                    )
                )

            if end >= len(normalized):
                break

            start += step
            chunk_index += 1

        return chunks

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize text before chunking.

        Keep this conservative in v1.
        """
        return text.replace("\r\n", "\n").replace("\r", "\n").strip()
