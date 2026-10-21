
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CLI = PROJECT_ROOT / "tinyguard.py"


def create_test_project(root: Path, forbidden_dependency: bool) -> None:
    """Create a small Python project for an isolated CLI test."""
    (root / "logic").mkdir()

    (root / "api.py").write_text(
        "import logic.orders\n",
        encoding="utf-8",
    )
    (root / "logic" / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )

    orders_code = "import database\n" if forbidden_dependency else (
        "def get_orders():\n"
        "    return []\n"
    )

    (root / "logic" / "orders.py").write_text(
        orders_code,
        encoding="utf-8",
    )
    (root / "database.py").write_text(
        "",
        encoding="utf-8",
    )


def run_tinyguard(app_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), str(app_root)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )


def test_transitive_violation() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        app_root = Path(temp_dir)
        create_test_project(app_root, forbidden_dependency=True)

        result = run_tinyguard(app_root)

        assert result.returncode == 1, (
            f"Expected exit code 1, got {result.returncode}\n"
            f"Output:\n{result.stdout}\n{result.stderr}"
        )
        assert "api -> logic.orders -> database" in result.stdout, (
            f"Expected dependency chain was not reported.\n"
            f"Output:\n{result.stdout}"
        )

        print("PASS: Transitive architectural violation detected.")


def test_safe_project() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        app_root = Path(temp_dir)
        create_test_project(app_root, forbidden_dependency=False)

        result = run_tinyguard(app_root)

        assert result.returncode == 0, (
            f"Expected exit code 0, got {result.returncode}\n"
            f"Output:\n{result.stdout}\n{result.stderr}"
        )

        print("PASS: Safe project accepted.")


if __name__ == "__main__":
    test_transitive_violation()
    test_safe_project()
    print("\nAll CLI tests passed.")
