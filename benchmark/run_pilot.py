from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "benchmark" / "fixtures"

# expected=True means a forbidden dependency should be detected.
CASES = {
    "01_direct_violation": (
        True,
        {
            "api.py": "import database\n\ndef get_data():\n    return database.fetch_data()\n",
            "database.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
    "02_direct_safe": (
        False,
        {
            "api.py": "import services\n\ndef get_data():\n    return services.fetch_data()\n",
            "services.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
    "03_transitive_violation": (
        True,
        {
            "api.py": "import logic\n\ndef get_data():\n    return logic.get_data()\n",
            "logic.py": "import database\n\ndef get_data():\n    return database.fetch_data()\n",
            "database.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
    "04_transitive_safe": (
        False,
        {
            "api.py": "import logic\n\ndef get_data():\n    return logic.get_data()\n",
            "logic.py": "import services\n\ndef get_data():\n    return services.fetch_data()\n",
            "services.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
    "05_relative_violation": (
        True,
        {
            "app/__init__.py": "",
            "app/api/__init__.py": "",
            "app/api/routes.py": "from .. import database\n\ndef get_data():\n    return database.fetch_data()\n",
            "app/database.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
    "06_relative_safe": (
        False,
        {
            "app/__init__.py": "",
            "app/api/__init__.py": "",
            "app/api/routes.py": "from .. import services\n\ndef get_data():\n    return services.fetch_data()\n",
            "app/services.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
    "07_package_reexport_violation": (
        True,
        {
            "api.py": "import storage\n\ndef get_data():\n    return storage.fetch_data()\n",
            "storage/__init__.py": "from .database import fetch_data\n",
            "storage/database.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
    "08_package_reexport_safe": (
        False,
        {
            "api.py": "import storage\n\ndef get_data():\n    return storage.fetch_data()\n",
            "storage/__init__.py": "from .memory import fetch_data\n",
            "storage/memory.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
    "09_src_layout_violation": (
        True,
        {
            "src/api.py": "import database\n\ndef get_data():\n    return database.fetch_data()\n",
            "src/database.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
    "10_src_layout_safe": (
        False,
        {
            "src/api.py": "import services\n\ndef get_data():\n    return services.fetch_data()\n",
            "src/services.py": "def fetch_data():\n    return ['data']\n",
        },
    ),
}


def create_fixtures():
    for name, (_, files) in CASES.items():
        project = FIXTURES / name

        if project.exists():
            import shutil
            shutil.rmtree(project)

        for relative_path, contents in files.items():
            target = project / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding="utf-8")


def run_benchmark():
    tp = fp = tn = fn = errors = 0

    print("\nTinyGuard detection benchmark — pilot")
    print("=" * 55)

    for name, (expected_violation, _) in CASES.items():
        project = FIXTURES / name

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tinyguard.py"),
                str(project),
            ],
            capture_output=True,
            text=True,
        )

        # Exit code 1 = violation, 0 = clean, 2 = analysis error.
        if result.returncode == 2:
            errors += 1
            actual = "ERROR"
        elif result.returncode == 1:
            actual = "VIOLATION"
        elif result.returncode == 0:
            actual = "CLEAN"
        else:
            errors += 1
            actual = f"UNEXPECTED EXIT {result.returncode}"

        if actual == "ERROR" or actual.startswith("UNEXPECTED"):
            status = "ERROR"
        elif expected_violation and actual == "VIOLATION":
            tp += 1
            status = "PASS"
        elif expected_violation and actual == "CLEAN":
            fn += 1
            status = "FAIL"
        elif not expected_violation and actual == "VIOLATION":
            fp += 1
            status = "FAIL"
        else:
            tn += 1
            status = "PASS"

        print(f"{name:32} expected={'VIOLATION' if expected_violation else 'CLEAN':10} actual={actual:10} {status}")

        if result.stdout.strip():
            print("  " + result.stdout.strip().replace("\n", "\n  "))
        if result.stderr.strip():
            print("  STDERR: " + result.stderr.strip().replace("\n", "\n  "))

    print("\nResults")
    print("-" * 55)
    print(f"True positives:  {tp}")
    print(f"False positives: {fp}")
    print(f"True negatives:  {tn}")
    print(f"False negatives: {fn}")
    print(f"Analysis errors: {errors}")

    if errors:
        print("\nMetrics withheld: resolve analysis errors before interpreting results.")
        return

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    print(f"\nPrecision: {precision:.1%}")
    print(f"Recall:    {recall:.1%}")
    print(f"F1 score:  {f1:.1%}")
    print(f"Correct:   {tp + tn}/{len(CASES)}")


if __name__ == "__main__":
    create_fixtures()
    run_benchmark()
