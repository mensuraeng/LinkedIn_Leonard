"""Fail CI if local-only source acquires transports or real URLs."""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ALLOWED_ABSOLUTE_IMPORTS = frozenset({
    "__future__", "collections", "dataclasses", "datetime", "enum", "hashlib", "json", "re",
    "types", "typing",
})
FORBIDDEN_TRANSPORT_IMPORTS = frozenset({
    "aiohttp", "grpc", "http", "httpx", "oauthlib", "requests", "selenium", "socket",
    "urllib", "urllib3", "websockets",
})
FORBIDDEN_CALLS = frozenset({("asyncio", "open_connection")})
DYNAMIC_EXECUTION_CALLS = frozenset({"__import__", "compile", "eval", "exec"})
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


def dynamic_execution_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name) and node.id in DYNAMIC_EXECUTION_CALLS:
        return node.id
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "__builtins__"
        and node.attr in DYNAMIC_EXECUTION_CALLS
    ):
        return node.attr
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "__builtins__"
    ):
        attribute = string_value(node.slice)
        if attribute in DYNAMIC_EXECUTION_CALLS:
            return attribute
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "__builtins__"
    ):
        attribute = string_value(node.args[1])
        if attribute in DYNAMIC_EXECUTION_CALLS:
            return attribute
    return None


class TransportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imported: set[str] = set()
        self.disallowed_imports: set[str] = set()
        self.module_aliases: dict[str, str] = {}
        self.call_aliases: dict[str, tuple[str, str]] = {}
        self.calls: set[tuple[str, str]] = set()
        self.dynamic_execution_calls: set[str] = set()
        self.dynamic_execution_aliases: dict[str, str] = {}
        self.builtins_aliases: set[str] = set()
        self.runtime_reflections: set[str] = set()

    def dynamic_execution_name(self, node: ast.AST) -> str | None:
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in self.builtins_aliases
            and node.attr in DYNAMIC_EXECUTION_CALLS
        ):
            return node.attr
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id in self.builtins_aliases
        ):
            attribute = string_value(node.slice)
            if attribute in DYNAMIC_EXECUTION_CALLS:
                return attribute
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in self.builtins_aliases
        ):
            attribute = string_value(node.args[1])
            if attribute in DYNAMIC_EXECUTION_CALLS:
                return attribute
        return dynamic_execution_name(node)

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
            if isinstance(value, ast.Name) and value.id in {"__builtins__", *self.builtins_aliases}:
                self.builtins_aliases.add(target.id)
            else:
                self.builtins_aliases.discard(target.id)
            builtin = self.dynamic_execution_name(value)
            if builtin is None and isinstance(value, ast.Name):
                builtin = self.dynamic_execution_aliases.get(value.id)
            if builtin is not None:
                self.dynamic_execution_aliases[target.id] = builtin
                return
            self.dynamic_execution_aliases.pop(target.id, None)
            return
        if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (ast.Tuple, ast.List)):
            for nested_target, nested_value in zip(target.elts, value.elts):
                self.bind(nested_target, nested_value)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            canonical = alias.name.split(".")[0]
            self.imported.add(canonical)
            if canonical not in ALLOWED_ABSOLUTE_IMPORTS:
                self.disallowed_imports.add(canonical)
            self.module_aliases[alias.asname or canonical] = canonical

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level or not node.module:
            return
        canonical = node.module.split(".")[0]
        self.imported.add(canonical)
        if canonical not in ALLOWED_ABSOLUTE_IMPORTS:
            self.disallowed_imports.add(canonical)
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
        for expression in (*node.decorator_list, *node.args.defaults, *node.args.kw_defaults):
            if expression is not None:
                self.visit(expression)
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            if argument.annotation is not None:
                self.visit(argument.annotation)
        if node.args.vararg and node.args.vararg.annotation is not None:
            self.visit(node.args.vararg.annotation)
        if node.args.kwarg and node.args.kwarg.annotation is not None:
            self.visit(node.args.kwarg.annotation)
        if node.returns is not None:
            self.visit(node.returns)
        outer_aliases = self.call_aliases
        outer_dynamic_aliases = self.dynamic_execution_aliases
        outer_builtins_aliases = self.builtins_aliases
        self.call_aliases = outer_aliases.copy()
        self.dynamic_execution_aliases = outer_dynamic_aliases.copy()
        self.builtins_aliases = outer_builtins_aliases.copy()
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            self.call_aliases.pop(argument.arg, None)
            self.dynamic_execution_aliases.pop(argument.arg, None)
            self.builtins_aliases.discard(argument.arg)
        if node.args.vararg:
            self.call_aliases.pop(node.args.vararg.arg, None)
            self.dynamic_execution_aliases.pop(node.args.vararg.arg, None)
            self.builtins_aliases.discard(node.args.vararg.arg)
        if node.args.kwarg:
            self.call_aliases.pop(node.args.kwarg.arg, None)
            self.dynamic_execution_aliases.pop(node.args.kwarg.arg, None)
            self.builtins_aliases.discard(node.args.kwarg.arg)
        for statement in node.body:
            self.visit(statement)
        self.call_aliases = outer_aliases
        self.dynamic_execution_aliases = outer_dynamic_aliases
        self.builtins_aliases = outer_builtins_aliases

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_function(node)

    def visit_Global(self, node: ast.Global) -> None:
        self.runtime_reflections.add("global")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "__builtins__":
            self.runtime_reflections.add("__builtins__")

    def visit_Call(self, node: ast.Call) -> None:
        dynamic_call = self.dynamic_execution_name(node.func)
        if dynamic_call is None and isinstance(node.func, ast.Name):
            dynamic_call = self.dynamic_execution_aliases.get(node.func.id)
        if dynamic_call is not None:
            self.dynamic_execution_calls.add(dynamic_call)
            if dynamic_call == "__import__" and node.args:
                module = string_value(node.args[0])
                if module is not None:
                    canonical = module.split(".")[0]
                    self.imported.add(canonical)
                    if canonical not in ALLOWED_ABSOLUTE_IMPORTS:
                        self.disallowed_imports.add(canonical)
        if isinstance(node.func, ast.Name) and node.func.id in {"globals", "locals", "vars"}:
            self.runtime_reflections.add(node.func.id)
        call = self.resolve_call(node.func)
        if call in FORBIDDEN_CALLS:
            self.calls.add(call)
        self.generic_visit(node)


