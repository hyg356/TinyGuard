# TinyGuard

**A lightweight Python architectural linter with experimental local-LLM-assisted repair suggestions.**

TinyGuard analyzes Python projects to detect forbidden architectural dependencies. It builds a module dependency graph, identifies API entry points, and reports when an API module can reach a restricted module—such as a database layer—either directly or through intermediate modules.

It also includes an experimental repair workflow that uses a locally hosted language model to propose changes. Proposed patches are checked statically in a temporary project copy and are **never applied automatically**.

> **Project status: Early prototype.** The analyzer has a deterministic test suite and has been evaluated on controlled benchmarks and a small number of real-world scenarios. The AI repair verifier checks structural compatibility, not behavioral equivalence. Review every proposed patch manually.

---

## Why TinyGuard?

Architectural boundaries are easy to violate as Python projects grow.

For example, an API module may be intended to communicate with the application logic layer rather than accessing the database directly. That dependency can appear harmless at first, but it creates tighter coupling and makes the architecture harder to maintain.

The violation may also be indirect:

```text
api
 └── logic.orders
      └── database
```

A simple search for database imports inside API files would miss this transitive dependency.

TinyGuard analyzes the dependency graph to detect these paths and reports the shortest forbidden dependency chain it finds for each entry point.

## Features

### Static architectural analysis

- Automatically identifies API entry points using configurable path conventions.
- Builds a module dependency graph from Python source.
- Detects direct and transitive dependencies on forbidden modules.
- Follows relative imports and package re-exports.
- Accounts for ancestor package initialization through `__init__.py`.
- Handles namespace packages and common `src/` layouts.
- Detects literal dynamic imports through `importlib.import_module()` and `__import__()`.
- Reports unresolved computed dynamic imports as warnings.
- Fails closed when a Python file cannot be parsed or decoded.

### Configurable policies

Define forbidden modules, entry points, and excluded directories in `tinyguard.toml` or in `pyproject.toml` under `[tool.tinyguard]`.

### Multiple output formats

- Human-readable terminal output.
- JSON output for programmatic use.
- GitHub Actions error annotations.

### Experimental AI-assisted repair

TinyGuard can ask a locally hosted language model to propose a repair for a detected violation.

The workflow:

1. Selects relevant project files based on the dependency chain and surrounding imports.
2. Sends the selected context to a local model.
3. Validates the model's structured proposal and restricts edits to files it was shown.
4. Applies the proposed changes in a temporary copy of the project.
5. Runs static verification against the patched copy.
6. Writes a proposal and diff for human review.

The original project is not modified, and proposals are never applied automatically.

---

## Quick start

### Requirements

- Python 3.10 or newer.
- No third-party dependencies are required for the core analyzer.
- Python 3.10 requires `tomli` if you want to read TOML configuration files.

Clone the repository:

```bash
git clone https://github.com/hyg356/TinyGuard.git
cd TinyGuard
```

Run TinyGuard against a Python project:

```bash
python3 tinyguard.py /path/to/your/project
```

Example output:

```text
VIOLATION: api.py: forbidden dependency chain: api -> logic.orders -> database

TinyGuard failed: 1 violation(s) found.
```

A project without detected violations produces a passing result.

### Exit codes

| Exit code | Meaning |
|---|---|
| `0` | Analysis completed; no forbidden dependency chain was found. |
| `1` | One or more forbidden dependency chains were found. |
| `2` | TinyGuard could not complete the requested analysis, for example because of invalid arguments, configuration errors, parsing errors, or no recognized entry points. |

An exit code of `2` should not be interpreted as a clean analysis. Check the diagnostic output.

## Output formats

```bash
python3 tinyguard.py /path/to/project --format json
```

```bash
python3 tinyguard.py /path/to/project --format github
```

The JSON format is intended for other tools and scripts. The GitHub format emits workflow annotations that can appear in pull request checks.

---

## How dependency detection works

TinyGuard performs static analysis of Python source files.

At a high level:

```text
Python project
      |
      v
Discover Python modules
      |
      v
Resolve imports
      |
      v
Build dependency graph
      |
      v
Identify API entry points
      |
      v
Traverse dependency paths
      |
      v
Check against forbidden modules
      |
      v
Report violations
```

