# Small-C 互動式解譯器

本專案以 Python 3 實作一套 Small-C 互動式解譯器，包含詞法分析器、遞迴下降語法分析器、tree-walking interpreter、模擬記憶體模型、內建函式，以及帶有程式緩衝區管理指令的 REPL 互動環境。

## 執行方式

啟動互動模式：

```bash
python3 main.py
```

直接執行 `.sc` 程式檔：

```bash
python3 main.py tests/01_arithmetic.sc
```

執行內建測試：

```bash
python3 run_tests.py
```

## REPL 使用方式

進入互動模式後，畫面會出現 `sc>`。`sc>` 是提示符，不需要自己輸入，只要輸入後面的指令即可。

基本指令：

```text
HELP
ABOUT
CLEAR
QUIT
```

程式緩衝區操作：

```text
LOAD examples/primes.sc
LIST
LIST 1-10
CHECK
FUNCS
RUN
```

清空後載入另一個程式：

```text
NEW
LOAD examples/bubble_sort.sc
LIST 1-20
CHECK
RUN
```

展示追蹤模式：

```text
TRACE ON
RUN
TRACE OFF
```

## 即時輸入範例

以下程式碼可以直接在 `sc>` 後輸入，用來測試互動式執行。

算術優先順序：

```c
printf("%d\n", 2 + 3 * 4);
printf("%d\n", (2 + 3) * 4);
```

短路求值：

```c
int x = 0;
printf("%d\n", x && (10 / x));
printf("%d\n", 1 || (10 / x));
```

字元輸出：

```c
putchar(65);
putchar('\n');
```

字串長度：

```c
printf("%d\n", strlen("Hello World"));
```

指標操作：

```c
int a = 42;
int *p;
p = &a;
printf("%d\n", *p);
*p = 99;
printf("%d\n", a);
```

## Demo 建議流程

先在終端機啟動 REPL：

```bash
python3 main.py
```

進入 REPL 後，展示基本互動能力：

```text
HELP
printf("%d\n", 2 + 3 * 4);
int x = 0;
printf("%d\n", x && (10 / x));
printf("%d\n", strlen("Hello"));
putchar(65);
putchar('\n');
```

展示完整程式一：質數程式。

```text
LOAD examples/primes.sc
LIST 1-12
CHECK
FUNCS
RUN
```

展示完整程式二：泡沫排序。

```text
NEW
LOAD examples/bubble_sort.sc
LIST 1-20
CHECK
RUN
```

展示 TRACE：

```text
TRACE ON
RUN
TRACE OFF
```

離開 REPL：

```text
QUIT
```

最後在終端機執行全部測試：

```bash
python3 run_tests.py
```

## 測試與範例檔案

可用於 demo 的完整範例：

```text
examples/primes.sc
examples/bubble_sort.sc
```

所有測試 `.sc` 檔：

```text
tests/01_arithmetic.sc
tests/02_short_circuit.sc
tests/03_if_else.sc
tests/04_loops.sc
tests/05_arrays.sc
tests/06_strings.sc
tests/07_pointers.sc
tests/08_functions.sc
tests/09_recursion.sc
tests/10_runtime_error.sc
tests/11_syntax_error.sc
```

所有預期輸出 `.expected` 檔：

```text
tests/01_arithmetic.expected
tests/02_short_circuit.expected
tests/03_if_else.expected
tests/04_loops.expected
tests/05_arrays.expected
tests/06_strings.expected
tests/07_pointers.expected
tests/08_functions.expected
tests/09_recursion.expected
tests/10_runtime_error.expected
tests/11_syntax_error.expected
```

可直接複製的 `LOAD` 指令：

```text
LOAD tests/01_arithmetic.sc
LOAD tests/02_short_circuit.sc
LOAD tests/03_if_else.sc
LOAD tests/04_loops.sc
LOAD tests/05_arrays.sc
LOAD tests/06_strings.sc
LOAD tests/07_pointers.sc
LOAD tests/08_functions.sc
LOAD tests/09_recursion.sc
LOAD tests/10_runtime_error.sc
LOAD tests/11_syntax_error.sc
LOAD examples/primes.sc
LOAD examples/bubble_sort.sc
```

載入後可以直接執行：

```text
RUN
```

也可以先檢查再執行：

```text
CHECK
RUN
```

## 操作注意事項

- `sc>` 是提示符，不要自己輸入；只要輸入 `LOAD tests/01_arithmetic.sc` 即可。
- `LOAD` 指令不分大小寫，但檔案路徑和檔名要完全正確。
- `putchar(65);` 只會輸出 `A`，不會自動換行；需要再輸入 `putchar('\n');`。
- `strlen("Hello");` 只會回傳長度，不會自動輸出；要用 `printf("%d\n", strlen("Hello"));` 才看得到結果。
- `LOAD` 之後可以直接 `RUN`，中間加 `LIST`、`CHECK`、`FUNCS` 是為了 demo 更完整。

## 專案結構

