import csv
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "benchmark" / "real_world"
REPOS = BASE / "repos"
RESULTS = BASE / "results"
TINYGUARD = ROOT / "tinyguard.py"

PROJECTS = [
    ("fastapi", "https://github.com/fastapi/fastapi.git"),
    ("starlette", "https://github.com/encode/starlette.git"),
    ("flask", "https://github.com/pallets/flask.git"),
    ("requests", "https://github.com/psf/requests.git"),
    ("sqlmodel", "https://github.com/fastapi/sqlmodel.git"),
    ("sqlalchemy", "https://github.com/sqlalchemy/sqlalchemy.git"),
    ("pydantic", "https://github.com/pydantic/pydantic.git"),
    ("httpx", "https://github.com/encode/httpx.git"),
    ("click", "https://github.com/pallets/click.git"),
    ("redis-py", "https://github.com/redis/redis-py.git"),
]

RESULTS.mkdir(parents=True, exist_ok=True)
REPOS.mkdir(parents=True, exist_ok=True)

def run(command, cwd=None, timeout=180):
    start = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "seconds": round(time.perf_counter() - start, 3),
            "error": "",
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "seconds": round(time.perf_counter() - start, 3),
            "error": f"Timed out after {timeout} seconds",
        }
    except Exception as exc:
        return {
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "seconds": round(time.perf_counter() - start, 3),
            "error": str(exc),
        }

def git_output(repo, *args):
    result = run(["git", *args], cwd=repo, timeout=30)
    if result["returncode"] == 0:
        return result["stdout"].strip()
    return ""

def clone_project(name, url):
    destination = REPOS / name

    if (destination / ".git").exists():
        return destination, "already_present"

    if destination.exists():
        return destination, "directory_exists_without_git"

    result = run(
        ["git", "clone", "--depth", "1", url, str(destination)],
        timeout=600,
    )

    if result["returncode"] == 0:
        return destination, "cloned"

    diagnostic = result["stderr"] or result["error"]
    (RESULTS / f"{name}_clone_error.txt").write_text(
        diagnostic, encoding="utf-8"
    )
    return destination, "clone_failed"

def inspect_project(repo):
    py_files = list(repo.rglob("*.py"))
    ignored = {
        ".git", ".venv", "venv", "__pycache__",
        "site-packages", "node_modules", "build", "dist",
    }

    relevant = [
        p for p in py_files
        if not any(part in ignored for part in p.parts)
    ]

    top_level = sorted({
        p.relative_to(repo).parts[0]
        for p in relevant
        if p.relative_to(repo).parts
    })

    return len(relevant), ", ".join(top_level[:25])

def classify(result):
    if result["error"]:
        return "ERROR"

    output = result["stdout"] + "\n" + result["stderr"]

    if result["returncode"] == 0 and "TinyGuard passed" in output:
        return "CLEAN"

    if result["returncode"] == 1 and "VIOLATION:" in output:
        return "VIOLATION"

    return "UNCLASSIFIED"

