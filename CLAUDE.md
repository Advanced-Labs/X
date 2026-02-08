# Umbrella Repository — AI Working Instructions

## What This Repo Is

This is an **umbrella repository** that combines multiple independent repos into one workspace using git subtrees. Each top-level directory maps to a separate source repo:

| Directory | Source Repo | Description |
|-----------|------------|-------------|
| `api/` | Advanced-Labs/test-api | Python Flask API (users, items endpoints) |
| `ui/` | Advanced-Labs/test-ui | HTML/JS frontend |
| `common/` | Advanced-Labs/test-common | Shared Python utilities, config, constants |

The mapping is defined in `.subtrees.json` at the repo root.

## How to Work in This Repo

**You work normally.** Edit files, commit, push. That's it.

The subtree structure is invisible to you — `api/`, `ui/`, and `common/` are just directories with regular files. There is nothing special you need to do.

### Do This
- Edit any file in any directory as needed
- Commit changes with clear, descriptive messages
- Push to the umbrella repo when your work is done
- Reference cross-directory dependencies naturally (e.g., `api/` code can import from `common/`)

### Do NOT Do This
- **NEVER** run `git subtree` commands (push, pull, split, add). The human operator handles subtree sync.
- **NEVER** modify `.subtrees.json` unless explicitly asked to
- **NEVER** try to push to the individual source repos (test-api, test-ui, test-common)
- **NEVER** add or remove git remotes

## Commit Guidelines

When committing changes that span multiple directories, use a single commit with a clear message indicating which areas are affected:

```
Update user validation across API and common utils

- api/routes/users.py: Add email validation to create endpoint
- common/utils.py: Add validate_email helper
```

This helps the operator know which subtrees need syncing.

## Git — Context Window Optimization

Git output can consume a lot of your context window. Use concise commands:

| Instead of | Use |
|-----------|-----|
| `git diff` (full output) | `git diff --stat` for overview, then `git diff -- path/to/file` for specific files |
| `git log` (verbose) | `git log --oneline -10` |
| `git status` (large repos) | `git status -s` (short format) |
| `git show <commit>` | `git show <commit> --stat` first, then specific files if needed |

**When reviewing changes before commit:** use `git diff --stat` to see which files changed, then read only the files you need to verify. Do not dump the full diff of all files.

## Project Structure

```
.
├── CLAUDE.md              ← You are here (AI instructions)
├── .subtrees.json         ← Subtree manifest (do not modify)
├── .gitignore
├── README.md
├── scripts/
│   └── subtree.py         ← Subtree manager (operator use only)
├── logs/                  ← Operation logs (gitignored)
├── api/                   ← Python Flask API
│   ├── app.py             ← Entry point, registers blueprints
│   ├── common_ref.py      ← Bridge to common/ utilities
│   ├── requirements.txt
│   └── routes/
│       ├── users.py       ← User endpoints
│       └── items.py       ← Item endpoints
├── ui/                    ← Frontend
│   ├── index.html         ← Main page
│   ├── styles.css         ← Styling
│   ├── api.js             ← API client
│   └── app.js             ← App logic
└── common/                ← Shared utilities
    ├── __init__.py         ← Package exports
    ├── config.py           ← App config (version, URLs)
    ├── utils.py            ← Helpers (formatting, validation)
    └── constants.py        ← Constants (HTTP codes, error msgs)
```

## Cross-Directory Dependencies

- `api/` uses `common/` for shared config and utilities (via `api/common_ref.py`)
- `ui/` calls `api/` endpoints (API_BASE in `ui/api.js`)
- `common/` is standalone — it should not import from `api/` or `ui/`

When making changes that affect interfaces between directories (e.g., changing an API endpoint that the UI calls, or changing a utility signature that the API uses), update all affected files in the same commit.

## Scripts Reference

There is one management script at `scripts/subtree.py`. **This is for the human operator, not for you.** But if you're curious about the subtree setup, you can run:

```
python scripts/subtree.py --help
```

This will explain the overall workflow without executing anything.
