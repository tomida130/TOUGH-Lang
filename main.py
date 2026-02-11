"""TOUGH 言語 - エントリポイント

使い方:
    python main.py                          # REPL（対話型シェル）を起動
    python main.py script.tough             # ファイルをコンパイル＆実行
    python main.py --emit-ir script.tough   # LLVM IR を表示
"""

import sys
import os

# プロジェクトルートを sys.path に追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tough.compiler import Compiler
from tough.lexer import LexerError
from tough.parser import ParseError
from tough.codegen import CodeGenError
from tough.repl import repl


def main():
    if len(sys.argv) == 1:
        # 引数なし → REPL 起動
        repl()
    elif len(sys.argv) == 2:
        filepath = sys.argv[1]
        if not os.path.isfile(filepath):
            print(f"エラー: ファイルが見つかりません: {filepath}", file=sys.stderr)
            sys.exit(1)
        try:
            compiler = Compiler()
            compiler.run_file(filepath)
        except (LexerError, ParseError, CodeGenError) as e:
            print(f"【エラー】{e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"【実行エラー】{e}", file=sys.stderr)
            sys.exit(1)
    elif len(sys.argv) == 3 and sys.argv[1] == "--emit-ir":
        # --emit-ir: LLVM IR を表示
        filepath = sys.argv[2]
        if not os.path.isfile(filepath):
            print(f"エラー: ファイルが見つかりません: {filepath}", file=sys.stderr)
            sys.exit(1)
        try:
            compiler = Compiler()
            llvm_ir = compiler.emit_ir_file(filepath)
            print("--- LLVM IR ---")
            print(llvm_ir)
        except (LexerError, ParseError, CodeGenError) as e:
            print(f"【エラー】{e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
