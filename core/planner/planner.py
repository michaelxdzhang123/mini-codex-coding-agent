"""Planner: generate structured plans using local models."""

from __future__ import annotations

import re

from core.models.roles import ModelRole
from core.models.router import ModelRouter
from core.planner.context_builder import ContextBuilder
from core.planner.plan import Plan


class Planner:
    """
    Generates structured implementation plans.

    Uses the instruct model (via M2 router) and combines:
    - task description
    - repository context
    - local RAG knowledge

    Planning does **not** modify files.
    """

    def __init__(self, router: ModelRouter, context_builder: ContextBuilder) -> None:
        self.router = router
        self.context_builder = context_builder

    def generate_plan(
        self,
        task_description: str,
        repo_files: list[str] | None = None,
    ) -> Plan:
        """
        Generate a structured plan for the given task.

        Args:
            task_description: What the user wants to achieve.
            repo_files: Optional list of relevant files in the repo.

        Returns:
            A populated Plan object.
        """
        context = self.context_builder.build(task_description, repo_files)
        prompt = self._build_planning_prompt(context)

        adapter = self.router.route_by_role(ModelRole.INSTRUCT)
        raw_response = adapter.generate(prompt)

        return self._parse_response(raw_response)

    @staticmethod
    def _build_planning_prompt(context: str) -> str:
        return (
            "You are a careful engineering planner. "
            "Given the context below, generate a structured implementation plan.\n\n"
            "Required output format:\n"
            "summary: <one-line summary>\n"
            "assumptions:\n"
            "- <assumption 1>\n"
            "steps:\n"
            "- <step 1>\n"
            "files_to_inspect:\n"
            "- <file path 1>\n"
            "knowledge_to_consult:\n"
            "- <knowledge source 1>\n"
            "commands_to_run:\n"
            "- <command 1>\n"
            "risks:\n"
            "- <risk 1>\n\n"
            f"Context:\n{context}\n"
        )

    @staticmethod
    def _parse_response(raw: str) -> Plan:
        """
        Parse a structured or semi-structured response into a Plan.

        Tries strict section parsing first, then falls back to heuristic extraction.
        """
        plan = Plan()
        if not raw or not raw.strip():
            return plan

        # Try strict section parsing
        sections = Planner._extract_sections(raw)
        if sections:
            plan.summary = sections.get("summary", [""])[0]
            plan.assumptions = sections.get("assumptions", [])
            plan.steps = sections.get("steps", [])
            plan.files_to_inspect = sections.get("files_to_inspect", [])
            plan.knowledge_to_consult = sections.get("knowledge_to_consult", [])
            plan.commands_to_run = sections.get("commands_to_run", [])
            plan.risks = sections.get("risks", [])

        if not plan.is_empty():
            return plan

        # Fallback: heuristic extraction for mock/template responses
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

        # First non-bracket line as summary
        for ln in lines:
            if not ln.startswith("[") and not ln.startswith("#"):
                plan.summary = ln
                break

        # Numbered or bullet lines as steps
        for ln in lines:
            if re.match(r"^\d+\.\s+", ln):
                plan.steps.append(re.sub(r"^\d+\.\s+", "", ln))
            elif ln.startswith("- ") and ln not in plan.summary:
                plan.steps.append(ln[2:])

        if not plan.summary:
            plan.summary = raw.strip().splitlines()[0][:200]

        return plan

    @staticmethod
    def _extract_sections(text: str) -> dict[str, list[str]] | None:
        """
        Extract sections like 'steps:', 'risks:', etc. from structured text.

        Returns None if no recognizable sections are found.
        """
        section_pattern = re.compile(
            r"^(summary|assumptions|steps|files_to_inspect|"
            r"knowledge_to_consult|commands_to_run|risks):\s*(.*)",
            re.IGNORECASE,
        )

        sections: dict[str, list[str]] = {}
        current_section: str | None = None

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            match = section_pattern.match(stripped)
            if match:
                current_section = match.group(1).lower()
                remainder = match.group(2).strip()
                if current_section not in sections:
                    sections[current_section] = []
                if remainder:
                    sections[current_section].append(remainder)
                continue

            if current_section and stripped.startswith("-"):
                sections[current_section].append(stripped[1:].strip())

        return sections if sections else None
