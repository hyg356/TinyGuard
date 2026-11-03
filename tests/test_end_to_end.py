
import tempfile
from pathlib import Path

from tinyguard.remediation import propose_and_verify


def main():
    with tempfile.TemporaryDirectory(prefix="tinyguard_demo_") as temp_dir:
        root = Path(temp_dir)

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
            "import database\n\n"
            "def get_orders():\n"
            "    return database.get_orders()\n",
            encoding="utf-8",
        )
        (root / "database.py").write_text(
            "def get_orders():\n"
            "    return []\n",
            encoding="utf-8",
        )

        source_code = {
            "api.py": (root / "api.py").read_text(encoding="utf-8"),
            "logic/orders.py": (
                root / "logic" / "orders.py"
            ).read_text(encoding="utf-8"),
            "database.py": (root / "database.py").read_text(
                encoding="utf-8"
            ),
        }

        result = propose_and_verify(
            violation="api -> logic.orders -> database",
            source_code=source_code,
            project_root=root,
        )

        proposal = result["proposal"]

        print("\nModel explanation:")
        print(proposal["explanation"])
        print("\nFiles proposed:")
        print(proposal["files_to_change"])
        print("\nVerification result:", result["verified"])

        for issue in result["verification_issues"]:
            print("-", issue)

        if result["verified"]:
            print("\nPASS: Proposed repair passed verification.")
        else:
            print(
                "\nREPAIR REJECTED: The proposal did not pass verification."
            )

        original = (root / "logic" / "orders.py").read_text(
            encoding="utf-8"
        )
        assert "import database" in original
        print("PASS: Original project files remained unchanged.")


if __name__ == "__main__":
    main()
