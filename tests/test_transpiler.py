"""TOUGH コンパイラのテスト"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tough.lexer import Lexer, LexerError
from tough.parser import Parser, ParseError
from tough.codegen import CodeGenerator, CodeGenError
from tough.compiler import Compiler
from tough.tokens import TokenType
from tough.ast_nodes import (
    DeclareStatement, AssignStatement, PrintStatement,
    IncrementStatement, DecrementStatement,
    IfStatement, WhileStatement,
    IntLiteral, StringLiteral, Identifier,
)


class TestLexer:
    """字句解析のテスト"""

    def test_program_start(self):
        lexer = Lexer("我が名は　尊鷹")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.PROGRAM_START

    def test_program_end(self):
        lexer = Lexer("逃げるんかいっ")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.PROGRAM_END

    def test_comment(self):
        lexer = Lexer("（祠部矢のコメント）これはテスト")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.COMMENT
        assert tokens[0].value == "これはテスト"

    def test_variable_declaration(self):
        lexer = Lexer("xだ xが正体を現すぞ")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.DECLARE_DA
        assert tokens[0].value == "x"

    def test_print(self):
        lexer = Lexer("「hello」 しゃあっ")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[1].type == TokenType.PRINT

    def test_increment(self):
        lexer = Lexer("x 進化したと言うてくれや")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENT
        assert tokens[1].type == TokenType.INCREMENT

    def test_if(self):
        lexer = Lexer("なにっ (x ガチンコ 0) {")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IF


class TestParser:
    """構文解析のテスト"""

    def _parse(self, source: str):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse()

    def test_declare(self):
        prog = self._parse("xだ xが正体を現すぞ")
        assert len(prog.statements) == 1
        assert isinstance(prog.statements[0], DeclareStatement)
        assert prog.statements[0].name == "x"

    def test_assign(self):
        prog = self._parse("42 を継ぐ x")
        assert len(prog.statements) == 1
        assert isinstance(prog.statements[0], AssignStatement)
        assert prog.statements[0].name == "x"

    def test_print_string(self):
        prog = self._parse("「hello」 しゃあっ")
        assert isinstance(prog.statements[0], PrintStatement)
        assert isinstance(prog.statements[0].value, StringLiteral)

    def test_print_variable(self):
        prog = self._parse("x しゃあっ")
        assert isinstance(prog.statements[0], PrintStatement)
        assert isinstance(prog.statements[0].value, Identifier)

    def test_increment(self):
        prog = self._parse("x 進化したと言うてくれや")
        assert isinstance(prog.statements[0], IncrementStatement)

    def test_if_else(self):
        source = """なにっ (x ガチンコ 1) {
x しゃあっ
}
う　あ　あ　あ　あ（ＰＣ書き文字） {
x しゃあっ
}"""
        prog = self._parse(source)
        assert isinstance(prog.statements[0], IfStatement)
        assert len(prog.statements[0].else_body) == 1

    def test_while(self):
        source = """禁断の"x に及ばない 10 度打ち" {
x 進化したと言うてくれや
}"""
        prog = self._parse(source)
        assert isinstance(prog.statements[0], WhileStatement)


class TestCodeGen:
    """コード生成のテスト（LLVM IR が生成されることを確認）"""

    def _gen_ir(self, source: str) -> str:
        compiler = Compiler()
        return compiler.emit_ir(source)

    def test_hello_generates_ir(self):
        ir_text = self._gen_ir("「Hello」 しゃあっ")
        assert "define" in ir_text
        assert "main" in ir_text
        assert "printf" in ir_text

    def test_variable_generates_ir(self):
        source = """xだ xが正体を現すぞ
42 を継ぐ x
x しゃあっ"""
        ir_text = self._gen_ir(source)
        assert "alloca" in ir_text
        assert "store" in ir_text

    def test_if_generates_ir(self):
        source = """xだ xが正体を現すぞ
1 を継ぐ x
なにっ (x ガチンコ 1) {
「yes」 しゃあっ
}"""
        ir_text = self._gen_ir(source)
        assert "if.then" in ir_text

    def test_while_generates_ir(self):
        source = """xだ xが正体を現すぞ
0 を継ぐ x
禁断の"x に及ばない 3 度打ち" {
x 進化したと言うてくれや
}"""
        ir_text = self._gen_ir(source)
        assert "while.cond" in ir_text
        assert "while.body" in ir_text
