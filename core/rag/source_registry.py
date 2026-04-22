from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class KnowledgeSource:
    """One configured local knowledge source."""

    name: str
    path: Path
    types: list[str]

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Knowledge source name cannot be empty")
        if not self.types:
            raise ValueError(f"Knowledge source '{self.name}' must declare at least one file type")


@dataclass(slots=True)
class RAGSettings:
    """Global RAG settings loaded from config."""

    chunk_size: int
    chunk_overlap: int
    top_k: int
    persist_directory: Path
    collection_name: str

    def validate(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if self.top_k <= 0:
            raise ValueError("top_k must be > 0")
        if not self.collection_name.strip():
            raise ValueError("collection_name cannot be empty")


@dataclass(slots=True)
class RAGConfig:
    """Full RAG config loaded from YAML."""

    sources: list[KnowledgeSource]
    settings: RAGSettings

    def validate(self) -> None:
        self.settings.validate()
        if not self.sources:
            raise ValueError("At least one knowledge source must be configured")
        for source in self.sources:
            source.validate()


class SourceRegistry:
    """
    Reads and validates the local knowledge source registry.

    Current expectation:
    - config file path points to configs/rag_sources/default.yaml
    - relative paths are resolved from project root
    """

    def __init__(self, config_path: str | Path, project_root: str | Path | None = None) -> None:
        self.config_path = Path(config_path)
        self.project_root = Path(project_root) if project_root is not None else Path.cwd()

    def load(self) -> RAGConfig:
        """
        Load and validate YAML config.
        """
        raw = self._read_yaml()
        config = self._parse_config(raw)
        config.validate()
        return config

    def _read_yaml(self) -> dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"RAG config not found: {self.config_path}")

        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            raise ValueError("RAG config must be a YAML mapping/object")

        return data

    def _parse_config(self, raw: dict) -> RAGConfig:
        raw_sources = raw.get("sources", [])
        raw_settings = raw.get("settings", {})

        sources = [
            KnowledgeSource(
                name=item["name"],
                path=self._resolve_path(item["path"]),
                types=list(item.get("types", [])),
            )
            for item in raw_sources
        ]

        settings = RAGSettings(
            chunk_size=int(raw_settings.get("chunk_size", 800)),
            chunk_overlap=int(raw_settings.get("chunk_overlap", 120)),
            top_k=int(raw_settings.get("top_k", 5)),
            persist_directory=self._resolve_path(
                raw_settings.get("persist_directory", "./data/chroma")
            ),
            collection_name=str(raw_settings.get("collection_name", "local_knowledge")),
        )

        return RAGConfig(sources=sources, settings=settings)

    def _resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (self.project_root / path).resolve()
