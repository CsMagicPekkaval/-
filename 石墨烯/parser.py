from __future__ import annotations

from typing import List, Optional

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
    Param,
    PostfixOp,
    Program,
    ReturnStmt,
    StringLiteral,
    TypeSpec,
    UnaryOp,
    VarDecl,
    WhileStmt,
)
from lexer import Lexer, Token


class ParseError(Exception):
    pass


TYPE_KEYWORDS = {"int", "char", "void"}
ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%="}


class Parser:
    def __init__(self, source: str):
        self.tokens = Lexer(source).tokenize()
        self.index = 0

    def parse_program(self) -> Program:
        items = []
        while not self._match("EOF"):
            items.append(self.parse_toplevel())
        line = items[0].line if items else 1
        return Program(line=line, items=items)

    def parse_toplevel(self):
        if self._is_type():
            save = self.index
            first = self._current()
            type_spec = self.parse_type_spec()
            name = self._expect("IDENT").value
            if self._accept("OP", "("):
                params = self.parse_params()
                body = self.parse_block()
                return FunctionDef(line=first.line, return_type=type_spec, name=name, params=params, body=body)
            self.index = save
            decl = self.parse_var_decl()
            self._expect("OP", ";")
            return decl
        stmt = self.parse_statement()
        return stmt

    def parse_statement(self):
        if self._accept_keyword("if"):
            line = self._previous().line
            self._expect("OP", "(")
            condition = self.parse_expression()
            self._expect("OP", ")")
            then_branch = self.parse_statement()
            else_branch = self.parse_statement() if self._accept_keyword("else") else None
            return IfStmt(line=line, condition=condition, then_branch=then_branch, else_branch=else_branch)
        if self._accept_keyword("while"):
            line = self._previous().line
            self._expect("OP", "(")
            condition = self.parse_expression()
            self._expect("OP", ")")
            body = self.parse_statement()
            return WhileStmt(line=line, condition=condition, body=body)
        if self._accept_keyword("do"):
            line = self._previous().line
            body = self.parse_statement()
            self._expect_keyword("while")
            self._expect("OP", "(")
            condition = self.parse_expression()
            self._expect("OP", ")")
            self._expect("OP", ";")
            return DoWhileStmt(line=line, body=body, condition=condition)
        if self._accept_keyword("for"):
            line = self._previous().line
            self._expect("OP", "(")
            init: Optional[object]
            if self._is_type():
                init = self.parse_var_decl()
                self._expect("OP", ";")
            else:
                init_expr = None if self._check("OP", ";") else self.parse_expression()
                self._expect("OP", ";")
                init = ExprStmt(line=line, expr=init_expr)
            condition = None if self._check("OP", ";") else self.parse_expression()
            self._expect("OP", ";")
            update = None if self._check("OP", ")") else self.parse_expression()
            self._expect("OP", ")")
            body = self.parse_statement()
            return ForStmt(line=line, init=init, condition=condition, update=update, body=body)
        if self._accept_keyword("break"):
            line = self._previous().line
            self._expect("OP", ";")
            return BreakStmt(line=line)
        if self._accept_keyword("continue"):
            line = self._previous().line
            self._expect("OP", ";")
            return ContinueStmt(line=line)
        if self._accept_keyword("return"):
            line = self._previous().line
            value = None if self._check("OP", ";") else self.parse_expression()
            self._expect("OP", ";")
            return ReturnStmt(line=line, value=value)
        if self._check("OP", "{"):
            return self.parse_block()
        if self._is_type():
            decl = self.parse_var_decl()
            self._expect("OP", ";")
            return decl
        line = self._current().line
        expr = None if self._check("OP", ";") else self.parse_expression()
        self._expect("OP", ";")
        return ExprStmt(line=line, expr=expr)

    def parse_block(self) -> Block:
        left = self._expect("OP", "{")
        statements = []
        while not self._check("OP", "}"):
            if self._match("EOF"):
                raise ParseError("Unexpected end of input inside block.")
            statements.append(self.parse_statement())
        self._expect("OP", "}")
        return Block(line=left.line, statements=statements)

    def parse_var_decl(self) -> VarDecl:
        type_spec = self.parse_type_spec()
        items: List[DeclItem] = []
        while True:
            ident = self._expect("IDENT")
            array_size = None
            init = None
            if self._accept("OP", "["):
                array_size = self.parse_expression()
                self._expect("OP", "]")
            if self._accept("OP", "="):
                init = self.parse_expression()
            items.append(DeclItem(line=ident.line, name=ident.value, array_size=array_size, init=init))
            if not self._accept("OP", ","):
                break
        return VarDecl(line=items[0].line, type_spec=type_spec, items=items)

    def parse_type_spec(self) -> TypeSpec:
        token = self._expect("KEYWORD")
        if token.value not in TYPE_KEYWORDS:
            raise ParseError(f"Expected type at line {token.line}.")
        pointer = 0
        while self._accept("OP", "*"):
            pointer += 1
        if pointer > 1:
            raise ParseError("Multiple pointer levels are not supported.")
        return TypeSpec(base=token.value, pointer=pointer)

    def parse_params(self) -> List[Param]:
        params: List[Param] = []
        if self._accept("OP", ")"):
            return params
        if self._check("KEYWORD", "void") and self._peek(1).value == ")":
            self._advance()
            self._expect("OP", ")")
            return params
        while True:
            type_spec = self.parse_type_spec()
            name = self._expect("IDENT")
            params.append(Param(line=name.line, type_spec=type_spec, name=name.value))
            if self._accept("OP", ")"):
                break
            self._expect("OP", ",")
        return params

    def parse_expression(self) -> Expr:
        return self.parse_assignment()

    def parse_assignment(self) -> Expr:
        expr = self.parse_logical_or()
        if self._check("OP") and self._current().value in ASSIGN_OPS:
            op = self._advance().value
            value = self.parse_assignment()
            return AssignExpr(line=expr.line, op=op, target=expr, value=value)
        return expr

    def parse_logical_or(self) -> Expr:
        return self._left_assoc(self.parse_logical_and, {"||"})

    def parse_logical_and(self) -> Expr:
        return self._left_assoc(self.parse_bitwise_or, {"&&"})

    def parse_bitwise_or(self) -> Expr:
        return self._left_assoc(self.parse_bitwise_xor, {"|"})

    def parse_bitwise_xor(self) -> Expr:
        return self._left_assoc(self.parse_bitwise_and, {"^"})

    def parse_bitwise_and(self) -> Expr:
        return self._left_assoc(self.parse_equality, {"&"})

    def parse_equality(self) -> Expr:
        return self._left_assoc(self.parse_relational, {"==", "!="})

    def parse_relational(self) -> Expr:
        return self._left_assoc(self.parse_shift, {"<", "<=", ">", ">="})

    def parse_shift(self) -> Expr:
        return self._left_assoc(self.parse_additive, {"<<", ">>"})

    def parse_additive(self) -> Expr:
        return self._left_assoc(self.parse_multiplicative, {"+", "-"})

    def parse_multiplicative(self) -> Expr:
        return self._left_assoc(self.parse_unary, {"*", "/", "%"})

    def parse_unary(self) -> Expr:
        if self._check("OP") and self._current().value in {"-", "!", "~", "*", "&", "++", "--", "+"}:
            token = self._advance()
            operand = self.parse_unary()
            return UnaryOp(line=token.line, op=token.value, operand=operand)
        return self.parse_postfix()

    def parse_postfix(self) -> Expr:
        expr = self.parse_primary()
        while True:
            if self._accept("OP", "("):
                if not isinstance(expr, Identifier):
                    raise ParseError(f"Only direct function calls are supported at line {expr.line}.")
                args = []
                if not self._accept("OP", ")"):
                    while True:
                        args.append(self.parse_expression())
                        if self._accept("OP", ")"):
                            break
                        self._expect("OP", ",")
                expr = CallExpr(line=expr.line, callee=expr.name, args=args)
                continue
            if self._accept("OP", "["):
                index = self.parse_expression()
                self._expect("OP", "]")
                expr = IndexExpr(line=expr.line, target=expr, index=index)
                continue
            if self._check("OP") and self._current().value in {"++", "--"}:
                token = self._advance()
                expr = PostfixOp(line=expr.line, op=token.value, operand=expr)
                continue
            break
        return expr

    def parse_primary(self) -> Expr:
        token = self._current()
        if self._accept("NUMBER"):
            value = int(token.value, 16) if token.value.lower().startswith("0x") else int(token.value, 10)
            return IntLiteral(line=token.line, value=value)
        if self._accept("CHAR"):
            return CharLiteral(line=token.line, value=decode_escape(token.value))
        if self._accept("STRING"):
            return StringLiteral(line=token.line, value=decode_string(token.value))
        if self._accept("IDENT"):
            return Identifier(line=token.line, name=token.value)
        if self._accept("OP", "("):
            expr = self.parse_expression()
            self._expect("OP", ")")
            return expr
        raise ParseError(f"Unexpected token '{token.value}' at line {token.line}, expected expression.")

    def _left_assoc(self, parse_lower, operators: set[str]) -> Expr:
        expr = parse_lower()
        while self._check("OP") and self._current().value in operators:
            token = self._advance()
            rhs = parse_lower()
            expr = BinaryOp(line=token.line, op=token.value, left=expr, right=rhs)
        return expr

    def _is_type(self) -> bool:
        return self._check("KEYWORD") and self._current().value in TYPE_KEYWORDS

    def _accept(self, kind: str, value: Optional[str] = None) -> bool:
        if self._check(kind, value):
            self._advance()
            return True
        return False

    def _accept_keyword(self, value: str) -> bool:
        return self._accept("KEYWORD", value)

    def _expect_keyword(self, value: str) -> Token:
        return self._expect("KEYWORD", value)

    def _expect(self, kind: str, value: Optional[str] = None) -> Token:
        if not self._check(kind, value):
            current = self._current()
            wanted = value if value is not None else kind
            raise ParseError(f"Unexpected token '{current.value}' at line {current.line}, expected {wanted}.")
        return self._advance()

    def _check(self, kind: str, value: Optional[str] = None) -> bool:
        current = self._current()
        if current.kind != kind:
            return False
        return value is None or current.value == value

    def _match(self, kind: str) -> bool:
        return self._current().kind == kind

    def _current(self) -> Token:
        return self.tokens[self.index]

    def _peek(self, offset: int) -> Token:
        return self.tokens[self.index + offset]

    def _advance(self) -> Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def _previous(self) -> Token:
        return self.tokens[self.index - 1]


def decode_escape(value: str) -> int:
    mapping = {
        "n": "\n",
        "t": "\t",
        "0": "\0",
        "\\": "\\",
        "'": "'",
        '"': '"',
    }
    if value.startswith("\\"):
        return ord(mapping.get(value[1], value[1]))
    return ord(value)


def decode_string(value: str) -> str:
    result = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            result.append(chr(decode_escape(value[i : i + 2])))
            i += 2
        else:
            result.append(value[i])
            i += 1
    return "".join(result)
