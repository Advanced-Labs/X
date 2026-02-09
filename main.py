"""Read and parse gitignore templates from the gitignore submodule."""

import os
from pathlib import Path

SUBMODULE_DIR = Path(__file__).parent / "submodules" / "gitignore"


def read_gitignore_template(language: str) -> str:
    """Read a .gitignore template file for the given language."""
    template_path = SUBMODULE_DIR / f"{language}.gitignore"
    if not template_path.exists():
        raise FileNotFoundError(f"No gitignore template found for '{language}'")
    return template_path.read_text()


def parse_patterns(content: str) -> list[str]:
    """Extract active (non-comment, non-empty) patterns from gitignore content."""
    return [
        line
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def main():
    template = read_gitignore_template("Python")
    patterns = parse_patterns(template)

    print(f"Python .gitignore template loaded from: {SUBMODULE_DIR}")
    print(f"Total lines: {len(template.splitlines())}")
    print(f"Active patterns: {len(patterns)}")
    print()
    print("First 10 active patterns:")
    for pattern in patterns[:10]:
        print(f"  {pattern}")


if __name__ == "__main__":
    main()
