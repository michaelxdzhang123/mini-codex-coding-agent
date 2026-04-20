# Product

## 1. Overview

This project is a local coding agent platform for small engineering teams.

It is designed to combine:

- local code repositories
- local language models
- local knowledge retrieval (RAG)
- safe command execution
- controlled file editing
- approval workflows
- auditability

The system is intended to help developers complete coding tasks with better context, stronger control, and lower dependence on external cloud tools.

Phase 1 uses a Flask-based web interface as the primary entry point.

---

## 2. Product Positioning

This product should be understood as:

> a team-facing local coding agent console

It is not just:
- a chatbot
- a code generator
- a web IDE
- a vector search demo

It is a controlled engineering workflow system that helps a team:

- plan coding work
- inspect repositories
- retrieve relevant local knowledge
- propose code changes
- review diffs
- run safe checks
- keep an audit trail

The main use case is still **programming**.
Local models and local RAG are there to improve programming quality and relevance.

---

## 3. Target Users

Primary users:

- small engineering teams
- backend or platform teams
- teams working with local/private repositories
- teams that want local model support
- teams that want local knowledge retrieval
- teams that need review and safety controls

Typical team size for initial design:
- 3 to 20 engineers

---

## 4. Problems This Product Solves

Small teams often face these issues:

### 4.1 Repetitive coding work
Examples:
- adding similar features
- writing test scaffolds
- updating config patterns
- refactoring repeated code

### 4.2 Codebase navigation cost
Large or unfamiliar repositories are hard to search and understand quickly.

### 4.3 Knowledge fragmentation
Important project knowledge may exist across:
- docs
- markdown notes
- wiki exports
- PDFs
- coding standards
- architecture writeups

This makes it hard for a coding assistant to produce project-appropriate changes.

### 4.4 Unsafe automation risk
A coding agent that can read files and run commands can become dangerous if it is not controlled.

### 4.5 Lack of team-level control
Individual coding tools may help one developer, but teams also need:
- shared rules
- protected files
- approved command paths
- review steps
- audit logs

---

## 5. Product Goals

The product should allow a user to:

1. create a coding task
2. select a local approved repository
3. inspect code and files
4. generate a structured implementation plan
5. retrieve relevant local knowledge
6. combine repository context and knowledge context
7. propose code edits
8. review diffs before apply
9. run safe checks such as test/lint/format
10. approve or reject sensitive actions
11. view logs and history of what happened

---

## 6. Phase 1 Scope

Phase 1 focuses on a minimal but complete workflow.

### Included in Phase 1
- Flask web UI
- task creation and tracking
- repository registration and browsing
- local workspace restrictions
- structured planning
- local multi-model routing (minimal version)
- local RAG (minimal version)
- patch proposal
- diff preview
- approval before apply
- safe command execution through allowlist
- logs and audit trail

### Not included in Phase 1
- VS Code integration
- full multi-repo orchestration
- unrestricted shell execution
- enterprise auth / RBAC
- deployment automation
- cloud-first architecture
- fully autonomous coding with no approval
- advanced multi-agent collaboration

---

## 7. Core Functional Areas

## 7.1 Task Management
Users can:
- create tasks
- view task status
- inspect task details
- read task logs

This is the main workflow entry point.

---

## 7.2 Repository Inspection
Users can:
- register approved repositories
- browse file trees
- read file content
- search code by keyword

This allows the system to reason about real code rather than only generic prompts.

---

## 7.3 Planning
The system should generate a structured plan for a task.

A plan should include:
- summary
- assumptions
- steps
- files to inspect
- knowledge to consult
- commands to run
- risks

This keeps agent behavior more transparent and reviewable.

---

## 7.4 Local Knowledge Retrieval (RAG)
The system should retrieve relevant local knowledge from approved sources such as:
- project docs
- coding standards
- design notes
- wiki exports
- PDFs
- domain-specific references

The goal is to give the coding workflow project-aware context.

---

## 7.5 Patch Proposal
The system should:
- propose edits
- generate diffs
- keep file changes inside approved workspace roots
- require review before apply

This keeps the coding workflow visible and controlled.

---

## 7.6 Safe Command Execution
The system should allow only approved development commands, such as:
- tests
- lint checks
- formatting
- approved migration steps

These should run only through controlled entry points.

---

