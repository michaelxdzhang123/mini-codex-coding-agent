# AGENTS.md

## Project

Build a minimal internal web-based coding agent for small engineering teams in China.

Phase 1 is **web-only** and uses **Flask** as the main framework.

This project is intended to be implemented incrementally by milestone.

---

## Phase 1 Goal

Deliver a working MVP that allows a user to:

1. submit a coding task in a Flask web UI
2. register and inspect a local repository/workspace
3. generate a structured task plan
4. search code and files
5. propose and apply file edits inside the workspace only
6. run lint/test/build through a whitelist-controlled command runner
7. display logs, diffs, and task results in the web UI
8. require user approval before finalizing file changes

---

## Non-Goals

The following are explicitly out of scope for Phase 1:

- no VS Code extension
- no React, Vue, or Next.js frontend
- no multi-repo orchestration
- no production deployment automation
- no arbitrary shell access
- no SSH / SCP
- no destructive system operations
- no full RBAC or enterprise permission center
- no direct production database writes
- no fully autonomous coding without human review

---

## Framework and Stack Constraints

Use the following stack unless a milestone explicitly states otherwise:

- Python 3.11+
- Flask
- Flask application factory pattern
- Flask Blueprints
- Jinja2 templates for UI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- RQ or Celery for background jobs
- OpenAI-compatible LLM adapter abstraction
- Mock LLM provider is allowed in early milestones

## Local RAG Rules

Phase 1 includes a minimal local RAG system for project knowledge retrieval.

### RAG goals
The local RAG layer may be used to:
- retrieve relevant local project documentation
- retrieve coding standards
- retrieve design notes
- retrieve domain knowledge that helps coding tasks

### RAG constraints
- Keep RAG minimal in Phase 1
- Use local-persistence Chroma for vector storage
- Use sentence-transformers for embeddings
- Use local files only
- Do not introduce external hosted vector databases in Phase 1
- Do not add heavy infrastructure unless explicitly required

### Dependency rules
- You may update `pyproject.toml` to add Python dependencies needed for local RAG
- Do not install system packages automatically
- Do not use `pip install`, `uv pip install`, `apt`, `apt-get`, `yum`, `dnf`, `brew`, or remote install scripts
- Assume the user will run `uv sync` manually after dependency changes

### RAG execution rules
- Use approved Makefile targets only
- Prefer:
  - `make index-knowledge`
  - `make query-knowledge`
- Do not execute raw shell commands for indexing or retrieval if a Makefile target exists

### Knowledge source rules
- Only use approved local knowledge sources from config
- Do not scan arbitrary filesystem paths
- Do not retrieve from outside configured knowledge roots
- Do not silently add new knowledge roots without explicit human request

### Retrieval behavior
- Retrieve only the most relevant chunks
- Keep context small and useful
- Preserve source name and source path where possible
- Do not dump large unrelated documents into prompts


### Frontend Constraints

Phase 1 UI must be server-rendered and simple.

Use:

- Flask routes
- Jinja2 templates
- basic static CSS/JS only when needed

Do not introduce:

- React
- Vue
- Next.js
- SPA architecture
- heavy frontend build tooling unless absolutely necessary

---

## Architecture Expectations

The codebase should follow a clean modular structure.

Expected top-level areas:

- `app/` for Flask app, blueprints, models, templates, static files, and service layer
- `core/` for agent logic, tools, safety, repo handling, and LLM adapters
- `worker/` for background jobs
- `configs/` for whitelist and repo rule configuration
- `docs/` for product, architecture, milestone, security, and runbook documentation
- `tests/` for unit and integration tests

### Flask Structure Expectations

Within `app/`, prefer:

- `blueprints/web/` for HTML page routes
- `blueprints/api/` for JSON APIs
- `models/` for SQLAlchemy models
- `templates/` for Jinja templates
- `static/` for small CSS/JS assets
- `services/` for application service logic

Avoid placing all logic inside a single `app.py`.

---
## Python Environment

This project uses `uv` as the standard Python environment and dependency manager.

Rules:
- Use `uv sync` to create or update the local environment.
- Use `uv run ...` for project commands.
- Prefer the local `.venv` managed by `uv`.
- Do not use `pip install` unless explicitly requested.
- Do not introduce Poetry or Pipenv.

Examples:
- `uv sync`
- `uv run flask run`
- `uv run pytest`
- `uv run ruff check .`
## Command Execution

Prefer using Makefile targets for all operations.
Do not run raw commands unless necessary.



## Working Style

Before implementing anything:

1. read `AGENTS.md`
2. read `docs/product.md`
3. read `docs/architecture.md`
4. read `docs/milestones.md`

Implementation rules:

