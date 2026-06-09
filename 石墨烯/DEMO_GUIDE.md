# Small-C 解譯器 Demo 操作手冊

這份檔案是 demo 時用來直接複製指令的操作清單。  
注意：畫面上出現的 `sc>` 是提示符，不需要自己輸入。

## 1. 啟動方式

在終端機執行互動式 REPL：

```bash
python3 main.py
```

直接執行單一 Small-C 檔案：

```bash
python3 main.py examples/primes.sc
```

一次執行全部測試：

```bash
python3 run_tests.py
```

## 2. REPL 基本指令

以下指令是在進入 `python3 main.py` 之後輸入。

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

清空後載入另一個範例：

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

## 3. 即時輸入測試

以下指令可以直接在 `sc>` 後輸入，用來展示互動式執行。

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

## 4. Demo 流程

先啟動 REPL：

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

最後在終端機跑全部測試：

```bash
python3 run_tests.py
```

## 5. 範例檔案清單

可用於 demo 的完整範例：

```text
examples/primes.sc
examples/bubble_sort.sc
```

直接執行範例：

```bash
python3 main.py examples/primes.sc
python3 main.py examples/bubble_sort.sc
```

在 REPL 中載入範例：

```text
LOAD examples/primes.sc
LOAD examples/bubble_sort.sc
```

## 6. 測試檔案清單

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

## 7. 可直接複製的 LOAD 指令

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

## 8. 常見注意事項

- `sc>` 是提示符，不要自己輸入；只要輸入 `LOAD tests/01_arithmetic.sc` 即可。
- `LOAD` 指令不分大小寫，但檔案路徑和檔名要完全正確。
- `putchar(65);` 只會輸出 `A`，不會自動換行；需要再輸入 `putchar('\n');`。
- `strlen("Hello");` 只會回傳長度，不會自動輸出；要用 `printf("%d\n", strlen("Hello"));` 才看得到結果。
- `LOAD` 之後可以直接 `RUN`，中間加 `LIST`、`CHECK`、`FUNCS` 是為了 demo 更完整。
