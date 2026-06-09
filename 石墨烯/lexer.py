from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


KEYWORDS = {
    "int",
    "char",
    "void",
    "if",
    "else",
    "while",
    "for",
    "do",
    "break",
    "continue",
    "return",
}


MULTI_OPERATORS = [
    ">>=",
    "<<=",
    "++",
    "--",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "==",
    "!=",
    "<=",
    ">=",
    "&&",
    "||",
    "<<",
    ">>",
]


SINGLE_OPERATORS = set("+-*/%(){}[];,<>!=&|^~")


@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int


class LexError(Exception):
    pass


def preprocess(source: str) -> str:
    defines: Dict[str, str] = {}
    output: List[str] = []
    for raw_line in source.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if stripped.startswith("#define"):
            parts = stripped.split(maxsplit=2)
            if len(parts) != 3:
                raise LexError("Only simple #define NAME VALUE is supported.")
            _, name, value = parts
            defines[name] = value
            continue
        for name, value in defines.items():
            line = replace_identifier(line, name, value)
        output.append(line)
    return "\n".join(output)


def replace_identifier(text: str, name: str, value: str) -> str:
    result: List[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"' or ch == "'":
            quote = ch
            start = i
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            result.append(text[start:i])
            continue
        if ch.isalpha() or ch == "_":
            start = i
            i += 1
            while i < len(text) and (text[i].isalnum() or text[i] == "_"):
                i += 1
            ident = text[start:i]
            result.append(value if ident == name else ident)
            continue
        result.append(ch)
        i += 1
    return "".join(result)


class Lexer:
    def __init__(self, source: str):
        self.source = preprocess(source)
        self.length = len(self.source)
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while not self._eof():
            ch = self._peek()
            if ch in " \t\r":
                self._advance()
                continue
            if ch == "\n":
                self._advance()
                continue
            if ch == "/" and self._peek(1) == "/":
                self._skip_line_comment()
                continue
            if ch == "/" and self._peek(1) == "*":
                self._skip_block_comment()
                continue
            if ch.isalpha() or ch == "_":
                tokens.append(self._identifier())
                continue
            if ch.isdigit():
                tokens.append(self._number())
                continue
            if ch == "'":
                tokens.append(self._char_literal())
                continue
            if ch == '"':
                tokens.append(self._string_literal())
                continue
            multi = next((op for op in MULTI_OPERATORS if self.source.startswith(op, self.index)), None)
            if multi:
                tokens.append(self._make_token("OP", multi, len(multi)))
                continue
            if ch in SINGLE_OPERATORS:
                tokens.append(self._make_token("OP", ch, 1))
                continue
            raise LexError(f"Unexpected character {ch!r} at line {self.line}, column {self.column}.")
        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens

    def _identifier(self) -> Token:
        line, column = self.line, self.column
        start = self.index
        while not self._eof() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        value = self.source[start:self.index]
        kind = "KEYWORD" if value in KEYWORDS else "IDENT"
        return Token(kind, value, line, column)

    def _number(self) -> Token:
        line, column = self.line, self.column
        start = self.index
        if self.source.startswith(("0x", "0X"), self.index):
            self._advance()
            self._advance()
            while not self._eof() and (self._peek().isdigit() or self._peek().lower() in "abcdef"):
                self._advance()
        else:
            while not self._eof() and self._peek().isdigit():
                self._advance()
        return Token("NUMBER", self.source[start:self.index], line, column)

    def _char_literal(self) -> Token:
        line, column = self.line, self.column
        self._advance()
        if self._eof():
            raise LexError(f"Unterminated character literal at line {line}.")
        if self._peek() == "\\":
            value = "\\" + self._peek(1)
            self._advance()
            self._advance()
        else:
            value = self._peek()
            self._advance()
        if self._peek() != "'":
            raise LexError(f"Unterminated character literal at line {line}.")
        self._advance()
        return Token("CHAR", value, line, column)

    def _string_literal(self) -> Token:
        line, column = self.line, self.column
        self._advance()
        pieces: List[str] = []
        while not self._eof():
            ch = self._peek()
            if ch == '"':
                self._advance()
                return Token("STRING", "".join(pieces), line, column)
            if ch == "\\":
                pieces.append("\\" + self._peek(1))
                self._advance()
                self._advance()
                continue
            pieces.append(ch)
            self._advance()
        raise LexError(f"Unterminated string literal at line {line}.")

    def _skip_line_comment(self) -> None:
        while not self._eof() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        self._advance()
        self._advance()
        while not self._eof():
            if self._peek() == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                return
            self._advance()
        raise LexError("Unterminated block comment.")

    def _make_token(self, kind: str, value: str, width: int) -> Token:
        token = Token(kind, value, self.line, self.column)
        for _ in range(width):
            self._advance()
        return token

    def _peek(self, offset: int = 0) -> str:
        if self.index + offset >= self.length:
            return "\0"
        return self.source[self.index + offset]

    def _advance(self) -> None:
        if self._eof():
            return
        ch = self.source[self.index]
        self.index += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

    def _eof(self) -> bool:
        return self.index >= self.length
