"""Verify proposed source replacements in a disposable project copy."""

import shutil
import tempfile
import tokenize
from pathlib import Path

from tinyguard.graph_engine import (
    GraphBuildError,
    build_dependency_graph,
    find_forbidden_path,
)
from tinyguard.module_resolver import module_name_for_file
from tinyguard.rules import discover_python_files, is_api_entrypoint


def verify_project(root: Path) -> tuple[bool, list[str]]:
    """Check syntax/encoding and architectural rules consistently with CLI."""
    root = Path(root).resolve()
    files = discover_python_files(root)
    try:
        graph = build_dependency_graph(root)
    except GraphBuildError as exc:
        return False, [f"Invalid project source: {issue}" for issue in exc.issues]

    entrypoints = [p for p in files if is_api_entrypoint(p.relative_to(root))]
    if not entrypoints:
        return False, ["No API entry points found; nothing was checked."]

    issues = []
    for filepath in entrypoints:
        relative = filepath.relative_to(root)
        module = module_name_for_file(root, filepath)
        path = find_forbidden_path(graph, start=module)
        if path:
            issues.append(
                f"{relative}: forbidden dependency chain: {' -> '.join(path)}"
            )
    return not issues, issues


def verify_patch(
    project_root: str | Path,
    proposed_files: dict[str, str],
) -> tuple[bool, list[str]]:
    """Verify complete replacements in a temporary copy; never edit originals."""
    source_root = Path(project_root).resolve()
    if not source_root.is_dir():
        return False, [f"Project directory does not exist: {source_root}"]
    if not isinstance(proposed_files, dict) or not proposed_files:
        return False, ["No proposed file changes were supplied."]

    for relative_name, contents in proposed_files.items():
        if not isinstance(relative_name, str) or not relative_name.strip():
            return False, ["Every proposed path must be a non-empty string."]
        relative_path = Path(relative_name)
        if (
            relative_path.is_absolute()
            or ".." in relative_path.parts
            or "\\" in relative_name
            or relative_path.suffix != ".py"
        ):
            return False, [f"Unsafe or unsupported file path: {relative_name!r}"]
        if not isinstance(contents, str):
            return False, [f"File contents must be text: {relative_name!r}"]
        destination = (source_root / relative_path).resolve()
        if not destination.is_relative_to(source_root):
            return False, [f"Path escapes project root: {relative_name!r}"]
        if not destination.is_file():
            return False, [
                f"Proposed changes must target existing files: {relative_name!r}"
            ]

    try:
        with tempfile.TemporaryDirectory(prefix="tinyguard_verify_") as temp_dir:
            temporary_root = Path(temp_dir) / "project"
            shutil.copytree(
                source_root,
                temporary_root,
                ignore=shutil.ignore_patterns(
                    ".git", ".venv", "venv", "__pycache__", ".tox", ".mypy_cache"
                ),
            )
            for relative_name, contents in proposed_files.items():
                (temporary_root / relative_name).write_text(contents, encoding="utf-8")
            passed, issues = verify_project(temporary_root)
            return (True, ["Syntax and architectural checks passed."]) if passed else (False, issues)
    except (OSError, UnicodeError) as exc:
        return False, [f"Could not verify proposed patch: {exc}"]
