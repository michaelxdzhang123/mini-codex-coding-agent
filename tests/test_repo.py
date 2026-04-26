"""Tests for the M7 repo inspection module."""

from __future__ import annotations

import pytest

from core.repo.browser import RepoBrowser


@pytest.fixture
def sample_repo(tmp_path: pytest.TempPathFactory) -> str:
    root = tmp_path / "sample_repo"
    root.mkdir()
    (root / "README.md").write_text("# Sample\nThis is a sample repo.", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("def main():\n    print('hello')\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_app.py").write_text("def test_main():\n    pass\n", encoding="utf-8")
    return str(root)


def test_browser_lists_files(sample_repo: str) -> None:
    browser = RepoBrowser(sample_repo)
    entries = browser.list_dir()
    names = {e.name for e in entries}
    assert "README.md" in names
    assert "src" in names
    assert "tests" in names


def test_browser_lists_subdir(sample_repo: str) -> None:
    browser = RepoBrowser(sample_repo)
    entries = browser.list_dir("src")
    names = {e.name for e in entries}
    assert "app.py" in names


def test_browser_read_file(sample_repo: str) -> None:
    browser = RepoBrowser(sample_repo)
    content = browser.read_file("src/app.py")
    assert "def main():" in content


def test_browser_search_keyword(sample_repo: str) -> None:
    browser = RepoBrowser(sample_repo)
    results = browser.search_keyword("hello")
    assert len(results) == 1
    assert results[0]["path"] == "src/app.py"
    assert results[0]["line"] == 2


def test_browser_blocks_traversal(sample_repo: str) -> None:
    browser = RepoBrowser(sample_repo)
    with pytest.raises(ValueError, match="outside repo"):
        browser.list_dir("../etc")
    with pytest.raises(ValueError, match="outside repo"):
        browser.read_file("../secret.txt")


def test_browser_missing_root() -> None:
    with pytest.raises(FileNotFoundError):
        RepoBrowser("/nonexistent/path")
