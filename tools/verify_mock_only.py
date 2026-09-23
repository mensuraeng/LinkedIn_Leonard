"""Fail CI if local-only source acquires transports or real URLs."""
from __future__ import annotations

import ast
from pathlib import Path
import sys

FORBIDDEN_IMPORTS = frozenset({"http", "urllib", "socket", "requests", "oauthlib", "selenium"})
SOURCE_ROOT = Path("src")


def violations(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    findings: list[str] = []
    blocked = imported.intersection(FORBIDDEN_IMPORTS)
    if blocked:
        findings.append(f"forbidden transport import(s): {', '.join(sorted(blocked))}")
    if "http://" in source or "https://" in source:
        findings.append("real URL literal")
    return findings


def main() -> int:
    findings = [(path, issue) for path in SOURCE_ROOT.rglob("*.py") for issue in violations(path)]
    if findings:
        for path, issue in findings:
            print(f"mock-only violation: {path}: {issue}")
        return 1
    print("mock-only AST/URL scan passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
