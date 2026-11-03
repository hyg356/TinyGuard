"""Convert project-relative Python paths to importable module names."""

from pathlib import Path


def path_to_module(filepath: Path) -> str:
    """
    Convert a path relative to a project root into a dotted module name.

    In a conventional ``src/`` layout, ``src`` is a source root rather than
    part of the import name: ``src/pkg/api.py`` becomes ``pkg.api``.
    """
    module_path = Path(filepath).with_suffix("")
    parts = list(module_path.parts)

    if parts and parts[0] == "src":
        parts.pop(0)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def module_name_for_file(project_root: Path, filepath: Path) -> str:
    """Map a discovered file to its import name, including src-layout files."""
    root = Path(project_root).resolve()
    path = Path(filepath).resolve()
    relative = path.relative_to(root)
    return path_to_module(relative)
