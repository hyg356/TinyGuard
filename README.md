# TinyGuard

**An automated architectural linter for Python that catches forbidden dependencies before they reach your codebase.**

TinyGuard uses Python's Abstract Syntax Tree (AST) to detect architectural violations and returns CI-friendly exit codes, making it suitable for automated pull-request checks.

## Features

- **AST-based analysis:** Inspects actual Python import statements rather than matching text in comments or strings.
- **Architectural rule enforcement:** Currently flags imports involving forbidden `db` and `database` module names inside directories named `api`.
- **Recursive scanning:** Discovers Python files throughout a repository while excluding common generated and virtual-environment directories.
- **CI-friendly:** Returns a nonzero exit code when violations are detected, allowing CI pipelines to fail automatically.

## Getting Started

### Requirements

- Python 3.9 or later.

### Usage

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
cd TinyGuard
```

Run TinyGuard against a Python repository:

```bash
python3 tinyguard.py /path/to/your/project
```

To check the current directory:

```bash
python3 tinyguard.py .
```

### Example

Given a project containing:

```python
# app/api/routes.py
from app.database import connect
```

TinyGuard reports a violation because API code imports a forbidden database module.

```text
VIOLATION: app/api/routes.py:1: API code imports forbidden module 'app.database'

TinyGuard failed: 1 issue(s) found.
```

The exact output depends on the repository structure and detected import.

## Current Scope and Limitations

This is an early MVP. It currently enforces one hard-coded architectural rule and scans Python files inside directories named `api`.

It does not yet perform general dependency-graph analysis, support configurable rules, or use AI for remediation.

## Roadmap

-  Add automated tests for import detection and edge cases.
-  Integrate with GitHub Actions to check pull requests.
-  Build dependency-graph analysis for transitive architectural violations.
-  Support configurable architectural rules.
-  Explore optional local AI-assisted remediation.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
