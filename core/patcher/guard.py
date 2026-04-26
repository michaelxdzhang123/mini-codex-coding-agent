"""Path guard: enforce workspace boundaries and protected files."""

from __future__ import annotations

from pathlib import Path

# Default protected files for Phase 1.
# These should never be modified automatically.
DEFAULT_PROTECTED_FILES: set[str] = {
    ".env",
    ".env.local",
    ".env.production",
    "pyproject.toml",
    "requirements.txt",
    "uv.lock",
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "Dockerfile",
    "docker-compose.yml",
    "Makefile",
    ".gitignore",
    ".gitattributes",
    "LICENSE",
    "README.md",
    "AGENTS.md",
}


class PathGuard:
    """
    Enforces safe file editing boundaries.

    Rules:
    1. No path traversal (../)
    2. Edits must be inside an allowed workspace root
    3. Protected files cannot be modified
    """

    def __init__(
        self,
        allowed_roots: list[str | Path],
        protected_files: set[str] | None = None,
    ) -> None:
        self.allowed_roots = [Path(r).resolve() for r in allowed_roots]
        self.protected_files = protected_files or set(DEFAULT_PROTECTED_FILES)

    def validate(self, path: str | Path) -> Path:
        """
        Validate that a path is safe to edit.

        Returns the resolved Path if valid.

        Raises:
            ValueError: If the path violates any safety rule.
        """
        raw = str(path)

        # Rule 1: block path traversal
        if ".." in raw:
            raise ValueError(f"Path traversal not allowed: {raw}")

        target = Path(raw).resolve()

        # Rule 2: must be inside an allowed workspace root
        if not any(
            self._is_inside(target, root) for root in self.allowed_roots
        ):
            raise ValueError(
                f"Edit outside workspace not allowed: {target}"
            )

        # Rule 3: protected files
        if target.name in self.protected_files:
            raise ValueError(
                f"Protected file cannot be modified: {target.name}"
            )

        return target

    def validate_all(self, paths: list[str | Path]) -> list[Path]:
        """Validate multiple paths, returning resolved paths."""
        return [self.validate(p) for p in paths]

    @staticmethod
    def _is_inside(target: Path, root: Path) -> bool:
        try:
            target.relative_to(root)
            return True
        except ValueError:
            return False
