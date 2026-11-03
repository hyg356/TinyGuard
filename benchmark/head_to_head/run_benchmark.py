import csv
import importlib.metadata
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TINYGUARD = ROOT / "tinyguard.py"
OUT = ROOT / "benchmark" / "head_to_head" / "results"
OUT.mkdir(parents=True, exist_ok=True)

# Each case is explicitly authored. "violation" means app.api can
# reach app.database through the project's import graph.
CASES = [
    # ---------------- CORE: expected violations ----------------
    {
        "id": "P01_direct_absolute",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "import app.database\n",
    },
    {
        "id": "P02_direct_from",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "from app import database\n",
    },
    {
        "id": "P03_transitive_one_hop",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "import app.service\n",
        "files": {"app/service.py": "import app.database\n"},
    },
    {
        "id": "P04_transitive_two_hops",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "import app.service\n",
        "files": {
            "app/service.py": "import app.logic\n",
            "app/logic.py": "import app.database\n",
        },
    },
    {
        "id": "P05_relative_direct",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "from . import database\n",
    },
    {
        "id": "P06_relative_transitive",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "from . import service\n",
        "files": {"app/service.py": "from . import database\n"},
    },
    {
        "id": "P07_package_reexport",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "from app.service import fetch\n",
        "files": {
            "app/service/__init__.py": "from .repository import fetch\n",
            "app/service/repository.py": (
                "from app.database import fetch\n"
            ),
        },
    },
    {
        "id": "P08_aliased_import",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "import app.database as storage\n",
    },
    {
        "id": "P09_function_local_import",
        "expected": "VIOLATION",
        "scope": "core",
        "api": (
            "def get_data():\n"
            "    import app.database\n"
            "    return app.database\n"
        ),
    },
    {
        "id": "P10_conditional_import",
        "expected": "VIOLATION",
        "scope": "core",
        "api": (
            "if True:\n"
            "    import app.database\n"
        ),
    },
    {
        "id": "P11_wildcard_import",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "from app.database import *\n",
    },
    {
        "id": "P12_nested_database_package",
        "expected": "VIOLATION",
        "scope": "core",
        "api": "import app.database.models\n",
        "files": {
            "app/database/__init__.py": "",
            "app/database/models.py": "class Model: pass\n",
        },
    },

    # ---------------- CORE: expected clean ----------------
    {
        "id": "N01_safe_service_chain",
        "expected": "CLEAN",
        "scope": "core",
        "api": "import app.service\n",
        "files": {
            "app/service.py": "import app.models\n",
        },
    },
    {
        "id": "N02_third_party_db_symbol",
        "expected": "CLEAN",
        "scope": "core",
        "api": "from flask_sqlalchemy import db\n",
    },
    {
        "id": "N03_nested_external_db",
        "expected": "CLEAN",
        "scope": "core",
        "api": "import some.lib.db\n",
    },
    {
        "id": "N04_database_unreachable",
        "expected": "CLEAN",
        "scope": "core",
        "api": "import app.models\n",
    },
    {
        "id": "N05_similarly_named_module",
        "expected": "CLEAN",
        "scope": "core",
        "api": "import app.database_utils\n",
        "files": {"app/database_utils.py": "VALUE = 1\n"},
    },
    {
        "id": "N06_comment_and_string_only",
        "expected": "CLEAN",
        "scope": "core",
        "api": (
            "# import app.database\n"
            "MESSAGE = 'app.database is not imported'\n"
        ),
    },
    {
        "id": "N07_external_db_through_service",
        "expected": "CLEAN",
        "scope": "core",
        "api": "import app.service\n",
        "files": {
            "app/service.py": "import some.lib.db\n",
        },
    },
    {
        "id": "N08_db_client_name",
        "expected": "CLEAN",
        "scope": "core",
        "api": "import app.db_client\n",
        "files": {"app/db_client.py": "class Client: pass\n"},
    },
    {
        "id": "N09_database_symbol_from_models",
        "expected": "CLEAN",
        "scope": "core",
        "api": "from app.models import Database\n",
        "files": {"app/models.py": "class Database: pass\n"},
    },
    {
        "id": "N10_type_checking_safe_import",
        "expected": "CLEAN",
        "scope": "core",
        "api": (
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from app.models import User\n"
        ),
        "files": {"app/models.py": "class User: pass\n"},
    },
    {
        "id": "N11_database_tools_name",
        "expected": "CLEAN",
        "scope": "core",
        "api": "import app.database_tools\n",
        "files": {"app/database_tools.py": "VALUE = 1\n"},
    },
    {
        "id": "N12_database_module_not_reached",
        "expected": "CLEAN",
        "scope": "core",
        "api": "import app.service\n",
        "files": {
            "app/service.py": "VALUE = 1\n",
        },
    },

    # -------- TinyGuard-only extension track: dynamic imports --------
    {
        "id": "X01_importlib_constant",
        "expected": "VIOLATION",
        "scope": "tinyguard_extension",
        "api": (
            "import importlib\n"
            "importlib.import_module('app.database')\n"
        ),
    },
    {
        "id": "X02_dunder_import_constant",
        "expected": "VIOLATION",
        "scope": "tinyguard_extension",
        "api": "__import__('app.database')\n",
    },
]


