# TinyGuard head-to-head benchmark

## Policy

`app.api` must not depend directly or transitively on `app.database`.

## Method

- Hand-authored fixture projects; each case has an explicit expected label.
- Core comparison uses ordinary Python imports supported by both tools.
- Dynamic-import cases are reported separately as TinyGuard extensions.
- Tool errors are counted separately and excluded from the valid-prediction accuracy denominator.
- Runtime is measured per fixture; this is not a large-repository performance test.

## Results

| Tool | Scope | Cases | TP | FP | TN | FN | Errors | Precision | Recall | F1 | Accuracy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tinyguard | core | 24 | 12 | 0 | 12 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| import_linter | core | 24 | 12 | 12 | 0 | 0 | 0 | 0.500 | 1.000 | 0.667 | 0.500 |
| tinyguard | tinyguard_extension | 2 | 2 | 0 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |

## Interpretation limits

This is a controlled conformance benchmark, not a representative sample of all Python repositories. It tests a specific architectural policy and a curated set of import patterns. It does not establish general real-world accuracy, security, or performance at scale.

Import Linter and TinyGuard may differ in import-resolution semantics. Review individual disagreements and diagnostic files before drawing conclusions.

## Reproduction

Run `python3 benchmark/head_to_head/run_benchmark.py` from the repository root.
