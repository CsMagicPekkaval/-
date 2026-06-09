from __future__ import annotations

import sys

from interpreter import Interpreter, ParseError, RuntimeErrorSC
from lexer import LexError
from repl import SmallCRepl


def main() -> None:
    # 如果有提供 .sc 檔名就直接執行該程式。
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        with open(filename, "r", encoding="utf-8") as fh:
            source = fh.read()

        # 將原始碼載入解譯器的程式緩衝區，接著執行。
        interpreter = Interpreter()
        interpreter.load_buffer(source)
        try:
            for line in interpreter.run_buffer():
                print(line)
        except (LexError, ParseError, RuntimeErrorSC) as exc:
            # 以簡單的命令列格式回報語法錯誤或執行期錯誤。
            print(f"Error: {exc}")
            sys.exit(1)
        return

    # 如果沒有提供檔名，就啟動互動式 Small-C REPL。
    SmallCRepl().run()


if __name__ == "__main__":
    # Python 標準入口點寫法，直接執行 main.py 時會呼叫 main()。
    main()
