"""Tests for the M4 planner and context builder."""

from __future__ import annotations

from core.models.config import ModelRegistryConfig, ProjectDefaults
from core.models.roles import ModelRole
from core.models.router import ModelRouter, RoutingPolicy
from core.planner.context_builder import ContextBuilder
from core.planner.plan import Plan
from core.planner.planner import Planner

# ─── Helpers ──────────────────────────────────────────────────────────


def _mock_router() -> ModelRouter:
    from core.models.config import ModelConfig

    registry = ModelRegistryConfig(
        models=[
            ModelConfig(
                id="mock-instruct",
                name="Mock Instruct",
                role=ModelRole.INSTRUCT,
                provider="mock",
                enabled=True,
            ),
        ],
        project_defaults=ProjectDefaults(
            default_coder="mock-instruct",
            default_instruct="mock-instruct",
            default_embedding="mock-instruct",
            default_reranker="mock-instruct",
        ),
    )
    return ModelRouter(registry, policy=RoutingPolicy(prefer_mock=True))


# ─── Plan Dataclass ───────────────────────────────────────────────────


def test_plan_json_roundtrip() -> None:
    plan = Plan(
        summary="Add auth",
        assumptions=["JWT is acceptable"],
        steps=["Create model", "Add routes"],
        files_to_inspect=["app.py"],
        knowledge_to_consult=["auth_standard"],
        commands_to_run=["make test"],
        risks=["Breaking change"],
    )
    raw = plan.to_json()
    restored = Plan.from_json(raw)
    assert restored.summary == plan.summary
    assert restored.steps == plan.steps


def test_plan_is_empty() -> None:
    assert Plan().is_empty()
    assert not Plan(summary="x").is_empty()
    assert not Plan(steps=["a"]).is_empty()


# ─── Context Builder ──────────────────────────────────────────────────


def test_context_builder_basic() -> None:
    builder = ContextBuilder()
    ctx = builder.build("Add login feature")
    assert "Task: Add login feature" in ctx


def test_context_builder_with_repo_files() -> None:
    builder = ContextBuilder()
    ctx = builder.build("Add login", repo_files=["auth.py", "models.py"])
    assert "auth.py" in ctx
    assert "models.py" in ctx


def test_context_builder_caps_repo_files() -> None:
    builder = ContextBuilder()
    files = [f"file_{i}.py" for i in range(30)]
    ctx = builder.build("task", repo_files=files)
    # Should cap at 20 files
    assert ctx.count("file_") == 20


# ─── Planner ──────────────────────────────────────────────────────────


def test_planner_generate_plan() -> None:
    router = _mock_router()
    builder = ContextBuilder()
    planner = Planner(router, builder)

    plan = planner.generate_plan("Refactor the user service")
    assert isinstance(plan, Plan)
    assert plan.summary  # mock adapter returns some text
    assert len(plan.steps) >= 1


def test_planner_parse_structured_response() -> None:
    raw = """
summary: Add JWT authentication
assumptions:
- API uses Flask
steps:
- Create auth module
- Add login endpoint
files_to_inspect:
- app.py
knowledge_to_consult:
- auth_standard
commands_to_run:
- make test
risks:
- Breaking existing clients
"""
    plan = Planner._parse_response(raw)
    assert plan.summary == "Add JWT authentication"
    assert "Flask" in plan.assumptions[0]
    assert len(plan.steps) == 2
    assert "app.py" in plan.files_to_inspect
    assert "auth_standard" in plan.knowledge_to_consult
    assert "make test" in plan.commands_to_run
    assert "Breaking" in plan.risks[0]


def test_planner_parse_numbered_fallback() -> None:
    raw = """[MockInstruct:mock-instruct]
Summary/Plan for: add auth

1. Create model
2. Add routes
3. Write tests
"""
    plan = Planner._parse_response(raw)
    assert "Summary/Plan for: add auth" in plan.summary
    assert plan.steps == ["Create model", "Add routes", "Write tests"]


def test_planner_empty_response() -> None:
    plan = Planner._parse_response("")
    assert plan.is_empty()


def test_planner_no_sections_fallback() -> None:
    raw = "Just do it.\n\n- Step A\n- Step B"
    plan = Planner._parse_response(raw)
    assert plan.summary == "Just do it."
    assert "Step A" in plan.steps
    assert "Step B" in plan.steps


def test_planner_does_not_modify_files() -> None:
    """Sanity check: planning is read-only."""
    router = _mock_router()
    planner = Planner(router, ContextBuilder())
    plan = planner.generate_plan("Delete everything")
    # Planning itself never touches the filesystem.
    assert plan.summary