def main():
    if not TINYGUARD.exists():
        print("ERROR: tinyguard.py was not found at:", TINYGUARD)
        sys.exit(1)

    print("=" * 65)
    print("TINYGUARD REAL-WORLD REPOSITORY DISCOVERY")
    print("=" * 65)
    print("Project:", ROOT)
    print("Python:", sys.version.split()[0])
    print("Platform:", platform.platform())
    print("Repositories:", len(PROJECTS))
    print()

    rows = []

    for index, (name, url) in enumerate(PROJECTS, 1):
        print(f"[{index}/{len(PROJECTS)}] {name}")

        repo, clone_status = clone_project(name, url)

        row = {
            "repository": name,
            "url": url,
            "clone_status": clone_status,
            "commit": "",
            "python_files": 0,
            "top_level_structure": "",
            "tinyguard_result": "NOT_RUN",
            "runtime_seconds": "",
            "exit_code": "",
            "diagnostic_file": "",
        }

        if clone_status in ("clone_failed", "directory_exists_without_git"):
            print("  Clone status:", clone_status)
            rows.append(row)
            continue

        row["commit"] = git_output(repo, "rev-parse", "HEAD")

        count, structure = inspect_project(repo)
        row["python_files"] = count
        row["top_level_structure"] = structure

        print("  Commit:", row["commit"][:12])
        print("  Python files:", count)

        result = run(
            [sys.executable, str(TINYGUARD), str(repo)],
            cwd=ROOT,
            timeout=180,
        )

        classification = classify(result)
        row["tinyguard_result"] = classification
        row["runtime_seconds"] = result["seconds"]
        row["exit_code"] = (
            "" if result["returncode"] is None
            else result["returncode"]
        )

        diagnostic = (
            f"Repository: {name}\n"
            f"URL: {url}\n"
            f"Commit: {row['commit']}\n"
            f"Classification: {classification}\n"
            f"Exit code: {result['returncode']}\n"
            f"Runtime: {result['seconds']} seconds\n"
            f"Error: {result['error']}\n\n"
            f"STDOUT:\n{result['stdout']}\n\n"
            f"STDERR:\n{result['stderr']}\n"
        )

        if classification in ("ERROR", "UNCLASSIFIED"):
            diagnostic_path = RESULTS / f"{name}_diagnostic.txt"
            diagnostic_path.write_text(diagnostic, encoding="utf-8")
            row["diagnostic_file"] = str(diagnostic_path)

        print("  TinyGuard:", classification)
        print("  Runtime:", result["seconds"], "seconds")
        rows.append(row)

    csv_path = RESULTS / "repository_results.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "benchmark": "TinyGuard Real-World Repository Discovery",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "repositories_attempted": len(PROJECTS),
        "repositories_cloned_or_present": sum(
            r["clone_status"] in ("cloned", "already_present")
            for r in rows
        ),
        "clean": sum(r["tinyguard_result"] == "CLEAN" for r in rows),
        "violations": sum(
            r["tinyguard_result"] == "VIOLATION" for r in rows
        ),
        "errors": sum(r["tinyguard_result"] == "ERROR" for r in rows),
        "unclassified": sum(
            r["tinyguard_result"] == "UNCLASSIFIED" for r in rows
        ),
        "results": rows,
        "interpretation": (
            "Discovery only. Baseline classifications are not ground truth. "
            "Each repository must be inspected for architectural boundaries "
            "before scoring false positives or false negatives. No injected "
            "violations have been tested in this stage."
        ),
    }

    json_path = RESULTS / "discovery_metrics.json"
    json_path.write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    report = [
        "# TinyGuard Real-World Repository Discovery",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Environment",
        "",
        f"- Python: {sys.version.split()[0]}",
        f"- Platform: {platform.platform()}",
        f"- Repositories attempted: {len(PROJECTS)}",
        "",
        "## Results",
        "",
        "| Repository | Clone status | Python files | TinyGuard | Runtime (s) | Commit |",
        "|---|---|---:|---|---:|---|",
    ]

    for r in rows:
        report.append(
            f"| {r['repository']} | {r['clone_status']} "
            f"| {r['python_files']} | {r['tinyguard_result']} "
            f"| {r['runtime_seconds']} | {r['commit'][:12]} |"
        )

    report += [
        "",
        "## Summary",
        "",
        f"- Clean classifications: {summary['clean']}",
        f"- Violation classifications: {summary['violations']}",
        f"- Errors: {summary['errors']}",
        f"- Unclassified: {summary['unclassified']}",
        "",
        "## Important interpretation limits",
        "",
        "This is a repository discovery and baseline execution run, not a",
        "scored accuracy benchmark. A repository's baseline result is not",
        "ground truth until its architecture and intended policy are reviewed.",
        "The direct and transitive violation injection experiments have not",
        "yet been performed. Repositories without suitable architectural",
        "boundaries must be excluded or replaced.",
        "",
        "## Reproduction",
        "",
        "Run `python3 benchmark/real_world/run_discovery.py` from the project root.",
    ]

    report_path = RESULTS / "discovery_report.md"
    report_path.write_text("\n".join(report), encoding="utf-8")

    print()
    print("=" * 65)
    print("DISCOVERY COMPLETE")
    print("=" * 65)
    print("Clean:", summary["clean"])
    print("Violations:", summary["violations"])
    print("Errors:", summary["errors"])
    print("Unclassified:", summary["unclassified"])
    print()
    print("Saved:")
    print(csv_path)
    print(json_path)
    print(report_path)

if __name__ == "__main__":
    main()
