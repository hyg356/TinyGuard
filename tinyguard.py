"""TinyGuard command-line entry point."""

import sys
import tokenize
from pathlib import Path

from tinyguard.graph_engine import (
    GraphBuildError,
    build_dependency_graph,
    find_forbidden_path,
)
from tinyguard.module_resolver import module_name_for_file
from tinyguard.rules import discover_python_files, is_api_entrypoint


def check_repository(root: Path) -> int:
    """Check API entry points for direct and transitive forbidden imports."""
    root = Path(root).resolve()
    files = discover_python_files(root)
    try:
        graph = build_dependency_graph(root)
    except GraphBuildError as exc:
        for issue in exc.issues:
            print(f"ERROR: {issue}")
        print(f"\nTinyGuard failed: {len(exc.issues)} analysis error(s).")
        return len(exc.issues)

    entrypoints = [path for path in files if is_api_entrypoint(path.relative_to(root))]
    if not entrypoints:
        print("ERROR: No API entry points found; nothing was checked.")
        return 2

    violations = 0
    for filepath in entrypoints:
        relative_path = filepath.relative_to(root)
        start_module = module_name_for_file(root, filepath)
        forbidden_path = find_forbidden_path(graph, start=start_module)
        if forbidden_path:
            print(
                f"VIOLATION: {relative_path}: forbidden dependency chain: "
                f"{' -> '.join(forbidden_path)}"
            )
            violations += 1

    if violations:
        print(f"\nTinyGuard failed: {violations} violation(s) found.")
    else:
        print(
            f"TinyGuard passed: {len(entrypoints)} API entry point(s) checked; "
            "no forbidden dependencies found."
        )
    return violations


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"ERROR: Not a directory: {root}", file=sys.stderr)
        return 2
    result = check_repository(root)
    return 0 if result == 0 else 1 if result == 1 else 2


if __name__ == "__main__":
    sys.exit(main())