def violations(path: Path, *, require_allowed_imports: bool = False) -> list[str]:
    source = path.read_text(encoding="utf-8")
    visitor = TransportVisitor()
    visitor.visit(ast.parse(source, filename=str(path)))
    findings: list[str] = []
    if require_allowed_imports and visitor.disallowed_imports:
        findings.append(f"non-allowlisted import(s): {', '.join(sorted(visitor.disallowed_imports))}")
    blocked_imports = visitor.imported.intersection(FORBIDDEN_TRANSPORT_IMPORTS)
    if blocked_imports:
        findings.append(f"forbidden transport import(s): {', '.join(sorted(blocked_imports))}")
    if visitor.dynamic_execution_calls:
        rendered = ", ".join(sorted(visitor.dynamic_execution_calls))
        findings.append(f"forbidden dynamic execution call(s): {rendered}")
    if visitor.runtime_reflections:
        rendered = ", ".join(sorted(visitor.runtime_reflections))
        findings.append(f"forbidden runtime reflection(s): {rendered}")
    blocked_calls = visitor.calls.intersection(FORBIDDEN_CALLS)
    if blocked_calls:
        rendered = ", ".join(".".join(call) for call in sorted(blocked_calls))
        findings.append(f"forbidden transport call(s): {rendered}")
    if "http://" in source or "https://" in source:
        findings.append("real URL literal")
    return findings


def main() -> int:
    findings = [
        (path, issue)
        for path in SOURCE_ROOT.rglob("*.py")
        for issue in violations(path, require_allowed_imports=True)
    ]
    if findings:
        for path, issue in findings:
            print(f"mock-only violation: {path}: {issue}")
        return 1
    print("mock-only AST/URL scan passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())