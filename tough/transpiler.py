"""TOUGH → Python トランスパイラ

TOUGH ソースコードの各行を正規表現でマッチし、
対応する Python コードに変換する。
"""

import re
import sys


class ToughTranspileError(Exception):
    """トランスパイル時エラー"""

    def __init__(self, message: str, line_number: int = 0):
        self.line_number = line_number
        super().__init__(f"行 {line_number}: {message}")


class ToughTranspiler:
    """TOUGH ソースコードを Python コードに変換するトランスパイラ"""

    def __init__(self):
        self._indent_level = 0
        self._indent_stack: list[int] = []

    def _indent(self) -> str:
        """現在のインデントレベルに応じた空白文字列を返す"""
        return "    " * self._indent_level

    def _open_block(self) -> None:
        """新しいブロックを開く（インデントレベルを1上げる）"""
        self._indent_stack.append(self._indent_level)
        self._indent_level += 1

    def _close_block(self) -> None:
        """ブロックを閉じる（インデントレベルを戻す）"""
        if self._indent_stack:
            self._indent_level = self._indent_stack.pop()
        else:
            self._indent_level = max(0, self._indent_level - 1)

    def _transpile_line(self, line: str, line_number: int) -> str | None:
        """1行のTOUGHコードをPythonコードに変換する

        Returns:
            変換後のPython行。スキップすべき行の場合は None。
        """
        stripped = line.strip()

        # --- 空行 ---
        if not stripped:
            return ""

        # --- ブロック終了のみ: } ---
        if stripped == "}":
            self._close_block()
            return None  # Python ではブロック終了記号は不要

        # --- コメント: （○○のコメント）コメント内容 ---
        # （○○のコメント）が Python の # に相当。○○は何でも良い。
        m = re.match(r"^（(.+?)のコメント）(.*)$", stripped)
        if m:
            comment_text = m.group(2).strip()
            if comment_text:
                return f"{self._indent()}# {comment_text}"
            return f"{self._indent()}# {m.group(1)}のコメント"

        # --- プログラム開始: 我が名は　尊鷹 / 我が名は 尊鷹 ---
        if re.match(r"^我が名は[　\s]+尊鷹$", stripped):
            return f"{self._indent()}import sys"

        # --- プログラム終了: 逃げるんかいっ ---
        if stripped == "逃げるんかいっ":
            return f"{self._indent()}sys.exit(0)"

        # --- 変数宣言: Xだ Xが正体を現すぞ ---
        m = re.match(r"^(.+?)だ\s+\1が正体を現すぞ$", stripped)
        if m:
            var_name = m.group(1).strip()
            return f"{self._indent()}{var_name} = None"

        # --- 代入: (値) を継ぐ (変数) ---
        m = re.match(r"^(.+?)\s+を継ぐ\s+(.+)$", stripped)
        if m:
            value = self._transpile_expr(m.group(1).strip())
            var_name = m.group(2).strip()
            return f"{self._indent()}{var_name} = {value}"

        # --- 出力: (値) しゃあっ ---
        m = re.match(r"^(.+?)\s+しゃあっ$", stripped)
        if m:
            value = self._transpile_expr(m.group(1).strip())
            return f"{self._indent()}print({value})"

        # --- 入力: (変数) を教えてくれよ ---
        m = re.match(r"^(.+?)\s+を教えてくれよ$", stripped)
        if m:
            var_name = m.group(1).strip()
            return f"{self._indent()}{var_name} = input()"

        # --- インクリメント: (変数) 進化したと言うてくれや ---
        m = re.match(r"^(.+?)\s+進化したと言うてくれや$", stripped)
        if m:
            var_name = m.group(1).strip()
            return f"{self._indent()}{var_name} += 1"

        # --- デクリメント: (変数) （哀） ---
        m = re.match(r"^(.+?)\s+（哀）$", stripped)
        if m:
            var_name = m.group(1).strip()
            return f"{self._indent()}{var_name} -= 1"

        # --- 関数定義: 自分たちの手で作るから尊いんだ (関数)が ((引数))るんだ { ---
        m = re.match(
            r"^自分たちの手で作るから尊いんだ\s+(.+?)が\s+\((.+?)\)るんだ\s*\{$",
            stripped,
        )
        if m:
            func_name = m.group(1).strip()
            args = m.group(2).strip()
            result = f"{self._indent()}def {func_name}({args}):"
            self._open_block()
            return result

        # --- if: なにっ ((条件)) { ---
        m = re.match(r"^なにっ\s+\((.+?)\)\s*\{$", stripped)
        if m:
            condition = self._transpile_expr(m.group(1).strip())
            result = f"{self._indent()}if {condition}:"
            self._open_block()
            return result

        # --- elif: いやちょっとまてよ ((条件)) { ---
        # } で閉じた直後に来るので、前のブロックは既に閉じている
        m = re.match(r"^いやちょっとまてよ\s+\((.+?)\)\s*\{$", stripped)
        if m:
            condition = self._transpile_expr(m.group(1).strip())
            result = f"{self._indent()}elif {condition}:"
            self._open_block()
            return result

        # --- else: う　あ　あ　あ　あ（ＰＣ書き文字） { ---
        m = re.match(r"^う[　\s]+あ[　\s]+あ[　\s]+あ[　\s]+あ[（(]\s*[ＰP][ＣC]書き文字\s*[）)]\s*\{$", stripped)
        if m:
            result = f"{self._indent()}else:"
            self._open_block()
            return result

        # --- while: 禁断の"((条件))度打ち" { ---
        m = re.match(r'^禁断の[""「](.+?)度打ち[""」]\s*\{$', stripped)
        if m:
            condition = self._transpile_expr(m.group(1).strip())
            result = f"{self._indent()}while {condition}:"
            self._open_block()
            return result

        # --- 例外捕捉: } (変数) はルールで禁止スよね { ---
        m = re.match(r"^\}\s*(.+?)\s+はルールで禁止スよね\s*\{$", stripped)
        if m:
            var_name = m.group(1).strip()
            self._close_block()
            result = f"{self._indent()}except Exception as {var_name}:"
            self._open_block()
            return result

        # --- 例外送出: はっきり言ってそれって病気だから お前死ぬよ ---
        if re.match(
            r"^はっきり言ってそれって病気だから\s+お前死ぬよ$", stripped
        ):
            return f"{self._indent()}raise Exception()"

        # --- 認識できない行 ---
        raise ToughTranspileError(f"認識できない構文: {stripped}", line_number)

    def _transpile_expr(self, expr: str) -> str:
        """式中のTOUGH演算子をPython演算子に変換する"""
        # 比較演算子（長いパターンを先にマッチ）
        expr = expr.replace("ガチンコじゃない", " != ")
        expr = expr.replace("ガチンコ", " == ")
        expr = expr.replace("を超えた", " > ")
        expr = expr.replace("に及ばない", " < ")


        # 文字列リテラル: 「...」 → "..."
        expr = re.sub(r"「(.+?)」", r'"\1"', expr)

        # 余分な空白を整理
        expr = re.sub(r"\s+", " ", expr).strip()

        return expr

    def transpile(self, source: str) -> str:
        """TOUGH ソースコード全体を Python コードに変換する

        Args:
            source: TOUGH ソースコード文字列

        Returns:
            変換後の Python コード文字列
        """
        self._indent_level = 0
        self._indent_stack.clear()
        lines = source.splitlines()
        python_lines: list[str] = []

        for i, line in enumerate(lines, start=1):
            try:
                result = self._transpile_line(line, i)
                if result is not None:
                    python_lines.append(result)
            except ToughTranspileError:
                raise
            except Exception as e:
                raise ToughTranspileError(str(e), i) from e

        return "\n".join(python_lines)


def run_tough(source: str) -> None:
    """TOUGH ソースコードをトランスパイルして実行する"""
    transpiler = ToughTranspiler()
    python_code = transpiler.transpile(source)
    exec(python_code, {"__builtins__": __builtins__, "sys": sys})


def run_tough_file(filepath: str) -> None:
    """TOUGH ファイルを読み込んでトランスパイルして実行する"""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    run_tough(source)
