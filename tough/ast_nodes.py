"""TOUGH 言語 - AST ノード定義

抽象構文木（AST）の各ノード型を定義する。
"""

from dataclasses import dataclass, field


# ============================================================
# 基底クラス
# ============================================================

@dataclass
class ASTNode:
    """AST ノードの基底クラス"""
    line: int = 0


@dataclass
class Expression(ASTNode):
    """式の基底クラス"""
    pass


@dataclass
class Statement(ASTNode):
    """文の基底クラス"""
    pass


# ============================================================
# リテラル・識別子
# ============================================================

@dataclass
class IntLiteral(Expression):
    """整数リテラル"""
    value: int = 0


@dataclass
class FloatLiteral(Expression):
    """浮動小数点リテラル"""
    value: float = 0.0


@dataclass
class StringLiteral(Expression):
    """文字列リテラル"""
    value: str = ""


@dataclass
class Identifier(Expression):
    """識別子（変数参照）"""
    name: str = ""


# ============================================================
# 演算
# ============================================================

@dataclass
class BinaryOp(Expression):
    """二項演算（比較演算子・剰余）"""
    op: str = ""          # "==", "!=", ">", "<", "%"
    left: Expression = None
    right: Expression = None


# ============================================================
# 文（Statement）
# ============================================================

@dataclass
class Program(ASTNode):
    """プログラム全体"""
    statements: list[Statement] = field(default_factory=list)


@dataclass
class ProgramStart(Statement):
    """プログラム開始: 我が名は　尊鷹"""
    pass


@dataclass
class ProgramEnd(Statement):
    """プログラム終了: 逃げるんかいっ"""
    pass


@dataclass
class Comment(Statement):
    """コメント"""
    text: str = ""


@dataclass
class DeclareStatement(Statement):
    """変数宣言: Xだ Xが正体を現すぞ"""
    name: str = ""


@dataclass
class AssignStatement(Statement):
    """代入: (値) を継ぐ (変数)"""
    name: str = ""
    value: Expression = None


@dataclass
class PrintStatement(Statement):
    """出力: (値) しゃあっ"""
    value: Expression = None


@dataclass
class InputStatement(Statement):
    """入力: (変数) を教えてくれよ"""
    name: str = ""


@dataclass
class IncrementStatement(Statement):
    """インクリメント: (変数) 進化したと言うてくれや"""
    name: str = ""


@dataclass
class DecrementStatement(Statement):
    """デクリメント: (変数) （哀）"""
    name: str = ""


@dataclass
class IfStatement(Statement):
    """条件分岐: なにっ / いやちょっとまてよ / う　あ　あ　あ　あ"""
    condition: Expression = None
    then_body: list[Statement] = field(default_factory=list)
    elif_clauses: list[tuple[Expression, list[Statement]]] = field(default_factory=list)
    else_body: list[Statement] = field(default_factory=list)


@dataclass
class WhileStatement(Statement):
    """ループ: 禁断の"...度打ち" """
    condition: Expression = None
    body: list[Statement] = field(default_factory=list)


@dataclass
class FnStatement(Statement):
    """関数定義"""
    name: str = ""
    params: list[str] = field(default_factory=list)
    body: list[Statement] = field(default_factory=list)


@dataclass
class ThrowStatement(Statement):
    """例外送出"""
    pass
