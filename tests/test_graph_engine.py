
from tinyguard.graph_engine import find_forbidden_path


def test_transitive_violation():
    graph = {
        "api": ["logic.orders"],
        "logic.orders": ["database"],
        "database": [],
    }

    path = find_forbidden_path(
        graph,
        start="api",
        forbidden={"database"},
    )

    assert path == ["api", "logic.orders", "database"]
    print("PASS: Transitive dependency violation detected.")


def test_safe_graph():
    graph = {
        "api": ["logic.orders"],
        "logic.orders": ["models"],
        "models": [],
    }

    path = find_forbidden_path(
        graph,
        start="api",
        forbidden={"database"},
    )

    assert path is None
    print("PASS: Safe dependency graph accepted.")


def test_cycle_terminates():
    graph = {
        "api": ["logic"],
        "logic": ["services"],
        "services": ["logic", "database"],
        "database": [],
    }

    path = find_forbidden_path(
        graph,
        start="api",
        forbidden={"database"},
    )

    assert path == ["api", "logic", "services", "database"]
    print("PASS: Cyclic graph handled without looping.")


if __name__ == "__main__":
    test_transitive_violation()
    test_safe_graph()
    test_cycle_terminates()
    print("\nAll graph-engine tests passed.")
