"""Build and inspect a repository-local Python dependency graph."""

import ast
import tokenize
from collections import deque
from pathlib import Path

from tinyguard.import_resolver import resolve_import
from tinyguard.module_resolver import module_name_for_file, path_to_module
from tinyguard.rules import (
    FORBIDDEN_NAMES,
    discover_python_files,
    is_forbidden_module_name,
)


class GraphBuildError(ValueError):
    """Raised when source files cannot be parsed safely enough to analyze."""

    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("; ".join(issues))


def find_forbidden_path(graph, start, forbidden=FORBIDDEN_NAMES):
    """Return the shortest path from start to any forbidden module."""
    visited = {start}
    queue = deque([(start, [start])])

    while queue:
        current, path = queue.popleft()
        if current != start and is_forbidden_module_name(current, forbidden):
            return path
        for neighbor in graph.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None


def _resolve_module(project_root: Path, dotted_name: str) -> str | None:
    target_path = resolve_import(project_root, dotted_name)
    if target_path is None:
        return None
    if target_path.is_dir():
        # Namespace package directory. It has no __init__.py to map.
        relative = target_path.relative_to(project_root)
        if relative.parts and relative.parts[0] == "src":
            relative = Path(*relative.parts[1:])
        return ".".join(relative.parts)
    return module_name_for_file(project_root, target_path)


def _add_edge(graph: dict[str, list[str]], src: str, target: str | None) -> None:
    if target and target != src and target not in graph.setdefault(src, []):
        graph[src].append(target)


def _add_dotted_edges(
    graph: dict[str, list[str]],
    src: str,
    dotted_name: str,
    project_root: Path,
) -> None:
    """Add resolvable prefixes; retain unresolved forbidden module targets."""
    parts = dotted_name.split(".")
    for i in range(1, len(parts) + 1):
        prefix = ".".join(parts[:i])
        target = _resolve_module(project_root, prefix)
        if target:
            _add_edge(graph, src, target)
        elif prefix.split(".")[0] in FORBIDDEN_NAMES:
            # Catch direct imports named db/database, but do not flag an
            # unrelated external package merely because one of its nested
            # modules happens to be called ``db``.
            _add_edge(graph, src, prefix)
            graph.setdefault(prefix, [])


def _resolve_relative_base(current_module, is_package, level, module):
    """Resolve a relative import; return None for beyond-top-level imports."""
    parts = current_module.split(".")
    package_parts = parts if is_package else parts[:-1]
    up = level - 1

    # ``from .. import x`` in pkg/a.py attempts to go above pkg and is invalid.
    if up >= len(package_parts):
        return None

    base_parts = package_parts[:len(package_parts) - up] if up else package_parts[:]
    if module:
        base_parts.extend(module.split("."))
    return ".".join(base_parts)


def _dynamic_import_names(tree: ast.AST):
    """Yield constant module names used by importlib.import_module/__import__."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        func = node.func
        is_import_call = isinstance(func, ast.Name) and func.id == "__import__"
        is_importlib_call = (
            isinstance(func, ast.Attribute)
            and func.attr == "import_module"
            and isinstance(func.value, ast.Name)
            and func.value.id == "importlib"
        )
        is_import_module_alias = isinstance(func, ast.Name) and func.id == "import_module"
        if not (is_import_call or is_importlib_call or is_import_module_alias):
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            yield first.value


def build_dependency_graph(package_root: Path) -> dict[str, list[str]]:
    """
    Build a dependency graph. Parse/decode failures raise GraphBuildError
    rather than being silently omitted.
    """
    project_root = Path(package_root).resolve()
    discovered = discover_python_files(project_root)
    package_names = {
        module_name_for_file(project_root, path)
        for path in discovered
        if path.name == "__init__.py"
    }
    # If both pkg.py and pkg/__init__.py exist, Python imports the package.
    files = [
        path for path in discovered
        if path.name == "__init__.py"
        or module_name_for_file(project_root, path) not in package_names
    ]
    graph: dict[str, list[str]] = {}
    parse_issues: list[str] = []

    # Register modules and namespace-package prefixes first.
    for filepath in files:
        module_name = module_name_for_file(project_root, filepath)
        graph.setdefault(module_name, [])
        parts = module_name.split(".")
        for i in range(1, len(parts)):
            graph.setdefault(".".join(parts[:i]), [])

    for filepath in files:
        current_module = module_name_for_file(project_root, filepath)
        is_package = filepath.name == "__init__.py"
        relative = filepath.relative_to(project_root)

        try:
            # Honors UTF-8 BOMs and PEP 263 encoding declarations.
            with tokenize.open(filepath) as handle:
                source = handle.read()
            tree = ast.parse(source, filename=str(relative))
        except (SyntaxError, UnicodeError, OSError) as exc:
            parse_issues.append(f"Invalid Python file {relative}: {exc}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _add_dotted_edges(graph, current_module, alias.name, project_root)

            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base_module = _resolve_relative_base(
                        current_module, is_package, node.level, node.module
                    )
                    if base_module is None:
                        # Invalid relative import: surface as a graph issue.
                        parse_issues.append(
                            f"Invalid relative import in {relative}:{node.lineno}"
                        )
                        continue
                else:
                    base_module = node.module
                    if base_module is None:
                        continue

                if base_module:
                    _add_dotted_edges(graph, current_module, base_module, project_root)

                for alias in node.names:
                    if alias.name == "*":
                        continue
                    candidate = f"{base_module}.{alias.name}" if base_module else alias.name
                    target = _resolve_module(project_root, candidate)
                    if target:
                        _add_edge(graph, current_module, target)
                    # Do not treat a symbol named ``db`` from an unrelated
                    # third-party package as a forbidden module.

        for dynamic_name in _dynamic_import_names(tree):
            if dynamic_name.startswith("."):
                # Relative dynamic imports require runtime package context.
                continue
            _add_dotted_edges(graph, current_module, dynamic_name, project_root)

    if parse_issues:
        raise GraphBuildError(parse_issues)
    return graph
