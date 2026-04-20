# Python Backend Coding Standard

## General Principles
- Prefer simple and explicit code
- Keep modules small and focused
- Avoid hidden side effects
- Prefer readability over clever abstractions
- Add type hints for public functions and core internal modules

## Project Structure
- Flask app code goes under `app/`
- core agent logic goes under `core/`
- background jobs go under `worker/`
- configs go under `configs/`
- tests go under `tests/`

## Flask Conventions
- Use Flask application factory pattern
- Use Blueprints for route separation
- Keep web routes and API routes separate
- Do not place all logic in one file
- Templates should remain simple and server-rendered in Phase 1

## Service Layer
- Business logic should not live directly inside route handlers
- Route handlers should validate input, call services, and return results
- Services should remain focused and testable

## Error Handling
- Raise clear exceptions for invalid input
- Return consistent API responses
- Log important failures
- Do not expose secrets in error output

## File Safety
- Only modify files inside approved workspace roots
- Never modify protected files automatically
- Always generate a diff before applying file edits
- Require approval before applying sensitive changes

## Command Execution
- Use Makefile targets as the public command interface
- Prefer:
  - `make test`
  - `make lint`
  - `make format`
  - `make index-knowledge`
  - `make query-knowledge`
- Do not run arbitrary shell commands
- Do not install system packages automatically

## Python Style
- Use descriptive names
- Keep functions short where practical
- Avoid long nested conditionals
- Prefer dataclasses for simple data containers
- Prefer pathlib over raw path strings when possible

## Typing
- Public APIs should use type hints
- Dataclasses should define field types clearly
- Keep typed return values for core modules

## Testing
- Add tests for safety-critical logic
- Add tests for core routes and services
- At minimum, cover:
  - path guard
  - command guard
  - task creation
  - repo access rules
  - RAG config loading
  - patch approval flow

## Logging
- Log task creation
- Log command execution
- Log denied operations
- Do not log secrets
- Keep logs useful for debugging and audit

## RAG Rules
- Retrieve only relevant local knowledge
- Keep injected context concise
- Preserve source name and source path when possible
- Do not flood prompts with unnecessary text

## Final Rule
When in doubt:
- choose the simpler design
- keep behavior explicit
- preserve safety boundaries
