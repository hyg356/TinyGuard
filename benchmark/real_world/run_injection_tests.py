
import csv
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "benchmark/real_world/repos/full-stack-fastapi"
WORK = ROOT / "benchmark/real_world/injection_work"
RESULTS = ROOT / "benchmark/real_world/results"

API_FILE = Path("backend/app/api/routes/utils.py")

CASES = [
    {
        "id": "RW-DIRECT-01",
        "type": "direct",
        "description": "API route directly imports app.core.db",
        "files": {
            API_FILE: (
                "\n\n# TinyGuard benchmark injection: direct forbidden dependency\n"
                "from app.core import db as benchmark_db\n"
            )
        },
        "expected": "VIOLATION",
    },
    {
        "id": "RW-TRANSITIVE-01",
        "type": "transitive",
        "description": "API route imports helper that imports app.core.db",
        "files": {
            API_FILE: (
                "\n\n# TinyGuard benchmark injection: transitive dependency\n"
                "from app import benchmark_helper\n"
            ),
            Path("backend/app/benchmark_helper.py"): (
                '"""Temporary benchmark helper."""\n'
                "from app.core import db as benchmark_db\n"
            ),
        },
        "expected": "VIOLATION",
    },
]


def run_case(case):
    case_dir = WORK / case["id"]

    if case_dir.exists():
        shutil.rmtree(case_dir)

    shutil.copytree(
        SOURCE,
        case_dir,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            ".venv",
            ".agents",
            ".claude",
            "node_modules",
        ),
        symlinks=True,
    )

    # Apply each controlled injection.
    for relative_path, addition in case["files"].items():
        target = case_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            original = target.read_text(encoding="utf-8")
            target.write_text(original + addition, encoding="utf-8")
        else:
            target.write_text(addition, encoding="utf-8")

    start = time.perf_counter()

    result = subprocess.run(
        [sys.executable, str(ROOT / "tinyguard.py"), str(case_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )

    elapsed = round(time.perf_counter() - start, 3)
    output = result.stdout + "\n" + result.stderr

    # TinyGuard may return exit code 2 when multiple violations exist.
    # The actual detection result is determined from its diagnostic output.
    if "VIOLATION:" in output and "TinyGuard failed:" in output:
        actual = "VIOLATION"
    elif result.returncode == 0 and "TinyGuard passed" in output:
        actual = "CLEAN"
    else:
        actual = "ERROR"

    return {
        "case_id": case["id"],
        "type": case["type"],
        "description": case["description"],
        "expected": case["expected"],
        "actual": actual,
        "passed": actual == case["expected"],
        "runtime_seconds": elapsed,
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Source repository not found: {SOURCE}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("TINYGUARD REAL-WORLD INJECTION TESTS")
    print("=" * 65)
    print("Original repository will not be modified.")
    print()

    results = []

    for case in CASES:
        print(f"Running {case['id']} ({case['type']})...")

        try:
            outcome = run_case(case)
        except Exception as exc:
            outcome = {
                "case_id": case["id"],
                "type": case["type"],
                "description": case["description"],
                "expected": case["expected"],
                "actual": "ERROR",
                "passed": False,
                "runtime_seconds": None,
                "exit_code": None,
                "stdout": "",
                "stderr": repr(exc),
            }

        results.append(outcome)

        print("Expected:", outcome["expected"])
        print("Actual:  ", outcome["actual"])
        print("Result:  ", "PASS" if outcome["passed"] else "FAIL")
        print("Runtime: ", outcome["runtime_seconds"], "seconds")

        if outcome["stdout"]:
            print("Output:")
            print(outcome["stdout"])

        if outcome["stderr"]:
            print("Stderr:")
            print(outcome["stderr"])

        print()

    csv_path = RESULTS / "injection_results.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "case_id",
            "type",
            "description",
            "expected",
            "actual",
            "passed",
            "runtime_seconds",
            "exit_code",
            "stdout",
            "stderr",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    summary = {
        "benchmark": "TinyGuard real-world controlled injection tests",
        "source_repository": "fastapi/full-stack-fastapi-template",
        "injection_cases": len(results),
        "passed": sum(r["passed"] for r in results),
        "failed": sum(not r["passed"] for r in results),
        "results": results,
        "limitations": [
            "One repository was tested.",
            "The injected dependencies are controlled modifications.",
            "This measures detection of the specified forbidden import policy, not general architectural correctness.",
        ],
    }

    json_path = RESULTS / "injection_metrics.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("=" * 65)
    print("INJECTION TEST SUMMARY")
    print("=" * 65)
    print("Passed:", summary["passed"], "/", summary["injection_cases"])
    print("Failed:", summary["failed"])
    print()
    print("Saved:")
    print(csv_path)
    print(json_path)


if __name__ == "__main__":
    main()