### Entry-point discovery

By default, TinyGuard recognizes:

- Files named `api.py`.
- Files inside an `api/` directory.
- Files inside `routes/`, `routers/`, `views/`, or `endpoints/` directories.

Directories such as `tests/`, `test/`, `docs/`, `examples/`, `build/`, and `dist/` are excluded from default entry-point discovery.

These conventions can be overridden through configuration.

### Forbidden modules

The default policy targets database-related module names, including `db` and `database`, as well as configured database drivers and ORM modules.

Matching is based on module components rather than arbitrary substrings. For example, a component named `db` matches `app.db`, but does not match `db_utils`.

The forbidden-module list can be customized for a project's architecture.

### Dependency chains

TinyGuard traverses the dependency graph to find paths from API entry points to forbidden modules.

For example:

```text
api.py
  |
  v
logic.orders
  |
  v
database
```

The reported chain makes the architectural violation easier to locate than a simple list of imports.

---

## Configuration

TinyGuard supports `tinyguard.toml` at the project root or a `[tool.tinyguard]` section in `pyproject.toml`.

Example:

```toml
[tool.tinyguard]
forbidden = ["db", "database", "redis_store"]
entrypoints = ["**/api.py", "**/api/**", "**/handlers/**"]
non_application_dirs = ["tests", "docs"]
ignored_dirs = [".git", ".venv", "venv", "__pycache__", "node_modules"]
```

Configuration lists replace the corresponding defaults. Include any default entries you still want to retain.

Unknown configuration keys are treated as errors rather than silently ignored.

---

## AI-assisted repair

TinyGuard's repair workflow is experimental and requires [Ollama](https://ollama.com/) running locally.

The default model is `qwen2.5:3b`.

Pull the model:

```bash
ollama pull qwen2.5:3b
```

Generate repair proposals:

```bash
python3 tinyguard.py /path/to/project --propose --out tinyguard-proposals
```

For each violation, TinyGuard selects relevant source files automatically. The model is asked to return a structured proposal describing the files to change and the repair strategy.

The proposed changes are checked in a temporary copy of the project. The workflow produces:

```text
tinyguard-proposals/
├── proposal.json
└── changes.diff
```

The proposal is intended for inspection and review—not automatic application.

### What the verifier checks

A proposed patch is accepted only if it passes the following static checks:

1. The modified source files parse and decode successfully.
2. No forbidden dependency chain remains from recognized API entry points.
3. Previously defined public top-level functions, classes, and public methods are preserved.
4. Functions that performed meaningful work have not been replaced with trivial implementations.
5. Cross-module references to module attributes still resolve to names bound by the patched module.
6. The patch introduces no new unresolved dynamic imports.

The verifier also rejects proposals with insufficient context, low confidence, invalid output, or edits to files outside the set provided to the model.

### Important limitations

These checks do **not** prove that a patch preserves program behavior.

For example, a function may still exist and return a value of the same general shape while producing incorrect results. TinyGuard does not execute the application or compare its runtime behavior before and after a patch.

A proposal marked `verified` therefore means that it passed TinyGuard's structural checks—not that the repair is behaviorally correct.

Run the project's own tests and review the diff before considering any proposed change.

---

## Benchmarking and evaluation

TinyGuard includes a benchmark suite intended to evaluate detection behavior, compare its results with an established tool, and test selected real-world scenarios.

See [`benchmark/README.md`](benchmark/README.md) for the benchmark methodology, commands, result files, and limitations.

### Current evaluation coverage

| Evaluation | Coverage |
|---|---|
| Standard benchmark | 100 controlled cases across five import-pattern categories, with 50 violation and 50 safe cases. |
| Head-to-head benchmark | Compares TinyGuard with Import Linter on a shared core test corpus, with a separate track for literal dynamic imports. |
| Real-world discovery | Attempts analysis on 10 public Python repositories. |
| Real-world fault injection | Two controlled dependency violations injected into a FastAPI-based project; both expected chains were detected. |
| Mutation testing | A preliminary scaffold exists; a completed mutation score has not yet been established. |

