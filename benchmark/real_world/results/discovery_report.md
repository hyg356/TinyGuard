# TinyGuard Real-World Repository Discovery

Generated: 2026-11-01T07:08:03.105924+00:00

## Environment

- Python: 3.14.0
- Platform: macOS-26.5.2-arm64-arm-64bit-Mach-O
- Repositories attempted: 10

## Results

| Repository | Clone status | Python files | TinyGuard | Runtime (s) | Commit |
|---|---|---:|---|---:|---|
| fastapi | already_present | 1219 | NO_ENTRYPOINTS | 3.839 | 45cb2252c737 |
| starlette | already_present | 84 | NO_ENTRYPOINTS | 0.819 | 2745bbc5afa2 |
| flask | already_present | 83 | NO_ENTRYPOINTS | 0.696 | 49943b5a9441 |
| requests | already_present | 37 | CLEAN | 0.465 | 3c7baaa05ab4 |
| sqlmodel | already_present | 334 | NO_ENTRYPOINTS | 1.853 | 462b59d9cd1c |
| sqlalchemy | already_present | 676 | CLEAN | 19.109 | c6494316e0b4 |
| pydantic | already_present | 3150 | NO_ENTRYPOINTS | 25.164 | 132df974eaf9 |
| httpx | already_present | 60 | NO_ENTRYPOINTS | 0.418 | b5addb64f016 |
| click | already_present | 91 | NO_ENTRYPOINTS | 0.773 | 2247b35ea1c4 |
| redis-py | already_present | 337 | NO_ENTRYPOINTS | 6.669 | 05712b2f0995 |

## Summary

- Clean classifications: 2
- Violation classifications: 0
- Errors: 0
- Repositories without API entry points: 8

## Important interpretation limits

This is a repository discovery and baseline execution run, not a
scored accuracy benchmark. A repository's baseline result is not
ground truth until its architecture and intended policy are reviewed.
Direct and transitive controlled injection experiments are reported
separately. Repositories without suitable architectural boundaries
are not included in the default-policy accuracy assessment.

## Reproduction

Run `python3 benchmark/real_world/run_discovery.py` from the project root.