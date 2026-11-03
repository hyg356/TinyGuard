# TinyGuard Real-World Repository Discovery

Generated: 2026-11-03T09:00:34.626287+00:00

## Environment

- Python: 3.14.0
- Platform: macOS-26.5.2-arm64-arm-64bit-Mach-O
- Repositories attempted: 10

## Results

| Repository | Clone status | Python files | TinyGuard | Runtime (s) | Commit |
|---|---|---:|---|---:|---|
| fastapi | cloned | 1219 | NO_ENTRYPOINTS | 20.34 | 5cb6272ed7e3 |
| starlette | cloned | 84 | NO_ENTRYPOINTS | 3.9 | 0f08970e5cce |
| flask | cloned | 83 | NO_ENTRYPOINTS | 3.54 | 49943b5a9441 |
| requests | cloned | 37 | CLEAN | 0.98 | 3c7baaa05ab4 |
| sqlmodel | cloned | 334 | NO_ENTRYPOINTS | 4.619 | 6a939fb04074 |
| sqlalchemy | cloned | 678 | CLEAN | 66.712 | 57ddc05ffafe |
| pydantic | cloned | 3155 | ERROR | 180.012 | 577aa83f5075 |
| httpx | cloned | 60 | NO_ENTRYPOINTS | 0.69 | b5addb64f016 |
| click | cloned | 91 | NO_ENTRYPOINTS | 2.4 | 2247b35ea1c4 |
| redis-py | cloned | 339 | NO_ENTRYPOINTS | 18.998 | 58bc34e51e20 |

## Summary

- Clean classifications: 2
- Violation classifications: 0
- Errors: 1
- Repositories without API entry points: 7

## Important interpretation limits

This is a repository discovery and baseline execution run, not a
scored accuracy benchmark. A repository's baseline result is not
ground truth until its architecture and intended policy are reviewed.
Direct and transitive controlled injection experiments are reported
separately. Repositories without suitable architectural boundaries
are not included in the default-policy accuracy assessment.

## Reproduction

Run `python3 benchmark/real_world/run_discovery.py` from the project root.