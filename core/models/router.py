"""Model router: decides which model role and adapter should handle a step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.models.adapter import MockModelAdapter, ModelAdapter
from core.models.config import ModelConfig, ModelRegistryConfig
from core.models.roles import ModelRole, role_for_task


@dataclass(slots=True)
class RoutingPolicy:
    """
    Routing policy constraints.

    - prefer_mock: if True, always return mock adapters (safe fallback mode)
    - allow_fallback: if True, fallback to mock when a real model is unhealthy
    """

    prefer_mock: bool = False
    allow_fallback: bool = True


class ModelRouter:
    """
    Central router for model selection.

    Responsibilities:
    1. Map task/step names to model roles
    2. Look up the configured default model for that role
    3. Instantiate the correct adapter (or mock fallback)
    4. Ensure no business logic hardcodes a specific model name
    """

    def __init__(
        self,
        registry: ModelRegistryConfig,
        policy: RoutingPolicy | None = None,
    ) -> None:
        self.registry = registry
        self.policy = policy or RoutingPolicy()
        self._adapters: dict[str, ModelAdapter] = {}

    def route(self, task: str, **kwargs: Any) -> ModelAdapter:
        """
        Route a task to the appropriate model adapter.

        Args:
            task: A task name or step category (e.g. "plan", "generate_code", "index")
            **kwargs: Optional extra context (ignored by base router, reserved for extensions)

        Returns:
            A ModelAdapter ready to serve the task.
        """
        role = role_for_task(task)
        return self.route_by_role(role)

    def route_by_role(self, role: ModelRole) -> ModelAdapter:
        """
        Route directly by model role.

        This is useful when the caller already knows the required role
        and does not need task-to-role resolution.
        """
        if self.policy.prefer_mock:
            return self._mock_for_role(role)

        model_config = self.registry.get_default_for_role(role)
        adapter = self._get_or_create_adapter(model_config)

        health = adapter.health()
        if health.get("status") != "healthy" and self.policy.allow_fallback:
            return self._mock_for_role(role)

        return adapter

    def list_available_roles(self) -> list[ModelRole]:
        """Return roles that have at least one enabled model."""
        return [role for role in ModelRole.all_roles() if self.registry.list_enabled_by_role(role)]

    def health_check(self) -> dict[str, Any]:
        """Run a health check across all registered models."""
        results: dict[str, Any] = {}
        for model in self.registry.models:
            adapter = self._get_or_create_adapter(model)
            results[model.id] = adapter.health()
        return results

    def _get_or_create_adapter(self, config: ModelConfig) -> ModelAdapter:
        if config.id in self._adapters:
            return self._adapters[config.id]

        adapter = self._build_adapter(config)
        self._adapters[config.id] = adapter
        return adapter

    def _build_adapter(self, config: ModelConfig) -> ModelAdapter:
        if config.provider == "mock":
            return MockModelAdapter(
                model_id=config.id,
                role=config.role,
                config=config.config,
            )

        # TODO: Add real providers (ollama, llama.cpp, vllm, etc.) in later milestones.
        # For M2, any unknown provider falls back to mock so the system stays runnable.
        return MockModelAdapter(
            model_id=config.id,
            role=config.role,
            config={
                **(config.config or {}),
                "response_template": (
                    f"[MockFallback:{config.id}] "
                    f"Provider '{config.provider}' is not implemented yet. "
                    "Returning mock response for: {prompt}"
                ),
            },
        )

    def _mock_for_role(self, role: ModelRole) -> ModelAdapter:
        return MockModelAdapter(
            model_id=f"mock-{role.value}",
            role=role,
        )
