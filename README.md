# X — Umbrella Repository

This repository combines multiple project repos into a single workspace using git subtrees.

## Structure

| Directory | Source | Description |
|-----------|--------|-------------|
| `api/` | [test-api](https://github.com/Advanced-Labs/test-api) | Python Flask API |
| `ui/` | [test-ui](https://github.com/Advanced-Labs/test-ui) | HTML/JS frontend |
| `common/` | [test-common](https://github.com/Advanced-Labs/test-common) | Shared utilities |

## Subtree Management

See `scripts/subtree.py --help` for sync/pull operations.

See `CLAUDE.md` for AI assistant working instructions.
