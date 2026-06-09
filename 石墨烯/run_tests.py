from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).parent
    tests_dir = root / "tests"
    cases = sorted(tests_dir.glob("*.sc"))
    failed = 0
    for case in cases:
        expected = case.with_suffix(".expected").read_text(encoding="utf-8").strip()
        proc = subprocess.run(
            [sys.executable, str(root / "main.py"), str(case)],
            capture_output=True,
            text=True,
            cwd=root,
        )
        actual = proc.stdout.strip()
        ok = actual == expected
        print(f"[{'PASS' if ok else 'FAIL'}] {case.name}")
        if not ok:
            failed += 1
            print("Expected:")
            print(expected)
            print("Actual:")
            print(actual)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
