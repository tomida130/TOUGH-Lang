"""TOUGH 言語 - 字句解析器（Lexer）

TOUGH ソースコードを行単位で解析し、トークン列に変換する。
日本語キーワードを優先的にマッチし、残りを識別子・数値・記号として認識する。
"""

import re
from tough.tokens import Token, TokenType


class LexerError(Exception):
    """字句解析エラー"""
    def __init__(self, message: str, line: int):
        self.line = line
        super().__init__(f"行 {line}: {message}")


class Lexer:
    """TOUGH 字句解析器"""

    # 行全体でマッチするキーワードパターン（優先度順）
    LINE_PATTERNS: list[tuple[str, TokenType]] = [
        (r"^我が名は[　\s]+尊鷹$", TokenType.PROGRAM_START),
        (r"^逃げるんかいっ$", TokenType.PROGRAM_END),
        (r"^はっきり言ってそれって病気だから\s+お前死ぬよ$", TokenType.THROW),
    ]

    # 行末キーワード（行の一部としてマッチ）
    SUFFIX_KEYWORDS: list[tuple[str, TokenType]] = [
        ("しゃあっ", TokenType.PRINT),
        ("を教えてくれよ", TokenType.INPUT),
        ("進化したと言うてくれや", TokenType.INCREMENT),
        ("（哀）", TokenType.DECREMENT),
        ("が正体を現すぞ", TokenType.DECLARE_REVEAL),
        ("を継ぐ", TokenType.ASSIGN_TSUGU),
    ]

    # 式内のキーワード（長いものを先に）
    EXPR_KEYWORDS: list[tuple[str, TokenType]] = [
        ("ガチンコじゃない", TokenType.NEQ),
        ("ガチンコ", TokenType.EQ),
        ("を超えた", TokenType.GT),
        ("に及ばない", TokenType.LT),
    ]

    def __init__(self, source: str):
        self.source = source
        self.lines = source.splitlines()
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        """ソース全体をトークン化する"""
        self.tokens = []

        for line_num, line in enumerate(self.lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            self._tokenize_line(stripped, line_num)
            self.tokens.append(Token(TokenType.NEWLINE, "\\n", line_num))

        self.tokens.append(Token(TokenType.EOF, "", len(self.lines) + 1))
        return self.tokens

    def _tokenize_line(self, line: str, line_num: int) -> None:
        """1行をトークン化する"""

        # --- コメント: （○○のコメント）... ---
        m = re.match(r"^（(.+?)のコメント）(.*)$", line)
        if m:
            comment_text = m.group(2).strip() if m.group(2).strip() else f"{m.group(1)}のコメント"
            self.tokens.append(Token(TokenType.COMMENT, comment_text, line_num))
            return

        # --- 行全体マッチパターン ---
        for pattern, token_type in self.LINE_PATTERNS:
            if re.match(pattern, line):
                self.tokens.append(Token(token_type, line, line_num))
                return

        # --- 変数宣言: Xだ Xが正体を現すぞ ---
        m = re.match(r"^(.+?)だ\s+\1が正体を現すぞ$", line)
        if m:
            var_name = m.group(1).strip()
            self.tokens.append(Token(TokenType.DECLARE_DA, var_name, line_num))
            self.tokens.append(Token(TokenType.DECLARE_REVEAL, var_name, line_num))
            return

        # --- 関数定義: 自分たちの手で作るから尊いんだ Xが (Y)るんだ { ---
        m = re.match(
            r"^自分たちの手で作るから尊いんだ\s+(.+?)が\s+\((.+?)\)るんだ\s*\{$",
            line,
        )
        if m:
            func_name = m.group(1).strip()
            args = m.group(2).strip()
            self.tokens.append(Token(TokenType.FN_PREFIX, "自分たちの手で作るから尊いんだ", line_num))
            self.tokens.append(Token(TokenType.IDENT, func_name, line_num))
            self.tokens.append(Token(TokenType.FN_GA, "が", line_num))
            # 引数を分割
            for arg in args.split(","):
                self.tokens.append(Token(TokenType.IDENT, arg.strip(), line_num))
            self.tokens.append(Token(TokenType.FN_RUNDA, "るんだ", line_num))
            self.tokens.append(Token(TokenType.LBRACE, "{", line_num))
            return

        # --- if: なにっ (条件) { ---
        m = re.match(r"^なにっ\s+\((.+?)\)\s*\{$", line)
        if m:
            self.tokens.append(Token(TokenType.IF, "なにっ", line_num))
            self.tokens.append(Token(TokenType.LPAREN, "(", line_num))
            self._tokenize_expr(m.group(1).strip(), line_num)
            self.tokens.append(Token(TokenType.RPAREN, ")", line_num))
            self.tokens.append(Token(TokenType.LBRACE, "{", line_num))
            return

        # --- elif: いやちょっとまてよ (条件) { ---
        m = re.match(r"^いやちょっとまてよ\s+\((.+?)\)\s*\{$", line)
        if m:
            self.tokens.append(Token(TokenType.ELIF, "いやちょっとまてよ", line_num))
            self.tokens.append(Token(TokenType.LPAREN, "(", line_num))
            self._tokenize_expr(m.group(1).strip(), line_num)
            self.tokens.append(Token(TokenType.RPAREN, ")", line_num))
            self.tokens.append(Token(TokenType.LBRACE, "{", line_num))
            return

        # --- else: う　あ　あ　あ　あ（ＰＣ書き文字） { ---
        m = re.match(r"^う[　\s]+あ[　\s]+あ[　\s]+あ[　\s]+あ[（(]\s*[ＰP][ＣC]書き文字\s*[）)]\s*\{$", line)
        if m:
            self.tokens.append(Token(TokenType.ELSE, "う　あ　あ　あ　あ（ＰＣ書き文字）", line_num))
            self.tokens.append(Token(TokenType.LBRACE, "{", line_num))
            return

        # --- while: 禁断の"(条件)度打ち" { ---
        m = re.match(r'^禁断の[""「](.+?)度打ち[""」]\s*\{$', line)
        if m:
            self.tokens.append(Token(TokenType.WHILE, "禁断の", line_num))
            self.tokens.append(Token(TokenType.LPAREN, "(", line_num))
            self._tokenize_expr(m.group(1).strip(), line_num)
            self.tokens.append(Token(TokenType.RPAREN, ")", line_num))
            self.tokens.append(Token(TokenType.LBRACE, "{", line_num))
            return

        # --- catch: } X はルールで禁止スよね { ---
        m = re.match(r"^\}\s*(.+?)\s+はルールで禁止スよね\s*\{$", line)
        if m:
            var_name = m.group(1).strip()
            self.tokens.append(Token(TokenType.RBRACE, "}", line_num))
            self.tokens.append(Token(TokenType.CATCH, "はルールで禁止スよね", line_num))
            self.tokens.append(Token(TokenType.IDENT, var_name, line_num))
            self.tokens.append(Token(TokenType.LBRACE, "{", line_num))
            return

        # --- ブロック終了: } ---
        if line == "}":
            self.tokens.append(Token(TokenType.RBRACE, "}", line_num))
            return

        # --- 代入: (値) を継ぐ (変数) ---
        m = re.match(r"^(.+?)\s+を継ぐ\s+(.+)$", line)
        if m:
            self._tokenize_expr(m.group(1).strip(), line_num)
            self.tokens.append(Token(TokenType.ASSIGN_TSUGU, "を継ぐ", line_num))
            self.tokens.append(Token(TokenType.IDENT, m.group(2).strip(), line_num))
            return

        # --- 出力: (値) しゃあっ ---
        m = re.match(r"^(.+?)\s+しゃあっ$", line)
        if m:
            self._tokenize_expr(m.group(1).strip(), line_num)
            self.tokens.append(Token(TokenType.PRINT, "しゃあっ", line_num))
            return

        # --- 入力: (変数) を教えてくれよ ---
        m = re.match(r"^(.+?)\s+を教えてくれよ$", line)
        if m:
            self.tokens.append(Token(TokenType.IDENT, m.group(1).strip(), line_num))
            self.tokens.append(Token(TokenType.INPUT, "を教えてくれよ", line_num))
            return

        # --- インクリメント: (変数) 進化したと言うてくれや ---
        m = re.match(r"^(.+?)\s+進化したと言うてくれや$", line)
        if m:
            self.tokens.append(Token(TokenType.IDENT, m.group(1).strip(), line_num))
            self.tokens.append(Token(TokenType.INCREMENT, "進化したと言うてくれや", line_num))
            return

        # --- デクリメント: (変数) （哀） ---
        m = re.match(r"^(.+?)\s+（哀）$", line)
        if m:
            self.tokens.append(Token(TokenType.IDENT, m.group(1).strip(), line_num))
            self.tokens.append(Token(TokenType.DECREMENT, "（哀）", line_num))
            return

        raise LexerError(f"認識できない構文: {line}", line_num)

    def _tokenize_expr(self, expr: str, line_num: int) -> None:
        """式をトークン化する（比較演算子・数値・識別子・文字列・%）"""
        pos = 0
        while pos < len(expr):
            # 空白スキップ
            if expr[pos] in " \t　":
                pos += 1
                continue

            # 式内キーワード（比較演算子）
            matched = False
            for keyword, token_type in self.EXPR_KEYWORDS:
                if expr[pos:].startswith(keyword):
                    self.tokens.append(Token(token_type, keyword, line_num))
                    pos += len(keyword)
                    matched = True
                    break
            if matched:
                continue

            # 文字列リテラル 「...」
            if expr[pos] == "「":
                end = expr.index("」", pos + 1)
                self.tokens.append(Token(TokenType.STRING, expr[pos + 1:end], line_num))
                pos = end + 1
                continue

            # 数値リテラル
            if expr[pos].isdigit() or (expr[pos] == "-" and pos + 1 < len(expr) and expr[pos + 1].isdigit()):
                m = re.match(r"-?\d+(\.\d+)?", expr[pos:])
                if m:
                    val = m.group(0)
                    if "." in val:
                        self.tokens.append(Token(TokenType.FLOAT, val, line_num))
                    else:
                        self.tokens.append(Token(TokenType.INT, val, line_num))
                    pos += len(val)
                    continue

            # パーセント記号
            if expr[pos] == "%":
                self.tokens.append(Token(TokenType.PERCENT, "%", line_num))
                pos += 1
                continue

            # 括弧
            if expr[pos] == "(":
                self.tokens.append(Token(TokenType.LPAREN, "(", line_num))
                pos += 1
                continue
            if expr[pos] == ")":
                self.tokens.append(Token(TokenType.RPAREN, ")", line_num))
                pos += 1
                continue

            # 識別子（英数字 + アンダースコア + 日本語）
            m = re.match(r"[a-zA-Z_\u3040-\u9fff][a-zA-Z0-9_\u3040-\u9fff]*", expr[pos:])
            if m:
                self.tokens.append(Token(TokenType.IDENT, m.group(0), line_num))
                pos += len(m.group(0))
                continue

            raise LexerError(f"認識できない文字: {expr[pos]!r}", line_num)
