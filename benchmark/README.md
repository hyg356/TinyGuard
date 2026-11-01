# TinyGuard Benchmark Suite

This directory contains controlled tests and initial real-world experiments for evaluating TinyGuard's architectural dependency analysis.

The benchmark suite is intended to make the project's behavior reproducible and to expose its limitations. It includes synthetic fixtures, a comparison with Import Linter, repository discovery scans, and controlled fault injection.

> **Evaluation status:** the suite contains several completed experiments, but not every benchmark track is complete. In particular, the mutation runner currently records a baseline and marks mutations as not yet tested. Repository discovery is not a scored accuracy benchmark, and the real-world fault-injection experiment currently covers two cases in one FastAPI-based codebase.

## 1. Benchmark overview

| Track | Purpose | Current status |
|---|---|---|
| Pilot | Initial 10-case sanity check | Results saved |
| Standard fixtures | 100 controlled cases across five categories | Results saved |
| Head-to-head | Compare TinyGuard with Import Linter on a shared corpus | Results and report saved |
| Mutation | Establish baseline and prepare mutation experiments | Incomplete |
| Real-world discovery | Scan 10 open-source repositories | All 10 scans completed |
| Real-world injection | Verify detection of deliberately introduced violations | 2 of 2 cases passed |

These tracks answer different questions. Results should not be combined into a single accuracy score.

## 2. Directory structure

```text
benchmark/
├── README.md
├── fixtures/
├── standard_fixtures/
├── head_to_head/
│   ├── run_benchmark.py
│   └── results/
│       ├── case_results.csv
│       ├── metrics.json
│       └── report.md
├── mutation/
│   ├── run_mutations.py
│   └── results/
├── real_world/
│   ├── run_discovery.py
│   ├── run_injection_tests.py
│   └── results/
│       ├── discovery_metrics.json
│       ├── discovery_report.md
│       ├── repository_results.csv
│       ├── injection_metrics.json
│       ├── injection_results.csv
│       └── *_diagnostic.txt
├── results/
│   ├── pilot.txt
│   └── standard_results.csv
├── run_pilot.py
└── run_standard.py
```

Some fixture directories and result files are generated or refreshed by the benchmark scripts. Do not edit generated results manually when reporting a new run.

## 3. Pilot benchmark

**Script:** `run_pilot.py`

The pilot benchmark runs 10 initial cases to provide a quick sanity check of TinyGuard's behavior.

Run from the repository root:

```bash
python3 benchmark/run_pilot.py
```

The pilot output is also preserved in:

```text
benchmark/results/pilot.txt
```

The pilot is an initial smoke-test benchmark. It should not be presented as a comprehensive evaluation.

## 4. Standard fixture benchmark

**Script:** `run_standard.py`

The standard benchmark contains 100 controlled fixture cases, divided into five categories.

| Category | Violation cases | Safe cases | Total |
|---|---:|---:|---:|
| Direct imports | 10 | 10 | 20 |
| Transitive dependencies | 10 | 10 | 20 |
| Relative imports | 10 | 10 | 20 |
| Package re-exports | 10 | 10 | 20 |
| `src/` project layouts | 10 | 10 | 20 |
| **Total** | **50** | **50** | **100** |

### What the categories test

**Direct imports**

Checks direct dependencies from an API entry point to a forbidden module, including different import forms and aliases.

**Transitive dependencies**

Checks whether TinyGuard can detect a forbidden dependency reached through intermediate modules at different chain depths.

**Relative imports**

Checks relative import resolution inside package layouts.

**Package re-exports**

Checks whether a dependency can be followed through a package's `__init__.py` re-exports.

**`src/` project layouts**

Checks dependency resolution when application modules are located under a `src/` directory.

### Run

From the repository root:

```bash
python3 benchmark/run_standard.py
```

The script creates or refreshes the generated standard fixtures and writes:

```text
benchmark/results/standard_results.csv
```

The CSV contains the individual case outcomes and expected classifications.

### Interpretation

The standard benchmark is a hand-authored controlled fixture suite. Its expected labels are known because the cases are constructed specifically for the experiment.

It measures behavior on the tested import patterns. It does not establish general accuracy across arbitrary Python repositories.