CONFIG = """[importlinter]
root_package = app

[importlinter:contract:api-no-database]
name = API must not depend on database
type = forbidden
source_modules =
    app.api
forbidden_modules =
    app.database
"""


def classify_tinyguard(result):
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode == 0:
        return "CLEAN"
    if result.returncode == 1 and "VIOLATION:" in output:
        return "VIOLATION"
    return "ERROR"


def classify_import_linter(result):
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    upper = output.upper()

    if "BROKEN" in upper:
        return "VIOLATION"
    if "KEPT" in upper and result.returncode == 0:
        return "CLEAN"
    return "ERROR"


def run_tool(command, cwd, classifier, timeout=60):
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.perf_counter() - started
        return classifier(result), elapsed, result.returncode, (
            (result.stdout or "") + "\n" + (result.stderr or "")
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - started
        return "ERROR", elapsed, "TIMEOUT", str(exc)
    except Exception as exc:
        elapsed = time.perf_counter() - started
        return "ERROR", elapsed, "EXCEPTION", repr(exc)


def create_fixture(case, root):
    app = root / "app"
    app.mkdir(parents=True)

    (app / "__init__.py").write_text("", encoding="utf-8")
    (app / "api.py").write_text(case["api"], encoding="utf-8")

    extra_files = case.get("files", {})
    has_database_package = "app/database/__init__.py" in extra_files

    if not has_database_package:
        (app / "database.py").write_text(
            "def fetch():\n    return None\n",
            encoding="utf-8",
        )

    if "app/models.py" not in extra_files:
        (app / "models.py").write_text("VALUE = 1\n", encoding="utf-8")

    for relative_name, contents in extra_files.items():
        destination = root / relative_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents, encoding="utf-8")

    (root / ".importlinter").write_text(CONFIG, encoding="utf-8")


def metrics(rows, tool, scope):
    selected = [
        row for row in rows
        if row["scope"] == scope and row[tool] != "NOT_RUN"
    ]

    tp = fp = tn = fn = errors = 0

    for row in selected:
        expected = row["expected"]
        actual = row[tool]

        if actual == "ERROR":
            errors += 1
        elif expected == "VIOLATION" and actual == "VIOLATION":
            tp += 1
        elif expected == "CLEAN" and actual == "VIOLATION":
            fp += 1
        elif expected == "CLEAN" and actual == "CLEAN":
            tn += 1
        elif expected == "VIOLATION" and actual == "CLEAN":
            fn += 1

    valid = tp + fp + tn + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    accuracy = (tp + tn) / valid if valid else 0.0

    return {
        "tool": tool,
        "scope": scope,
        "cases": len(selected),
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "ERROR": errors,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "F1": round(f1, 4),
        "accuracy_on_valid_predictions": round(accuracy, 4),
    }


