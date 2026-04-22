"""Model role definitions for the local coding agent."""

from __future__ import annotations

from enum import Enum


class ModelRole(str, Enum):
    """
    Supported model roles in the local coding agent.

    Each role represents a distinct capability needed by the system.
    The router uses these roles to select the right model for a step.
    """

    CODER = "coder"
    INSTRUCT = "instruct"
    EMBEDDING = "embedding"
    RERANKER = "reranker"

    @classmethod
    def all_roles(cls) -> list[ModelRole]:
        return [cls.CODER, cls.INSTRUCT, cls.EMBEDDING, cls.RERANKER]


# ─── Task-to-Role Mapping ─────────────────────────────────────────────

# Lightweight policy table: task category / step name -> model role.
# Business logic should reference these constants rather than hardcoding
# a specific model name.

TASK_ROLE_MAP: dict[str, ModelRole] = {
    # Planning & interpretation
    "plan": ModelRole.INSTRUCT,
    "summarize": ModelRole.INSTRUCT,
    "explain": ModelRole.INSTRUCT,
    "interpret": ModelRole.INSTRUCT,
    "analyze_log": ModelRole.INSTRUCT,
    # Code generation & modification
    "generate_code": ModelRole.CODER,
    "patch": ModelRole.CODER,
    "refactor": ModelRole.CODER,
    "write_tests": ModelRole.CODER,
    "fix_code": ModelRole.CODER,
    # Retrieval
    "index": ModelRole.EMBEDDING,
    "retrieve": ModelRole.EMBEDDING,
    "embed": ModelRole.EMBEDDING,
    "semantic_search": ModelRole.EMBEDDING,
    # Ranking
    "rerank": ModelRole.RERANKER,
    "rank": ModelRole.RERANKER,
    "filter": ModelRole.RERANKER,
}


def role_for_task(task: str) -> ModelRole:
    """
    Resolve a task name or step category to a model role.

    Falls back to INSTRUCT for unknown tasks so the system stays usable
    even when a new task type is introduced.
    """
    return TASK_ROLE_MAP.get(task, ModelRole.INSTRUCT)