### Interpreting the results

The standard benchmark uses controlled, hand-authored fixtures. It demonstrates behavior on the tested patterns, not general accuracy across arbitrary Python projects.

The real-world discovery experiment distinguishes between clean results, violations, errors, and repositories with no recognized API entry points. A repository with no recognized entry points has not received a meaningful clean analysis.

The fault-injection experiment tests whether TinyGuard detects two deliberately introduced dependency paths in one real project. It is useful evidence of integration behavior, but it is not a broad real-world accuracy study.

The head-to-head benchmark reports per-case outcomes and aggregate metrics. Comparative claims should be based on the generated results rather than assumed from the tools' feature sets.

---

## Running the tests

Install `pytest`:

```bash
python3 -m pip install pytest
```

On Python 3.10, install `tomli` if configuration tests require TOML parsing:

```bash
python3 -m pip install tomli
```

Run the test suite:

```bash
python3 -m pytest -q
```

The suite is designed to run offline. Tests requiring a live Ollama model are skipped automatically when the local service is unavailable.

The tests cover dependency graph construction, import resolution, CLI behavior, configuration, entry-point discovery, proposal validation, patch verification, and end-to-end behavior.

---

## Project structure

```text
TinyGuard/
├── tinyguard.py
├── tinyguard/
│   ├── module_resolver.py
│   ├── import_resolver.py
│   ├── graph_engine.py
│   └── remediation.py
├── tests/
├── benchmark/
│   ├── README.md
│   ├── results/
│   ├── head_to_head/
│   ├── mutation/
│   └── real_world/
├── examples/
├── pytest.ini
├── .gitignore
├── LICENSE
└── README.md
```

The tree above highlights the main project areas; consult the repository for the complete file list.

---

## Known limitations

- **Heuristic entry-point discovery:** Projects with unconventional layouts may need custom entry-point patterns.
- **Static import analysis:** Imports performed through `exec`, `eval`, or other unsupported dynamic mechanisms may not be detected.
- **Name-based policy:** A database dependency through a library not included in the forbidden policy may go unnoticed.
- **One reported chain per entry point:** The current reporting behavior focuses on the shortest discovered forbidden chain rather than enumerating every possible path.
- **Static repair verification:** Passing the verifier does not establish behavioral correctness.
- **Public interface preservation:** Legitimate refactors that rename or move public symbols may be rejected.
- **Analysis performance:** The analyzer parses project files and is not yet optimized for very large repositories.
- **Local model quality:** Repair usefulness depends on the model, available context, and complexity of the violation.

---

## Roadmap

Potential next steps include:

1. Add optional behavioral verification by running selected tests against a patched temporary project.
2. Report every reachable forbidden module and identify the minimal set of dependency edges responsible for violations.
3. Improve import resolution and reduce false positives across unusual Python project layouts.
4. Add configurable severity levels and exclusion rules.
5. Improve performance on large repositories.
6. Evaluate repair quality systematically against a broader set of real architectural violations and compare it with unverified LLM-generated repairs.

---

## Related work

TinyGuard operates in an established area of software architecture enforcement. Related projects include:

- [Import Linter](https://github.com/seddonym/import-linter) — checks Python import contracts, including layered and forbidden dependencies.
- [Tach](https://github.com/gauge-sh/tach) — enforces module dependency boundaries and architectural constraints.

TinyGuard does not claim to introduce dependency graph analysis or architectural linting as new concepts. Its focus is on combining lightweight Python dependency analysis with an experimental local-model repair workflow and static verification of proposed patches.

---

## Contributing

Bug reports, minimal reproductions, and additional test cases are welcome.

Particularly useful contributions include:

- Import-resolution edge cases.
- Projects where entry-point discovery is incorrect.
- False positives or missed dependency chains.
- Repair proposals that pass structural verification but break behavior.
- Reproducible benchmark cases from real Python projects.

When reporting a detection issue, include a minimal project structure and the expected dependency behavior.

## License

TinyGuard is released under the MIT License. See [`LICENSE`](LICENSE).
