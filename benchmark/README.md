# TinyGuard Benchmark Suite

This directory contains the benchmark and evaluation scripts used to assess TinyGuard's architectural dependency detection.

TinyGuard has two distinct capabilities:

1. **Deterministic analysis:** Detects direct and transitive forbidden dependencies between Python modules.
2. **AI-assisted remediation:** Uses a small local LLM to suggest potential repairs for detected violations, followed by static verification of the proposed changes.

The current benchmark suite primarily measures the first capability. The quality and behavioral correctness of AI-generated repair suggestions have not yet been comprehensively evaluated.

> **Evaluation status:** These experiments provide early evidence of correctness on controlled cases. They do not establish general accuracy across arbitrary Python repositories or production systems.

## Results at a glance

| Evaluation | Cases | Result |
|---|---:|---|
| Synthetic benchmark | 100 | 100 passed |
| Head-to-head core corpus: TinyGuard | 24 | 24 correct |
| Head-to-head core corpus: Import Linter | 24 | 12 correct |
| TinyGuard dynamic import extensions | 2 | 2 detected |
| FastAPI controlled injection | 2 | 2 passed |
| Automated regression tests | 29 | 29 passed |

## 1. Synthetic benchmark

**Runner:** `run_standard.py`

Run from the repository root:

```bash
python3 benchmark/run_standard.py
```

### Methodology

The benchmark generates 100 controlled fixtures across five categories:

| Category | Fixtures |
|---|---:|
| Direct imports | 20 |
| Transitive imports | 20 |
| Relative imports | 20 |
| Package re-exports | 20 |
| `src/` layouts | 20 |
| **Total** | **100** |

### Results

| Metric | Result |
|---|---:|
| True positives | 50 |
| False positives | 0 |
| True negatives | 50 |
| False negatives | 0 |
| Errors | 0 |
| Precision | 100% |
| Recall | 100% |
| F1 | 100% |
| Accuracy | 100% |

All five categories passed 20/20 fixtures.

### Interpretation

This demonstrates that TinyGuard correctly handled the tested synthetic cases. It does not establish 100% accuracy on arbitrary Python projects.

## 2. Head-to-head comparison with Import Linter

**Runner:** `benchmark/head_to_head/run_benchmark.py`

Run:

```bash
python3 benchmark/head_to_head/run_benchmark.py
```

### Environment

| Property | Value |
|---|---|
| Python | 3.14.0 |
| Platform | macOS 26.5.2, arm64 |
| Import Linter | 2.15 |
| Core cases | 24 |
| Additional TinyGuard extension cases | 2 |
| Total recorded cases | 26 |

### Tested policy

The core corpus evaluates the policy:

```text
app.api must not depend directly or transitively on app.database
```

### Core results

| Metric | TinyGuard | Import Linter |
|---|---:|---:|
| Cases | 24 | 24 |
| True positives | 12 | 12 |
| False positives | 0 | 12 |
| True negatives | 12 | 0 |
| False negatives | 0 | 0 |
| Errors | 0 | 0 |
| Precision | 100% | 50% |
| Recall | 100% | 100% |
| F1 | 100% | 66.67% |
| Accuracy on valid predictions | 100% | 50% |

### TinyGuard-specific extension cases

Two additional cases tested constant-string dynamic imports:

- `importlib.import_module("...")`
- `__import__("...")`

TinyGuard detected both cases.

These are reported separately because they are extensions of the tested TinyGuard behavior, not part of the 24-case core comparison.

### Interpretation and limitations

The corpus is hand-authored and contains only 24 core cases. The results are specific to the selected policy and fixture construction.

The comparison should not be interpreted as evidence that TinyGuard is generally more accurate or capable than Import Linter.

## 3. Real-world repository discovery

**Runner:** `benchmark/real_world/run_discovery.py`

Run:

```bash
python3 benchmark/real_world/run_discovery.py
```

### Methodology

The discovery experiment cloned or analyzed ten public Python repositories and ran TinyGuard using its configured default policy.

The repositories were:

- FastAPI
- Starlette
- Flask
- Requests
- SQLModel
- SQLAlchemy
- Pydantic
- HTTPX
- Click
- redis-py

The run used Python 3.14.0 on macOS 26.5.2 arm64.

### Results

| Repository | Python files | Classification | Runtime (s) |
|---|---:|---|---:|
| FastAPI | 1,219 | NO_ENTRYPOINTS | 20.34 |
| Starlette | 84 | NO_ENTRYPOINTS | 3.90 |
| Flask | 83 | NO_ENTRYPOINTS | 3.54 |
| Requests | 37 | CLEAN | 0.98 |
| SQLModel | 334 | NO_ENTRYPOINTS | 4.619 |
| SQLAlchemy | 678 | CLEAN | 66.712 |
| Pydantic | 3,155 | ERROR | 180.012 |
| HTTPX | 60 | NO_ENTRYPOINTS | 0.69 |
| Click | 91 | NO_ENTRYPOINTS | 2.40 |
| redis-py | 339 | NO_ENTRYPOINTS | 18.998 |

### Summary

| Classification | Count |
|---|---:|
| Clean | 2 |
| Violations | 0 |
| No recognized API entry points | 7 |
| Errors | 1 |
| **Repositories attempted** | **10** |

### Important interpretation limits

This is a discovery and baseline execution run, not a scored accuracy benchmark.

`NO_ENTRYPOINTS` means TinyGuard did not recognize an API entry point under its configured conventions. It does not mean the repository is clean.

The two `CLEAN` classifications are observations from the default policy, not independently verified true negatives.

Pydantic timed out after 180 seconds. It must be counted as an error for this run, not as a clean result.

## 4. FastAPI real-world controlled injection tests

**Runner:** `benchmark/real_world/run_injection_tests.py`

