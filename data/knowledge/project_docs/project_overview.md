# Project Overview

## Project Name
Mini Local Coding Agent Platform

## Purpose
This project is a local coding agent platform for small engineering teams.

It helps users:
- create coding tasks
- inspect local repositories
- retrieve local knowledge
- generate implementation plans
- propose code edits
- run safe checks
- review diffs and logs

## Phase 1 Scope
Phase 1 includes:
- Flask web UI
- local repository browsing
- structured task planning
- local RAG support
- safe patch proposal
- diff preview
- safe command execution through allowlist
- human approval before file apply

Phase 1 does not include:
- VS Code extension
- multi-repo orchestration
- production deployment
- arbitrary shell execution
- full enterprise permission system

## Main Modules

### Web Layer
The user interacts through a Flask web UI.

### Task Module
Stores and tracks coding tasks.

### Repository Module
Provides controlled access to approved local repositories.

### Planner
Builds structured implementation plans from user tasks.

### Local RAG
Retrieves relevant local knowledge from approved sources.

### Patch Generator
Proposes file changes and diffs.

### Command Runner
Runs safe commands such as test/lint/format through allowlisted Makefile targets.

### Approval Layer
Requires human approval before applying file changes or running sensitive actions.

## Expected User Flow
1. User creates a coding task
2. User selects a repository
3. System generates a structured plan
4. System retrieves relevant local knowledge
5. System proposes a patch
6. User reviews the diff
7. User approves the change
8. System runs safe checks
9. User reviews results and logs

## Safety Principles
- workspace-only file access
- whitelist-based command execution
- protected files cannot be modified automatically
- all risky actions require approval
- logs must be visible and auditable

## Local Model Roles
This project may use multiple local models:

- coder model: code generation and patching
- instruct model: planning and explanation
- embedding model: knowledge indexing
- reranker model: retrieval ranking

## Notes
This file is intended as a project-level knowledge source for the RAG system.
