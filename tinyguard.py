
import ast
import sys
from pathlib import Path


FORBIDDEN_NAMES = {"db", "database"}
IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__"}


def discover_python_files(root: Path) -> list[Path]:
    """Find Python files recursively, excluding common generated directories."""
    files = []

    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        files.append(path)

    return files


def contains_forbidden_name(module_name: str) -> bool:
    """Check whether a dotted module path contains db or database."""
    if not module_name:
        return False

    return any(
        part in FORBIDDEN_NAMES
        for part in module_name.split(".")
    )


def get_forbidden_imports(tree: ast.AST):
    """Yield (line number, imported module) for forbidden imports."""
    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for alias in node.names:
                if contains_forbidden_name(alias.name):
                    yield node.lineno, alias.name

        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")

            if contains_forbidden_name(module):
                yield node.lineno, module


            for alias in node.names:
                if contains_forbidden_name(alias.name):
                    imported = f"{module}.{alias.name}" if module else alias.name
                    yield node.lineno, imported


def check_repository(root: Path) -> int:
    """Scan API files and return the number of violations."""
    violations = 0

    for filepath in discover_python_files(root):
        relative_path = filepath.relative_to(root)

        if "api" not in relative_path.parts[:-1]:
            continue

        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(filepath))
        except (SyntaxError, UnicodeDecodeError) as exc:
            print(f"ERROR: Could not parse {relative_path}: {exc}")
            violations += 1
            continue

        for line_number, imported_module in get_forbidden_imports(tree):
            print(
                f"VIOLATION: {relative_path}:{line_number}: "
                f"API code imports forbidden module '{imported_module}'"
            )
            violations += 1

    if violations:
        print(f"\nTinyGuard failed: {violations} issue(s) found.")
    else:
        print("TinyGuard passed: no forbidden API imports found.")

    return violations


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    if not root.is_dir():
        print(f"ERROR: Not a directory: {root}", file=sys.stderr)
        return 2

    violations = check_repository(root)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
