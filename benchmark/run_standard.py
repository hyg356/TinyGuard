from pathlib import Path
import csv
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "benchmark" / "standard_fixtures"
RESULTS = ROOT / "benchmark" / "results"

CASES = []


def add(category, name, expected, files):
    CASES.append({
        "category": category,
        "name": name,
        "expected": expected,
        "files": files,
    })


def api_file(import_statement, function_body):
    return (
        import_statement
        + "\n\ndef get_data():\n"
        + "    " + function_body + "\n"
    )


# --------------------------------------------------
# CATEGORY 1: DIRECT IMPORTS
# --------------------------------------------------

direct_imports = [
    ("import database", "return database.fetch_data()"),
    ("import database as db", "return db.fetch_data()"),
    ("from database import fetch_data", "return fetch_data()"),
    ("from database import fetch_data as load", "return load()"),
    ("import database\nimport services", "return database.fetch_data()"),
    ("import database as storage", "return storage.fetch_data()"),
    ("from database import fetch_data, save_data", "return fetch_data()"),
    ("import database  # persistence dependency", "return database.fetch_data()"),
    ("from database import fetch_data as get", "return get()"),
    ("import database\nimport math", "return database.fetch_data()"),
]

safe_imports = [
    ("import services", "return services.fetch_data()"),
    ("import services as svc", "return svc.fetch_data()"),
    ("from services import fetch_data", "return fetch_data()"),
    ("from services import fetch_data as load", "return load()"),
    ("import services\nimport math", "return services.fetch_data()"),
    ("import services as storage", "return storage.fetch_data()"),
    ("from services import fetch_data, save_data", "return fetch_data()"),
    ("import services  # allowed dependency", "return services.fetch_data()"),
    ("from services import fetch_data as get", "return get()"),
    ("import services\nimport json", "return services.fetch_data()"),
]

for i in range(10):
    add(
        "direct_imports",
        f"direct_violation_{i+1:02}",
        True,
        {
            "api.py": api_file(*direct_imports[i]),
            "database.py": "def fetch_data():\n    return ['data']\n",
            "services.py": "def fetch_data():\n    return ['data']\n",
        },
    )

    add(
        "direct_imports",
        f"direct_safe_{i+1:02}",
        False,
        {
            "api.py": api_file(*safe_imports[i]),
            "services.py": "def fetch_data():\n    return ['data']\n",
        },
    )


# --------------------------------------------------
# CATEGORY 2: TRANSITIVE DEPENDENCIES
# --------------------------------------------------

for i in range(10):
    depth = 2 + (i % 4)

    for expected, suffix in [(True, "violation"), (False, "safe")]:
        files = {
            "api.py": (
                "import layer_0\n\n"
                "def get_data():\n"
                "    return layer_0.get_data()\n"
            )
        }

        for j in range(depth):
            next_module = (
                f"layer_{j+1}" if j < depth - 1
                else ("database" if expected else "services")
            )

            files[f"layer_{j}.py"] = (
                f"import {next_module}\n\n"
                "def get_data():\n"
                "    return "
                f"{next_module}.fetch_data()"
                if j == depth - 1
                else (
                    f"import {next_module}\n\n"
                    "def get_data():\n"
                    f"    return {next_module}.get_data()\n"
                )
            )

        final_module = "database" if expected else "services"
        files[f"{final_module}.py"] = (
            "def fetch_data():\n    return ['data']\n"
        )

        add(
            "transitive",
            f"transitive_{suffix}_{i+1:02}",
            expected,
            files,
        )


# --------------------------------------------------
# CATEGORY 3: RELATIVE IMPORTS
# --------------------------------------------------

for i in range(10):
    for expected, suffix in [(True, "violation"), (False, "safe")]:
        target = "database" if expected else "services"

        if i % 3 == 0:
            statement = f"from .. import {target}"
            body = f"return {target}.fetch_data()"
        elif i % 3 == 1:
            statement = f"from ..{target} import fetch_data"
            body = "return fetch_data()"
        else:
            statement = f"from .. import {target} as backend"
            body = "return backend.fetch_data()"

        files = {
            "app/__init__.py": "",
            "app/api/__init__.py": "",
            "app/api/routes.py": api_file(statement, body),
            f"app/{target}.py": (
                "def fetch_data():\n    return ['data']\n"
            ),
        }

        add(
            "relative_imports",
            f"relative_{suffix}_{i+1:02}",
            expected,
            files,
        )


# --------------------------------------------------
# CATEGORY 4: PACKAGE RE-EXPORTS
# --------------------------------------------------

packages = [
    "storage", "persistence", "repository", "backend", "records",
    "store", "data_layer", "access", "models", "db_layer",
]

for i, package in enumerate(packages):
    for expected, suffix in [(True, "violation"), (False, "safe")]:
        target = "database" if expected else "services"

        files = {
            "api.py": (
                f"import {package}\n\n"
                "def get_data():\n"
                f"    return {package}.fetch_data()\n"
            ),
            f"{package}/__init__.py": (
                f"from .{target} import fetch_data\n"
            ),
            f"{package}/{target}.py": (
                "def fetch_data():\n    return ['data']\n"
            ),
        }

        add(
            "package_reexports",
            f"reexport_{suffix}_{i+1:02}",
            expected,
            files,
        )


