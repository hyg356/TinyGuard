"""Shared TinyGuard policy and source-discovery helpers."""

from pathlib import Path

FORBIDDEN_NAMES = frozenset({"db", "database"})
IGNORED_DIRS = frozenset({".git", ".venv", "venv", "__pycache__", ".tox", ".mypy_cache"})
NON_APPLICATION_DIRS = frozenset({"tests", "test", "docs", "examples", "build", "dist"})


def is_forbidden_module_name(name: str, forbidden=FORBIDDEN_NAMES) -> bool:
    """Match forbidden module components, not arbitrary imported symbols."""
    if not isinstance(name, str) or not name:
        return False
    parts = [part for part in name.split(".") if part]
    return any(part in forbidden for part in parts)


def discover_python_files(root: Path) -> list[Path]:
    """Discover project Python files without testing ancestor path components."""
    root = Path(root).resolve()
    if not root.is_dir():
        return []
    files = []
    for path in root.rglob("*.py"):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in IGNORED_DIRS for part in relative.parts[:-1]):
            continue
        files.append(path)
    return sorted(files)


def is_api_entrypoint(relative_path: Path) -> bool:
    """Identify likely application API modules, excluding test/docs trees."""
    parts = relative_path.parts
    if any(part.lower() in NON_APPLICATION_DIRS for part in parts[:-1]):
        return False
    return relative_path.name == "api.py" or "api" in parts[:-1]
