"""TOUGH 言語 - トークン定義"""

from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """トークン種別"""

    # リテラル
    INT = auto()        # 整数リテラル
    FLOAT = auto()      # 浮動小数点リテラル
    STRING = auto()     # 文字列リテラル 「...」
    IDENT = auto()      # 識別子（変数名・関数名）

    # キーワード: プログラム構造
    PROGRAM_START = auto()   # 我が名は　尊鷹
    PROGRAM_END = auto()     # 逃げるんかいっ

    # キーワード: 変数
    DECLARE_DA = auto()      # ～だ
    DECLARE_REVEAL = auto()  # ～が正体を現すぞ
    ASSIGN_TSUGU = auto()    # を継ぐ

    # キーワード: 入出力
    PRINT = auto()           # しゃあっ
    INPUT = auto()           # を教えてくれよ

    # キーワード: インクリメント / デクリメント
    INCREMENT = auto()       # 進化したと言うてくれや
    DECREMENT = auto()       # （哀）

    # キーワード: 比較演算子
    EQ = auto()              # ガチンコ (==)
    NEQ = auto()             # ガチンコじゃない (!=)
    GT = auto()              # を超えた (>)
    LT = auto()              # に及ばない (<)

    # キーワード: 制御構文
    IF = auto()              # なにっ
    ELIF = auto()            # いやちょっとまてよ
    ELSE = auto()            # う　あ　あ　あ　あ（ＰＣ書き文字）
    WHILE = auto()           # 禁断の"...度打ち"
    FN_PREFIX = auto()       # 自分たちの手で作るから尊いんだ
    FN_GA = auto()           # ～が
    FN_RUNDA = auto()        # ～るんだ

    # キーワード: 例外
    CATCH = auto()           # はルールで禁止スよね
    THROW = auto()           # はっきり言ってそれって病気だから お前死ぬよ

    # キーワード: コメント
    COMMENT = auto()         # （○○のコメント）...

    # 記号
    LBRACE = auto()          # {
    RBRACE = auto()          # }
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    PERCENT = auto()         # %

    # 特殊
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    """トークン"""
    type: TokenType
    value: str
    line: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"
