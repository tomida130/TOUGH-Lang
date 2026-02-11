"""TOUGH REPL - 対話型シェル (LLVM 版)"""

import sys
from tough.compiler import Compiler
from tough.lexer import LexerError
from tough.parser import ParseError
from tough.codegen import CodeGenError


def repl() -> None:
    """TOUGH の対話型シェル（REPL）を起動する"""
    print("=" * 50)
    print("  TOUGH 言語 v0.2.0 - LLVM コンパイラ")
    print("  終了するには「逃げるんかいっ」または Ctrl+C")
    print("=" * 50)
    print()

    compiler = Compiler()
    buffer: list[str] = []
    brace_depth = 0

    while True:
        try:
            if brace_depth > 0:
                prompt = "...> "
            else:
                prompt = "tough> "

            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n逃げるんかいっ！")
            break

        # ブレース深度を追跡して複数行入力に対応
        brace_depth += line.count("{") - line.count("}")
        buffer.append(line)

        # ブレースが閉じていない場合は次の行を待つ
        if brace_depth > 0:
            continue

        # バッファの内容をコンパイル＆実行
        source = "\n".join(buffer)
        buffer.clear()
        brace_depth = 0

        if not source.strip():
            continue

        try:
            compiler.run(source)
        except SystemExit:
            print("逃げるんかいっ！")
            break
        except (LexerError, ParseError, CodeGenError) as e:
            print(f"【エラー】{e}", file=sys.stderr)
        except Exception as e:
            print(f"【実行エラー】{e}", file=sys.stderr)
