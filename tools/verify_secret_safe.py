"""Fail CI on likely hard-coded credentials without rendering matched values."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|password)\b\s*[:=]\s*['\"]([^'\"]{8,})['\"]"
)
SKIP_PARTS = frozenset({".git", "__pycache__"})
SCAN_ROOTS = (Path("src"), Path("tests"), Path("tools"), Path(".github"))


def main() -> int:
    violations: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
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
