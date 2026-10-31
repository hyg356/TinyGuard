# TinyGuard Benchmark Suite

This directory contains the evaluation framework for **TinyGuard**, a Python architectural dependency guardrail designed to detect forbidden dependency relationships and support AI-assisted remediation.

The benchmark evaluates TinyGuard across controlled architectural scenarios, real-world Python repositories, and deliberately injected architectural violations.

## 1. Benchmark Structure

```text
benchmark/
├── README.md
├── datasets/
│   ├── fixtures/
│   └── standard_fixtures/
├── scripts/
│   ├── run_pilot.py
│   ├── run_standard.py
│   ├── mutation/
│   │   └── run_mutations.py
│   ├── head_to_head/
│   │   └── run_benchmark.py
│   └── real_world/
│       ├── run_discovery.py
│       └── run_injection_tests.py
└── results/
    ├── pilot.txt
    ├── standard_results.csv
    ├── head_to_head/
    └── real_world/
        ├── diagnostics/
        ├── discovery_metrics.json
        ├── discovery_report.md
        ├── repository_results.csv
        ├── injection_metrics.json
        └── injection_results.csv
```

*Note: This is the intended published organization. Individual result files may vary depending on which experiments have been executed.*

## 2. Evaluation Categories

### A. Controlled Fixture Benchmark

The standard fixture suite contains **100 test cases**, divided into five architectural scenarios:

| Category | Safe cases | Violation cases |
|---|---:|---:|
| Direct dependencies | 10 | 10 |
| Package re-exports | 10 | 10 |
| Relative imports | 10 | 10 |
| `src/` layouts | 10 | 10 |
| Transitive dependencies | 10 | 10 |
| **Total** | **50** | **50** |

The suite evaluates whether TinyGuard can distinguish permitted dependency relationships from architectural violations across different Python import structures.

### B. Pilot Benchmark

The pilot benchmark provides an initial evaluation using a smaller collection of architectural fixtures.

It serves as an early validation step before running the expanded standard fixture suite.

### C. Head-to-Head Evaluation

The head-to-head benchmark evaluates TinyGuard against an existing Python architecture-linting tool under selected dependency-policy scenarios.

The purpose is to investigate differences in detection behavior, rather than assume that either tool is universally superior.

### D. Real-World Repository Discovery

TinyGuard was evaluated against a collection of established Python repositories and frameworks.

This experiment examines how the analyzer behaves when presented with real-world project structures, including repositories that may not satisfy the analyzer's entrypoint or policy assumptions.

Results distinguish detected violations, clean classifications, and unclassified cases.

**Important:** A clean classification does not independently establish correctness without ground-truth architectural labels.

### E. Real-World Fault Injection

Controlled architectural violations were introduced into copies of a real-world FastAPI application.

Two scenarios were evaluated:

- **Direct violation:** Introduces a forbidden dependency directly into an API route.
- **Transitive violation:** Introduces a dependency chain through an intermediate module that ultimately reaches a forbidden module.

The original application is preserved; experiments operate on generated copies.

## 3. Engineering Considerations

The benchmark also exercises behavior around:

- Direct and transitive dependency chains.
- Relative imports and package re-exports.
- Nested Python source roots.
- `src/` project layouts.
- Dynamic imports.
- Third-party module resolution.
- Malformed Python files and parsing failures.
- Safe and violating architectural configurations.

These scenarios help evaluate analyzer robustness beyond basic import detection.

## 4. Reproducing Experiments

Run benchmark scripts from the TinyGuard repository root.

For example:

```bash
python3 benchmark/scripts/run_pilot.py
python3 benchmark/scripts/run_standard.py
```

Additional experiments are available under:

```text
benchmark/scripts/mutation/
benchmark/scripts/head_to_head/
benchmark/scripts/real_world/
```

Refer to the individual scripts and their configuration for experiment-specific requirements.

Real-world experiments may require cloning the upstream repositories used by the evaluation. Generated repository copies and upstream source clones are intentionally excluded from the published benchmark directory.

## 5. Results and Interpretation

Experiment outputs are stored under `results/`.

Depending on the experiment, these include:

- CSV files containing individual test outcomes.
- JSON files containing aggregate metrics.
- Markdown reports summarizing experiments.
- Diagnostic text files containing analyzer output.

Results should be interpreted within the scope of their corresponding experiment.

In particular, controlled fixtures and injected violations demonstrate behavior under specified conditions; they should not be interpreted as proof of general accuracy across all Python repositories.

## 6. Reproducibility and Limitations

For reproducible comparisons, record:

- TinyGuard version or commit.
- Upstream repository commit hashes.
- Python version and dependencies.
- Benchmark configuration and architectural policies.
- Exact commands used to execute experiments.

The current benchmark is an engineering evaluation suite, not an exhaustive assessment of Python architectural analysis.

Its controlled fixtures, repository discovery experiments, and fault-injection scenarios provide complementary forms of evidence, each with different limitations.

## 7. Project

TinyGuard combines deterministic dependency analysis with locally hosted LLM-assisted remediation.

The benchmark is intended to make its detection behavior, limitations, and experimental results transparent and reproducible.
