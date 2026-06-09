from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Node:
    line: int


@dataclass
class Program(Node):
    items: List[Node] = field(default_factory=list)


@dataclass
class TypeSpec:
    base: str
    pointer: int = 0

    def __str__(self) -> str:
        return self.base + ("*" * self.pointer)

    @property
    def size(self) -> int:
        if self.pointer:
            return 4
        return 4 if self.base == "int" else 1

    def is_void(self) -> bool:
        return self.base == "void" and self.pointer == 0


@dataclass
class DeclItem(Node):
    name: str
    array_size: Optional["Expr"] = None
    init: Optional["Expr"] = None


@dataclass
class VarDecl(Node):
    type_spec: TypeSpec
    items: List[DeclItem] = field(default_factory=list)


@dataclass
class Param(Node):
    type_spec: TypeSpec
    name: str


@dataclass
class FunctionDef(Node):
    return_type: TypeSpec
    name: str
    params: List[Param]
    body: "Block"


@dataclass
class Block(Node):
    statements: List[Node] = field(default_factory=list)


@dataclass
class IfStmt(Node):
    condition: "Expr"
    then_branch: Node
    else_branch: Optional[Node] = None


@dataclass
class WhileStmt(Node):
    condition: "Expr"
    body: Node


@dataclass
class DoWhileStmt(Node):
    body: Node
    condition: "Expr"


@dataclass
class ForStmt(Node):
    init: Optional[Node]
    condition: Optional["Expr"]
    update: Optional["Expr"]
    body: Node


@dataclass
class BreakStmt(Node):
    pass


@dataclass
class ContinueStmt(Node):
    pass


@dataclass
class ReturnStmt(Node):
    value: Optional["Expr"] = None


@dataclass
class ExprStmt(Node):
    expr: Optional["Expr"] = None


@dataclass
class Expr(Node):
    pass


@dataclass
class IntLiteral(Expr):
    value: int


@dataclass
class CharLiteral(Expr):
    value: int


@dataclass
class StringLiteral(Expr):
    value: str


@dataclass
class Identifier(Expr):
    name: str


@dataclass
class UnaryOp(Expr):
    op: str
    operand: Expr


@dataclass
class BinaryOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class AssignExpr(Expr):
    op: str
    target: Expr
    value: Expr


@dataclass
class CallExpr(Expr):
    callee: str
    args: List[Expr] = field(default_factory=list)


@dataclass
class IndexExpr(Expr):
    target: Expr
    index: Expr


@dataclass
class PostfixOp(Expr):
    op: str
    operand: Expr
