"""Small self-contained graph-builder smoke test."""

import sys
import tempfile
from pathlib import Path

# Permit both ``python tinyguard/test_graph_builder.py`` and ``python -m ...``.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tinyguard.graph_engine import build_dependency_graph


with tempfile.TemporaryDirectory(prefix="tinyguard_graph_demo_") as temp_dir:
    root = Path(temp_dir)
    (root / "api.py").write_text("import logic.service\n", encoding="utf-8")
    (root / "logic").mkdir()
    (root / "logic" / "__init__.py").write_text("", encoding="utf-8")
    (root / "logic" / "service.py").write_text(
        "def run():\n    return True\n", encoding="utf-8"
    )

    graph = build_dependency_graph(root)

    print("Dependency graph:")
    for module, dependencies in sorted(graph.items()):
        print(f"{module} -> {dependencies}")

    assert "api" in graph, "FAIL: API module was not discovered."
    assert "logic.service" in graph["api"], "FAIL: Import edge was not discovered."
    print("\nPASS: Graph builder discovered modules and dependency edges.")
