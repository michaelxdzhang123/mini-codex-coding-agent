# AGENTS.md

## Project
Build a minimal internal web-based coding agent for small engineering teams in China.

Phase 1 is web-only and uses Flask as the main framework.

## Default run scope
- Work on exactly one milestone per run.
- Unless the user explicitly says otherwise, always choose the earliest incomplete milestone.
- If the user says "start from M1", treat all milestones after M1 as future context only.
- Do not implement, plan in detail, or scaffold future milestones unless required by the current milestone.
- Do not spawn one agent per milestone.
- Prefer a single-agent workflow for milestone implementation unless the user explicitly requests subagents.

## Required reading order
Before implementing:
1. Read `docs/product.md`
2. Read `docs/architecture.md`
3. Read `docs/milestones.md`
3. Summarize only the current milestone's required outputs, done-when criteria, and missing pieces.

## Current milestone discipline
For each run:
1. Identify the current milestone.
2. Summarize what is missing for that milestone only.
3. Propose a short implementation plan for that milestone only.
4. Implement only that milestone.
5. Run only the relevant checks for files changed.
6. Update docs affected by the current milestone.
7. Report changed files, assumptions, and remaining gaps.

## Tech and environment
- Python 3.11+
- Flask application factory pattern
- Flask Blueprints
- Jinja2 templates
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- RQ or Celery
- `uv` for environment and dependency management

## Command rules
- Prefer `make` targets over raw shell commands.
- Prefer:
  - `make dev`
  - `make test`
  - `make lint`
  - `make format`
  - `make db-upgrade`
- Do not install system packages automatically.
- Do not use `pip install`, `uv pip install`, `apt`, `apt-get`, `yum`, `dnf`, or `brew` unless the user explicitly asks.
- Assume the user will run `uv sync` manually after dependency changes.

## Safety
- Only access configured workspace roots.
- Only read and write files inside approved workspace directories.
- Block path traversal such as `../`.
- Never modify files outside approved workspace roots.
- Require proposal → diff → approval before apply for code edits.
- Never suggest destructive commands such as `sudo`, `rm -rf`, `ssh`, `scp`, or `curl | bash`.

## Planning output
Planning must not modify files.
Preferred plan fields:
- `summary`
- `assumptions`
- `steps`
- `files_to_inspect`
- `risks`

## Testing and verification
At minimum, protect with tests when relevant:
- path guard behavior
- command guard behavior
- task creation flow
- repo access restrictions
- plan schema behavior
- edit approval flow

## Done when
A milestone is done only if:
- the Flask app runs locally
- the milestone's core flow works end-to-end
- relevant tests pass
- docs are updated
- unsafe actions remain blocked
- the implementation matches the current milestone scope
