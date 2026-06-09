from __future__ import annotations

from dataclasses import dataclass
from typing import List

from interpreter import Interpreter, RuntimeErrorSC
from lexer import LexError
from parser import ParseError


COMMANDS = {
    "LOAD",
    "SAVE",
    "LIST",
    "EDIT",
    "DELETE",
    "INSERT",
    "APPEND",
    "NEW",
    "RUN",
    "CHECK",
    "TRACE",
    "VARS",
    "FUNCS",
    "HELP",
    "ABOUT",
    "CLEAR",
    "QUIT",
    "EXIT",
}


@dataclass
class ReplResult:
    should_exit: bool = False


class SmallCRepl:
    def __init__(self) -> None:
        self.interpreter = Interpreter()
        self.dirty = False

    def run(self) -> None:
        print("=" * 48)
        print("Small-C Interactive Interpreter v1.0")
        print("System Software Final Project")
        print("=" * 48)
        print("Type 'HELP' for a list of commands.")
        while True:
            try:
                line = input("sc> ")
            except EOFError:
                print()
                break
            if not line.strip():
                continue
            result = self.handle_line(line)
            if result.should_exit:
                break

    def handle_line(self, line: str) -> ReplResult:
        stripped = normalize_prompt(line)
        command = stripped.split(maxsplit=1)[0].upper()
        if command in COMMANDS and is_command_context(stripped):
            return self._handle_command(stripped)
        source = self._collect_multiline(stripped)
        try:
            self.interpreter.execute_snippet(source)
        except (LexError, ParseError, RuntimeErrorSC) as exc:
            print(f"Error: {exc}")
        return ReplResult()

    def _handle_command(self, command_line: str) -> ReplResult:
        parts = command_line.split(maxsplit=1)
        command = parts[0].upper()
        arg = parts[1] if len(parts) > 1 else ""
        try:
            if command == "LOAD":
                self._cmd_load(arg)
            elif command == "SAVE":
                self._cmd_save(arg)
            elif command == "LIST":
                self._cmd_list(arg)
            elif command == "EDIT":
                self._cmd_edit(arg)
            elif command == "DELETE":
                self._cmd_delete(arg)
            elif command == "INSERT":
                self._cmd_insert(arg)
            elif command == "APPEND":
                self._cmd_append()
            elif command == "NEW":
                self._cmd_new()
            elif command == "RUN":
                for line in self.interpreter.run_buffer():
                    print(line)
            elif command == "CHECK":
                self.interpreter.check_source(self.interpreter.buffer_source())
                print("No errors found.")
            elif command == "TRACE":
                self._cmd_trace(arg)
            elif command == "VARS":
                lines = self.interpreter.list_variables()
                print("\n".join(lines or ["No global variables."]))
            elif command == "FUNCS":
                source = self.interpreter.buffer_source()
                lines = self.interpreter.preview_functions(source) if source.strip() else self.interpreter.list_functions()
                print("\n".join(lines or ["No functions defined."]))
            elif command == "HELP":
                print(help_text(arg))
            elif command == "ABOUT":
                print("Small-C Interactive Interpreter v1.0")
            elif command == "CLEAR":
                print("\033[2J\033[H", end="")
            elif command in {"QUIT", "EXIT"}:
                if self.dirty:
                    confirm = input("Unsaved changes. Quit anyway? (y/N) ")
                    if confirm.strip().lower() != "y":
                        return ReplResult()
                print("Goodbye.")
                return ReplResult(should_exit=True)
        except (OSError, ValueError, LexError, ParseError, RuntimeErrorSC) as exc:
            print(f"Error: {exc}")
        return ReplResult()

    def _cmd_load(self, filename: str) -> None:
        if not filename:
            raise ValueError("LOAD requires a filename.")
        if not self._confirm_discard("Load a file and replace the current buffer"):
            return
        with open(filename, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        self.interpreter.set_buffer_lines(lines)
        self.dirty = False
        print(f"Loaded {len(lines)} lines from '{filename}'.")

    def _cmd_save(self, filename: str) -> None:
        if not filename:
            raise ValueError("SAVE requires a filename.")
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(self.interpreter.buffer_source())
            if self.interpreter.buffer_lines:
                fh.write("\n")
        self.dirty = False
        print(f"Saved {len(self.interpreter.buffer_lines)} lines to '{filename}'.")

    def _cmd_list(self, arg: str) -> None:
        lines = self.interpreter.buffer_lines
        if not lines:
            print("Program buffer is empty.")
            return
        start, end = parse_range(arg, len(lines))
        for idx in range(start, end + 1):
            print(f"{idx}: {lines[idx - 1]}")

    def _cmd_edit(self, arg: str) -> None:
        n = int(arg.strip())
        lines = self.interpreter.buffer_lines
        if not (1 <= n <= len(lines)):
            raise ValueError("EDIT line out of range.")
        print(f"{n}: {lines[n - 1]}")
        new_text = input(f"{n}> ")
        if new_text:
            lines[n - 1] = new_text
            self.dirty = True

    def _cmd_delete(self, arg: str) -> None:
        lines = self.interpreter.buffer_lines
        if not lines:
            return
        start, end = parse_range(arg, len(lines))
        del lines[start - 1 : end]
        self.dirty = True

    def _cmd_insert(self, arg: str) -> None:
        n = int(arg.strip())
        if n < 1 or n > len(self.interpreter.buffer_lines) + 1:
            raise ValueError("INSERT line out of range.")
        new_lines = self._collect_buffer_input(n)
        self.interpreter.buffer_lines[n - 1 : n - 1] = new_lines
        self.dirty = True

    def _cmd_append(self) -> None:
        start = len(self.interpreter.buffer_lines) + 1
        new_lines = self._collect_buffer_input(start)
        self.interpreter.buffer_lines.extend(new_lines)
        self.dirty = True

    def _cmd_new(self) -> None:
        if not self._confirm_discard("Clear the current buffer and reset runtime state"):
            return
        self.interpreter.set_buffer_lines([])
        self.interpreter.reset_runtime()
        self.dirty = False
        print("All cleared.")

    def _cmd_trace(self, arg: str) -> None:
        mode = arg.strip().upper()
        if mode == "ON":
            self.interpreter.trace_enabled = True
            print("Trace mode enabled.")
        elif mode == "OFF":
            self.interpreter.trace_enabled = False
            print("Trace mode disabled.")
        else:
            raise ValueError("TRACE expects ON or OFF.")

    def _collect_buffer_input(self, start_line: int) -> List[str]:
        lines: List[str] = []
        current = start_line
        while True:
            line = input(f"{current}> ")
            if line.strip() == ".":
                break
            lines.append(line)
            current += 1
        return lines

    def _collect_multiline(self, first_line: str) -> str:
        lines = [first_line]
        brace_depth = first_line.count("{") - first_line.count("}")
        while brace_depth > 0:
            line = input("> ")
            lines.append(line)
            brace_depth += line.count("{") - line.count("}")
        return "\n".join(lines)

    def _confirm_discard(self, action: str) -> bool:
        if not self.dirty:
            return True
        confirm = input(f"{action}? Unsaved buffer changes will be lost. (y/N) ")
        return confirm.strip().lower() == "y"


def parse_range(arg: str, total: int) -> tuple[int, int]:
    arg = arg.strip()
    if not arg:
        return 1, total
    if "-" in arg:
        left, right = arg.split("-", 1)
        start = int(left)
        end = int(right)
    else:
        start = end = int(arg)
    if start < 1 or end > total or start > end:
        raise ValueError("Line range out of bounds.")
    return start, end


def is_command_context(text: str) -> bool:
    return ";" not in text and not text.endswith("{")


def normalize_prompt(text: str) -> str:
    stripped = text.strip()
    if stripped.lower().startswith("sc>"):
        return stripped[3:].strip()
    return stripped


def help_text(command: str) -> str:
    details = {
        "LOAD": "LOAD <filename>: replace the current buffer with a Small-C source file.",
        "SAVE": "SAVE <filename>: write the current program buffer to disk.",
        "LIST": "LIST [n | n1-n2]: show the whole buffer or a selected line range.",
        "EDIT": "EDIT <n>: replace one existing line. Press Enter to keep the old line.",
        "DELETE": "DELETE <n | n1-n2>: remove one line or a line range from the buffer.",
        "INSERT": "INSERT <n>: insert new lines before line n. Enter a single '.' to finish.",
        "APPEND": "APPEND: add new lines at the end of the buffer. Enter a single '.' to finish.",
        "NEW": "NEW: clear the program buffer and reset all runtime state.",
        "RUN": "RUN: execute the current buffer, starting from main().",
        "CHECK": "CHECK: parse and validate the current buffer without executing it.",
        "TRACE": "TRACE ON | OFF: enable or disable per-statement execution tracing during RUN.",
        "VARS": "VARS: show current global variables and their values.",
        "FUNCS": "FUNCS: list user-defined functions and built-ins.",
        "HELP": "HELP [command]: show the command summary or detailed help for one command.",
        "ABOUT": "ABOUT: show interpreter version information.",
        "CLEAR": "CLEAR: clear the terminal screen.",
        "QUIT": "QUIT: leave the interpreter, with confirmation if the buffer is dirty.",
        "EXIT": "EXIT: same as QUIT.",
    }
    if not command:
        return (
            "Commands: LOAD SAVE LIST EDIT DELETE INSERT APPEND NEW RUN CHECK TRACE VARS FUNCS HELP ABOUT CLEAR QUIT EXIT\n"
            "Use HELP <command> for details."
        )
    key = command.strip().upper()
    return details.get(key, f"Unknown command '{key}'.")
