from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from ast_nodes import (
    AssignExpr,
    BinaryOp,
    Block,
    BreakStmt,
    CallExpr,
    CharLiteral,
    ContinueStmt,
    DeclItem,
    DoWhileStmt,
    Expr,
    ExprStmt,
    ForStmt,
    FunctionDef,
    Identifier,
    IfStmt,
    IndexExpr,
    IntLiteral,
    PostfixOp,
    Program,
    ReturnStmt,
    StringLiteral,
    TypeSpec,
    UnaryOp,
    VarDecl,
    WhileStmt,
)
from memory import Memory, MemoryErrorSC
from parser import ParseError, Parser
from symtable import Scope, Symbol


class SmallCError(Exception):
    pass


class RuntimeErrorSC(SmallCError):
    pass


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value: int):
        super().__init__()
        self.value = value


class ExitSignal(Exception):
    def __init__(self, code: int):
        super().__init__()
        self.code = code


@dataclass
class Value:
    value: int
    type_spec: TypeSpec
    address: Optional[int] = None
    array_length: Optional[int] = None


@dataclass
class CompiledProgram:
    program: Program
    source_lines: List[str]


class Interpreter:
    def __init__(self) -> None:
        self.memory = Memory()
        self.random = random.Random()
        self.trace_enabled = False
        self.program_lines: List[str] = []
        self.buffer_lines: List[str] = []
        self.builtins: Dict[str, Callable[[List[Value]], int]] = {}
        self._register_builtins()
        self.reset_runtime()

    def reset_runtime(self) -> None:
        self.memory.reset()
        self.global_scope = Scope()
        self.functions: Dict[str, FunctionDef] = {}
        self.function_lines: Dict[str, int] = {}
        self.string_literals: List[int] = []
        for name in self.builtins:
            self.function_lines[name] = -1

    def compile_source(self, source: str) -> CompiledProgram:
        parser = Parser(source)
        return CompiledProgram(program=parser.parse_program(), source_lines=source.splitlines())

    def check_source(self, source: str) -> None:
        compiled = self.compile_source(source)
        self._validate_program(compiled.program)

    def preview_functions(self, source: str) -> List[str]:
        compiled = self.compile_source(source)
        functions = self._collect_function_signatures(compiled.program)
        lines = list(functions)
        for name in sorted(self.builtins):
            lines.append(f"{builtin_signature(name)}\t[built-in]")
        return lines

    def load_buffer(self, source: str) -> None:
        self.buffer_lines = source.splitlines()

    def buffer_source(self) -> str:
        return "\n".join(self.buffer_lines)

    def set_buffer_lines(self, lines: List[str]) -> None:
        self.buffer_lines = list(lines)

    def execute_snippet(self, source: str) -> List[str]:
        compiled = self.compile_source(source)
        self.program_lines = compiled.source_lines
        output = self._execute_program(compiled.program, reset=False, run_main=False)
        return output

    def run_buffer(self) -> List[str]:
        source = self.buffer_source()
        compiled = self.compile_source(source)
        self.program_lines = compiled.source_lines
        return self._execute_program(compiled.program, reset=True, run_main=True)

    def list_functions(self) -> List[str]:
        lines: List[str] = []
        for name, func in sorted(self.functions.items(), key=lambda item: item[1].line):
            params = ", ".join(f"{param.type_spec} {param.name}" for param in func.params)
            lines.append(f"{func.return_type} {name}({params})\tline {func.line}")
        for name in sorted(self.builtins):
            lines.append(f"{builtin_signature(name)}\t[built-in]")
        return lines

    def list_variables(self) -> List[str]:
        lines: List[str] = []
        for symbol in self.global_scope.symbols.values():
            if symbol.is_function:
                continue
            if symbol.array_length:
                values = []
                limit = min(symbol.array_length, 10)
                for i in range(limit):
                    values.append(str(self._read_scalar(symbol.address + i * symbol.type_spec.size, symbol.type_spec)))
                body = ", ".join(values)
                if symbol.array_length > 10:
                    body += ", ..."
                lines.append(f"{symbol.type_spec} {symbol.name}[{symbol.array_length}] = {{{body}}}")
            else:
                value = self._read_scalar(symbol.address, symbol.type_spec)
                if symbol.type_spec.base == "char" and symbol.type_spec.pointer == 0:
                    lines.append(f"{symbol.type_spec} {symbol.name} = {value} ({repr(chr(value & 0xFF))})")
                elif symbol.type_spec.pointer:
                    lines.append(f"{symbol.type_spec} {symbol.name} = {value}")
                else:
                    lines.append(f"{symbol.type_spec} {symbol.name} = {value}")
        return lines

    def _execute_program(self, program: Program, reset: bool, run_main: bool) -> List[str]:
        if reset:
            self.reset_runtime()
        self._validate_program(program)
        output: List[str] = []
        try:
            for item in program.items:
                if isinstance(item, FunctionDef):
                    continue
                if isinstance(item, VarDecl):
                    self._exec_vardecl(item, self.global_scope, output)
                elif not run_main:
                    self._exec_stmt(item, self.global_scope, output)
            if run_main:
                main = self.functions.get("main")
                if main is None:
                    raise RuntimeErrorSC("No main() function defined.")
                result = self._call_function("main", [], output)
                output.append(f"Program exited with return value {result}.")
        except ExitSignal as signal:
            output.append(f"Program exited with return value {signal.code}.")
        return output

    def _index_functions(self, program: Program) -> None:
        self.functions = {}
        self.function_lines = {name: -1 for name in self.builtins}
        for item in program.items:
            if isinstance(item, FunctionDef):
                self.functions[item.name] = item
                self.function_lines[item.name] = item.line

    def _validate_program(self, program: Program) -> None:
        self._index_functions(program)
        seen = set()
        for item in program.items:
            if isinstance(item, FunctionDef):
                if item.name in seen:
                    raise RuntimeErrorSC(f"Redeclaration of function '{item.name}'.")
                seen.add(item.name)
                self._validate_function(item)
            elif isinstance(item, VarDecl):
                self._validate_decl(item, set())
            else:
                self._validate_stmt(item, set())

    def _collect_function_signatures(self, program: Program) -> List[str]:
        signatures: List[str] = []
        seen = set()
        for item in sorted((node for node in program.items if isinstance(node, FunctionDef)), key=lambda func: func.line):
            if item.name in seen:
                raise RuntimeErrorSC(f"Redeclaration of function '{item.name}'.")
            seen.add(item.name)
            params = ", ".join(f"{param.type_spec} {param.name}" for param in item.params)
            signatures.append(f"{item.return_type} {item.name}({params})\tline {item.line}")
        return signatures

    def _validate_function(self, func: FunctionDef) -> None:
        names = set()
        for param in func.params:
            if param.name in names:
                raise RuntimeErrorSC(f"Duplicate parameter '{param.name}' in function '{func.name}'.")
            names.add(param.name)
        self._validate_stmt(func.body, set(names))

    def _validate_stmt(self, stmt, names: set[str]) -> None:
        if isinstance(stmt, Block):
            local_names = set(names)
            for sub in stmt.statements:
                self._validate_stmt(sub, local_names)
            return
        if isinstance(stmt, VarDecl):
            self._validate_decl(stmt, names)
            return
        if isinstance(stmt, IfStmt):
            self._validate_expr(stmt.condition)
            self._validate_stmt(stmt.then_branch, set(names))
            if stmt.else_branch is not None:
                self._validate_stmt(stmt.else_branch, set(names))
            return
        if isinstance(stmt, WhileStmt):
            self._validate_expr(stmt.condition)
            self._validate_stmt(stmt.body, set(names))
            return
        if isinstance(stmt, DoWhileStmt):
            self._validate_stmt(stmt.body, set(names))
            self._validate_expr(stmt.condition)
            return
        if isinstance(stmt, ForStmt):
            loop_names = set(names)
            if stmt.init is not None:
                if isinstance(stmt.init, VarDecl):
                    self._validate_decl(stmt.init, loop_names)
                elif isinstance(stmt.init, ExprStmt) and stmt.init.expr is not None:
                    self._validate_expr(stmt.init.expr)
            if stmt.condition is not None:
                self._validate_expr(stmt.condition)
            if stmt.update is not None:
                self._validate_expr(stmt.update)
            self._validate_stmt(stmt.body, loop_names)
            return
        if isinstance(stmt, ReturnStmt):
            if stmt.value is not None:
                self._validate_expr(stmt.value)
            return
        if isinstance(stmt, ExprStmt):
            if stmt.expr is not None:
                self._validate_expr(stmt.expr)
            return

    def _validate_decl(self, decl: VarDecl, names: set[str]) -> None:
        for item in decl.items:
            if item.name in names:
                raise RuntimeErrorSC(f"Redeclaration of '{item.name}'.")
            names.add(item.name)
            if item.array_size is not None:
                self._validate_expr(item.array_size)
            if item.init is not None:
                self._validate_expr(item.init)

    def _validate_expr(self, expr: Expr) -> None:
        if isinstance(expr, (IntLiteral, CharLiteral, StringLiteral, Identifier)):
            return
        if isinstance(expr, UnaryOp):
            self._validate_expr(expr.operand)
            return
        if isinstance(expr, PostfixOp):
            self._validate_expr(expr.operand)
            return
        if isinstance(expr, IndexExpr):
            self._validate_expr(expr.target)
            self._validate_expr(expr.index)
            return
        if isinstance(expr, AssignExpr):
            self._validate_expr(expr.target)
            self._validate_expr(expr.value)
            return
        if isinstance(expr, BinaryOp):
            self._validate_expr(expr.left)
            self._validate_expr(expr.right)
            return
        if isinstance(expr, CallExpr):
            if expr.callee not in self.functions and expr.callee not in self.builtins:
                raise RuntimeErrorSC(f"Undefined function '{expr.callee}'.")
            for arg in expr.args:
                self._validate_expr(arg)
            return

    def _exec_stmt(self, stmt, scope: Scope, output: List[str]) -> None:
        self._trace(stmt)
        if isinstance(stmt, Block):
            block_scope = Scope(scope)
            for sub in stmt.statements:
                self._exec_stmt(sub, block_scope, output)
            return
        if isinstance(stmt, VarDecl):
            self._exec_vardecl(stmt, scope, output)
            return
        if isinstance(stmt, ExprStmt):
            if stmt.expr is not None:
                self._eval(stmt.expr, scope, output)
            return
        if isinstance(stmt, IfStmt):
            if self._truthy(self._eval(stmt.condition, scope, output).value):
                self._exec_stmt(stmt.then_branch, scope, output)
            elif stmt.else_branch is not None:
                self._exec_stmt(stmt.else_branch, scope, output)
            return
        if isinstance(stmt, WhileStmt):
            while self._truthy(self._eval(stmt.condition, scope, output).value):
                try:
                    self._exec_stmt(stmt.body, scope, output)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
            return
        if isinstance(stmt, DoWhileStmt):
            while True:
                try:
                    self._exec_stmt(stmt.body, scope, output)
                except ContinueSignal:
                    pass
                except BreakSignal:
                    break
                if not self._truthy(self._eval(stmt.condition, scope, output).value):
                    break
            return
        if isinstance(stmt, ForStmt):
            loop_scope = Scope(scope)
            if stmt.init is not None:
                if isinstance(stmt.init, VarDecl):
                    self._exec_vardecl(stmt.init, loop_scope, output)
                else:
                    self._exec_stmt(stmt.init, loop_scope, output)
            while stmt.condition is None or self._truthy(self._eval(stmt.condition, loop_scope, output).value):
                try:
                    self._exec_stmt(stmt.body, loop_scope, output)
                except ContinueSignal:
                    pass
                except BreakSignal:
                    break
                if stmt.update is not None:
                    self._eval(stmt.update, loop_scope, output)
            return
        if isinstance(stmt, BreakStmt):
            raise BreakSignal()
        if isinstance(stmt, ContinueStmt):
            raise ContinueSignal()
        if isinstance(stmt, ReturnStmt):
            value = 0
            if stmt.value is not None:
                value = self._eval(stmt.value, scope, output).value
            raise ReturnSignal(value)
        raise RuntimeErrorSC(f"Unsupported statement at line {stmt.line}.")

    def _exec_vardecl(self, decl: VarDecl, scope: Scope, output: List[str]) -> None:
        for item in decl.items:
            array_length = None
            if item.array_size is not None:
                array_length = self._eval(item.array_size, scope, output).value
                if array_length <= 0:
                    raise RuntimeErrorSC("Array size must be positive.")
            if decl.type_spec.is_void() and array_length is None:
                raise RuntimeErrorSC("void variables are not allowed.")
            addr = self.memory.allocate(decl.type_spec.size * (array_length or 1))
            symbol = Symbol(name=item.name, type_spec=decl.type_spec, address=addr, array_length=array_length)
            try:
                scope.define(symbol)
            except ValueError as exc:
                raise RuntimeErrorSC(str(exc)) from exc
            if item.init is not None:
                if array_length:
                    if not isinstance(item.init, StringLiteral):
                        raise RuntimeErrorSC("Only string literal initialization is supported for arrays.")
                    self.memory.write_c_string(addr, item.init.value, max_size=array_length)
                else:
                    value = self._eval(item.init, scope, output)
                    self._write_scalar(addr, decl.type_spec, value.value)

    def _eval(self, expr: Expr, scope: Scope, output: List[str]) -> Value:
        if isinstance(expr, IntLiteral):
            return Value(expr.value, TypeSpec("int"))
        if isinstance(expr, CharLiteral):
            return Value(expr.value, TypeSpec("char"))
        if isinstance(expr, StringLiteral):
            addr = self.memory.allocate(len(expr.value.encode("utf-8")) + 1)
            self.memory.write_c_string(addr, expr.value)
            self.string_literals.append(addr)
            return Value(addr, TypeSpec("char", 1))
        if isinstance(expr, Identifier):
            symbol = scope.lookup(expr.name)
            if symbol is None:
                raise RuntimeErrorSC(f"Undefined identifier '{expr.name}'.")
            if symbol.array_length:
                return Value(symbol.address, TypeSpec(symbol.type_spec.base, 1), address=symbol.address, array_length=symbol.array_length)
            return Value(self._read_scalar(symbol.address, symbol.type_spec), symbol.type_spec, address=symbol.address)
        if isinstance(expr, UnaryOp):
            return self._eval_unary(expr, scope, output)
        if isinstance(expr, PostfixOp):
            lvalue = self._resolve_lvalue(expr.operand, scope, output)
            old = self._read_scalar(lvalue.address, lvalue.type_spec)
            delta = 1 if expr.op == "++" else -1
            self._write_scalar(lvalue.address, lvalue.type_spec, old + delta)
            return Value(old, lvalue.type_spec)
        if isinstance(expr, IndexExpr):
            lvalue = self._resolve_lvalue(expr, scope, output)
            return Value(self._read_scalar(lvalue.address, lvalue.type_spec), lvalue.type_spec, address=lvalue.address)
        if isinstance(expr, AssignExpr):
            return self._eval_assign(expr, scope, output)
        if isinstance(expr, BinaryOp):
            return self._eval_binary(expr, scope, output)
        if isinstance(expr, CallExpr):
            args = [self._eval(arg, scope, output) for arg in expr.args]
            value = self._call_function(expr.callee, args, output)
            return Value(value, TypeSpec("int"))
        raise RuntimeErrorSC(f"Unsupported expression at line {expr.line}.")

    def _eval_unary(self, expr: UnaryOp, scope: Scope, output: List[str]) -> Value:
        if expr.op in {"++", "--"}:
            lvalue = self._resolve_lvalue(expr.operand, scope, output)
            old = self._read_scalar(lvalue.address, lvalue.type_spec)
            delta = 1 if expr.op == "++" else -1
            new = old + delta
            self._write_scalar(lvalue.address, lvalue.type_spec, new)
            return Value(new, lvalue.type_spec)
        if expr.op == "&":
            lvalue = self._resolve_lvalue(expr.operand, scope, output)
            if lvalue.type_spec.pointer:
                raise RuntimeErrorSC("Multiple pointer levels are not supported.")
            return Value(lvalue.address, TypeSpec(lvalue.type_spec.base, 1))
        if expr.op == "*":
            value = self._eval(expr.operand, scope, output)
            if value.type_spec.pointer != 1:
                raise RuntimeErrorSC("Cannot dereference a non-pointer value.")
            deref_type = TypeSpec(value.type_spec.base, 0)
            return Value(self._read_scalar(value.value, deref_type), deref_type, address=value.value)
        value = self._eval(expr.operand, scope, output)
        if expr.op == "-":
            return Value(-value.value, value.type_spec)
        if expr.op == "+":
            return Value(+value.value, value.type_spec)
        if expr.op == "!":
            return Value(0 if self._truthy(value.value) else 1, TypeSpec("int"))
        if expr.op == "~":
            return Value(~value.value, TypeSpec("int"))
        raise RuntimeErrorSC(f"Unsupported unary operator {expr.op}.")

    def _eval_assign(self, expr: AssignExpr, scope: Scope, output: List[str]) -> Value:
        lvalue = self._resolve_lvalue(expr.target, scope, output)
        rhs = self._eval(expr.value, scope, output).value
        current = self._read_scalar(lvalue.address, lvalue.type_spec)
        if expr.op == "=":
            result = rhs
        elif expr.op == "+=":
            result = current + rhs
        elif expr.op == "-=":
            result = current - rhs
        elif expr.op == "*=":
            result = current * rhs
        elif expr.op == "/=":
            if rhs == 0:
                raise RuntimeErrorSC("division by zero.")
            result = int(current / rhs)
        elif expr.op == "%=":
            if rhs == 0:
                raise RuntimeErrorSC("division by zero.")
            result = current % rhs
        else:
            raise RuntimeErrorSC(f"Unsupported assignment operator {expr.op}.")
        self._write_scalar(lvalue.address, lvalue.type_spec, result)
        return Value(result, lvalue.type_spec, address=lvalue.address)

    def _eval_binary(self, expr: BinaryOp, scope: Scope, output: List[str]) -> Value:
        if expr.op == "&&":
            left = self._eval(expr.left, scope, output)
            if not self._truthy(left.value):
                return Value(0, TypeSpec("int"))
            right = self._eval(expr.right, scope, output)
            return Value(1 if self._truthy(right.value) else 0, TypeSpec("int"))
        if expr.op == "||":
            left = self._eval(expr.left, scope, output)
            if self._truthy(left.value):
                return Value(1, TypeSpec("int"))
            right = self._eval(expr.right, scope, output)
            return Value(1 if self._truthy(right.value) else 0, TypeSpec("int"))
        left = self._eval(expr.left, scope, output)
        right = self._eval(expr.right, scope, output)
        if expr.op in {"+", "-"}:
            pointer = self._pointer_arithmetic(expr.op, left, right)
            if pointer is not None:
                return pointer
        if expr.op == "/" or expr.op == "%":
            if right.value == 0:
                raise RuntimeErrorSC("division by zero.")
        if expr.op == "*":
            result = left.value * right.value
        elif expr.op == "/":
            result = int(left.value / right.value)
        elif expr.op == "%":
            result = left.value % right.value
        elif expr.op == "+":
            result = left.value + right.value
        elif expr.op == "-":
            result = left.value - right.value
        elif expr.op == "<<":
            result = left.value << right.value
        elif expr.op == ">>":
            result = left.value >> right.value
        elif expr.op == "<":
            result = 1 if left.value < right.value else 0
        elif expr.op == "<=":
            result = 1 if left.value <= right.value else 0
        elif expr.op == ">":
            result = 1 if left.value > right.value else 0
        elif expr.op == ">=":
            result = 1 if left.value >= right.value else 0
        elif expr.op == "==":
            result = 1 if left.value == right.value else 0
        elif expr.op == "!=":
            result = 1 if left.value != right.value else 0
        elif expr.op == "&":
            result = left.value & right.value
        elif expr.op == "^":
            result = left.value ^ right.value
        elif expr.op == "|":
            result = left.value | right.value
        else:
            raise RuntimeErrorSC(f"Unsupported binary operator {expr.op}.")
        return Value(result, TypeSpec("int"))

    def _pointer_arithmetic(self, op: str, left: Value, right: Value) -> Optional[Value]:
        if left.type_spec.pointer == 1 and right.type_spec.pointer == 0:
            scale = 4 if left.type_spec.base == "int" else 1
            delta = right.value * scale
            value = left.value + delta if op == "+" else left.value - delta
            return Value(value, left.type_spec)
        if left.type_spec.pointer == 0 and right.type_spec.pointer == 1 and op == "+":
            scale = 4 if right.type_spec.base == "int" else 1
            return Value(right.value + left.value * scale, right.type_spec)
        return None

    def _resolve_lvalue(self, expr: Expr, scope: Scope, output: List[str]) -> Value:
        if isinstance(expr, Identifier):
            symbol = scope.lookup(expr.name)
            if symbol is None:
                raise RuntimeErrorSC(f"Undefined identifier '{expr.name}'.")
            if symbol.array_length:
                raise RuntimeErrorSC("Array name is not assignable.")
            return Value(symbol.address, symbol.type_spec, address=symbol.address)
        if isinstance(expr, UnaryOp) and expr.op == "*":
            pointer = self._eval(expr.operand, scope, output)
            if pointer.type_spec.pointer != 1:
                raise RuntimeErrorSC("Cannot dereference a non-pointer value.")
            deref_type = TypeSpec(pointer.type_spec.base, 0)
            return Value(pointer.value, deref_type, address=pointer.value)
        if isinstance(expr, IndexExpr):
            base = self._eval(expr.target, scope, output)
            index = self._eval(expr.index, scope, output).value
            if base.type_spec.pointer != 1:
                raise RuntimeErrorSC("Indexing requires an array or pointer.")
            elem_type = TypeSpec(base.type_spec.base, 0)
            if base.array_length is not None and not (0 <= index < base.array_length):
                raise RuntimeErrorSC(f"array index out of bounds (index {index}, size {base.array_length}).")
            addr = base.value + index * elem_type.size
            return Value(addr, elem_type, address=addr)
        raise RuntimeErrorSC("Expression is not assignable.")

    def _call_function(self, name: str, args: List[Value], output: List[str]) -> int:
        if name in self.builtins:
            return self.builtins[name](args)
        func = self.functions.get(name)
        if func is None:
            raise RuntimeErrorSC(f"Undefined function '{name}'.")
        if len(args) != len(func.params):
            raise RuntimeErrorSC(f"Function '{name}' expects {len(func.params)} argument(s).")
        frame = Scope(self.global_scope)
        for param, arg in zip(func.params, args):
            addr = self.memory.allocate(param.type_spec.size)
            symbol = Symbol(name=param.name, type_spec=param.type_spec, address=addr)
            frame.define(symbol)
            self._write_scalar(addr, param.type_spec, arg.value)
        try:
            self._exec_stmt(func.body, frame, output)
        except ReturnSignal as signal:
            return signal.value
        return 0

    def _read_scalar(self, addr: int, type_spec: TypeSpec) -> int:
        try:
            if type_spec.pointer or type_spec.base == "int":
                return self.memory.read_int(addr)
            return self.memory.read_char(addr)
        except MemoryErrorSC as exc:
            raise RuntimeErrorSC(str(exc)) from exc

    def _write_scalar(self, addr: int, type_spec: TypeSpec, value: int) -> None:
        try:
            if type_spec.pointer or type_spec.base == "int":
                self.memory.write_int(addr, value)
            else:
                self.memory.write_char(addr, value)
        except MemoryErrorSC as exc:
            raise RuntimeErrorSC(str(exc)) from exc

    def _truthy(self, value: int) -> bool:
        return value != 0

    def _trace(self, stmt) -> None:
        if not self.trace_enabled:
            return
        line_no = stmt.line
        text = ""
        if 1 <= line_no <= len(self.program_lines):
            text = self.program_lines[line_no - 1].strip()
        print(f"[line {line_no}] {text}")

    def _register_builtins(self) -> None:
        self.builtins = {
            "putchar": self._builtin_putchar,
            "getchar": self._builtin_getchar,
            "printf": self._builtin_printf,
            "puts": self._builtin_puts,
            "scanf": self._builtin_scanf,
            "strlen": self._builtin_strlen,
            "strcpy": self._builtin_strcpy,
            "strcmp": self._builtin_strcmp,
            "strcat": self._builtin_strcat,
            "abs": lambda args: abs(self._expect_args("abs", args, 1)[0].value),
            "max": lambda args: max(v.value for v in self._expect_args("max", args, 2)),
            "min": lambda args: min(v.value for v in self._expect_args("min", args, 2)),
            "pow": self._builtin_pow,
            "sqrt": self._builtin_sqrt,
            "mod": self._builtin_mod,
            "rand": self._builtin_rand,
            "srand": self._builtin_srand,
            "memset": self._builtin_memset,
            "sizeof_int": lambda args: 4 if not args else self._wrong_arity("sizeof_int", 0),
            "sizeof_char": lambda args: 1 if not args else self._wrong_arity("sizeof_char", 0),
            "atoi": self._builtin_atoi,
            "itoa": self._builtin_itoa,
            "exit": self._builtin_exit,
        }

    def _expect_args(self, name: str, args: List[Value], count: int) -> List[Value]:
        if len(args) != count:
            raise RuntimeErrorSC(f"{name} expects {count} argument(s).")
        return args

    def _wrong_arity(self, name: str, count: int) -> int:
        raise RuntimeErrorSC(f"{name} expects {count} argument(s).")

    def _builtin_putchar(self, args: List[Value]) -> int:
        ch = self._expect_args("putchar", args, 1)[0].value & 0xFF
        sys.stdout.write(chr(ch))
        sys.stdout.flush()
        return ch

    def _builtin_getchar(self, args: List[Value]) -> int:
        self._expect_args("getchar", args, 0)
        try:
            text = input()
        except EOFError:
            return -1
        return ord(text[0]) if text else ord("\n")

    def _builtin_printf(self, args: List[Value]) -> int:
        if not args:
            raise RuntimeErrorSC("printf expects at least one argument.")
        fmt = self.memory.read_c_string(args[0].value)
        rendered = render_printf(fmt, args[1:], self.memory)
        sys.stdout.write(rendered)
        sys.stdout.flush()
        return len(rendered)

    def _builtin_puts(self, args: List[Value]) -> int:
        ptr = self._expect_args("puts", args, 1)[0].value
        text = self.memory.read_c_string(ptr)
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
        return len(text)

    def _builtin_scanf(self, args: List[Value]) -> int:
        if not args:
            raise RuntimeErrorSC("scanf expects at least one argument.")
        fmt = self.memory.read_c_string(args[0].value)
        specifiers = [ch for i, ch in enumerate(fmt) if ch in "dc" and i > 0 and fmt[i - 1] == "%"]
        if len(specifiers) != len(args) - 1:
            raise RuntimeErrorSC("scanf format/argument count mismatch.")
        try:
            text = input()
        except EOFError:
            return 0
        parts = text.split()
        if len(parts) < len(specifiers):
            return 0
        for spec, arg, part in zip(specifiers, args[1:], parts):
            if spec == "d":
                self.memory.write_int(arg.value, int(part, 10))
            else:
                self.memory.write_char(arg.value, ord(part[0]))
        return len(specifiers)

    def _builtin_strlen(self, args: List[Value]) -> int:
        ptr = self._expect_args("strlen", args, 1)[0].value
        return len(self.memory.read_c_string(ptr))

    def _builtin_strcpy(self, args: List[Value]) -> int:
        dest, src = self._expect_args("strcpy", args, 2)
        text = self.memory.read_c_string(src.value)
        size = self.memory.allocation_size(dest.value)
        self.memory.write_c_string(dest.value, text, max_size=size)
        return dest.value

    def _builtin_strcmp(self, args: List[Value]) -> int:
        s1, s2 = self._expect_args("strcmp", args, 2)
        left = self.memory.read_c_string(s1.value)
        right = self.memory.read_c_string(s2.value)
        if left < right:
            return -1
        if left > right:
            return 1
        return 0

    def _builtin_strcat(self, args: List[Value]) -> int:
        dest, src = self._expect_args("strcat", args, 2)
        left = self.memory.read_c_string(dest.value)
        right = self.memory.read_c_string(src.value)
        size = self.memory.allocation_size(dest.value)
        self.memory.write_c_string(dest.value, left + right, max_size=size)
        return dest.value

    def _builtin_pow(self, args: List[Value]) -> int:
        base, exp = self._expect_args("pow", args, 2)
        if exp.value < 0:
            return 0
        return base.value ** exp.value

    def _builtin_sqrt(self, args: List[Value]) -> int:
        value = self._expect_args("sqrt", args, 1)[0].value
        if value < 0:
            raise RuntimeErrorSC("sqrt() argument must be non-negative.")
        return math.isqrt(value)

    def _builtin_mod(self, args: List[Value]) -> int:
        a, b = self._expect_args("mod", args, 2)
        if b.value == 0:
            raise RuntimeErrorSC("division by zero.")
        return a.value % b.value

    def _builtin_rand(self, args: List[Value]) -> int:
        self._expect_args("rand", args, 0)
        return self.random.randint(0, 32767)

    def _builtin_srand(self, args: List[Value]) -> int:
        seed = self._expect_args("srand", args, 1)[0].value
        self.random.seed(seed)
        return 0

    def _builtin_memset(self, args: List[Value]) -> int:
        ptr, val, size = self._expect_args("memset", args, 3)
        self.memory.memset(ptr.value, val.value, size.value)
        return ptr.value

    def _builtin_atoi(self, args: List[Value]) -> int:
        ptr = self._expect_args("atoi", args, 1)[0].value
        text = self.memory.read_c_string(ptr).strip()
        try:
            return int(text, 10)
        except ValueError:
            return 0

    def _builtin_itoa(self, args: List[Value]) -> int:
        value, ptr = self._expect_args("itoa", args, 2)
        size = self.memory.allocation_size(ptr.value)
        self.memory.write_c_string(ptr.value, str(value.value), max_size=size)
        return ptr.value

    def _builtin_exit(self, args: List[Value]) -> int:
        code = self._expect_args("exit", args, 1)[0].value
        raise ExitSignal(code)


