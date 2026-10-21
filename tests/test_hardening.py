import codecs
import tempfile
from pathlib import Path

from tinyguard.graph_engine import GraphBuildError, build_dependency_graph, find_forbidden_path, _resolve_relative_base
from tinyguard.import_resolver import resolve_import
from tinyguard.patch_verifier import verify_project
from tinyguard.rules import discover_python_files
from tinyguard import graph_engine


def write(path: Path, content: str, encoding="utf-8"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def test_nested_forbidden_namespace_package():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "api.py", "import svc\n")
        write(root / "svc.py", "import database.models\n")
        write(root / "database" / "models.py", "class Model: pass\n")
        graph = build_dependency_graph(root)
        path = find_forbidden_path(graph, "api")
        assert path == ["api", "svc", "database"] or path == ["api", "svc", "database.models"], path


def test_src_layout():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "src" / "pkg" / "api.py", "import pkg.service\n")
        write(root / "src" / "pkg" / "service.py", "import database\n")
        graph = build_dependency_graph(root)
        path = find_forbidden_path(graph, "pkg.api")
        assert path and "database" in path, (graph, path)


def test_third_party_symbol_db_is_not_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "api.py", "from flask_sqlalchemy import db\n")
        graph = build_dependency_graph(root)
        assert find_forbidden_path(graph, "api") is None, graph


def test_unrelated_nested_external_db_is_not_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "api.py", "import some.lib.db\n")
        graph = build_dependency_graph(root)
        assert find_forbidden_path(graph, "api") is None, graph


def test_constant_dynamic_import_is_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "api.py", 'import importlib\nimportlib.import_module("database")\n')
        graph = build_dependency_graph(root)
        assert find_forbidden_path(graph, "api") is not None, graph


def test_parse_failure_fails_closed():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "api.py", "import svc\n")
        write(root / "svc.py", "def broken(:\n")
        try:
            build_dependency_graph(root)
        except GraphBuildError as exc:
            assert any("svc.py" in issue for issue in exc.issues)
        else:
            raise AssertionError("Expected GraphBuildError")


def test_utf8_bom_is_supported():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "api.py").write_bytes(codecs.BOM_UTF8 + b"import database\n")
        graph = build_dependency_graph(root)
        assert find_forbidden_path(graph, "api") is not None


def test_ancestor_directory_named_venv_does_not_hide_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "venv" / "myproject"
        write(root / "api.py", "import database\n")
        discovered = discover_python_files(root)
        assert [path.relative_to(root.resolve()) for path in discovered] == [Path("api.py")]


def test_no_entrypoint_is_not_success():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "main.py", "print('hello')\n")
        passed, issues = verify_project(root)
        assert not passed
        assert any("No API entry points" in issue for issue in issues)


def test_api_under_tests_is_not_entrypoint():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "tests" / "api.py", "import database\n")
        write(root / "api.py", "print('safe')\n")
        passed, issues = verify_project(root)
        assert passed, issues



def test_relative_import_cannot_escape_top_level():
    assert _resolve_relative_base("pkg.a", False, 2, None) is None
    assert _resolve_relative_base("pkg.sub.a", False, 2, None) == "pkg"


def test_package_wins_over_same_named_module():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write(root / "api.py", "import pkg\n")
        write(root / "pkg.py", "import database\n")
        write(root / "pkg" / "__init__.py", "VALUE = 1\n")
        resolved = resolve_import(root, "pkg")
        assert resolved.resolve() == (root / "pkg" / "__init__.py").resolve(), resolved
        graph = build_dependency_graph(root)
        assert find_forbidden_path(graph, "api") is None, graph


def test_declared_source_encoding_is_supported():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = b"# coding: cp1252\n# caf\\xe9\nimport database\n"
        (root / "api.py").write_bytes(data)
        graph = build_dependency_graph(root)
        assert find_forbidden_path(graph, "api") is not None


if __name__ == "__main__":
    tests = [
        test_nested_forbidden_namespace_package,
        test_src_layout,
        test_third_party_symbol_db_is_not_flagged,
        test_unrelated_nested_external_db_is_not_flagged,
        test_constant_dynamic_import_is_flagged,
        test_parse_failure_fails_closed,
        test_utf8_bom_is_supported,
        test_ancestor_directory_named_venv_does_not_hide_files,
        test_no_entrypoint_is_not_success,
        test_api_under_tests_is_not_entrypoint,
        test_relative_import_cannot_escape_top_level,
        test_package_wins_over_same_named_module,
        test_declared_source_encoding_is_supported,
    ]
    for test_fn in tests:
        test_fn()
        print("PASS:", test_fn.__name__)
    print("\nAll hardening tests passed.")