def main():
    if not TINYGUARD.exists():
        raise SystemExit(f"Cannot find TinyGuard CLI: {TINYGUARD}")

    if not shutil.which("lint-imports"):
        raise SystemExit(
            "Cannot find lint-imports. Install it with:\n"
            "python3 -m pip install import-linter"
        )

    try:
        il_version = importlib.metadata.version("import-linter")
    except importlib.metadata.PackageNotFoundError:
        il_version = "unknown"

    print("TinyGuard vs Import Linter")
    print("==========================")
    print(f"Project: {ROOT}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"OS: {platform.platform()}")
    print(f"Import Linter: {il_version}")
    print(f"Cases: {len(CASES)}")
    print()

    rows = []

    for index, case in enumerate(CASES, start=1):
        with tempfile.TemporaryDirectory(
            prefix=f"tg_bench_{case['id']}_"
        ) as temp:
            fixture = Path(temp)
            create_fixture(case, fixture)

            tg, tg_time, tg_rc, tg_output = run_tool(
                [sys.executable, str(TINYGUARD), str(fixture)],
                ROOT,
                classify_tinyguard,
            )

            if case["scope"] == "core":
                il, il_time, il_rc, il_output = run_tool(
                    [
                        "lint-imports",
                        "--config",
                        ".importlinter",
                        "--no-cache",
                    ],
                    fixture,
                    classify_import_linter,
                )
            else:
                il = "NOT_RUN"
                il_time = ""
                il_rc = ""
                il_output = "Extension case: not part of parity comparison."

            row = {
                "case": case["id"],
                "scope": case["scope"],
                "expected": case["expected"],
                "tinyguard": tg,
                "tinyguard_seconds": round(tg_time, 6),
                "tinyguard_exit": tg_rc,
                "import_linter": il,
                "import_linter_seconds": (
                    round(il_time, 6) if il_time != "" else ""
                ),
                "import_linter_exit": il_rc,
            }
            rows.append(row)

            tg_status = "OK" if tg == case["expected"] else tg
            il_status = (
                "N/A" if il == "NOT_RUN"
                else ("OK" if il == case["expected"] else il)
            )

            print(
                f"[{index:02d}/{len(CASES)}] {case['id']:<34} "
                f"expected={case['expected']:<9} "
                f"TinyGuard={tg_status:<9} "
                f"ImportLinter={il_status}"
            )

            # Save detailed outputs for diagnosing errors or disagreements.
            if tg == "ERROR" or il == "ERROR":
                (OUT / f"{case['id']}_diagnostics.txt").write_text(
                    "=== TinyGuard ===\n"
                    + tg_output
                    + "\n=== Import Linter ===\n"
                    + il_output,
                    encoding="utf-8",
                )

    csv_path = OUT / "case_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summaries = [
        metrics(rows, "tinyguard", "core"),
        metrics(rows, "import_linter", "core"),
        metrics(rows, "tinyguard", "tinyguard_extension"),
    ]

    summary_path = OUT / "metrics.json"
    summary_path.write_text(
        json.dumps(
            {
                "method": "hand-authored controlled conformance corpus",
                "policy": (
                    "app.api must not depend directly or transitively "
                    "on app.database"
                ),
                "python": sys.version,
                "platform": platform.platform(),
                "import_linter_version": il_version,
                "case_count": len(CASES),
                "summaries": summaries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    report = [
        "# TinyGuard head-to-head benchmark",
        "",
        "## Policy",
        "",
        "`app.api` must not depend directly or transitively on `app.database`.",
        "",
        "## Method",
        "",
        "- Hand-authored fixture projects; each case has an explicit expected label.",
        "- Core comparison uses ordinary Python imports supported by both tools.",
        "- Dynamic-import cases are reported separately as TinyGuard extensions.",
        "- Tool errors are counted separately and excluded from the valid-prediction accuracy denominator.",
        "- Runtime is measured per fixture; this is not a large-repository performance test.",
        "",
        "## Results",
        "",
        "| Tool | Scope | Cases | TP | FP | TN | FN | Errors | Precision | Recall | F1 | Accuracy |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for item in summaries:
        report.append(
            f"| {item['tool']} | {item['scope']} | {item['cases']} "
            f"| {item['TP']} | {item['FP']} | {item['TN']} | {item['FN']} "
            f"| {item['ERROR']} | {item['precision']:.3f} "
            f"| {item['recall']:.3f} | {item['F1']:.3f} "
            f"| {item['accuracy_on_valid_predictions']:.3f} |"
        )

    report.extend([
        "",
        "## Interpretation limits",
        "",
        "This is a controlled conformance benchmark, not a representative sample "
        "of all Python repositories. It tests a specific architectural policy "
        "and a curated set of import patterns. It does not establish general "
        "real-world accuracy, security, or performance at scale.",
        "",
        "Import Linter and TinyGuard may differ in import-resolution semantics. "
        "Review individual disagreements and diagnostic files before drawing "
        "conclusions.",
        "",
        "## Reproduction",
        "",
        "Run `python3 benchmark/head_to_head/run_benchmark.py` from the repository root.",
        "",
    ])

    report_path = OUT / "report.md"
    report_path.write_text("\n".join(report), encoding="utf-8")

    print("\n================ SUMMARY ================")
    for item in summaries:
        print(json.dumps(item, indent=2))

    print("\nSaved:")
    print(csv_path)
    print(summary_path)
    print(report_path)


if __name__ == "__main__":
    main()
