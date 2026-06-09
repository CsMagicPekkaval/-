from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ast_nodes import TypeSpec


@dataclass
class Symbol:
    name: str
    type_spec: TypeSpec
    address: int
    array_length: Optional[int] = None
    is_function: bool = False

    @property
    def total_size(self) -> int:
        return self.type_spec.size * (self.array_length or 1)


class Scope:
    def __init__(self, parent: Optional["Scope"] = None):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            raise ValueError(f"Redeclaration of '{symbol.name}'.")
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        scope: Optional[Scope] = self
        while scope is not None:
            symbol = scope.symbols.get(name)
            if symbol is not None:
                return symbol
            scope = scope.parent
        return None