- implement **one milestone at a time**
- do not skip milestones
- do not implement future milestones early unless required
- keep modules small and explicit
- prefer the smallest working implementation
- update docs whenever architecture or APIs change
- add tests for core behavior
- explain large file changes before making them
- prefer clarity over clever abstractions

If something is ambiguous:

- choose the simplest design consistent with the MVP
- avoid adding infrastructure that is not yet needed

---

## Milestone Discipline

This project is milestone-driven.

For each milestone, do the following:

1. inspect current repository state
2. summarize what is missing for this milestone
3. propose a short implementation plan
4. implement only the current milestone
5. run relevant tests if available
6. update docs
7. report changed files, assumptions, and remaining gaps

Do not bundle multiple milestones into one run unless explicitly requested.

---

## Safety Constraints

Safety is more important than automation.

### Workspace Safety

- only access configured workspace roots
- only read and write files inside allowed workspace directories
- block path traversal such as `../`
- never modify files outside approved workspace roots

### Command Safety

All shell commands must pass whitelist validation.

Allowed command categories should be limited to development checks such as:

- lint
- test
- build

Examples of potentially allowed commands, depending on whitelist config:

- `pytest`
- `ruff check`
- `npm test`
- `make test`

Never execute or suggest execution of destructive or dangerous commands such as:

- `sudo`
- `rm -rf`
- `ssh`
- `scp`
- `curl | bash`
- arbitrary remote download-and-execute patterns

### Secrets and Environment

- do not read secrets outside this project
- do not assume network access is available
- prefer local mocks or test adapters in early milestones
- do not exfiltrate repository contents

---

## Editing Constraints

When implementing file editing features:

- support proposal before apply
- show diff before final apply
- require explicit approval before applying edits
- keep edits within workspace boundaries
- prefer recovery-friendly or backup-aware behavior

Do not make silent destructive file changes.

---

## Planning Constraints

When implementing planning features:

- planning must not directly modify files
- planning output should be structured
- planning output should be easy to display in the web UI

Preferred plan fields:

- `summary`
- `assumptions`
- `steps`
- `files_to_inspect`
- `risks`

Use a mock planner if no real LLM is configured yet.

---

## Testing Expectations

Every milestone should include reasonable tests.

Prefer:

- unit tests for safety rules and core services
- integration tests for main Flask routes and APIs
- simple, deterministic tests over fragile ones

At minimum, protect these with tests as soon as relevant:

- path guard behavior
- command guard behavior
- task creation flow
- repo access restrictions
- plan schema behavior
- edit approval flow

---

## Documentation Expectations

Keep documentation current.

Relevant files include:

- `README.md`
- `docs/product.md`
- `docs/architecture.md`
- `docs/milestones.md`
- `docs/api.md`
- `docs/security.md`
- `docs/runbook.md`

If implementation changes behavior, docs should be updated in the same milestone.

---

## Definition of Done

A milestone is done only if:

- the Flask app runs locally
- the milestone's core flow works end-to-end
- relevant tests pass
- docs are updated
- unsafe actions remain blocked
- the implementation matches the current milestone scope

---

## Output Expectations for Each Run

At the end of each implementation run, provide:

1. a short summary of what was completed
2. the files added or changed
3. any assumptions made
4. commands to run locally
5. remaining gaps or next steps for the current milestone

---

## Priority Order

When making tradeoffs, prioritize in this order:

1. safety
2. milestone scope discipline
3. clarity
4. local runnability
5. testability
6. extensibility

Do not optimize for future complexity too early.

---

## Phase 1 Success Criteria

Phase 1 is successful if a user can:

1. open the Flask web UI
2. create a task
3. inspect a registered repository
4. generate a structured plan
5. review a proposed edit
6. approve the edit
7. run safe checks
8. review logs and results

## Local RAG Rules

Phase 1 includes a minimal local RAG system for project knowledge retrieval.

### RAG goals
The local RAG layer may be used to:
- retrieve relevant local project documentation
- retrieve coding standards
- retrieve design notes
- retrieve domain knowledge that helps coding tasks

### RAG constraints
- Keep RAG minimal in Phase 1
- Use local-persistence Chroma for vector storage
- Use sentence-transformers for embeddings
- Use local files only
- Do not introduce external hosted vector databases in Phase 1
- Do not add heavy infrastructure unless explicitly required

### Dependency rules
- You may update `pyproject.toml` to add Python dependencies needed for local RAG
- Do not install system packages automatically
- Do not use `pip install`, `uv pip install`, `apt`, `apt-get`, `yum`, `dnf`, `brew`, or remote install scripts
- Assume the user will run `uv sync` manually after dependency changes


That is enough for Phase 1.
