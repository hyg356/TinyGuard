# TinyGuard

**A lightweight architectural linter for Python that detects structural violations and explores privacy-preserving, local AI-assisted remediation.**

TinyGuard analyzes Python imports and module dependencies to identify architectural violations before they become harder to fix. It builds a dependency graph, checks dependencies against architectural rules, and can use a locally running language model to propose potential remediations.

The goal is to combine **deterministic architectural enforcement** with **local AI-assisted repair**, keeping the core rule-checking process independent of an external AI service.

## Key Features

- **AST-based analysis:** Inspects Python source code structurally rather than relying on simple text matching.
- **Dependency graph analysis:** Models relationships between modules and detects violations that can emerge across dependency chains.
- **Architectural rule enforcement:** Checks imports against defined architectural boundaries.
- **Import resolution:** Handles Python module and package resolution, including relative imports and common project layouts.
- **Local AI-assisted remediation:** Can use a locally running Ollama model to suggest potential fixes for detected violations.
- **Proposal validation:** Validates remediation proposals before they are considered for further processing.
- **Patch verification:** Provides a verification layer for proposed changes rather than blindly trusting model-generated output.
- **Hardening tests:** Exercises edge cases involving nested packages, `src/` layouts, dynamic imports, malformed source files, and relative-import boundaries.

## How It Works

```text
Python Project
      |
      v
Source Parsing (AST)
      |
      v
Module & Import Resolution
      |
      v
Dependency Graph
      |
      v
Architectural Rule Checking
      |
      v
Violation Report
      |
      +-----------------------+
      |                       |
      v                       v
Local AI Remediation     Manual Fix
      |
      v
Proposal Validation
      |
      v
Patch Verification
```

The architectural analysis is deterministic: the rule engine determines whether a dependency violates the configured policy. The language model assists with remediation, but its suggestions should not be treated as inherently correct or safe.

## Installation

### Prerequisites

- Python 3.10 or later is recommended.
- Git
- [Ollama](https://ollama.com/) and a compatible locally available model for AI-assisted remediation.

The core analysis is designed to use Python's standard library. AI-assisted features may require Ollama and a compatible model, depending on the implementation.

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/TinyGuard.git
cd TinyGuard
```

Replace `YOUR-USERNAME` with your GitHub username.

## Usage

Run TinyGuard against a Python project directory:

```bash
python3 tinyguard.py /path/to/your/python-project
```

Replace the example path with the directory you want to analyze.

TinyGuard reports architectural violations identified by its configured rules. Review the findings and inspect the relevant source files before making changes.

### AI-Assisted Remediation

For remediation features that use Ollama:

1. Install and start Ollama.
2. Download a model supported by your local TinyGuard configuration.
3. Run the remediation workflow using the interface implemented by the project.
4. Review the generated proposal and verification results before accepting any changes.

Model names and configuration depend on the implementation. AI-generated changes should always be reviewed by a developer.

## Running Tests

The repository includes tests for the CLI, graph engine, patch verification, proposal validation, remediation, end-to-end behavior, and hardening edge cases.

Run the individual test files from the repository root:

```bash
python3 test_cli.py
python3 test_graph_engine.py
python3 test_patch_verifier.py
python3 test_proposal_validation.py
python3 test_hardening.py
```

AI-dependent tests may require Ollama to be running and a compatible model to be available:

```bash
python3 test_remediation.py
python3 test_end_to_end.py
```

The graph-builder tests are located inside the package:

```bash
python3 -m unittest tinyguard.test_graph_builder
```

A passing test suite demonstrates behavior covered by those tests; it does not guarantee that every Python project layout or architectural policy is supported.

## Design Principles

**Deterministic enforcement.** Architectural violations should be identified by explicit rules rather than delegated to a language model.

**Local-first operation.** Core analysis can run locally, and remediation can use a local model to reduce dependence on external AI services.

**Validation before action.** Model-generated proposals should be validated and their resulting changes verified before being trusted.

**Explicit failure handling.** Unsupported or malformed input should not silently be treated as a clean architectural result.

## Current Scope and Limitations

TinyGuard is an early-stage project. Its behavior depends on the implemented rules, import-resolution logic, and supported Python project layouts.

- It is not a complete Python type checker or security scanner.
- Architectural policies must be defined and supported by the current rule engine.
- Dynamic imports and unusual runtime module-loading patterns may require additional handling.
- AI remediation can produce incorrect or incomplete suggestions.
- Passing patch verification does not prove that a change preserves all program behavior.
- AI-assisted workflows require an appropriate local model and runtime configuration.

Contributions that improve import resolution, graph analysis, false-positive control, test coverage, and safe remediation are welcome.

## Roadmap

Potential future improvements include:

- More configurable architectural policies.
- Better support for complex Python package layouts.
- Improved handling of dynamic imports.
- Additional real-world test projects and benchmarks.
- Stronger validation of proposed patches.
- Pull-request integration for automated architectural checks.

These are prospective improvements, not claims that every feature is already implemented.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
