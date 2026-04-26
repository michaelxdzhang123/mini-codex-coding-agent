# Milestones

This document defines the phased implementation plan for the local coding agent platform.

The platform is designed for:
- local repositories
- local models
- local RAG
- safe command execution
- approval and audit workflows

Each milestone should be implemented independently.
Do not bundle multiple milestones unless explicitly requested.

---

## M0 — Flask Bootstrap

### Goal
Set up the basic Flask project and local development workflow.

### Tasks
- create Flask application factory
- create web and api blueprints
- add base templates
- configure SQLAlchemy
- configure Alembic
- configure Redis
- add `/health`
- add homepage
- add Makefile and uv-based scripts
- initialize docs and project structure

### Output
- runnable Flask app
- `/health` endpoint
- base HTML layout
- DB migration setup
- local dev commands documented

### Done When
- `make dev` works
- homepage loads
- `/health` returns success
- DB migration tooling is initialized

---

## M1 — Tasks and Repository Access

### Goal
Allow users to create tasks and inspect approved local repositories.

### Tasks
- create `Task` and `TaskLog` models
- create `Repo` model
- implement task create/list/detail
- implement repo registration
- implement repo tree browsing
- implement file read
- implement code keyword search
- enforce workspace root restrictions
- add task and repo pages in Flask/Jinja

### Output
- `/tasks` pages
- `/repos` pages
- task APIs
- repo APIs
- path safety for repo access

### Done When
- user can submit a task
- user can register a repo
- user can browse repo files
- path traversal is blocked
- task and repo pages work end-to-end

---

## M2 — Model Router ✅ Completed

### Goal
Introduce a local multi-model routing layer.

### Tasks
- add model registry/config support
- add model router module
- define model roles:
  - coder
  - instruct
  - embedding
  - reranker
- support mock adapters first
- define task-to-model routing policy
- add project-level model defaults

### Output
- `core/models/router.py`
- model role definitions
- model config file(s)
- mock local model adapter

### Delivered
- `core/models/roles.py` — `ModelRole` enum and `role_for_task()` mapping
- `core/models/config.py` — `ModelConfig`, `ProjectDefaults`, `ModelRegistryConfig`, `ModelRegistry`
- `core/models/adapter.py` — `ModelAdapter` base class + `MockModelAdapter`
- `core/models/router.py` — `ModelRouter` with `RoutingPolicy`
- `configs/models/default.yaml` — default mock model registry
- `tests/test_model_router.py` — 18 tests covering routing, fallback, config loading

### Done When
- system can decide which model role should handle a step
- routing is configurable
- no business logic is hardcoded to a single model
- mock fallback works without real local models

---

## M3 — Local RAG Foundation ✅ Completed

### Goal
Add minimal local RAG support for project knowledge retrieval.

### Tasks
- add knowledge source registry
- add chunker
- add indexer
- add retriever
- support local file types:
  - md
  - txt
  - pdf
- use local persistence vector store
- add config for knowledge sources
- add Makefile targets:
  - `make index-knowledge`
  - `make query-knowledge`

### Output
- `core/rag/` modules
- `configs/rag_sources/default.yaml`
- local knowledge directories
- working local indexing and query flow

### Delivered
- `core/rag/chunker.py` — sliding-window text chunking (already present)
- `core/rag/source_registry.py` — YAML knowledge source registry with path validation
- `core/rag/indexer.py` — ChromaDB-based indexer with `DefaultEmbeddingFunction`
- `core/rag/retriever.py` — ChromaDB semantic retriever returning `RetrievedChunk` with source labels
- `configs/rag_sources/default.yaml` — approved knowledge source config
- `tests/test_rag.py` — 12 tests covering index, query, source labels, empty collection, roundtrip
- Connected M3 RAG into M1 Flask app (`flask/flaskr/blog.py`) so chat uses vector retrieval when `use_rag=true`

### Done When
- system can index approved local knowledge
- system can retrieve top-k relevant chunks
- retrieval returns source labels
- no arbitrary filesystem scanning is allowed

---

## M4 — Planning and Context Builder ✅ Completed

### Goal
Generate structured plans using local models and relevant local knowledge.

### Tasks
- implement planner
- implement context builder
- planner output must include:
  - summary
  - assumptions
  - steps
  - files_to_inspect
  - knowledge_to_consult
  - commands_to_run
  - risks
- retrieve local knowledge when relevant
- combine repo context + RAG context + rules
- add plan display page

### Output
- task-to-plan flow
- context builder module
- plan UI
- structured plan JSON

### Delivered
- `core/planner/plan.py` — `Plan` dataclass with JSON serialization
- `core/planner/context_builder.py` — `ContextBuilder` that combines task + repo files + RAG chunks
- `core/planner/planner.py` — `Planner` using M2 instruct model; structured section parser + fallback heuristic
- `tests/test_planner.py` — 11 tests covering plan roundtrip, parsing, fallback, read-only safety
- Flask integration:
  - `plan` table in DB with migration support
  - `POST /api/plan` — generate plan from conversation
  - `GET /plans` and `GET /plan/<id>` — plan list and detail pages
  - `GET /api/plans` — API list
  - Templates: `plans.html`, `plan.html`
  - "Generate Plan" button in chat UI
  - "Plans" card on dashboard menu

### Done When
- user can generate a plan from a task
- plan references relevant files and knowledge
- context stays compact and task-focused
- planning does not modify files

---

## M5 — Patch Proposal and Approval ✅ Completed

### Goal
Generate controlled code edits and require approval before apply.

