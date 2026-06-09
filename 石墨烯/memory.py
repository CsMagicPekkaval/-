from __future__ import annotations

from typing import Dict, List


class MemoryErrorSC(Exception):
    pass


class Memory:
    def __init__(self) -> None:
        self.bytes: Dict[int, int] = {}
        self.heap_top = 1000
        self.allocations: Dict[int, int] = {}

    def reset(self) -> None:
        self.bytes.clear()
        self.heap_top = 1000
        self.allocations.clear()

    def allocate(self, size: int) -> int:
        if size <= 0:
            raise MemoryErrorSC("Cannot allocate non-positive memory size.")
        addr = self.heap_top
        self.heap_top += size
        self.allocations[addr] = size
        for i in range(size):
            self.bytes[addr + i] = 0
        return addr

    def read_char(self, addr: int) -> int:
        self._check_address(addr)
        value = self.bytes.get(addr, 0)
        return value if value < 128 else value - 256

    def write_char(self, addr: int, value: int) -> None:
        self._check_address(addr)
        self.bytes[addr] = value & 0xFF

    def read_int(self, addr: int) -> int:
        self._check_span(addr, 4)
        value = 0
        for i in range(4):
            value |= (self.bytes.get(addr + i, 0) & 0xFF) << (8 * i)
        if value & 0x80000000:
            value -= 0x100000000
        return value

    def write_int(self, addr: int, value: int) -> None:
        self._check_span(addr, 4)
        value &= 0xFFFFFFFF
        for i in range(4):
            self.bytes[addr + i] = (value >> (8 * i)) & 0xFF

    def read_c_string(self, addr: int) -> str:
        chars: List[str] = []
        while True:
            value = self.bytes.get(addr, 0)
            if value == 0:
                break
            chars.append(chr(value))
            addr += 1
        return "".join(chars)

    def write_c_string(self, addr: int, value: str, max_size: int | None = None) -> None:
        encoded = value.encode("utf-8")
        if max_size is not None and len(encoded) + 1 > max_size:
            raise MemoryErrorSC("String write exceeds destination size.")
        for index, byte in enumerate(encoded):
            self.write_char(addr + index, byte)
        self.write_char(addr + len(encoded), 0)

    def memset(self, addr: int, value: int, size: int) -> None:
        self._check_span(addr, size)
        for i in range(size):
            self.bytes[addr + i] = value & 0xFF

    def allocation_size(self, addr: int) -> int | None:
        return self.allocations.get(addr)

    def _check_address(self, addr: int) -> None:
        if not any(base <= addr < base + size for base, size in self.allocations.items()):
            raise MemoryErrorSC(f"Invalid memory access at address {addr}.")

    def _check_span(self, addr: int, size: int) -> None:
        for offset in range(size):
            self._check_address(addr + offset)