# --------------------------------------------------
# CATEGORY 5: SRC PROJECT LAYOUTS
# --------------------------------------------------

for i in range(10):
    for expected, suffix in [(True, "violation"), (False, "safe")]:
        target = "database" if expected else "services"

        if i % 3 == 0:
            statement = f"import {target}"
            body = f"return {target}.fetch_data()"
        elif i % 3 == 1:
            statement = f"from {target} import fetch_data"
            body = "return fetch_data()"
        else:
            statement = f"import {target} as backend"
            body = "return backend.fetch_data()"

        files = {
            "src/api.py": api_file(statement, body),
            f"src/{target}.py": (
                "def fetch_data():\n    return ['data']\n"
            ),
        }

        add(
            "src_layout",
            f"src_{suffix}_{i+1:02}",
            expected,
            files,
        )


# --------------------------------------------------
# FIXTURE GENERATION
# --------------------------------------------------

def create_fixtures():
    if FIXTURES.exists():
        shutil.rmtree(FIXTURES)

    FIXTURES.mkdir(parents=True)

    for case in CASES:
        project = FIXTURES / case["name"]

        for relative, contents in case["files"].items():
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding="utf-8")

    print(f"Generated {len(CASES)} fixtures.")


# --------------------------------------------------
# RUN AND EVALUATE
# --------------------------------------------------

def run_case(case):
    project = FIXTURES / case["name"]

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tinyguard.py"),
            str(project),
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )

    output = result.stdout + "\n" + result.stderr

    if result.returncode == 2:
        return "ERROR", result.returncode, output

    if result.returncode == 1 and "VIOLATION:" in output:
        return "VIOLATION", result.returncode, output

    if result.returncode == 0:
        return "CLEAN", result.returncode, output

    return "ERROR", result.returncode, output


def calculate_metrics(rows):
    tp = sum(
        r["expected"] == "VIOLATION" and r["actual"] == "VIOLATION"
        for r in rows
    )
    fp = sum(
        r["expected"] == "CLEAN" and r["actual"] == "VIOLATION"
        for r in rows
    )
    tn = sum(
        r["expected"] == "CLEAN" and r["actual"] == "CLEAN"
        for r in rows
    )
    fn = sum(
        r["expected"] == "VIOLATION" and r["actual"] == "CLEAN"
        for r in rows
    )

    errors = sum(r["actual"] == "ERROR" for r in rows)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )
    accuracy = (tp + tn) / (tp + tn + fp + fn) if tp + tn + fp + fn else 0

    return {
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "errors": errors,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)

    rows = []

    print("\nTINYGUARD STANDARD DETECTION BENCHMARK")
    print("=" * 75)

    for case in CASES:
        actual, exit_code, output = run_case(case)
        expected = "VIOLATION" if case["expected"] else "CLEAN"

        status = "PASS" if actual == expected else "FAIL"

        row = {
            "category": case["category"],
            "case": case["name"],
            "expected": expected,
            "actual": actual,
            "status": status,
            "exit_code": exit_code,
        }
        rows.append(row)

        print(
            f"{case['name']:36} "
            f"expected={expected:10} "
            f"actual={actual:10} "
            f"{status}"
        )

        if status == "FAIL":
            print("  Diagnostic output:")
            print("  " + output.strip().replace("\n", "\n  "))

    output_file = RESULTS / "standard_results.csv"

    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("\n" + "=" * 75)
    print("CATEGORY RESULTS")

    categories = sorted(set(r["category"] for r in rows))

    for category in categories:
        subset = [r for r in rows if r["category"] == category]
        metrics = calculate_metrics(subset)

        print(
            f"{category:22} "
            f"correct={metrics['TP'] + metrics['TN']}/"
            f"{len(subset)} "
            f"precision={metrics['precision']:.1%} "
            f"recall={metrics['recall']:.1%} "
            f"F1={metrics['f1']:.1%} "
            f"errors={metrics['errors']}"
        )

    overall = calculate_metrics(rows)

    print("\nOVERALL RESULTS")
    print("-" * 75)
    for key in ["TP", "FP", "TN", "FN", "errors"]:
        print(f"{key:15}: {overall[key]}")

    print(f"Precision       : {overall['precision']:.2%}")
    print(f"Recall          : {overall['recall']:.2%}")
    print(f"F1 score        : {overall['f1']:.2%}")
    print(f"Accuracy        : {overall['accuracy']:.2%}")

    if overall["errors"]:
        print("\nWARNING: Errors occurred. Do not publish aggregate metrics.")
    else:
        print("\nAll cases completed without analysis errors.")

    print(f"\nDetailed CSV: {output_file}")
    print(f"Total cases: {len(rows)}")


if __name__ == "__main__":
    if len(CASES) != 100:
        raise RuntimeError(f"Expected 100 cases, got {len(CASES)}")

    create_fixtures()
    main()
