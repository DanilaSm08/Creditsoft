"""Validate Conventional Commit subjects locally and in CI."""

import re
import subprocess
import sys
from pathlib import Path

PATTERN = re.compile(
    r"^(feat|fix|docs|test|chore|ci|build|refactor|perf|style)(\([a-z0-9_-]+\))?!?: .{3,100}$"
)


def valid(subject):
    return bool(PATTERN.fullmatch(subject)) or subject.startswith("Merge ")


def main():
    if len(sys.argv) == 2:
        subjects = [Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()[0]]
    else:
        subjects = subprocess.check_output(
            ["git", "log", "--format=%s", "--no-merges"], text=True, encoding="utf-8"
        ).splitlines()
    invalid = [subject for subject in subjects if not valid(subject)]
    if invalid:
        print("Invalid commit subjects:", *invalid, sep="\n")
        return 1
    print(f"Conventional Commits: {len(subjects)} valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
