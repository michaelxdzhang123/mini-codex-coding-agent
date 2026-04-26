"""Command guard: validate commands against the tool whitelist."""

from __future__ import annotations

from core.commands.config import AllowedCommand, ToolWhitelistConfig


class CommandGuard:
    """
    Enforces the command execution policy.

    Rules:
    1. Blocked patterns (exact and contains) are denied immediately.
    2. Only exact-match allowed commands may run.
    3. Commands requiring approval are flagged but not blocked here.
    """

    def __init__(self, config: ToolWhitelistConfig) -> None:
        self.config = config
        self._command_index = {self._normalize(c.command): c for c in config.allowed_commands}

    def validate(self, command: str) -> AllowedCommand:
        """
        Validate a command string against the whitelist.

        Returns the matching AllowedCommand entry if valid.

        Raises:
            ValueError: If the command is blocked or not in the allowlist.
        """
        raw = command.strip()
        if not raw:
            raise ValueError("Empty command")

        # Rule 1: blocked exact patterns
        if raw in self.config.blocked_exact:
            raise ValueError(f"Command blocked by exact match: {raw}")

        # Rule 1: blocked contains patterns
        for pattern in self.config.blocked_contains:
            if pattern in raw:
                raise ValueError(f"Command blocked by pattern: {pattern}")

        # Rule 2: must be exact allowlist match
        normalized = self._normalize(raw)

        if not self.config.case_sensitive:
            normalized = normalized.lower()

        matched = self._command_index.get(normalized)
        if matched is None:
            raise ValueError(
                f"Command not in allowlist: {raw}"
            )

        return matched

    def requires_approval(self, command: str) -> bool:
        """Check whether a command requires explicit approval before running."""
        try:
            matched = self.validate(command)
        except ValueError:
            # Unknown commands require approval if configured
            return self.config.require_approval_if_not_exact_match

        if matched.requires_approval:
            return True
        if matched.category in self.config.approval_categories:
            return True
        return False

    def _normalize(self, command: str) -> str:
        if self.config.normalize_whitespace:
            return " ".join(command.split())
        return command
