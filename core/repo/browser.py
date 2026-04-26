"""Browse, read, and search local repositories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileEntry:
    """A file or directory in a repo."""

    name: str
    path: str
    is_dir: bool


class RepoBrowser:
    """
    Inspect an approved local repository.

    Enforces workspace root restrictions:
    - all operations stay inside the repo root
    - path traversal is blocked
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"Repo root not found: {self.root}")
        if not self.root.is_dir():
            raise NotADirectoryError(f"Repo root is not a directory: {self.root}")

    def list_dir(self, rel_path: str = ".") -> list[FileEntry]:
        """List files and directories inside a repo-relative path."""
        target = self._resolve(rel_path)
        if not target.is_dir():
            return []

        entries: list[FileEntry] = []
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            rel = str(item.relative_to(self.root))
            entries.append(FileEntry(name=item.name, path=rel, is_dir=item.is_dir()))
        return entries

    def read_file(self, rel_path: str) -> str:
        """Read text content of a repo-relative file."""
        target = self._resolve(rel_path)
        if target.is_dir():
            raise IsADirectoryError(f"Path is a directory: {rel_path}")
        return target.read_text(encoding="utf-8", errors="replace")

    def search_keyword(self, keyword: str, max_results: int = 20) -> list[dict]:
        """
        Simple keyword search across text files in the repo.

        Returns file paths and line numbers where the keyword appears.
        """
        results: list[dict] = []
        keyword_lower = keyword.lower()

        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if path.stat().st_size > 1024 * 1024:  # skip files > 1MB
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            rel = str(path.relative_to(self.root))
            for lineno, line in enumerate(text.splitlines(), start=1):
                if keyword_lower in line.lower():
                    results.append(
                        {
                            "path": rel,
                            "line": lineno,
                            "preview": line.strip()[:120],
                        }
                    )
                    if len(results) >= max_results:
                        return results

        return results

    def _resolve(self, rel_path: str) -> Path:
        """Resolve a repo-relative path, blocking traversal outside root."""
        target = (self.root / rel_path).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as e:
            raise ValueError(f"Path outside repo root: {rel_path}") from e
        return target
