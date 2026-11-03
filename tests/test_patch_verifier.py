
import tempfile
from pathlib import Path

from tinyguard.patch_verifier import verify_patch


def create_project(root: Path) -> None:
    (root / "logic").mkdir()
    (root / "api.py").write_text(
        "import logic.orders\n",
        encoding="utf-8",
    )
    (root / "logic" / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )
    (root / "logic" / "orders.py").write_text(
        "import database\n",
        encoding="utf-8",
    )
    (root / "database.py").write_text(
        "# database implementation\n",
        encoding="utf-8",
    )


def test_invalid_patch_is_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        create_project(root)

        original = (root / "logic" / "orders.py").read_text(
            encoding="utf-8"
        )

        passed, issues = verify_patch(
            root,
            {
                "logic/orders.py": "def broken(:\n    pass\n",
            },
        )

        assert not passed
        assert any("Invalid Python file" in issue for issue in issues)
        assert (root / "logic" / "orders.py").read_text(
            encoding="utf-8"
        ) == original

        print("PASS: Invalid patch rejected; original file unchanged.")


def test_architectural_violation_is_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        create_project(root)

        passed, issues = verify_patch(
            root,
            {
                "logic/orders.py": "import database\n",
            },
        )

        assert not passed
        assert any("forbidden dependency chain" in issue for issue in issues)
        print("PASS: Remaining architectural violation rejected.")


def test_valid_patch_is_accepted():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        create_project(root)

        passed, issues = verify_patch(
            root,
            {
                "logic/orders.py": (
                    "def get_orders():\n"
                    "    return []\n"
                ),
            },
        )

        assert passed, issues
        print("PASS: Syntactically valid, compliant patch accepted.")


def test_unsafe_path_is_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        create_project(root)

        passed, issues = verify_patch(
            root,
            {
                "../outside.py": "print('unsafe')\n",
            },
        )

        assert not passed
        assert any("Unsafe" in issue for issue in issues)
        print("PASS: Unsafe patch path rejected.")


if __name__ == "__main__":
    test_invalid_patch_is_rejected()
    test_architectural_violation_is_rejected()
    test_valid_patch_is_accepted()
    test_unsafe_path_is_rejected()
    print("\nAll patch-verifier tests passed.")