def builtin_signature(name: str) -> str:
    signatures = {
        "putchar": "int putchar(int ch)",
        "getchar": "int getchar()",
        "printf": 'void printf(char *fmt, ...)',
        "puts": "void puts(char *s)",
        "scanf": 'int scanf(char *fmt, ...)',
        "strlen": "int strlen(char *s)",
        "strcpy": "void strcpy(char *dest, char *src)",
        "strcmp": "int strcmp(char *s1, char *s2)",
        "strcat": "void strcat(char *dest, char *src)",
        "abs": "int abs(int x)",
        "max": "int max(int a, int b)",
        "min": "int min(int a, int b)",
        "pow": "int pow(int base, int exp)",
        "sqrt": "int sqrt(int x)",
        "mod": "int mod(int a, int b)",
        "rand": "int rand()",
        "srand": "void srand(int seed)",
        "memset": "void memset(char *ptr, int val, int n)",
        "sizeof_int": "int sizeof_int()",
        "sizeof_char": "int sizeof_char()",
        "atoi": "int atoi(char *s)",
        "itoa": "void itoa(int val, char *str)",
        "exit": "void exit(int code)",
    }
    return signatures[name]


def render_printf(fmt: str, values: List[Value], memory: Memory) -> str:
    out: List[str] = []
    arg_index = 0
    i = 0
    while i < len(fmt):
        if fmt[i] == "%" and i + 1 < len(fmt):
            spec = fmt[i + 1]
            if spec == "%":
                out.append("%")
            else:
                if arg_index >= len(values):
                    raise RuntimeErrorSC("printf argument count mismatch.")
                value = values[arg_index]
                arg_index += 1
                if spec == "d":
                    out.append(str(value.value))
                elif spec == "c":
                    out.append(chr(value.value & 0xFF))
                elif spec == "s":
                    out.append(memory.read_c_string(value.value))
                elif spec == "x":
                    out.append(format(value.value & 0xFFFFFFFF, "x"))
                else:
                    raise RuntimeErrorSC(f"Unsupported printf format %{spec}.")
            i += 2
            continue
        out.append(fmt[i])
        i += 1
    return "".join(out)