- `main.py`：程式入口，可啟動 REPL 或直接執行檔案
- `lexer.py`：詞法分析與簡易 `#define` 前處理
- `parser.py`：具 C 風格運算子優先順序的遞迴下降語法分析器
- `ast_nodes.py`：抽象語法樹節點定義
- `interpreter.py`：執行期、求值器、內建函式、函式呼叫、陣列、指標與短路求值
- `memory.py`：以位元組為單位的模擬記憶體
- `symtable.py`：作用域與符號表管理
- `repl.py`：互動式命令列環境與程式緩衝區指令
- `tests/`：範例 `.sc` 測試程式與預期輸出
- `examples/`：適合展示或錄影使用的較完整範例程式
- `DEMO_GUIDE.md`：展示操作手冊與可直接複製的指令清單

## 已實作功能

- 型別：`int`、`char`、`int*`、`char*`
- 一維陣列
- 整數、字元、字串、十進位與十六進位常數
- 支援 postfix、unary、算術、位移、關係、相等、位元、邏輯與指定運算子的優先順序
- `&&` 與 `||` 的短路求值
- 敘述：`if`、`else`、`while`、`for`、`do/while`、`break`、`continue`、`return`
- 函式、參數傳遞、遞迴與 `main()`
- 內建函式：`printf`、`puts`、`scanf`、`strlen`、`strcpy`、`strcmp`、`strcat`、`abs`、`max`、`min`、`pow`、`sqrt`、`mod`、`rand`、`srand`、`memset`、`sizeof_int`、`sizeof_char`、`atoi`、`itoa`、`putchar`、`getchar`、`exit`
- REPL 指令：`LOAD`、`SAVE`、`LIST`、`EDIT`、`DELETE`、`INSERT`、`APPEND`、`NEW`、`RUN`、`CHECK`、`TRACE`、`VARS`、`FUNCS`、`HELP`、`ABOUT`、`CLEAR`、`QUIT`、`EXIT`

## 設計說明

本解譯器採用 tree-walking execution model，整體流程如下：

1. 先對原始碼做簡易 `#define NAME VALUE` 前處理。
2. 由 lexer 將原始碼切成 token。
3. 由 parser 使用遞迴下降法建立 AST。
4. 由 interpreter 直接走訪 AST 並執行。
5. 變數、陣列與指標都建立在模擬記憶體模型之上。

在本系統中，指標是以整數位址的形式模擬；`int` 佔 4 bytes，`char` 佔 1 byte。

## 模組協作流程

整體可以理解成一條解譯器流水線：

```text
main.py / repl.py
    ↓
lexer.py
    ↓
parser.py
    ↓
ast_nodes.py
    ↓
interpreter.py
    ↓
symtable.py + memory.py
```

`main.py` 是整個程式的入口，負責判斷使用者要進入互動模式，或是直接執行某個 `.sc` 檔案。若執行 `python3 main.py`，程式會啟動 REPL；若執行 `python3 main.py examples/primes.sc`，程式會直接讀取該 Small-C 檔案並執行。

`repl.py` 負責互動式環境，處理 `LOAD`、`LIST`、`CHECK`、`RUN`、`FUNCS` 等環境指令。當使用者輸入的是 Small-C 程式碼時，REPL 會把程式碼交給 interpreter 執行。

`lexer.py` 負責詞法分析，將 Small-C 原始碼切成 token。例如 `int x = 10;` 會被切成 `int`、`x`、`=`、`10`、`;` 等 token。這一步只負責切分文字，還不執行程式。

`parser.py` 負責語法分析，將 token 組成 AST。它也負責處理 C 風格的運算子優先順序，例如 `2 + 3 * 4` 會被解析成 `2 + (3 * 4)`，而不是 `(2 + 3) * 4`。

`ast_nodes.py` 定義 AST 的節點資料結構，例如 `IfStmt`、`ForStmt`、`BinaryOp`、`FunctionDef`。parser 會建立這些節點，interpreter 則依照節點內容執行。

`interpreter.py` 是核心執行器，負責走訪 AST 並真正執行程式。加減乘除、條件判斷、迴圈、函式呼叫、`return`、`break`、`continue`，以及 `&&` / `||` 的短路求值都在這裡處理。

`symtable.py` 是符號表，負責記錄變數名稱、型別、作用域與對應的記憶體位址。當程式使用變數時，interpreter 會透過符號表查出該變數的位置。

`memory.py` 是模擬記憶體，負責支援 `int`、`char`、陣列與指標。因為 Python 不會直接提供 C 語言式的位址操作，所以本專案用自訂的記憶體模型模擬 `&` 取址與 `*` 解參考。

簡化來說，`main.py` / `repl.py` 負責接收輸入，`lexer.py` 負責切 token，`parser.py` 負責建立 AST，`interpreter.py` 負責執行 AST，`symtable.py` 負責查變數，`memory.py` 負責模擬 C 語言的記憶體與指標。

## 目前限制

- 只支援簡單的 object-like `#define`
- 可變參數內建函式僅支援作業要求範圍內的格式化功能
- 尚未實作 `switch/case`
- 不支援前向宣告與多層指標
- 單次執行期間不會回收記憶體，但每次 `RUN` 前會重設執行環境