Run:

```bash
python3 benchmark/real_world/run_injection_tests.py
```

### Source application

The experiment uses:

[fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)

Expected local source directory:

```text
benchmark/real_world/repos/full-stack-fastapi
```

The runner creates controlled working copies for the injection experiments. The original cloned repository is not modified.

### Test cases

**RW-DIRECT-01 — Direct dependency**

A route is modified to import the persistence module directly.

Expected chain:

```text
app.api.routes.utils -> app.core.db
```

Result: **PASS**

Runtime: 0.541 seconds.

**RW-TRANSITIVE-01 — Transitive dependency**

An API entry point imports a helper module, which imports the persistence module.

Expected chain:

```text
app.api.benchmark_probe
    -> app.benchmark_helper
        -> app.core.db
```

Result: **PASS**

Runtime: 0.973 seconds.

### Results

| Test | Type | Expected | Actual | Runtime | Result |
|---|---|---|---|---:|---|
| RW-DIRECT-01 | Direct | VIOLATION | VIOLATION | 0.541 s | PASS |
| RW-TRANSITIVE-01 | Transitive | VIOLATION | VIOLATION | 0.973 s | PASS |
| **Total** | | | | | **2/2 passed** |

TinyGuard also reported other API entry points that reached the persistence layer through existing dependencies in the application.

### Limitations

- Only one source application was tested.
- The dependency violations were deliberately injected.
- The experiment measures detection of a specified forbidden import policy.
- It does not establish general architectural correctness.
- It does not measure the quality of AI-generated repairs.

## 5. AI-assisted repair workflow

TinyGuard includes an experimental remediation workflow that uses a small local language model to suggest fixes for detected architectural violations.

The workflow is designed as a separate stage after deterministic violation detection.

### Workflow

1. TinyGuard identifies a forbidden dependency chain.
2. Relevant source files are selected automatically, within a context budget.
3. A local LLM receives the violation and selected source context.
4. The model returns a structured repair proposal.
5. TinyGuard validates the proposal and its file paths.
6. Proposed changes are tested in a temporary project copy.
7. A static verifier checks the patched project's structural properties.
8. The proposal and diff are saved for developer review.

The original project is never automatically modified.

### Verification checks

The current static verifier checks:

- Successful parsing and decoding.
- Absence of forbidden dependency chains from detected API entry points.
- Preservation of original public top-level functions, classes, and public methods.
- Rejection of trivial replacement bodies for meaningful functions.
- Preservation of cross-module symbol references.
- Absence of newly introduced unresolved dynamic imports.

### Repair evaluation status

The current benchmark suite does not establish that the LLM consistently produces useful or behaviorally correct repairs.

A structurally valid patch may still change program behavior. The current verifier does not prove behavioral equivalence.

Future remediation benchmarks should measure:

- Whether proposed patches eliminate the original violation.
- Whether the patch passes the project's existing tests.
- Whether behavior is preserved.
- Whether proposals are applicable and useful to developers.
- How often the model produces invalid, incomplete, or unnecessary changes.

## 6. Automated regression tests

Run from the repository root:

```bash
python3 -m pytest -q
```

Latest recorded result:

```text
29 passed
```

The suite covers areas including:

- Dependency graph traversal.
- Direct and transitive violations.
- Import resolution.
- Relative imports and package re-exports.
- Configuration handling.
- CLI behavior and exit codes.
- Dynamic import handling.
- Proposal validation.
- Static patch verification.
- End-to-end behavior.

Some tests that require a live local Ollama model are skipped automatically when the service is unavailable.

## 7. Generated result files

### Standard benchmark

```text
benchmark/results/
    standard_results.csv
```

### Head-to-head benchmark

```text
benchmark/head_to_head/results/
    case_results.csv
    metrics.json
    report.md
```

### Real-world discovery

```text
benchmark/real_world/results/
    repository_results.csv
    discovery_metrics.json
    discovery_report.md
    pydantic_diagnostic.txt
```

### Real-world injection tests

```text
benchmark/real_world/results/
    injection_results.csv
    injection_metrics.json
```

These files contain the per-case results, aggregate metrics, diagnostics, and experiment reports.

## 8. Reproducing the complete evaluation

From the repository root:

```bash
# Automated tests
python3 -m pytest -q

# Synthetic benchmark
python3 benchmark/run_standard.py

# Head-to-head comparison
python3 benchmark/head_to_head/run_benchmark.py

# Repository discovery
python3 benchmark/real_world/run_discovery.py

# FastAPI controlled injection tests
python3 benchmark/real_world/run_injection_tests.py
```

The FastAPI injection runner requires the source repository at:

```text
benchmark/real_world/repos/full-stack-fastapi
```

The discovery runner may clone repositories and can take several minutes, depending on repository size and machine performance.

## 9. Overall evaluation

The current benchmark suite provides evidence in three distinct settings:

1. **Synthetic correctness:** TinyGuard handles the tested import patterns and dependency relationships.
2. **Controlled tool comparison:** TinyGuard performs well on the selected 24-case core corpus.
3. **Real-application structure:** TinyGuard detects direct and transitive controlled violations in a FastAPI application.

The AI-assisted repair workflow adds a second capability to the project, but its proposal quality and behavioral correctness require a separate evaluation.

The evidence does not yet establish:

- General accuracy across arbitrary Python repositories.
- Superiority over mature architectural analysis tools.
- Behavioral correctness of AI-generated repairs.
- Reliable performance on very large repositories.

Future evaluation should prioritize more independently selected real-world applications, clearly specified architectural policies, larger and more diverse test corpora, performance profiling, and behavioral testing of repair proposals.

**The goal of this benchmark suite is reproducible, honest measurement—not maximizing headline accuracy numbers.**
