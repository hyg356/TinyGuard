# TinyGuard
### Local-First AI-Assisted Architecture Guardrails for Python

TinyGuard is a Python architecture analysis tool that detects forbidden dependency chains across modules and uses a locally hosted language model to propose potential remediations.

It combines **deterministic static analysis** with **local LLM-assisted remediation**, aiming to make architectural violations easier to detect, understand, and address without sending source code to an external AI service.

---

## The Problem

As Python projects grow, their internal dependencies can become difficult to manage.

A module may appear architecturally safe when inspected in isolation while indirectly depending on a forbidden component through several intermediate modules.

For example:

```text
API Layer
   |
   v
Business Logic
   |
   v
Database Layer
```

If the API layer is not permitted to depend on the database layer, checking only direct imports is insufficient. The violation exists across a transitive dependency chain.

Existing architectural rules are also only useful when developers can understand and act on the violations they identify.

TinyGuard explores a workflow that combines dependency analysis with locally generated remediation proposals.

---

## Key Features

### 1. Dependency Graph Construction

TinyGuard analyzes Python imports and constructs a module dependency graph.

It supports analysis involving:

- Direct imports
- Transitive dependencies
- Relative imports
- Package re-exports
- Nested module structures
- `src/`-style project layouts
- Constant-based dynamic imports

### 2. Architectural Violation Detection

The graph engine traverses dependencies to identify forbidden architectural paths.

For example:

```text
api
 |
 v
logic.orders
 |
 v
database
```

If the architecture rules prohibit API modules from reaching the database layer, TinyGuard can report the complete dependency chain rather than only an isolated import.

### 3. Local LLM-Assisted Remediation

When a violation is detected, TinyGuard can communicate with a locally hosted Ollama model to generate a remediation proposal.

The proposal includes:

- An explanation of the issue
- The files proposed for modification
- A suggested patch strategy

The LLM is used as a remediation assistant, not as the authority deciding whether the architecture is valid.

### 4. Proposal Validation

LLM-generated proposals are untrusted input.

TinyGuard validates proposals before proceeding, including checks for:

- Required proposal fields
- Invalid or unexpected fields
- Empty file lists
- Mismatched file information
- Unsafe file paths

This creates a validation boundary between model-generated suggestions and subsequent operations.

### 5. Patch Verification

TinyGuard includes a patch-verification workflow that checks proposed changes without directly modifying the original project files.

The objective is to separate generating a potential fix from verifying whether that fix is acceptable.

### 6. Fail-Closed Analysis

The analyzer includes defensive handling for cases such as:

- Python parsing failures
- Unresolved or ambiguous project structures
- Relative imports escaping the project boundary
- Dynamic imports
- Nested source layouts
- Package-versus-module resolution

When analysis cannot safely establish the required information, TinyGuard is designed to avoid silently treating uncertainty as a successful result.

---

## Architecture

```text
                Python Project
                      |
                      v
             Module Resolution
                      |
                      v
              Import Resolution
                      |
                      v
             Dependency Graph
                      |
                      v
          Architectural Rule Checks
                      |
             +--------+--------+
             |                 |
             v                 v
          No Issue           Violation
             |                 |
             v                 v
          Pass Result     Local LLM Proposal
                               |
                               v
                       Proposal Validation
                               |
                               v
                        Patch Verification
                               |
                               v
                        Remediation Report
```

The architecture deliberately separates deterministic analysis from probabilistic LLM assistance.

The dependency graph and architectural checks determine whether a violation exists. The language model only proposes a possible remediation.

---

## Technology Stack

| Component | Technology |
|---|---|
| Core implementation | Python |
| Static analysis | Python AST |
| Dependency representation | Graph-based analysis |
| Local LLM inference | Ollama |
| Example local model | Qwen 2.5 3B |
| Testing | Python test scripts |
| Benchmarking | Custom Python benchmark harness |

TinyGuard is designed around local execution. The remediation component requires a locally running Ollama service and a compatible model.

---

## Project Structure

```text
TinyGuard/
│
├── tinyguard.py
│
├── tinyguard/
│   ├── __init__.py
│   ├── module_resolver.py
│   ├── import_resolver.py
│   ├── graph_engine.py
│   └── remediation.py
│
├── dummy_app/
│   └── ...
│
├── benchmark/
│   ├── README.md
│   ├── fixtures/
│   ├── standard_fixtures/
│   ├── head_to_head/
│   │   ├── run_benchmark.py
│   │   └── results/
│   ├── mutation/
│   │   └── run_mutations.py
│   ├── real_world/
│   │   ├── run_discovery.py
│   │   ├── run_injection_tests.py
│   │   └── results/
│   ├── results/
│   ├── run_pilot.py
│   └── run_standard.py
│
├── test_cli.py
├── test_graph_engine.py
├── test_remediation.py
├── test_proposal_validation.py
├── test_patch_verifier.py
├── test_end_to_end.py
└── test_hardening.py
```

*This is a representative structure. Retain only paths that exist in the version you publish.*

---

## Installation

### Requirements

