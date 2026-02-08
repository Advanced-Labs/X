#!/usr/bin/env python3
"""
Umbrella Repository -- Subtree Manager

Manages git subtree operations: sync (push to source repos), pull (update from
source repos), and status checks. Reads configuration from .subtrees.json.

IMPORTANT FOR AI ASSISTANTS:
  You should NOT need to run this script. The human operator handles subtree
  sync/pull operations. Your job is to edit files and commit to the umbrella
  repo normally. See CLAUDE.md for full instructions.

Usage:
    python scripts/subtree.py status                    Show subtree status
    python scripts/subtree.py sync [--prefix NAME]      Push changes to source repos
    python scripts/subtree.py pull [--prefix NAME]      Pull updates from source repos
    python scripts/subtree.py --help                    Show this help

Options:
    --prefix NAME    Target a specific subtree (e.g., --prefix api). Omit for all.
    --branch NAME    Target branch on source repos. Defaults to current umbrella branch.
    --dry-run        Show what would happen without executing.
    --help           Show detailed help with examples and workflow guidance.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / ".subtrees.json"
LOG_DIR = REPO_ROOT / "logs"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg, level="INFO"):
    """Print a message and append to the log file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)

    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"subtree-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_git(*args, dry_run=False, capture=False):
    """Run a git command from the repo root. Returns (returncode, stdout)."""
    cmd = ["git"] + list(args)
    display_cmd = " ".join(cmd)

    if dry_run:
        log(f"[DRY RUN] Would execute: {display_cmd}")
        return 0, ""

    log(f"Executing: {display_cmd}")
    result = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=300
    )

    if capture:
        return result.returncode, result.stdout.strip()

    if result.stdout.strip():
        # Truncate verbose output to save context window
        lines = result.stdout.strip().split("\n")
        if len(lines) > 30:
            print(f"  (showing first 15 and last 5 of {len(lines)} lines)")
            for line in lines[:15]:
                print(f"  {line}")
            print(f"  ... ({len(lines) - 20} lines omitted) ...")
            for line in lines[-5:]:
                print(f"  {line}")
        else:
            for line in lines:
                print(f"  {line}")

    if result.returncode != 0 and result.stderr.strip():
        for line in result.stderr.strip().split("\n"):
            print(f"  [stderr] {line}")

    return result.returncode, result.stdout.strip()


def load_manifest():
    """Load and return the .subtrees.json manifest."""
    if not MANIFEST_PATH.exists():
        log(f"ERROR: Manifest not found at {MANIFEST_PATH}", "ERROR")
        sys.exit(1)
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_current_branch():
    """Get the current git branch name."""
    _, branch = run_git("rev-parse", "--abbrev-ref", "HEAD", capture=True)
    return branch


def get_subtrees(manifest, prefix_filter=None):
    """Get subtrees from manifest, optionally filtered by prefix."""
    subtrees = manifest["subtrees"]
    if prefix_filter:
        if prefix_filter not in subtrees:
            log(f"ERROR: Unknown subtree prefix '{prefix_filter}'. "
                f"Valid: {', '.join(subtrees.keys())}", "ERROR")
            sys.exit(1)
        return {prefix_filter: subtrees[prefix_filter]}
    return subtrees


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_status(manifest, prefix_filter=None):
    """Show status of all subtrees."""
    subtrees = get_subtrees(manifest, prefix_filter)
    branch = get_current_branch()

    print(f"\n{'=' * 60}")
    print(f"  UMBRELLA SUBTREE STATUS")
    print(f"  Branch: {branch}")
    print(f"{'=' * 60}\n")

    for name, info in subtrees.items():
        prefix = info["prefix"]
        prefix_path = REPO_ROOT / prefix

        print(f"  [{name}]")
        print(f"    Prefix:   {prefix}/")
        print(f"    Source:   {info['remote_url']}")
        print(f"    Remote:   {info['remote_name']}")
        print(f"    Upstream: {info['upstream_branch']}")

        if prefix_path.exists():
            # Count files
            file_count = sum(1 for _ in prefix_path.rglob("*") if _.is_file())
            print(f"    Files:    {file_count}")

            # Check for uncommitted changes in this prefix
            rc, diff_out = run_git("diff", "--stat", "--", f"{prefix}/", capture=True)
            if diff_out:
                print(f"    Status:   HAS UNCOMMITTED CHANGES")
            else:
                rc, staged = run_git("diff", "--cached", "--stat", "--", f"{prefix}/", capture=True)
                if staged:
                    print(f"    Status:   HAS STAGED CHANGES")
                else:
                    print(f"    Status:   Clean")
        else:
            print(f"    Status:   MISSING (directory not found)")
        print()

    print(f"{'=' * 60}")
    print()


