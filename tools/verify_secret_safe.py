"""Fail CI on likely hard-coded credentials without rendering matched values."""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ASSIGNMENT = re.compile(
    r"(?i)(?<![a-z0-9_])['\"]?(?:[a-z0-9]+_)*(?:api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|password)['\"]?\s*[:=]\s*(?!(?:['\"])?(?:\$\{[^}]+\}|secret://[^\s'\",;)\]}#]+)(?:['\"])?(?=\s|$|[, ;)\]}#]))(?:(?:[fFrR]{0,2})?['\"][^'\"]{8,}['\"]|[^\s#'\"]{8,})"
)


def tracked_files() -> tuple[Path, ...]:
    """Return every Git-tracked path without traversing ignored workspace state."""
    result = subprocess.run(
        ("git", "ls-files", "-z"),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return tuple(Path(name.decode("utf-8")) for name in result.stdout.split(b"\0") if name)


def main() -> int:
    violations: list[Path] = []
    for path in tracked_files():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if ASSIGNMENT.search(text):
            violations.append(path)
    if violations:
        for path in violations:
            print(f"secret-safe violation: {path}")
        return 1
    print("secret-safe scan passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