## 5. Head-to-head comparison with Import Linter

**Script:** `head_to_head/run_benchmark.py`

This benchmark compares TinyGuard with [Import Linter](https://github.com/seddonym/import-linter) on a shared set of controlled fixture projects.

The core policy is:

> `app.api` must not depend directly or transitively on `app.database`.

The benchmark includes ordinary import patterns such as:

- Direct absolute imports.
- `from` imports.
- Transitive dependencies.
- Relative imports.
- Package re-exports.
- Aliased imports.
- Function-local imports.
- Conditional imports.
- Wildcard imports.
- Nested database packages.
- Safe dependency patterns and non-matching module names.

TinyGuard also has a separate extension track for literal calls to:

- `importlib.import_module("app.database")`
- `__import__("app.database")`

These extension cases are evaluated for TinyGuard but are not included in the Import Linter parity comparison.

### Install the comparison dependency

```bash
python3 -m pip install import-linter
```

Confirm that `lint-imports` is available:

```bash
lint-imports --version
```

### Run

From the repository root:

```bash
python3 benchmark/head_to_head/run_benchmark.py
```

### Output files

```text
benchmark/head_to_head/results/
├── case_results.csv
├── metrics.json
├── report.md
└── *_diagnostics.txt
```

The runner records:

- Expected classification for each case.
- TinyGuard classification and runtime.
- Import Linter classification and runtime for core cases.
- Exit codes.
- Diagnostic output for cases where a tool reports an error.

The metrics include:

- True positives.
- False positives.
- True negatives.
- False negatives.
- Errors.
- Precision.
- Recall.
- F1.
- Accuracy on valid predictions.

Errors are counted separately and excluded from the valid-prediction accuracy denominator.

### Interpretation limits

This is a controlled conformance comparison, not a general benchmark of all Python architecture policies.

Import Linter and TinyGuard may use different import-resolution semantics. Individual disagreements should be inspected rather than automatically treated as defects in one tool.

Runtime measurements are per-fixture measurements. They are not evidence of performance on very large repositories.

Use the generated `metrics.json` and `report.md` for the actual numerical results. Do not claim that one tool is universally more accurate or faster based on this corpus alone.

## 6. Mutation benchmark

**Script:** `mutation/run_mutations.py`

The mutation runner is currently a scaffold for future mutation testing.

Its present behavior is:

1. Run the project's baseline unit-test suite.
2. Record whether the baseline passes.
3. Write the mutation result records.
4. Mark mutations as `NOT_YET_TESTED`.

It does **not** currently apply mutations automatically or calculate a mutation score.

Run from the repository root:

```bash
python3 benchmark/mutation/run_mutations.py
```

Do not report mutation coverage or a mutation score until actual mutations have been executed and their outcomes recorded.

## 7. Real-world repository discovery

**Script:** `real_world/run_discovery.py`

This experiment scans a set of 10 open-source Python repositories:

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

The discovery runner prepares the repository inputs and executes TinyGuard against them. Repository clones are generated under:

```text
benchmark/real_world/repos/
```

These downloaded repositories are inputs to the experiment, not part of TinyGuard's source code. They should not be committed to the TinyGuard repository.

### Run

From the repository root:

```bash
python3 benchmark/real_world/run_discovery.py
```

The runner writes results under:

```text
benchmark/real_world/results/
```

Important output files:

- `repository_results.csv`
- `discovery_metrics.json`
- `discovery_report.md`
- Individual diagnostic text files for relevant repositories.

### Current experiment results

The recorded discovery run completed all 10 repository scans:

| Classification | Repositories |
|---|---:|
| Clean | 2 |
| Violations | 0 |
| Errors | 0 |
| No recognized API entry points | 8 |
| **Total** | **10** |

The `NO_ENTRYPOINTS` classification means TinyGuard's default entry-point rules did not identify an API entry point in that repository. It does not mean the repository was checked and found architecturally clean.

The two clean classifications mean no forbidden dependency path was reported among the entry points TinyGuard recognized. They are not independently verified ground-truth labels.

### Interpretation

This experiment provides initial evidence that TinyGuard can process a range of real-world Python repository layouts.

It is primarily a repository compatibility and discovery experiment, not a scored accuracy benchmark. The results do not establish that TinyGuard correctly identifies every architectural violation in those projects.

## 8. Real-world fault injection

**Script:** `real_world/run_injection_tests.py`

The fault-injection experiment checks whether TinyGuard detects known violations introduced into a real project.

The current experiment uses the backend of the FastAPI-based `full-stack-fastapi` project.

Two cases are tested:

| Case | Injected dependency | Expected behavior |
|---|---|---|
| `RW-DIRECT-01` | API module imports the database module directly | Detect the exact direct chain |
| `RW-TRANSITIVE-01` | API entry point imports a helper that imports the database module | Detect the exact indirect chain |

The transitive case uses an isolated API probe so that the expected chain can be verified independently of other existing dependency paths.

### Repository input

The injection runner expects the FastAPI repository clone at:

```text
benchmark/real_world/repos/full-stack-fastapi
```

Run the discovery script first if you need it to prepare the repository inputs:

```bash
python3 benchmark/real_world/run_discovery.py
```

### Run

From the repository root:

```bash
python3 benchmark/real_world/run_injection_tests.py
```

The script creates temporary working copies under:

```text
benchmark/real_world/injection_work/
```

It checks the exact expected diagnostics rather than treating any violation as a successful result.

### Recorded result

The current recorded experiment:

| Case | Result |
|---|---|
| Direct injection | PASS |
| Transitive injection | PASS |
| **Total** | **2/2 passed** |

The result files are:

```text
benchmark/real_world/results/injection_results.csv
benchmark/real_world/results/injection_metrics.json
```

### Interpretation limits

These are two controlled injections into one real codebase. They demonstrate that the tested direct and transitive violations were detected, but do not establish broad real-world accuracy.

The FastAPI project may already contain architectural violations. The experiment verifies the expected injected chains rather than claiming that every finding in the repository is caused by the injection.

## 9. Reproducing the main experiments

Run the core tests:

```bash
python3 -m pytest -q
```

Run the pilot and standard fixtures:

```bash
python3 benchmark/run_pilot.py
python3 benchmark/run_standard.py
```

Run the head-to-head comparison:

```bash
python3 -m pip install import-linter
python3 benchmark/head_to_head/run_benchmark.py
```

Run repository discovery and injection:

```bash
python3 benchmark/real_world/run_discovery.py
python3 benchmark/real_world/run_injection_tests.py
```

Run the mutation scaffold:

```bash
python3 benchmark/mutation/run_mutations.py
```

Some experiments generate repository clones, temporary working copies, and result files. Review the generated output before committing a new benchmark run.

## 10. Reproducibility and reporting guidelines

When publishing benchmark results, record:

- Python version.
- Operating system and architecture.
- TinyGuard commit or source revision.
- Import Linter version for head-to-head comparisons.
- Exact commands used.
- Raw CSV and JSON output.
- Any errors, skipped cases, or cases without recognized entry points.

Do not combine synthetic fixture accuracy, real-world discovery classifications, and fault-injection success into one overall accuracy figure. They measure different things.

Do not treat a clean classification as verified ground truth unless the repository's architecture and expected policy have been independently reviewed.

## 11. Current limitations and future work

The benchmark suite is an early evaluation framework. Future work includes:

1. Completing automated mutation execution and reporting.
2. Expanding real-world fault injection across multiple repositories.
3. Manually reviewing architectural ground truth for selected repositories.
4. Evaluating more complex package and dynamic-import patterns.
5. Measuring false positives and false negatives on independently labelled projects.
6. Evaluating the quality and behavioral correctness of LLM-generated repairs.
7. Comparing repair proposals with and without deterministic verification.

The longer-term research direction is to investigate whether deterministic static verification can improve the reliability of architectural repairs proposed by small local language models.

## 12. Summary

The benchmark suite currently provides:

- A 10-case pilot.
- A 100-case controlled standard fixture suite.
- A shared-corpus comparison with Import Linter.
- Repository discovery scans across 10 open-source projects.
- Two successful direct and transitive fault-injection cases on a FastAPI-based project.
- A mutation-testing scaffold whose actual mutation phase remains incomplete.

These experiments provide an initial, reproducible evaluation of TinyGuard's implementation. They should be interpreted within their stated scope and limitations.