
"""TinyGuard command-line entry point."""

import sys
from pathlib import Path

from tinyguard.graph_engine import (
    GraphBuildError,
    build_dependency_graph,
    find_forbidden_path,
)
from tinyguard.module_resolver import module_name_for_file
from tinyguard.rules import (
    IGNORED_DIRS,
    discover_python_files,
    is_api_entrypoint,
)


def _analyze_root(root: Path):
    """Build a graph and identify API entry points for one candidate root."""
    graph = build_dependency_graph(root)
    files = discover_python_files(root)

    entrypoints = [
        path
        for path in files
        if is_api_entrypoint(path.relative_to(root))
    ]

    edge_count = sum(len(edges) for edges in graph.values())

    return graph, files, entrypoints, (edge_count, len(entrypoints))


def _select_source_root(root: Path):
    """Select a uniquely better nested Python source root, if one exists."""
    root = Path(root).resolve()

    root_graph, root_files, root_entrypoints, root_score = _analyze_root(root)

    best_root = root
    best_graph = root_graph
    best_files = root_files
    best_entrypoints = root_entrypoints
    best_score = root_score
    ambiguous = False

    try:
        children = sorted(root.iterdir())
    except OSError:
        return root, root_graph, root_files, root_entrypoints

    for candidate in children:
        if not candidate.is_dir():
            continue

        if candidate.name.startswith(".") or candidate.name in IGNORED_DIRS:
            continue

        try:
            graph, files, entrypoints, score = _analyze_root(candidate)
        except GraphBuildError:
            continue

        if not entrypoints:
            continue

        if score > best_score:
            best_root = candidate
            best_graph = graph
            best_files = files
            best_entrypoints = entrypoints
            best_score = score
            ambiguous = False

        elif score == best_score and candidate != best_root:
            if score > root_score:
                ambiguous = True

    if ambiguous:
        return root, root_graph, root_files, root_entrypoints

    return best_root, best_graph, best_files, best_entrypoints


def check_repository(root: Path) -> int:
    """Check API entry points for direct and transitive forbidden imports."""
    root = Path(root).resolve()

    try:
        source_root, graph, files, entrypoints = _select_source_root(root)
    except GraphBuildError as exc:
        for issue in exc.issues:
            print(f"ERROR: {issue}")
        print(f"\nTinyGuard failed: {len(exc.issues)} analysis error(s).")
        return len(exc.issues)

    if source_root != root:
        print(
            "INFO: Detected Python source root: "
            f"{source_root.relative_to(root)}"
        )

    if not entrypoints:
        print("ERROR: No API entry points found; nothing was checked.")
        return 2

    violations = 0

    for filepath in entrypoints:
        relative_path = filepath.relative_to(source_root)
        start_module = module_name_for_file(source_root, filepath)

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
