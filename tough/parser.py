"""TOUGH 言語 - 構文解析器（Parser）

トークン列を受け取り、AST を構築する。
"""

from tough.tokens import Token, TokenType
from tough.ast_nodes import (
    Program, ProgramStart, ProgramEnd, Comment,
    DeclareStatement, AssignStatement, PrintStatement, InputStatement,
    IncrementStatement, DecrementStatement,
    IfStatement, WhileStatement, FnStatement, ThrowStatement,
    IntLiteral, FloatLiteral, StringLiteral, Identifier, BinaryOp,
    Expression, Statement,
)


class ParseError(Exception):
    """構文解析エラー"""
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"行 {line}: {message}")


class Parser:
    """TOUGH 構文解析器"""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, "", 0)

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, "", 0)

    def _advance(self) -> Token:
        tok = self._current()
        self.pos += 1
        return tok

    def _expect(self, token_type: TokenType) -> Token:
        tok = self._current()
        if tok.type != token_type:
            raise ParseError(
                f"期待: {token_type.name}, 実際: {tok.type.name} ({tok.value!r})",
                tok.line,
            )
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._current().type == TokenType.NEWLINE:
            self._advance()

    def parse(self) -> Program:
        """トークン列をパースして Program AST を返す"""
        program = Program(statements=[])
        self._skip_newlines()

        while self._current().type != TokenType.EOF:
            stmt = self._parse_statement()
            if stmt is not None:
                program.statements.append(stmt)
            self._skip_newlines()

        return program

    def _parse_statement(self) -> Statement | None:
        """1つの文をパースする"""
        tok = self._current()

        if tok.type == TokenType.COMMENT:
            self._advance()
            self._skip_newlines()
            return Comment(text=tok.value, line=tok.line)

        if tok.type == TokenType.PROGRAM_START:
            self._advance()
            self._skip_newlines()
            return ProgramStart(line=tok.line)

        if tok.type == TokenType.PROGRAM_END:
            self._advance()
            self._skip_newlines()
            return ProgramEnd(line=tok.line)

        if tok.type == TokenType.THROW:
            self._advance()
            self._skip_newlines()
            return ThrowStatement(line=tok.line)

        if tok.type == TokenType.DECLARE_DA:
            return self._parse_declare()

        if tok.type == TokenType.FN_PREFIX:
            return self._parse_function()

        if tok.type == TokenType.IF:
            return self._parse_if()

        if tok.type == TokenType.WHILE:
            return self._parse_while()

        # 式で始まる文（代入・出力・インクリメント・デクリメント）
        return self._parse_expr_statement()

    def _parse_declare(self) -> DeclareStatement:
        """変数宣言をパースする"""
        tok = self._advance()  # DECLARE_DA
        var_name = tok.value
        self._expect(TokenType.DECLARE_REVEAL)
        self._skip_newlines()
        return DeclareStatement(name=var_name, line=tok.line)

    def _parse_function(self) -> FnStatement:
        """関数定義をパースする"""
        tok = self._advance()  # FN_PREFIX
        name_tok = self._expect(TokenType.IDENT)
        self._expect(TokenType.FN_GA)

        params = []
        while self._current().type == TokenType.IDENT and self._peek(1).type != TokenType.FN_RUNDA:
            params.append(self._advance().value)
        if self._current().type == TokenType.IDENT:
            params.append(self._advance().value)

        self._expect(TokenType.FN_RUNDA)
        self._expect(TokenType.LBRACE)
        self._skip_newlines()

        body = self._parse_block()

        return FnStatement(name=name_tok.value, params=params, body=body, line=tok.line)

    def _parse_if(self) -> IfStatement:
        """if 文をパースする"""
        tok = self._advance()  # IF
        self._expect(TokenType.LPAREN)
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        self._skip_newlines()
        then_body = self._parse_block()

        elif_clauses: list[tuple[Expression, list[Statement]]] = []
        else_body: list[Statement] = []

        while self._current().type == TokenType.ELIF:
            self._advance()  # ELIF
            self._expect(TokenType.LPAREN)
            elif_cond = self._parse_expression()
            self._expect(TokenType.RPAREN)
            self._expect(TokenType.LBRACE)
            self._skip_newlines()
            elif_body = self._parse_block()
            elif_clauses.append((elif_cond, elif_body))

        if self._current().type == TokenType.ELSE:
            self._advance()  # ELSE
            self._expect(TokenType.LBRACE)
            self._skip_newlines()
            else_body = self._parse_block()

        return IfStatement(
            condition=condition,
            then_body=then_body,
            elif_clauses=elif_clauses,
            else_body=else_body,
            line=tok.line,
        )

    def _parse_while(self) -> WhileStatement:
        """while 文をパースする"""
        tok = self._advance()  # WHILE
        self._expect(TokenType.LPAREN)
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        self._skip_newlines()
        body = self._parse_block()
        return WhileStatement(condition=condition, body=body, line=tok.line)

    def _parse_block(self) -> list[Statement]:
        """} が来るまでの文リストをパースする"""
        stmts: list[Statement] = []
        while self._current().type not in (TokenType.RBRACE, TokenType.EOF):
            stmt = self._parse_statement()
            if stmt is not None:
                stmts.append(stmt)
            self._skip_newlines()
        if self._current().type == TokenType.RBRACE:
            self._advance()  # }
        self._skip_newlines()
        return stmts

    def _parse_expr_statement(self) -> Statement:
        """式で始まる文をパースする"""
        tok = self._current()

        # 識別子の後にキーワードが続くパターン
        if tok.type == TokenType.IDENT:
            next_tok = self._peek(1)

            # インクリメント
            if next_tok.type == TokenType.INCREMENT:
                self._advance()  # IDENT
                self._advance()  # INCREMENT
                self._skip_newlines()
                return IncrementStatement(name=tok.value, line=tok.line)

            # デクリメント
            if next_tok.type == TokenType.DECREMENT:
                self._advance()  # IDENT
                self._advance()  # DECREMENT
                self._skip_newlines()
                return DecrementStatement(name=tok.value, line=tok.line)

            # 入力
            if next_tok.type == TokenType.INPUT:
                self._advance()  # IDENT
                self._advance()  # INPUT
                self._skip_newlines()
                return InputStatement(name=tok.value, line=tok.line)

        # 式をパースし、次のトークンで文の種類を決定
        expr = self._parse_expression()

        cur = self._current()

        # 出力: ... しゃあっ
        if cur.type == TokenType.PRINT:
            self._advance()
            self._skip_newlines()
            return PrintStatement(value=expr, line=tok.line)

        # 代入: ... を継ぐ (変数)
        if cur.type == TokenType.ASSIGN_TSUGU:
            self._advance()
            var_tok = self._expect(TokenType.IDENT)
            self._skip_newlines()
            return AssignStatement(name=var_tok.value, value=expr, line=tok.line)

        raise ParseError(f"文の終端が不正: {cur.type.name}", cur.line)

    def _parse_expression(self) -> Expression:
        """式をパースする（比較演算子）"""
        left = self._parse_primary()

        while self._current().type in (TokenType.EQ, TokenType.NEQ, TokenType.GT, TokenType.LT, TokenType.PERCENT):
            op_tok = self._advance()
            op_map = {
                TokenType.EQ: "==",
                TokenType.NEQ: "!=",
                TokenType.GT: ">",
                TokenType.LT: "<",
                TokenType.PERCENT: "%",
            }
            right = self._parse_primary()
            left = BinaryOp(op=op_map[op_tok.type], left=left, right=right, line=op_tok.line)

        return left

    def _parse_primary(self) -> Expression:
        """基本式（リテラル・識別子・括弧）をパースする"""
        tok = self._current()

        if tok.type == TokenType.INT:
            self._advance()
            return IntLiteral(value=int(tok.value), line=tok.line)

        if tok.type == TokenType.FLOAT:
            self._advance()
            return FloatLiteral(value=float(tok.value), line=tok.line)

        if tok.type == TokenType.STRING:
            self._advance()
            return StringLiteral(value=tok.value, line=tok.line)

        if tok.type == TokenType.IDENT:
            self._advance()
            return Identifier(name=tok.value, line=tok.line)

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        raise ParseError(f"式が期待されましたが {tok.type.name} が見つかりました", tok.line)