def cmd_sync(manifest, prefix_filter=None, branch=None, dry_run=False):
    """Push umbrella changes to source repos."""
    subtrees = get_subtrees(manifest, prefix_filter)
    current_branch = get_current_branch()
    target_branch = branch or current_branch

    print(f"\n{'=' * 60}")
    print(f"  SUBTREE SYNC (push to source repos)")
    print(f"  Umbrella branch: {current_branch}")
    print(f"  Target branch on source repos: {target_branch}")
    if dry_run:
        print(f"  *** DRY RUN -- no changes will be made ***")
    print(f"{'=' * 60}\n")

    results = {}
    for name, info in subtrees.items():
        log(f"Syncing '{name}' -> {info['remote_url']} (branch: {target_branch})")

        rc, _ = run_git(
            "subtree", "push",
            f"--prefix={info['prefix']}",
            info["remote_name"],
            target_branch,
            dry_run=dry_run,
        )

        results[name] = "OK" if rc == 0 else "FAILED"
        if rc != 0:
            log(f"FAILED to sync '{name}'. Check output above.", "ERROR")
        else:
            log(f"Successfully synced '{name}'.")
        print()

    # Summary
    print(f"{'=' * 60}")
    print(f"  SYNC RESULTS:")
    for name, status in results.items():
        marker = "+" if status == "OK" else "X"
        print(f"    [{marker}] {name}: {status}")
    print(f"{'=' * 60}")

    # Reminders
    print(f"""
  ============================================================
  REMINDERS:
  - Source repos now have branch '{target_branch}' with your changes.
  - Open PRs on each source repo to merge into their main branch.
  - After merging PRs, run: python scripts/subtree.py pull
    to sync the merged state back into this umbrella repo.
  - Do NOT forget the pull step, or umbrella main will drift.
  ============================================================
""")


def cmd_pull(manifest, prefix_filter=None, branch=None, dry_run=False):
    """Pull updates from source repos into umbrella."""
    subtrees = get_subtrees(manifest, prefix_filter)

    print(f"\n{'=' * 60}")
    print(f"  SUBTREE PULL (update from source repos)")
    if dry_run:
        print(f"  *** DRY RUN -- no changes will be made ***")
    print(f"{'=' * 60}\n")

    results = {}
    for name, info in subtrees.items():
        target_branch = branch or info["upstream_branch"]
        log(f"Pulling '{name}' <- {info['remote_url']} (branch: {target_branch})")

        rc, _ = run_git(
            "subtree", "pull",
            f"--prefix={info['prefix']}",
            info["remote_name"],
            target_branch,
            "--squash",
            dry_run=dry_run,
        )

        results[name] = "OK" if rc == 0 else "FAILED"
        if rc != 0:
            log(f"FAILED to pull '{name}'. Check output above.", "ERROR")
        else:
            log(f"Successfully pulled '{name}'.")
        print()

    # Summary
    print(f"{'=' * 60}")
    print(f"  PULL RESULTS:")
    for name, status in results.items():
        marker = "+" if status == "OK" else "X"
        print(f"    [{marker}] {name}: {status}")
    print(f"{'=' * 60}")

    print(f"""
  ============================================================
  REMINDERS:
  - Review the pulled changes with: git log --oneline -5
  - If there are merge conflicts, resolve them before continuing.
  - Push the umbrella after pulling: git push
  ============================================================
""")


def show_help():
    """Show detailed help text."""
    print("""
==============================================================
           UMBRELLA SUBTREE MANAGER -- HELP
==============================================================

OVERVIEW:
  This repo is an "umbrella" that combines multiple source repos as
  subtrees. Each subdirectory (api/, ui/, common/) maps to its own
  GitHub repo. Changes flow through the umbrella and get synced back.

COMMANDS:

  status [--prefix NAME]
      Show the state of each subtree: source repo, branch, file count,
      and whether there are uncommitted changes.

  sync [--prefix NAME] [--branch BRANCH] [--dry-run]
      Push changes FROM this umbrella TO the source repos.
      Creates/updates the specified branch on each source repo.
      Default branch: current umbrella branch name.

  pull [--prefix NAME] [--branch BRANCH] [--dry-run]
      Pull changes FROM source repos INTO this umbrella.
      Default branch: each subtree's configured upstream_branch.

WORKFLOW:
  1. AI or human edits files in the umbrella, commits, pushes.
  2. Operator runs: python scripts/subtree.py sync
     -> This pushes changes to branches on source repos.
  3. Operator opens PRs on source repos and merges them.
  4. Operator runs: python scripts/subtree.py pull
     -> This syncs the merged state back into the umbrella.

FOR AI ASSISTANTS:
  You do NOT run this script. You work on files normally:
    - Edit any file in api/, ui/, common/, or root
    - Stage and commit with regular git commands
    - Push to the umbrella repo
  The human operator handles subtree sync/pull. See CLAUDE.md.

CONTEXT WINDOW TIPS (for AI):
  - Use 'git diff --stat' instead of full 'git diff' for overviews
  - Use 'git log --oneline -N' instead of verbose log
  - Avoid 'git status -uall' on large repos
  - When reading files, read only what you need (specific paths)
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        if not args:
            print(__doc__)
        else:
            show_help()
        return

    command = args[0]
    prefix_filter = None
    branch = None
    dry_run = "--dry-run" in args

    # Parse --prefix and --branch
    for i, arg in enumerate(args):
        if arg == "--prefix" and i + 1 < len(args):
            prefix_filter = args[i + 1]
        if arg == "--branch" and i + 1 < len(args):
            branch = args[i + 1]

    manifest = load_manifest()

    if command == "status":
        cmd_status(manifest, prefix_filter)
    elif command == "sync":
        cmd_sync(manifest, prefix_filter, branch, dry_run)
    elif command == "pull":
        cmd_pull(manifest, prefix_filter, branch, dry_run)
    else:
        log(f"Unknown command: {command}. Use --help for usage.", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
