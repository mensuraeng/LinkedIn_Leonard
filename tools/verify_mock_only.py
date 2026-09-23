"""Fail CI if local-only source acquires transports or real URLs."""
from __future__ import annotations

import ast
from pathlib import Path
import sys

FORBIDDEN_IMPORTS = frozenset({
    "aiohttp", "grpc", "http", "httpx", "oauthlib", "requests", "selenium", "socket",
    "urllib", "urllib3", "websockets",
})
FORBIDDEN_CALLS = frozenset({("asyncio", "open_connection")})
SOURCE_ROOT = Path("src")


def violations(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imported: set[str] = set()
    module_aliases: dict[str, str] = {}
    imported_calls: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                canonical = alias.name.split(".")[0]
                imported.add(canonical)
                module_aliases[alias.asname or canonical] = canonical
        elif isinstance(node, ast.ImportFrom) and node.module:
            canonical = node.module.split(".")[0]
            imported.add(canonical)
            for alias in node.names:
                if (canonical, alias.name) in FORBIDDEN_CALLS:
                    imported_calls[alias.asname or alias.name] = (canonical, alias.name)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        target = node.targets[0].id
        value = node.value
        if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
            call = (module_aliases.get(value.value.id, value.value.id), value.attr)
        elif (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "getattr"
            and len(value.args) >= 2
            and isinstance(value.args[0], ast.Name)
            and isinstance(value.args[1], ast.Constant)
            and isinstance(value.args[1].value, str)
        ):
            call = (module_aliases.get(value.args[0].id, value.args[0].id), value.args[1].value)
        else:
            continue
        if call in FORBIDDEN_CALLS:
            imported_calls[target] = call
    findings: list[str] = []
    blocked = imported.intersection(FORBIDDEN_IMPORTS)
    if blocked:
        findings.append(f"forbidden transport import(s): {', '.join(sorted(blocked))}")
    calls: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            calls.add((module_aliases.get(node.func.value.id, node.func.value.id), node.func.attr))
        elif isinstance(node.func, ast.Name) and node.func.id in imported_calls:
            calls.add(imported_calls[node.func.id])
    blocked_calls = calls.intersection(FORBIDDEN_CALLS)
    if blocked_calls:
        rendered = ", ".join(".".join(call) for call in sorted(blocked_calls))
        findings.append(f"forbidden transport call(s): {rendered}")
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
