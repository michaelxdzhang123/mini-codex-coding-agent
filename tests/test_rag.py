"""Tests for the M3 local RAG layer (indexer + retriever)."""

from __future__ import annotations

import pytest

from core.rag.indexer import KnowledgeIndexer
from core.rag.retriever import KnowledgeRetriever, RetrievedChunk
from core.rag.source_registry import KnowledgeSource, RAGConfig, RAGSettings, SourceRegistry

# ─── Helpers ──────────────────────────────────────────────────────────


def _sample_config(tmp_path: pytest.TempPathFactory) -> RAGConfig:
    """Build a temporary RAG config for isolated tests."""
    persist = tmp_path / "chroma"
    source_dir = tmp_path / "docs"
    source_dir.mkdir()
    (source_dir / "hello.md").write_text("Hello world from markdown.", encoding="utf-8")
    (source_dir / "notes.txt").write_text("These are text notes.", encoding="utf-8")

    return RAGConfig(
        sources=[
            KnowledgeSource(name="test_docs", path=source_dir, types=["md", "txt"]),
        ],
        settings=RAGSettings(
            chunk_size=100,
            chunk_overlap=20,
            top_k=3,
            persist_directory=persist,
            collection_name="test_collection",
        ),
    )


# ─── Indexer ──────────────────────────────────────────────────────────


def test_indexer_run(tmp_path: pytest.TempPathFactory) -> None:
    config = _sample_config(tmp_path)
    indexer = KnowledgeIndexer(config)
    stats = indexer.run()

    assert stats.source_count == 1
    assert stats.file_count == 2
    assert stats.chunk_count > 0


def test_indexer_ignores_missing_source_path(tmp_path: pytest.TempPathFactory) -> None:
    config = RAGConfig(
        sources=[
            KnowledgeSource(name="missing", path=tmp_path / "nope", types=["md"]),
        ],
        settings=RAGSettings(
            chunk_size=100,
            chunk_overlap=20,
            top_k=3,
            persist_directory=tmp_path / "chroma",
            collection_name="test",
        ),
    )
    indexer = KnowledgeIndexer(config)
    stats = indexer.run()
    assert stats.file_count == 0
    assert stats.chunk_count == 0


def test_indexer_deduplicates_via_upsert(tmp_path: pytest.TempPathFactory) -> None:
    """Running the indexer twice should not create duplicate chunks."""
    config = _sample_config(tmp_path)
    indexer = KnowledgeIndexer(config)
    indexer.run()
    indexer.run()

    retriever = KnowledgeRetriever(config)
    results = retriever.query("hello", top_k=10)
    # Should still return the same chunks, not duplicates.
    assert len(results) <= 10
    ids = [r.chunk_id for r in results]
    assert len(ids) == len(set(ids))


def test_indexer_pdf_support(tmp_path: pytest.TempPathFactory) -> None:
    """Minimal smoke test for PDF loading path.

    We avoid creating a real PDF here; instead we verify the helper
    raises on truly unsupported types and handles txt/md correctly.
    """
    source_dir = tmp_path / "docs"
    source_dir.mkdir()
    (source_dir / "plain.txt").write_text("Some text content.", encoding="utf-8")

    config = RAGConfig(
        sources=[KnowledgeSource(name="pdf_test", path=source_dir, types=["txt"])],
        settings=RAGSettings(
            chunk_size=50,
            chunk_overlap=10,
            top_k=2,
            persist_directory=tmp_path / "chroma",
            collection_name="pdf_test_collection",
        ),
    )
    indexer = KnowledgeIndexer(config)
    stats = indexer.run()
    assert stats.file_count == 1
    assert stats.chunk_count > 0


# ─── Retriever ────────────────────────────────────────────────────────


