"""Load and parse tool_whitelist.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class AllowedCommand:
    """One entry from the tool whitelist."""

    id: str
    command: str
    category: str
    description: str
    timeout_seconds: int
    requires_approval: bool


@dataclass(slots=True)
class ToolWhitelistConfig:
    """Parsed tool_whitelist.yaml."""

    policy_mode: str
    default_action: str
    require_exact_match: bool
    normalize_whitespace: bool
    case_sensitive: bool
    allow_shell: bool
    allow_chained_commands: bool
    allow_background_execution: bool
    allow_redirection: bool
    allow_pipes: bool
    allow_subshells: bool
    allow_env_prefixes: bool
    allowed_working_directories: list[str]
    timeout_defaults: dict[str, int]
    allowed_commands: list[AllowedCommand]
    blocked_exact: set[str]
    blocked_contains: list[str]
    approval_categories: set[str]
    require_approval_if_not_exact_match: bool


class ToolWhitelistLoader:
    """Reads and validates the tool whitelist YAML."""

    def __init__(self, config_path: str | Path, project_root: str | Path | None = None) -> None:
        self.config_path = Path(config_path)
        self.project_root = Path(project_root) if project_root is not None else Path.cwd()

    def load(self) -> ToolWhitelistConfig:
        path = self.config_path
        if not path.is_absolute():
            path = self.project_root / path

        if not path.exists():
            raise FileNotFoundError(f"Tool whitelist not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        return self._parse(raw)

    def _parse(self, raw: dict[str, Any]) -> ToolWhitelistConfig:
        policy = raw.get("policy", {})
        execution = raw.get("execution", {})
        approval = raw.get("approval", {})

        allowed_commands = [
            AllowedCommand(
                id=str(cmd["id"]),
                command=str(cmd["command"]),
                category=str(cmd.get("category", "misc")),
                description=str(cmd.get("description", "")),
                timeout_seconds=int(cmd.get("timeout_seconds", 600)),
                requires_approval=bool(cmd.get("requires_approval", False)),
            )
            for cmd in raw.get("allowed_commands", [])
        ]

        blocked = raw.get("blocked_patterns", {})

        return ToolWhitelistConfig(
            policy_mode=str(policy.get("mode", "allowlist")),
            default_action=str(policy.get("default_action", "deny")),
            require_exact_match=bool(policy.get("require_exact_match", True)),
            normalize_whitespace=bool(policy.get("normalize_whitespace", True)),
            case_sensitive=bool(policy.get("case_sensitive", True)),
            allow_shell=bool(execution.get("allow_shell", False)),
            allow_chained_commands=bool(execution.get("allow_chained_commands", False)),
            allow_background_execution=bool(execution.get("allow_background_execution", False)),
            allow_redirection=bool(execution.get("allow_redirection", False)),
            allow_pipes=bool(execution.get("allow_pipes", False)),
            allow_subshells=bool(execution.get("allow_subshells", False)),
            allow_env_prefixes=bool(execution.get("allow_env_prefixes", False)),
            allowed_working_directories=list(execution.get("allowed_working_directories", ["."])),
            timeout_defaults=dict(execution.get("timeout_seconds", {})),
            allowed_commands=allowed_commands,
            blocked_exact=set(blocked.get("exact", [])),
            blocked_contains=list(blocked.get("contains", [])),
            approval_categories=set(approval.get("require_user_approval_for_categories", [])),
            require_approval_if_not_exact_match=bool(
                approval.get("require_user_approval_if_not_exact_allowlist_match", True)
            ),
        )