### Tasks
- add patch model
- implement patch proposal flow
- generate diff preview
- support apply/reject actions
- enforce workspace-only edits
- add protected file rules
- add patch audit logging
- show diff in UI

### Output
- patch proposal API
- diff page
- approval/rejection flow
- protected file enforcement

### Delivered
- `core/patcher/patch.py` — `PatchProposal` and `FileEdit` dataclasses with JSON serialization
- `core/patcher/diff.py` — `DiffRenderer` using `difflib.unified_diff`
- `core/patcher/guard.py` — `PathGuard` with path-traversal blocking, workspace roots, and protected file enforcement
- `core/patcher/applier.py` — `PatchApplier` with `PatchAuditLog` (apply/reject/audit)
- `tests/test_patcher.py` — 14 tests covering diff rendering, path guard, protected files, apply/reject, audit logs
- Flask integration:
  - `patch` table in DB with migration support
  - `POST /api/patch/propose` — create proposal from plan/conversation
  - `GET /patches` and `GET /patch/<id>` — list and review pages
  - `POST /api/patch/<id>/approve` — apply after validation
  - `POST /api/patch/<id>/reject` — reject without modifying files
  - Templates: `patches.html`, `patch.html` with diff preview and approve/reject buttons
  - "Propose Patch" button on plan detail page
  - "Patches" card on dashboard menu

### Done When
- user can review patch proposals
- files are not modified silently
- protected files are blocked
- approval is required before apply

---

## M6 — Safe Command Runner ✅ Completed

### Goal
Allow safe development commands through controlled entry points.

### Tasks
- implement command guard
- load `configs/tool_whitelist.yaml`
- allow only approved Makefile targets
- capture stdout/stderr/exit code
- store execution logs
- add command log display page
- enforce approval for sensitive categories

### Output
- safe command execution flow
- command audit logs
- command review page
- whitelist-backed enforcement

### Delivered
- `core/commands/config.py` — `ToolWhitelistLoader` parsing `configs/tool_whitelist.yaml`
- `core/commands/guard.py` — `CommandGuard` with blocked-pattern checks, exact-match allowlist, and approval categorization
- `core/commands/runner.py` — `SafeCommandRunner` using `subprocess.run` with timeout, stdout/stderr/exit code capture
- `core/commands/audit.py` — `ExecutionLog` with full audit trail
- `tests/test_commands.py` — 14 tests covering config loading, guard allow/deny, approval logic, runner execution, audit accumulation
- Fixed malformed `configs/tool_whitelist.yaml` (moved `index-knowledge` and `query-knowledge` into `allowed_commands`)
- Flask integration:
  - `command_log` table in DB with migration support
  - `POST /api/command/run` — validates, runs immediately or creates pending request
  - `POST /api/command/<id>/approve` — approves and runs pending command
  - `POST /api/command/<id>/cancel` — cancels pending command
  - `GET /commands` and `GET /command/<id>` — list and detail pages
  - Templates: `commands.html` (with inline run form), `command.html` (with approve/cancel buttons)
  - "Commands" card on dashboard menu

### Done When
- allowed commands run successfully
- blocked commands are denied
- exact-match policy works
- logs are visible and traceable

---

## M7 — End-to-End MVP

### Goal
Connect the full local coding workflow into one demonstrable MVP.

### Tasks
- connect:
  - task creation
  - repo inspection
  - plan generation
  - local RAG retrieval
  - patch proposal
  - approval
  - safe command execution
  - logging
- add one complete demo scenario
- add integration tests
- improve README and runbook
- make local setup reproducible

### Output
- working MVP
- demo flow
- integration tests
- updated docs

### Done When
- user can complete:
  task → repo → plan → knowledge → patch → approval → checks → result
- at least one demo passes end-to-end
- setup works from documentation
- core security rules remain enforced

---

## M8 — Project Profiles and Multi-Project Defaults

### Goal
Support per-project configuration for models, knowledge sources, and safety defaults.

### Tasks
- add project registry config
- bind project to:
  - default coder model
  - default instruct model
  - default embedding model
  - default reranker model
  - approved workspace roots
  - attached knowledge sources
  - protected files
  - command defaults
- add project settings page

### Output
- project profile config
- project settings UI
- project-aware routing behavior

### Done When
- different projects can use different local defaults
- project-specific knowledge sources are respected
- project-specific protected files are enforced

---

## M9 — VS Code Integration Prep (Optional, Later)

### Goal
Prepare the backend to support a future IDE frontend without changing core logic.

### Tasks
- keep APIs stable
- separate UI logic from orchestration logic
- document IDE-facing API contracts
- ensure repo / plan / patch / command flows are API-driven

### Output
- stable backend contracts
- IDE-ready documentation

### Done When
- future VS Code integration can reuse existing APIs
- no major backend rewrite is needed for IDE support

---

# Execution Rules

- Only implement one milestone at a time
- Do not skip milestones
- Do not expand security permissions automatically
- Do not modify protected files unless explicitly requested by a human
- Prefer simple implementations over heavy abstractions
- Prefer local-first design
- Keep all command execution behind whitelist and approval rules
- Update docs after each milestone

---

# Priority Order

When making tradeoffs, prioritize in this order:

1. safety
2. milestone scope discipline
3. local runnability
4. repository correctness
5. RAG relevance
6. model routing clarity
7. extensibility

---

# Phase 1 Success Criteria

Phase 1 is successful if a user can:

1. open the Flask web UI
2. create a task
3. inspect a local approved repository
4. generate a structured plan
5. retrieve relevant local knowledge
6. review a proposed patch
7. approve the patch
8. run safe checks
9. review logs and results

That is enough for Phase 1.
