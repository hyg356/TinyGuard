# TinyGuard

A small, dependency-free architectural linter for Python. TinyGuard builds a module dependency graph from your source code, reports forbidden dependency chains (for example, an API layer that reaches the database layer through intermediate modules), and includes an **experimental** local-LLM workflow for proposing repairs.

> **Status: early prototype.** The detection side is tested and works on real projects. The AI-remediation side is a library-level experiment: it is not connected to the command line, and its patch verification is **static only** (see [What patch verification does and does not prove](#what-patch-verification-does-and-does-not-prove)).

## What it does

- Parses every Python file with the standard-library `ast` module and builds a dependency graph (nodes are modules, edges are imports).
- Finds the **shortest chain** from each API entry point to a forbidden module, including indirect chains.
- Understands relative imports, `__init__.py` re-exports, namespace packages, and `src/` layouts.
- **Fails closed:** a file it cannot parse is reported as an analysis error rather than silently skipped.
- Optionally asks a local [Ollama](https://ollama.com/) model to propose a repair, validates the model's JSON, and checks the proposed files in a temporary copy of the project. Your original files are never modified.

## What it does not do

- It has **one built-in rule** (see [The rule](#the-rule)); policies are not yet configurable.
- It does not prove that a repair preserves program behavior.
- It does not execute your code, run your tests, or type-check anything.
- It is not a replacement for mature tools such as [Import Linter](https://github.com/seddonym/import-linter) or [Tach](https://github.com/gauge-sh/tach), which support richer contract types and configuration.

## Quick start

Requires **Python 3.10+**. There are no third-party dependencies.

```bash
git clone https://github.com/hyg356/TinyGuard.git
cd TinyGuard
python3 tinyguard.py /path/to/your/project
```

Example output for a project where `api.py` imports `logic.orders`, which imports `database`:

```text
VIOLATION: api.py: forbidden dependency chain: api -> logic.orders -> database

TinyGuard failed: 1 violation(s) found.
```

A clean project prints:

```text
TinyGuard passed: 1 API entry point(s) checked; no forbidden dependencies found.
```

**Exit codes.** `0` means no violations. Any non-zero value means violations or an analysis error. Please do not rely on the specific non-zero value yet (see [Known issues](#known-issues)).

**Import root.** Point TinyGuard at the directory that Python would treat as the import root (for example `backend/` if your code does `from app.core import ...`). A top-level `src/` directory is detected automatically.

## The rule

The current policy is a hard-coded constant in `tinyguard/rules.py`:

| Concept | Current definition |
|---|---|
| Forbidden module | Any module with a dotted component named `db` or `database` (so `db`, `app.db`, and `database.models` match; `db_utils` and `dbus` do not) |
| API entry point | Any file named `api.py`, or any file inside a directory named `api` |
| Excluded from entry points | Paths under `tests`, `test`, `docs`, `examples`, `build`, `dist` |
| Ignored when scanning | `.git`, `.venv`, `venv`, `__pycache__`, `.tox`, `.mypy_cache` (matched against the path relative to the scanned root, so a project stored under a folder named `venv` is still scanned) |

The rule is **name-based**: a module called `persistence.py` or an import of `sqlite3` is not treated as "the database layer."

## How the graph is built

1. Every non-ignored `.py` file is parsed. Any file that fails to parse or decode (syntax error, bad encoding, invalid relative import) aborts the run with an `ERROR` line.
2. For each `import` / `from ... import` statement, TinyGuard resolves the target to a project module and adds an edge. Importing `a.b.c` also adds edges to `a` and `a.b`, because Python executes those packages' `__init__.py` files.
3. Relative imports are resolved against the importing module's package; imports that climb above the top-level package are reported as errors.
4. Calls to `importlib.import_module("x")`, `import_module("x")`, and `__import__("x")` with a **string-literal** argument are followed like ordinary imports.
5. For each entry point, a breadth-first search finds the shortest path to a forbidden module.

Imports inside functions and inside `if TYPE_CHECKING:` blocks are counted as dependencies.

## AI-assisted remediation (experimental)

This feature is a Python API, not a CLI command. It needs Ollama running locally.

```bash
ollama pull qwen2.5:3b
```

```python
from tinyguard.remediation import propose_and_verify

result = propose_and_verify(
    violation="api -> logic.orders -> database",
    source_code={                      # files you choose to show the model
        "api.py": "import logic.orders\n",
        "logic/orders.py": "import database\n",
    },
    project_root="/path/to/project",
)
```

What happens:

1. The violation and the supplied source files are sent to the model (`OLLAMA_URL` and `MODEL` are constants at the top of `tinyguard/remediation.py`).
2. The model's reply must be JSON with the required fields; paths, types, and confidence are validated, and low-confidence or missing-context proposals are withheld.
3. Proposed whole-file replacements are written into a **temporary copy** of the project and re-analysed. The original project is never edited and nothing is applied automatically.

### What patch verification does and does not prove

Verification currently checks that the patched files **parse** and that the **architectural check passes**. It does **not** check behavior. Consequently, these degenerate "repairs" are all accepted today:

- replacing a function body with `return []`
- deleting the function that other files import
- renaming the function so importers break
- inlining `sqlite3` access (the rule is name-based)
- computing the module name at runtime (`importlib.import_module("data" + "base")`)

A "verified" proposal therefore means "compliant and syntactically valid," not "correct." Review every proposal by hand. Closing this gap is the top roadmap item.

Additional limits of the current verifier:

- Only **existing** `.py` files can be replaced; creating new modules (such as an extracted interface) is not supported.
- The set of files a patch may touch is not restricted to the files shown to the model.
- The check is "the whole project has no violations," not "this patch fixed the targeted violation."

## Testing

```bash
python3 -m pytest tests
```

The offline suite covers graph traversal (including cycles), transitive violations, the CLI, proposal validation, patch verification, and hardening cases (nested and namespace packages, `src/` layouts, BOM-encoded files, relative-import boundaries, literal dynamic imports).

Two checks need a running Ollama instance and are run by hand:

```bash
python3 tests/test_remediation.py
python3 tests/test_end_to_end.py
```

Passing tests show only the behavior those tests cover.

### Validation on a real project

At the time of writing, on the backend of [`full-stack-fastapi-template`](https://github.com/fastapi/full-stack-fastapi-template), TinyGuard reports the real dependency `app.api.deps -> app.core.db` plus the entry points that reach it through `deps`. To reproduce:

```bash
git clone --depth 1 https://github.com/fastapi/full-stack-fastapi-template
python3 tinyguard.py full-stack-fastapi-template/backend
grep -n "core.db" full-stack-fastapi-template/backend/app/api/deps.py
```

This needs an interpreter new enough to parse the project's syntax. Results will change as that repository changes.

## Known issues

**Detection**

- The policy is hard-coded; there is no configuration file or CLI option for rules.
- A module's **own** ancestor packages are not followed. If `shop/__init__.py` imports `database` and `shop/api.py` imports nothing, TinyGuard passes even though Python loads `database` when `shop.api` is imported.
- Computed dynamic imports (anything other than a string literal) are not analysed, and are not reported either.
- The ignore list is short. A directory such as `env/`, `node_modules/`, or `site-packages/` containing an unparsable file will abort the run; there is no `--exclude` option yet.
- Any unparsable file aborts the whole run, including files outside the API layer.
- A relative import in a top-level module (`from . import x`) is reported as an error, and the scanned root is assumed to be the import root.
- Parsing uses the running interpreter's grammar, so source written for a newer Python version fails to parse on an older one.
- Each entry point produces its own report, so one bad import can yield many `VIOLATION` lines.
- Speed: the graph builder probes the filesystem for every import prefix; a ~2,900-file repository took about 13 seconds in testing.

**Command line**

- Exit codes are ambiguous: two or more violations and "no entry points found" both exit with `2`.

**Remediation**

- See [What patch verification does and does not prove](#what-patch-verification-does-and-does-not-prove).
- A path containing a null byte can raise an unhandled exception in `verify_patch`.
- Paths such as `./a.py` and `a.py` are not normalised, so they are treated as different files.
- The model name, URL, and 180-second timeout are constants; no temperature or seed is set.
- Source files are placed in the prompt, so a malicious comment in code could attempt prompt injection. Nothing is applied automatically, which limits the impact.

## Roadmap

In rough priority order. None of these are implemented yet.

1. **Behavior checks in the verifier:** confirm that every `from m import name` still resolves, flag newly undefined names, import every module in a subprocess, and optionally run the project's tests in a sandbox. Maintain a regression corpus of known-bad patches (stubbed, deleted, renamed, inlined, dynamically imported) that the verifier must reject.
2. **Fix detection gaps:** follow a module's own ancestor packages, warn on computed dynamic imports, widen the ignore list, add `--exclude`, and correct the exit codes.
3. **Configurable rules** in `pyproject.toml` (source and forbidden module sets), plus machine-readable output.
4. **Faster graph construction** using an in-memory module index.
5. **Report the minimal set of import edges to cut** instead of one chain per entry point.
6. **Scope-constrained patches** that allow new files and restrict edits to relevant files, with a bounded feedback loop.
7. **Evaluation on real projects** with test suites, comparing repair success against a plain "linter plus general coding agent" baseline.

## Related work

- [Import Linter](https://github.com/seddonym/import-linter) and [Tach](https://github.com/gauge-sh/tach) enforce import contracts in Python.
- [DCLfix](https://arxiv.org/abs/1506.07589) recommends repairs for architectural violations found by a conformance checker.
- [SmellBench](https://arxiv.org/abs/2605.07001) evaluates LLM agents on architectural smell repair.

TinyGuard does not claim to be novel in these areas. It is a small, readable implementation used to explore how well deterministic checks can supervise local-model repairs.

## Contributing

Issues and pull requests are welcome, especially:

- real-world projects where TinyGuard gives a wrong answer (include a minimal reproduction),
- additional tests for the known issues above,
- improvements to import resolution and false-positive control.

## License

MIT. See [LICENSE](LICENSE).
