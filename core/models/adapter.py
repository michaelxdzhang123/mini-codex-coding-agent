"""Model adapter interface and mock implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.models.roles import ModelRole


class ModelAdapter(ABC):
    """
    Abstract interface for a local model adapter.

    All concrete adapters (mock, ollama, llama.cpp, vllm, etc.)
    must implement this interface so the router stays provider-agnostic.
    """

    @property
    @abstractmethod
    def role(self) -> ModelRole:
        """Return the role this adapter serves."""
        ...

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the unique model identifier."""
        ...

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate a response for the given prompt.

        For embedding adapters this may return a serialized representation;
        the caller is responsible for parsing if needed.
        """
        ...

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return a lightweight health/status check result."""
        ...


class MockModelAdapter(ModelAdapter):
    """
    Mock adapter that returns canned responses.

    Used as a safe fallback when no real local model is available.
    Supports all roles so the system remains runnable end-to-end in M2.
    """

    def __init__(
        self,
        model_id: str,
        role: ModelRole,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._model_id = model_id
        self._role = role
        self._config = config or {}

    @property
    def role(self) -> ModelRole:
        return self._role

    @property
    def model_id(self) -> str:
        return self._model_id

    def generate(self, prompt: str, **kwargs: Any) -> str:
        template = self._config.get(
            "response_template",
            self._default_template_for_role(self._role),
        )
        return template.format(
            model_id=self._model_id,
            role=self._role.value,
            prompt=prompt,
        )

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "provider": "mock",
            "model_id": self._model_id,
            "role": self._role.value,
        }

    @staticmethod
    def _default_template_for_role(role: ModelRole) -> str:
        templates = {
            ModelRole.CODER: (
                "[MockCoder:{model_id}]\n"
                "```python\n"
                "# Placeholder code for: {prompt}\n"
                "def example():\n"
                "    pass\n"
                "```"
            ),
            ModelRole.INSTRUCT: (
                "[MockInstruct:{model_id}]\n"
                "Summary/Plan for: {prompt}\n\n"
                "1. Step one\n"
                "2. Step two\n"
                "3. Step three"
            ),
            ModelRole.EMBEDDING: (
                "[MockEmbedding:{model_id}]\n"
                "Embedding vector placeholder for: {prompt}"
            ),
            ModelRole.RERANKER: (
                "[MockReranker:{model_id}]\n"
                "Reranked results placeholder for: {prompt}"
            ),
        }
        return templates.get(role, "[Mock:{model_id}] Response for: {prompt}")
