import csv
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "benchmark" / "mutation" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

MUTATIONS = [
    {
        "name": "baseline",
        "description": "Unmodified TinyGuard",
    },
    {
        "name": "disable_transitive",
        "description": "Disable transitive dependency traversal",
    },
    {
        "name": "ignore_relative_imports",
        "description": "Ignore relative imports",
    },
    {
        "name": "ignore_package_reexports",
        "description": "Ignore package re-exports",
    },
    {
        "name": "flag_every_db_import",
        "description": "Incorrectly flag unrelated db imports",
    },
    {
        "name": "ignore_syntax_errors",
        "description": "Allow syntax errors to pass silently",
    },
]


def run_command(command, cwd):
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )


def main():
    print("TinyGuard mutation audit")
    print("========================")

    print("\nRunning baseline test suite...")

    baseline = run_command(
        [sys.executable, "-m", "unittest", "discover", "-v"],
        ROOT,
    )

    print(baseline.stdout)
    print(baseline.stderr)

    if baseline.returncode != 0:
        print(
            "\nWARNING: unittest discovery did not pass. "
            "This project may use standalone test scripts or pytest."
        )
        print("We will not report a mutation score from this run.")
        sys.exit(1)

    print("\nBaseline passed.")

    print(
        "\nIMPORTANT: This runner does not yet apply mutations "
        "automatically. It records the baseline and prepares "
        "the mutation audit."
    )

    output = RESULTS / "mutation_results.csv"

    with output.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "mutation",
                "description",
                "status",
            ],
        )
        writer.writeheader()

        writer.writerow({
            "mutation": "baseline",
            "description": "Unmodified TinyGuard",
            "status": "BASELINE_PASS",
        })

        for mutation in MUTATIONS[1:]:
            writer.writerow({
                "mutation": mutation["name"],
                "description": mutation["description"],
                "status": "NOT_YET_TESTED",
            })

    print("\nCreated:", output)
    print("\nNext step: inspect the actual source code and implement")
    print("each mutation against the correct function.")


if __name__ == "__main__":
    main()