- Python 3.10 or newer
- Ollama (for LLM-assisted remediation)
- A compatible locally available language model

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/TinyGuard.git
cd TinyGuard
```

No external LLM API key is required.

### Configure Ollama

Install Ollama from:

https://ollama.com/

Pull the example model:

```bash
ollama pull qwen2.5:3b
```

Start the local model:

```bash
ollama run qwen2.5:3b
```

TinyGuard's remediation component communicates with the local Ollama service.

---

## Usage

Run TinyGuard against a Python project:

```bash
python3 tinyguard.py /path/to/your/project
```

A detected violation may produce output similar to:

```text
VIOLATION: api.py: forbidden dependency chain:
api -> logic.orders -> database
```

A project without detected violations may produce:

```text
TinyGuard passed
```

The exact output depends on the analyzed project and configured architectural rules.

---

## Testing

TinyGuard includes tests for its graph engine, CLI, remediation workflow, proposal validation, patch verification, end-to-end behavior, and hardening scenarios.

Run the test suite:

```bash
python3 test_cli.py
python3 test_graph_engine.py
python3 test_remediation.py
python3 test_proposal_validation.py
python3 test_patch_verifier.py
python3 test_end_to_end.py
python3 test_hardening.py
```

The project has been tested against scenarios involving:

- Direct and transitive architectural violations
- Nested forbidden namespaces
- `src/` layouts
- Relative imports
- Package re-exports
- Third-party modules with potentially misleading names
- Constant dynamic imports
- Python parsing failures
- UTF-8 BOM handling
- Nested virtual-environment directories
- Projects without valid entry points
- Relative imports that attempt to escape the project boundary
- Package-versus-module resolution

---

## Benchmarking and Evaluation

TinyGuard includes a custom benchmark suite designed to evaluate dependency analysis and architectural violation detection.

### Controlled Benchmark

The standard fixture suite contains **100 controlled cases**:

| Category | Safe cases | Violation cases |
|---|---:|---:|
| Direct imports | 10 | 10 |
| Re-exports | 10 | 10 |
| Relative imports | 10 | 10 |
| `src/` layouts | 10 | 10 |
| Transitive dependencies | 10 | 10 |
| **Total** | **50** | **50** |

These fixtures test whether the analyzer distinguishes safe dependency structures from deliberately introduced violations.

### Mutation Testing

The mutation benchmark introduces controlled architectural violations into project structures to examine whether TinyGuard detects the resulting dependency problems.

### Real-World Repository Experiments

The real-world evaluation workflow includes repository discovery and controlled fault-injection experiments.

A FastAPI-based project was used for additional investigation:

- A shared architectural violation was identified across multiple API entry points.
- Direct and transitive violations were introduced into copies of the project.
- TinyGuard detected both injected scenarios.

The original upstream project was not modified during the injection experiments.

### Benchmark Limitations

The benchmark results should be interpreted carefully:

- Controlled fixtures do not represent the full diversity of production Python projects.
- Real-world repository discovery included projects without established ground-truth labels.
- A clean result is not proof that a repository has no architectural violations.
- Fault-injection experiments evaluate known, deliberately introduced violations; they do not establish general detection accuracy.
- No claim of superiority over established architecture-analysis tools is made.

The benchmark scripts and generated results are included to make the evaluation process inspectable and reproducible, subject to the documented setup requirements.

---

## Design Principles

TinyGuard follows several core principles:

**Deterministic enforcement:** Architectural violations are identified through static analysis and graph traversal, rather than relying on an LLM to judge correctness.

**Local-first AI:** Remediation proposals can be generated using a locally hosted model.

**Validation before action:** Model-generated proposals are treated as untrusted and validated before further processing.

**Separation of concerns:** Dependency resolution, graph construction, rule enforcement, remediation, and verification are separate components.

**Fail-closed behavior:** Uncertain or invalid analysis should not silently become a successful result.

---

## Current Limitations

TinyGuard is an experimental project and is not yet a replacement for mature static-analysis or architecture-enforcement platforms.

Current limitations include:

- Python-focused analysis
- Incomplete handling of arbitrary dynamic import behavior
- Heuristic project-root and source-layout detection
- Potentially unresolved dependencies in complex or unconventional project structures
- Remediation proposals may be incorrect or incomplete
- No guarantee that a suggested patch preserves application behavior
- Benchmark coverage is limited to the included fixtures and experiments

The tool should be used as an additional architectural safeguard, not as the sole mechanism for enforcing production software integrity.

---

## Future Work

Potential areas of development include:

- More robust multi-root and nested-source project resolution
- Broader support for Python import semantics
- Improved architectural rule configuration
- Larger and independently labeled real-world benchmark datasets
- Comparative evaluation against established tools
- More rigorous semantic verification of generated patches
- Support for additional programming languages
- CI/CD integration through GitHub Actions

---

## Contributing

Contributions, bug reports, benchmark cases, and suggestions are welcome.

If you encounter an incorrect dependency resolution or a missed architectural violation, a minimal reproducible example is especially helpful.

---

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Author

Developed as an independent engineering project exploring the intersection of static program analysis, software architecture enforcement, and local AI-assisted remediation.

**TinyGuard — Deterministic architecture checks. Local AI-assisted remediation.**
