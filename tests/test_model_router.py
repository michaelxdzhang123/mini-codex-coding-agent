"""Tests for the M2 model router layer."""

from __future__ import annotations

import pytest

from core.models.adapter import MockModelAdapter, ModelAdapter
from core.models.config import (
    ModelConfig,
    ModelRegistry,
    ModelRegistryConfig,
    ProjectDefaults,
)
from core.models.roles import ModelRole, role_for_task
from core.models.router import ModelRouter, RoutingPolicy

# ─── Helpers ──────────────────────────────────────────────────────────


def _sample_registry() -> ModelRegistryConfig:
    return ModelRegistryConfig(
        models=[
            ModelConfig(
                id="mock-coder",
                name="Mock Coder",
                role=ModelRole.CODER,
                provider="mock",
                enabled=True,
            ),
            ModelConfig(
                id="mock-instruct",
                name="Mock Instruct",
                role=ModelRole.INSTRUCT,
                provider="mock",
                enabled=True,
            ),
            ModelConfig(
                id="mock-embedding",
                name="Mock Embedding",
                role=ModelRole.EMBEDDING,
                provider="mock",
                enabled=True,
            ),
            ModelConfig(
                id="mock-reranker",
                name="Mock Reranker",
                role=ModelRole.RERANKER,
                provider="mock",
                enabled=True,
            ),
            ModelConfig(
                id="disabled-coder",
                name="Disabled Coder",
                role=ModelRole.CODER,
                provider="mock",
                enabled=False,
            ),
        ],
        project_defaults=ProjectDefaults(
            default_coder="mock-coder",
            default_instruct="mock-instruct",
            default_embedding="mock-embedding",
            default_reranker="mock-reranker",
        ),
    )


# ─── Role Resolution ──────────────────────────────────────────────────


def test_role_for_task_known_mappings() -> None:
    assert role_for_task("plan") == ModelRole.INSTRUCT
    assert role_for_task("generate_code") == ModelRole.CODER
    assert role_for_task("index") == ModelRole.EMBEDDING
    assert role_for_task("rerank") == ModelRole.RERANKER


def test_role_for_task_unknown_fallback() -> None:
    assert role_for_task("unknown_task") == ModelRole.INSTRUCT


# ─── Config Validation ────────────────────────────────────────────────


def test_project_defaults_validate_missing_model() -> None:
    defaults = ProjectDefaults(
        default_coder="missing",
        default_instruct="mock-instruct",
        default_embedding="mock-embedding",
        default_reranker="mock-reranker",
    )
    with pytest.raises(ValueError, match="missing"):
        defaults.validate({"mock-instruct", "mock-embedding", "mock-reranker"})


def test_registry_get_default_for_role() -> None:
    registry = _sample_registry()
    model = registry.get_default_for_role(ModelRole.CODER)
    assert model.id == "mock-coder"


def test_registry_list_enabled_by_role() -> None:
    registry = _sample_registry()
    enabled = registry.list_enabled_by_role(ModelRole.CODER)
    assert len(enabled) == 1
    assert enabled[0].id == "mock-coder"


def test_registry_config_validate_empty_models() -> None:
    with pytest.raises(ValueError, match="at least one model"):
        ModelRegistryConfig(models=[], project_defaults=ProjectDefaults("", "", "", "")).validate()


# ─── Mock Adapter ─────────────────────────────────────────────────────


def test_mock_adapter_properties() -> None:
    adapter = MockModelAdapter("test-id", ModelRole.CODER)
    assert adapter.model_id == "test-id"
    assert adapter.role == ModelRole.CODER


def test_mock_adapter_generate() -> None:
    adapter = MockModelAdapter("test-id", ModelRole.CODER)
    result = adapter.generate("hello")
    assert "MockCoder" in result
    assert "hello" in result


def test_mock_adapter_health() -> None:
    adapter = MockModelAdapter("test-id", ModelRole.INSTRUCT)
    health = adapter.health()
    assert health["status"] == "healthy"
    assert health["provider"] == "mock"


# ─── Router ───────────────────────────────────────────────────────────


def test_router_route_by_task() -> None:
    router = ModelRouter(_sample_registry())
    adapter = router.route("plan")
    assert isinstance(adapter, ModelAdapter)
    assert adapter.role == ModelRole.INSTRUCT


def test_router_route_by_role() -> None:
    router = ModelRouter(_sample_registry())
    adapter = router.route_by_role(ModelRole.CODER)
    assert adapter.role == ModelRole.CODER
    assert adapter.model_id == "mock-coder"


def test_router_returns_mock_for_all_roles() -> None:
    router = ModelRouter(_sample_registry())
    for role in ModelRole.all_roles():
        adapter = router.route_by_role(role)
        assert adapter.role == role
        assert adapter.health()["status"] == "healthy"


def test_router_prefer_mock_policy() -> None:
    router = ModelRouter(_sample_registry(), policy=RoutingPolicy(prefer_mock=True))
    adapter = router.route("generate_code")
    assert isinstance(adapter, MockModelAdapter)
    assert "mock-coder" in adapter.model_id


def test_router_unknown_provider_fallback() -> None:
    registry = ModelRegistryConfig(
        models=[
            ModelConfig(
                id="ollama-coder",
                name="Ollama Coder",
                role=ModelRole.CODER,
                provider="ollama",
                enabled=True,
            ),
        ],
        project_defaults=ProjectDefaults(
            default_coder="ollama-coder",
            default_instruct="ollama-coder",
            default_embedding="ollama-coder",
            default_reranker="ollama-coder",
        ),
    )
    router = ModelRouter(registry)
    adapter = router.route_by_role(ModelRole.CODER)
    result = adapter.generate("test prompt")
    assert "MockFallback" in result
    assert "ollama" in result


def test_router_list_available_roles() -> None:
    router = ModelRouter(_sample_registry())
    roles = router.list_available_roles()
    assert set(roles) == set(ModelRole.all_roles())


def test_router_health_check() -> None:
    router = ModelRouter(_sample_registry())
    health = router.health_check()
    assert "mock-coder" in health
    assert health["mock-coder"]["status"] == "healthy"


# ─── YAML Loading ─────────────────────────────────────────────────────


def test_model_registry_load_missing_file(tmp_path: pytest.TempPathFactory) -> None:
    registry = ModelRegistry(tmp_path / "missing.yaml")
    with pytest.raises(FileNotFoundError):
        registry.load()


def test_model_registry_load_minimal_valid(tmp_path: pytest.TempPathFactory) -> None:
    config_path = tmp_path / "models.yaml"
    config_path.write_text(
        """
models:
  - id: mock-instruct
    name: Mock Instruct
    role: instruct
    provider: mock
    enabled: true

project_defaults:
  default_coder: mock-instruct
  default_instruct: mock-instruct
  default_embedding: mock-instruct
  default_reranker: mock-instruct
""",
        encoding="utf-8",
    )
    registry = ModelRegistry(config_path, project_root=tmp_path)
    config = registry.load()
    assert len(config.models) == 1
    assert config.project_defaults.default_instruct == "mock-instruct"
