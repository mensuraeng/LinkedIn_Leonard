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


def string_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = string_value(node.left)
        right = string_value(node.right)
        if left is not None and right is not None:
            return left + right
    return None


class TransportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imported: set[str] = set()
        self.module_aliases: dict[str, str] = {}
        self.call_aliases: dict[str, tuple[str, str]] = {}
        self.calls: set[tuple[str, str]] = set()

    def resolve_call(self, node: ast.AST) -> tuple[str, str] | None:
        if isinstance(node, ast.Name):
            return self.call_aliases.get(node.id)
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return (self.module_aliases.get(node.value.id, node.value.id), node.attr)
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "__import__"
                and node.value.args
            ):
                module = string_value(node.value.args[0])
                if module is not None:
                    return (module.split(".")[0], node.attr)
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name)
            and node.value.attr == "__dict__"
        ):
            attribute = string_value(node.slice)
            if attribute is not None:
                module = self.module_aliases.get(node.value.value.id, node.value.value.id)
                return (module, attribute)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
        ):
            attribute = string_value(node.args[1])
            if attribute is not None:
                module = self.module_aliases.get(node.args[0].id, node.args[0].id)
                return (module, attribute)
        return None

    def bind(self, target: ast.AST, value: ast.AST) -> None:
        if isinstance(target, ast.Name):
            call = self.resolve_call(value)
            if call in FORBIDDEN_CALLS:
                self.call_aliases[target.id] = call
            else:
                self.call_aliases.pop(target.id, None)
            return
        if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (ast.Tuple, ast.List)):
            for nested_target, nested_value in zip(target.elts, value.elts):
                self.bind(nested_target, nested_value)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            canonical = alias.name.split(".")[0]
            self.imported.add(canonical)
            self.module_aliases[alias.asname or canonical] = canonical

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if not node.module:
            return
        canonical = node.module.split(".")[0]
        self.imported.add(canonical)
        for alias in node.names:
            call = (canonical, alias.name)
            if call in FORBIDDEN_CALLS:
                self.call_aliases[alias.asname or alias.name] = call

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for target in node.targets:
            self.bind(target, node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
            self.bind(node.target, node.value)

    def visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        outer_aliases = self.call_aliases
        self.call_aliases = outer_aliases.copy()
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            self.call_aliases.pop(argument.arg, None)
        if node.args.vararg:
            self.call_aliases.pop(node.args.vararg.arg, None)
        if node.args.kwarg:
            self.call_aliases.pop(node.args.kwarg.arg, None)
        for statement in node.body:
            self.visit(statement)
        self.call_aliases = outer_aliases

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "__import__" and node.args:
            module = string_value(node.args[0])
            if module is not None:
                self.imported.add(module.split(".")[0])
        call = self.resolve_call(node.func)
        if call in FORBIDDEN_CALLS:
            self.calls.add(call)
        self.generic_visit(node)


def violations(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    visitor = TransportVisitor()
    visitor.visit(ast.parse(source, filename=str(path)))
    findings: list[str] = []
    blocked = visitor.imported.intersection(FORBIDDEN_IMPORTS)
    if blocked:
        findings.append(f"forbidden transport import(s): {', '.join(sorted(blocked))}")
    blocked_calls = visitor.calls.intersection(FORBIDDEN_CALLS)
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