## 7.7 Approval and Audit
The system should:
- require approval for sensitive actions
- record what happened
- record which files were changed
- record which commands were run
- record which model path was used where helpful

This is critical for team trust.

---

## 8. Local Multi-Model Strategy

The system should support multiple local model roles rather than one single model for everything.

Recommended roles:

### 8.1 Coder model
Used for:
- code generation
- patch generation
- refactoring
- writing tests
- code fixes

### 8.2 Instruct model
Used for:
- task interpretation
- plan generation
- explanation
- summarization
- log/failure analysis

### 8.3 Embedding model
Used for:
- indexing local knowledge
- similarity retrieval
- local semantic search

### 8.4 Reranker model
Used for:
- ranking retrieved knowledge
- filtering noisy results
- improving retrieval precision

This makes the system more accurate and easier to tune.

---

## 9. Local Knowledge Strategy

The local RAG layer should be practical and narrow in Phase 1.

### Knowledge sources may include
- markdown docs
- txt files
- PDFs
- engineering standards
- architecture notes
- internal domain references

### Design constraints
- only use approved local sources
- do not scan arbitrary filesystem paths
- keep retrieval focused
- preserve source labels when possible
- avoid flooding the main model with too much retrieved text

---

## 10. Why This Product Still Matters If Other Coding Tools Exist

Even if developers already use coding assistants or coding CLIs, this product still provides unique value when teams need:

- local model support
- local knowledge support
- local/private repository workflows
- protected files
- command allowlists
- approval workflows
- audit trails
- project-level defaults

In that sense, this product is not trying to replace every coding assistant.
It is trying to provide a **team-safe local coding workflow layer**.

---

## 11. User Flow

A typical Phase 1 flow:

1. user opens the web UI
2. user creates a task
3. user selects a repository
4. system inspects relevant files
5. system optionally retrieves local knowledge
6. system generates a structured plan
7. system proposes a patch
8. user reviews the diff
9. user approves the change
10. system runs safe checks
11. system shows logs and results

This is the core workflow the MVP must support.

---

## 12. Example Use Cases

### Use Case A: Add a small backend feature
User asks:
> Add JWT authentication to the API.

System should:
- inspect auth-related files
- retrieve local auth standards if configured
- generate a plan
- propose code changes
- run tests
- show diff and results

### Use Case B: Write missing unit tests
User asks:
> Add tests for the repository service.

System should:
- inspect target module
- inspect existing test patterns
- optionally retrieve team testing standards
- generate patch proposal
- run approved test command

### Use Case C: Apply coding standard to a module
User asks:
> Refactor this module to follow our internal service pattern.

System should:
- inspect relevant code
- retrieve internal coding standard
- summarize intended changes
- propose patch
- request approval before apply

---

## 13. Success Criteria

Phase 1 is successful if a user can complete this flow:

task → repo → plan → local knowledge → patch → approval → checks → result

More specifically:

- the system runs locally
- users can inspect approved repositories
- users can retrieve relevant local knowledge
- plans are structured and readable
- changes are visible before being applied
- unsafe commands remain blocked
- command execution is auditable
- protected files remain protected

---

## 14. Safety Principles

This product must behave like a careful engineering assistant.

Core safety principles:

- safety is more important than speed
- local boundaries must be respected
- commands must be allowlisted
- edits must be reviewable
- protected files must not be modified automatically
- the system must not expand its own permissions
- unknown actions should be denied by default

---

## 15. Product Constraints

Phase 1 constraints:

- Flask-based web UI
- server-rendered pages
- local-first design
- minimal infrastructure
- no heavy frontend framework required
- no arbitrary shell access
- no automatic system package installation
- no uncontrolled remote execution

These constraints are deliberate and help keep the MVP safe and maintainable.

---

## 16. Future Directions

Later versions may add:

- VS Code integration
- richer project profiles
- stronger repository symbol analysis
- better patch validation
- more advanced RAG filtering
- multi-project routing
- project memory across tasks
- model performance tracking
- optional MCP integration
- automated repair loops for failed tests

These are future directions, not Phase 1 requirements.

---

## 17. Final Product Summary

This product is a local coding workflow system for teams.

It combines:
- programming assistance
- local repository awareness
- local model orchestration
- local knowledge retrieval
- safe execution
- review and auditability

The product is successful if it helps teams code faster **without giving up control**.
