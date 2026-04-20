from __future__ import annotations

import argparse
from dataclasses import dataclass

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
    3. querying local vector storage
    4. returning top-k chunks

    In this interface skeleton, result shape and flow are defined.
    Codex should implement:
    - embedding model loading
    - Chroma query logic
    - result mapping
    """

    def __init__(self, config: RAGConfig) -> None:
        self.config = config

    def query(self, query_text: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """
        Retrieve top-k relevant knowledge chunks for a query.
        """
        query_text = query_text.strip()
        if not query_text:
            raise ValueError("query_text cannot be empty")

        effective_top_k = top_k or self.config.settings.top_k

        # TODO: Codex should implement:
        # 1. create/load persistent Chroma client
        # 2. load embedding model
        # 3. embed query_text
        # 4. query collection
        # 5. map records -> RetrievedChunk
        _ = effective_top_k

        raise NotImplementedError("Knowledge retrieval is not implemented yet")

    # Optional extension for Codex later:
    # def query_with_source_filter(self, query_text: str, source_names: list[str]) -> list[RetrievedChunk]:
    #     raise NotImplementedError


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
