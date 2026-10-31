# TinyGuard Real-World Repository Discovery

Generated: 2026-10-31T14:59:52.618445+00:00

## Environment

- Python: 3.14.0
- Platform: macOS-26.5.2-arm64-arm-64bit-Mach-O
- Repositories attempted: 10

## Results

| Repository | Clone status | Python files | TinyGuard | Runtime (s) | Commit |
|---|---|---:|---|---:|---|
| fastapi | cloned | 1219 | UNCLASSIFIED | 9.5 | 45cb2252c737 |
| starlette | cloned | 84 | UNCLASSIFIED | 1.811 | 2745bbc5afa2 |
| flask | cloned | 83 | UNCLASSIFIED | 1.62 | 49943b5a9441 |
| requests | cloned | 37 | CLEAN | 0.9 | 3c7baaa05ab4 |
| sqlmodel | cloned | 334 | UNCLASSIFIED | 2.214 | 462b59d9cd1c |
| sqlalchemy | cloned | 676 | CLEAN | 39.593 | c6494316e0b4 |
| pydantic | cloned | 3150 | UNCLASSIFIED | 49.076 | 824cf7bfbfdc |
| httpx | cloned | 60 | UNCLASSIFIED | 1.277 | b5addb64f016 |
| click | cloned | 91 | UNCLASSIFIED | 2.01 | 2247b35ea1c4 |
| redis-py | cloned | 337 | UNCLASSIFIED | 14.825 | 05712b2f0995 |

## Summary

- Clean classifications: 2
- Violation classifications: 0
- Errors: 0
- Unclassified: 8

## Important interpretation limits

This is a repository discovery and baseline execution run, not a
scored accuracy benchmark. A repository's baseline result is not
ground truth until its architecture and intended policy are reviewed.
The direct and transitive violation injection experiments have not
yet been performed. Repositories without suitable architectural
boundaries must be excluded or replaced.

## Reproduction

Run `python3 benchmark/real_world/run_discovery.py` from the project root.