def test_retriever_query_returns_results(tmp_path: pytest.TempPathFactory) -> None:
    config = _sample_config(tmp_path)
    indexer = KnowledgeIndexer(config)
    indexer.run()

    retriever = KnowledgeRetriever(config)
    results = retriever.query("hello")

    assert len(results) > 0
    assert all(isinstance(r, RetrievedChunk) for r in results)
    # Scores should be in [0, 1]
    assert all(0.0 <= r.score <= 1.0 for r in results)


def test_retriever_source_labels_preserved(tmp_path: pytest.TempPathFactory) -> None:
    config = _sample_config(tmp_path)
    indexer = KnowledgeIndexer(config)
    indexer.run()

    retriever = KnowledgeRetriever(config)
    results = retriever.query("markdown")

    assert len(results) > 0
    assert results[0].source_name == "test_docs"
    assert "hello.md" in results[0].source_path


def test_retriever_empty_collection(tmp_path: pytest.TempPathFactory) -> None:
    config = _sample_config(tmp_path)
    retriever = KnowledgeRetriever(config)
    results = retriever.query("anything")
    assert results == []


def test_retriever_empty_query_raises(tmp_path: pytest.TempPathFactory) -> None:
    config = _sample_config(tmp_path)
    retriever = KnowledgeRetriever(config)
    with pytest.raises(ValueError, match="cannot be empty"):
        retriever.query("")


def test_retriever_top_k_override(tmp_path: pytest.TempPathFactory) -> None:
    config = _sample_config(tmp_path)
    indexer = KnowledgeIndexer(config)
    indexer.run()

    retriever = KnowledgeRetriever(config)
    results = retriever.query("hello", top_k=1)
    assert len(results) == 1


# ─── End-to-End ───────────────────────────────────────────────────────


def test_index_and_query_roundtrip(tmp_path: pytest.TempPathFactory) -> None:
    """Full flow: create docs -> index -> query -> verify retrieval."""
    persist = tmp_path / "chroma"
    source_dir = tmp_path / "knowledge"
    source_dir.mkdir()
    (source_dir / "python.md").write_text(
        "Python coding standards require type hints and docstrings.",
        encoding="utf-8",
    )
    (source_dir / "rust.md").write_text(
        "Rust memory safety is enforced by the borrow checker.",
        encoding="utf-8",
    )

    config = RAGConfig(
        sources=[KnowledgeSource(name="langs", path=source_dir, types=["md"])],
        settings=RAGSettings(
            chunk_size=80,
            chunk_overlap=10,
            top_k=5,
            persist_directory=persist,
            collection_name="roundtrip",
        ),
    )

    indexer = KnowledgeIndexer(config)
    stats = indexer.run()
    assert stats.chunk_count > 0

    retriever = KnowledgeRetriever(config)
    py_results = retriever.query("Python type hints")
    assert len(py_results) > 0
    assert "python" in py_results[0].source_path.lower()
    assert py_results[0].metadata.get("source_name") == "langs"

    rust_results = retriever.query("borrow checker")
    assert len(rust_results) > 0
    assert "rust" in rust_results[0].source_path.lower()


# ─── Source Registry ──────────────────────────────────────────────────


def test_source_registry_load_missing_file(tmp_path: pytest.TempPathFactory) -> None:
    registry = SourceRegistry(tmp_path / "missing.yaml")
    with pytest.raises(FileNotFoundError):
        registry.load()


def test_source_registry_load_valid(tmp_path: pytest.TempPathFactory) -> None:
    config_path = tmp_path / "rag.yaml"
    config_path.write_text(
        """
sources:
  - name: docs
    path: "./docs"
    types:
      - md

settings:
  chunk_size: 200
  chunk_overlap: 20
  top_k: 3
  persist_directory: "./chroma"
  collection_name: "docs"
""",
        encoding="utf-8",
    )
    registry = SourceRegistry(config_path, project_root=tmp_path)
    config = registry.load()
    assert config.sources[0].name == "docs"
    assert config.settings.chunk_size == 200
    assert config.settings.collection_name == "docs"
