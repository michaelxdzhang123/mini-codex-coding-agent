"""Local knowledge indexer: load, chunk, embed, and store in Chroma."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from pypdf import PdfReader

from core.rag.chunker import ChunkingConfig, SourceDocument, TextChunk, TextChunker
from core.rag.source_registry import RAGConfig, SourceRegistry


@dataclass(slots=True)
class IndexStats:
    """Simple indexing summary for logging/UI."""

    source_count: int = 0
    file_count: int = 0
    chunk_count: int = 0


class KnowledgeIndexer:
    """
    Responsible for:
    1. loading configured knowledge files
    2. chunking them
    3. embedding them
    4. storing them in local vector storage (ChromaDB)
    """

    # Shared embedder instance to avoid reloading the model repeatedly.
    _embedder: DefaultEmbeddingFunction | None = None

    def __init__(self, config: RAGConfig) -> None:
        self.config = config
        self.chunker = TextChunker(
            ChunkingConfig(
                chunk_size=config.settings.chunk_size,
                chunk_overlap=config.settings.chunk_overlap,
            )
        )
        self._client = chromadb.PersistentClient(
            path=str(config.settings.persist_directory)
        )
        self._collection = self._client.get_or_create_collection(
            name=config.settings.collection_name
        )

    @classmethod
    def _get_embedder(cls) -> DefaultEmbeddingFunction:
        if cls._embedder is None:
            cls._embedder = DefaultEmbeddingFunction()
        return cls._embedder

    def run(self) -> IndexStats:
        stats = IndexStats(source_count=len(self.config.sources))

        for source in self.config.sources:
            for file_path in self._iter_source_files(source.path, source.types):
                stats.file_count += 1

                document = self._load_document(source_name=source.name, path=file_path)
                chunks = self.chunker.chunk_document(document)
                self._upsert_chunks(chunks)
                stats.chunk_count += len(chunks)

        return stats

    def _iter_source_files(self, root: Path, allowed_types: list[str]) -> Iterable[Path]:
        if not root.exists():
            return []

        normalized_types = {ext.lower().lstrip(".") for ext in allowed_types}
        files: list[Path] = []

        for path in root.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower().lstrip(".")
            if suffix in normalized_types:
                files.append(path)

        return files

    def _load_document(self, source_name: str, path: Path) -> SourceDocument:
        suffix = path.suffix.lower().lstrip(".")

        if suffix in {"txt", "md"}:
            content = path.read_text(encoding="utf-8")
        elif suffix == "pdf":
            content = self._read_pdf(path)
        else:
            raise ValueError(f"Unsupported document type: {suffix}")

        return SourceDocument(
            source_name=source_name,
            path=path,
            content=content,
            file_type=suffix,
        )

    @staticmethod
    def _read_pdf(path: Path) -> str:
        reader = PdfReader(str(path))
        texts: list[str] = []

        for page in reader.pages:
            texts.append(page.extract_text() or "")

        return "\n".join(texts).strip()

    def _upsert_chunks(self, chunks: list[TextChunk]) -> None:
        """Embed and upsert chunks into Chroma."""
        if not chunks:
            return

        embedder = self._get_embedder()
        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        metadatas = [
            {
                "source_name": c.source_name,
                "source_path": c.source_path,
                "chunk_index": c.chunk_index,
                "file_type": c.file_type,
            }
            for c in chunks
        ]
        embeddings = embedder(texts)

        self._collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or refresh local knowledge index")
    parser.add_argument(
        "--config",
        default="configs/rag_sources/default.yaml",
        help="Path to RAG source config YAML",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    registry = SourceRegistry(args.config)
    config = registry.load()

    indexer = KnowledgeIndexer(config)
    stats = indexer.run()

    print(
        f"Indexed knowledge sources={stats.source_count}, "
        f"files={stats.file_count}, chunks={stats.chunk_count}"
    )


if __name__ == "__main__":
    main()
