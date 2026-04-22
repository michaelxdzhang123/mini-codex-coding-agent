"""Local knowledge retriever: query ChromaDB and return relevant chunks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from core.rag.source_registry import RAGConfig, SourceRegistry


@dataclass(slots=True)
class RetrievedChunk:
    """One retrieved result returned from local RAG."""

    chunk_id: str
    text: str
    source_name: str
    source_path: str
    score: float
    metadata: dict[str, str | int]


class KnowledgeRetriever:
    """
    Responsible for:
    1. receiving a user query
    2. embedding the query
    3. querying local vector storage (ChromaDB)
    4. returning top-k chunks with source labels
    """

    # Shared embedder instance to match the indexer.
    _embedder: DefaultEmbeddingFunction | None = None

    def __init__(self, config: RAGConfig) -> None:
        self.config = config
        self._client = chromadb.PersistentClient(
            path=str(config.settings.persist_directory)
        )
        # get_or_create so queries against an empty index don't crash.
        self._collection = self._client.get_or_create_collection(
            name=config.settings.collection_name
        )

    @classmethod
    def _get_embedder(cls) -> DefaultEmbeddingFunction:
        if cls._embedder is None:
            cls._embedder = DefaultEmbeddingFunction()
        return cls._embedder

    def query(self, query_text: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """
        Retrieve top-k relevant knowledge chunks for a query.

        Returns chunks ordered by relevance (highest score first).
        """
        query_text = query_text.strip()
        if not query_text:
            raise ValueError("query_text cannot be empty")

        effective_top_k = top_k or self.config.settings.top_k

        if self._collection.count() == 0:
            return []

        embedder = self._get_embedder()
        query_embedding = embedder([query_text])

        results = self._collection.query(
            query_embeddings=query_embedding,
            n_results=effective_top_k,
            include=["documents", "metadatas", "distances"],
        )

        return self._map_results(results)

    def _map_results(self, raw: dict) -> list[RetrievedChunk]:
        """Convert Choma query results into RetrievedChunk objects."""
        chunks: list[RetrievedChunk] = []

        ids = raw.get("ids", [[]])[0]
        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        for i in range(len(ids)):
            distance = float(distances[i]) if distances else 0.0
            # Convert L2 distance to a 0-1 similarity score.
            score = 1.0 / (1.0 + distance)

            meta = dict(metadatas[i]) if metadatas else {}
            chunks.append(
                RetrievedChunk(
                    chunk_id=ids[i],
                    text=documents[i] or "",
                    source_name=str(meta.get("source_name", "")),
                    source_path=str(meta.get("source_path", "")),
                    score=round(score, 4),
                    metadata=meta,
                )
            )

        # Chroma already returns results ordered by distance (ascending).
        # Since score = 1/(1+distance), the order is already best-first.
        return chunks


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query local knowledge index")
    parser.add_argument(
        "--config",
        default="configs/rag_sources/default.yaml",
        help="Path to RAG source config YAML",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Query text for knowledge retrieval",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Override default top_k",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    registry = SourceRegistry(args.config)
    config = registry.load()

    retriever = KnowledgeRetriever(config)
    results = retriever.query(query_text=args.query, top_k=args.top_k)

    for idx, item in enumerate(results, start=1):
        print(f"[{idx}] score={item.score:.4f} source={item.source_name} path={item.source_path}")
        print(item.text)
        print("-" * 80)


if __name__ == "__main__":
    main()
