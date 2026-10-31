TinyGuard review fixes
=====================

Changed/replaced:
- tinyguard.py
- tinyguard/graph_engine.py
- tinyguard/import_resolver.py
- tinyguard/module_resolver.py
- tinyguard/patch_verifier.py
- tinyguard/test_graph_builder.py

Added:
- tinyguard/rules.py: shared forbidden-module policy and project discovery
- test_hardening.py: regression tests for the review findings

Key behavior:
- Detects forbidden local modules named db/database even when nested in the
  project or under namespace packages.
- Understands conventional src/ layouts.
- Uses one shared entry-point/discovery policy for CLI and patch verification.
- Ignores ancestor directory names when excluding generated folders.
- Fails closed on parse/decode errors instead of silently omitting files.
- Reads Python source using encoding declarations and handles UTF-8 BOMs.
- Checks constant-string importlib.import_module(...) and __import__(...) calls.
- Avoids flagging an unrelated third-party `db` symbol, such as
  `from flask_sqlalchemy import db`.
- Uses package-over-module precedence and rejects relative imports that climb
  above the top-level package.
- Does not report success if no API entry points were discovered.

Known limits:
- Computed dynamic import names cannot be resolved statically.
- This is a name-based architectural rule, not a full detector for every
  database library or persistence layer. Configure/extend the policy for
  project-specific forbidden layers.
- The API entry-point heuristic is still intentionally simple; projects with
  unusual layouts may need explicit configuration in a future version.

Validation in this environment:
- Passing: test_hardening.py, test_graph_engine.py, test_cli.py,
  test_patch_verifier.py, test_proposal_validation.py, and compile checks.
- test_remediation.py and test_end_to_end.py call a local Ollama server/model;
  they could not be validated here because no Ollama server is available.
