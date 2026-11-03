"""Resolve import names to local modules, packages, or namespace packages."""

from pathlib import Path


def _valid_parts(module_name: str) -> list[str] | None:
    if not module_name or module_name.startswith("."):
        return None
    parts = module_name.split(".")
    if any(not part.isidentifier() for part in parts):
        return None
    return parts


def resolve_import(package_root: Path, module_name: str) -> Path | None:
    """
    Resolve a repository-local import.

    Package directories take precedence over same-named ``.py`` modules, as
    they do in Python's normal import resolution. Namespace package
    directories are returned when they contain Python source below them.
    ``src/`` is searched before the repository root.
    """
    root = Path(package_root).resolve()
    parts = _valid_parts(module_name)
    if parts is None:
        return None

    roots = [root / "src", root] if (root / "src").is_dir() else [root]
    for source_root in roots:
        module_path = source_root.joinpath(*parts)

        # Python package directory wins over a same-named module file.
        init_path = module_path / "__init__.py"
        if init_path.is_file():
            return init_path

        file_path = module_path.with_suffix(".py")
        if file_path.is_file():
            return file_path

        # PEP 420 namespace package: directory without __init__.py.
        if module_path.is_dir() and any(module_path.rglob("*.py")):
            return module_path

    return None
