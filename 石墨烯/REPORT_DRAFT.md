# Small-C Interactive Interpreter Report Draft

## 1. Project Overview

This project implements a Small-C interactive interpreter in Python 3. The goal is to provide a REPL-like environment that can:

- accept direct Small-C statements,
- manage a program buffer,
- parse and execute complete Small-C programs,
- support variables, functions, arrays, pointers, control flow, and built-in functions.

## 2. System Architecture

The system is divided into the following modules:

- `lexer.py`: lexical analysis and simple `#define` preprocessing
- `parser.py`: recursive-descent parsing with explicit operator-precedence levels
- `ast_nodes.py`: AST node definitions
- `interpreter.py`: semantic analysis and execution engine
- `memory.py`: simulated memory model
- `symtable.py`: symbol tables and lexical scopes
- `repl.py`: interactive shell and environment commands
- `main.py`: top-level entry point

## 3. Data Flow

1. The user inputs Small-C source code from the REPL or loads it from a file.
2. The lexer converts source text into tokens.
3. The parser consumes tokens and builds an AST.
4. The interpreter walks the AST and executes statements.
5. Variables and arrays are mapped into simulated memory.
6. REPL commands operate on the program buffer or the runtime state.

## 4. Memory Model

The interpreter uses a byte-addressable simulated memory space.

- `int` values occupy 4 bytes.
- `char` values occupy 1 byte.
- pointers are represented internally as integer addresses.
- arrays occupy contiguous memory.

This design allows pointer dereference, address-of, array indexing, and basic pointer arithmetic.

## 5. Parsing Strategy

The parser is implemented with recursive descent. Each precedence level is handled by a dedicated parsing function:

- postfix
- unary
- multiplicative
- additive
- shift
- relational
- equality
- bitwise AND / XOR / OR
- logical AND / OR
- assignment

This structure ensures that operator precedence and associativity match the required Small-C subset.

## 6. Execution Strategy

The interpreter uses tree-walking evaluation.

- expressions evaluate to runtime values,
- statements are executed recursively,
- loops use control signals for `break` and `continue`,
- functions use a return signal to unwind execution,
- recursion is supported through nested call frames.

Short-circuit evaluation is implemented for `&&` and `||`, so the right-hand side is evaluated only when needed.

## 7. Built-in Functions

Implemented built-ins include:

- I/O: `printf`, `puts`, `scanf`, `putchar`, `getchar`
- string: `strlen`, `strcpy`, `strcmp`, `strcat`
- math: `abs`, `max`, `min`, `pow`, `sqrt`, `mod`, `rand`, `srand`
- utilities: `memset`, `sizeof_int`, `sizeof_char`, `atoi`, `itoa`, `exit`

## 8. REPL Environment Commands

Implemented commands include:

- program buffer management: `LOAD`, `SAVE`, `LIST`, `EDIT`, `DELETE`, `INSERT`, `APPEND`, `NEW`
- execution and debugging: `RUN`, `CHECK`, `TRACE`, `VARS`, `FUNCS`
- system commands: `HELP`, `ABOUT`, `CLEAR`, `QUIT`, `EXIT`

## 9. Testing Strategy

The project includes a sample test suite in `tests/` with expected outputs.

Covered areas:

- arithmetic and precedence
- short-circuit logic
- conditionals
- loops
- arrays
- strings
- pointers
- function calls
- recursion
- runtime and syntax error handling

The helper script `run_tests.py` runs all sample cases automatically.

## 10. Known Limitations

- `switch/case` is not implemented.
- only simple object-like `#define` is supported.
- multi-level pointers are not supported.
- forward declarations are not supported.
- runtime memory is reset before `RUN`, but is not reclaimed during a single execution session.

## 11. Development Notes

The implementation followed a bottom-up strategy:

1. expression parsing and precedence
2. variable declaration and assignment
3. control flow
4. functions and recursion
5. arrays and pointers
6. REPL commands
7. tests and documentation

## 12. Future Improvements

- implement `switch/case`
- improve semantic checking before execution
- expand `HELP <command>` details
- refine `scanf` and terminal input behavior
- add richer diagnostics for parser recovery
