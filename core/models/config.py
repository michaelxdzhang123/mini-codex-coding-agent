"""Model registry and configuration support."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from core.models.roles import ModelRole


@dataclass(slots=True)
class ModelConfig:
    """Configuration for a single local model."""

    id: str
    name: str
    role: ModelRole
    provider: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id.strip():
            raise ValueError("model id cannot be empty")
        if not self.name.strip():
            raise ValueError("model name cannot be empty")
        if not self.provider.strip():
            raise ValueError("model provider cannot be empty")
        if self.role not in ModelRole.all_roles():
            raise ValueError(f"invalid model role: {self.role}")


@dataclass(slots=True)
class ProjectDefaults:
    """Project-level default model bindings by role."""

    default_coder: str
    default_instruct: str
    default_embedding: str
    default_reranker: str

    def validate(self, known_ids: set[str]) -> None:
        for attr in ("default_coder", "default_instruct", "default_embedding", "default_reranker"):
            model_id = getattr(self, attr)
            if model_id not in known_ids:
                raise ValueError(
                    f"project default '{attr}' references unknown model id: {model_id}"
                )

    def model_id_for_role(self, role: ModelRole) -> str:
        mapping = {
            ModelRole.CODER: self.default_coder,
            ModelRole.INSTRUCT: self.default_instruct,
            ModelRole.EMBEDDING: self.default_embedding,
            ModelRole.RERANKER: self.default_reranker,
        }
        return mapping[role]


@dataclass(slots=True)
class ModelRegistryConfig:
    """Full model registry loaded from YAML."""

    models: list[ModelConfig]
    project_defaults: ProjectDefaults

    def validate(self) -> None:
        if not self.models:
            raise ValueError("at least one model must be configured")
        known_ids = {m.id for m in self.models}
        for model in self.models:
            model.validate()
        self.project_defaults.validate(known_ids)

    def get_model(self, model_id: str) -> ModelConfig | None:
        for m in self.models:
            if m.id == model_id:
                return m
        return None

    def get_default_for_role(self, role: ModelRole) -> ModelConfig:
        model_id = self.project_defaults.model_id_for_role(role)
        model = self.get_model(model_id)
        if model is None:
            raise ValueError(f"default model for role {role.value} not found: {model_id}")
        if not model.enabled:
            raise ValueError(f"default model for role {role.value} is disabled: {model_id}")
        return model

    def list_enabled_by_role(self, role: ModelRole) -> list[ModelConfig]:
        return [m for m in self.models if m.role == role and m.enabled]


class ModelRegistry:
    """
    Reads and validates the local model registry from YAML.

    Current expectation:
    - config file path points to configs/models/default.yaml
    - relative paths are resolved from project root
    """

    def __init__(self, config_path: str | Path, project_root: str | Path | None = None) -> None:
        self.config_path = Path(config_path)
        self.project_root = Path(project_root) if project_root is not None else Path.cwd()

    def load(self) -> ModelRegistryConfig:
        raw = self._read_yaml()
        config = self._parse_config(raw)
        config.validate()
        return config

    def _read_yaml(self) -> dict:
        path = self.config_path
        if not path.is_absolute():
            path = self.project_root / path

        if not path.exists():
            raise FileNotFoundError(f"model config not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            raise ValueError("model config must be a YAML mapping/object")

        return data

    def _parse_config(self, raw: dict) -> ModelRegistryConfig:
        raw_models = raw.get("models", [])
        raw_defaults = raw.get("project_defaults", {})

        models = [
            ModelConfig(
                id=str(item["id"]),
                name=str(item["name"]),
                role=ModelRole(item["role"]),
                provider=str(item["provider"]),
                enabled=bool(item.get("enabled", True)),
                config=dict(item.get("config", {})),
            )
            for item in raw_models
        ]

        project_defaults = ProjectDefaults(
            default_coder=str(raw_defaults.get("default_coder", "")),
            default_instruct=str(raw_defaults.get("default_instruct", "")),
            default_embedding=str(raw_defaults.get("default_embedding", "")),
            default_reranker=str(raw_defaults.get("default_reranker", "")),
        )

        return ModelRegistryConfig(models=models, project_defaults=project_defaults)
