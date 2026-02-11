"""TOUGH 言語 - LLVM IR コード生成

AST を走査して llvmlite で LLVM IR を生成する。
"""

from llvmlite import ir

from tough.ast_nodes import (
    Program, ProgramStart, ProgramEnd, Comment,
    DeclareStatement, AssignStatement, PrintStatement, InputStatement,
    IncrementStatement, DecrementStatement,
    IfStatement, WhileStatement, FnStatement, ThrowStatement,
    IntLiteral, FloatLiteral, StringLiteral, Identifier, BinaryOp,
    Expression, Statement,
)


class CodeGenError(Exception):
    """コード生成エラー"""
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"行 {line}: {message}")


class CodeGenerator:
    """LLVM IR コード生成器"""

    def __init__(self):
        # モジュール
        self.module = ir.Module(name="tough_module")
        self.module.triple = ""  # JIT が自動設定

        # 型定義
        self.int_type = ir.IntType(64)
        self.int32_type = ir.IntType(32)
        self.char_type = ir.IntType(8)
        self.char_ptr_type = self.char_type.as_pointer()
        self.void_type = ir.VoidType()

        # 外部関数の宣言
        self._declare_externals()

        # 状態
        self.builder: ir.IRBuilder | None = None
        self.variables: dict[str, ir.AllocaInstr] = {}
        self.functions: dict[str, ir.Function] = {}
        self._string_counter = 0

    def _declare_externals(self) -> None:
        """C ランタイムの外部関数を宣言する"""
        # printf
        printf_type = ir.FunctionType(self.int32_type, [self.char_ptr_type], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")

        # scanf
        scanf_type = ir.FunctionType(self.int32_type, [self.char_ptr_type], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_type, name="scanf")

        # exit
        exit_type = ir.FunctionType(self.void_type, [self.int32_type])
        self.exit_func = ir.Function(self.module, exit_type, name="exit")

    def _create_global_string(self, value: str) -> ir.GlobalVariable:
        """グローバル文字列定数を作成する"""
        self._string_counter += 1
        encoded = bytearray(value.encode("utf-8")) + bytearray(b"\x00")
        str_type = ir.ArrayType(self.char_type, len(encoded))
        str_var = ir.GlobalVariable(self.module, str_type, name=f".str.{self._string_counter}")
        str_var.global_constant = True
        str_var.linkage = "internal"
        str_var.initializer = ir.Constant(str_type, encoded)
        return str_var

    def _get_string_ptr(self, global_str: ir.GlobalVariable) -> ir.Value:
        """グローバル文字列のポインタを取得する"""
        zero = ir.Constant(self.int_type, 0)
        return self.builder.gep(global_str, [zero, zero], inbounds=True)

    def generate(self, program: Program) -> ir.Module:
        """Program AST から LLVM IR を生成する"""
        # main 関数を作成
        main_type = ir.FunctionType(self.int32_type, [])
        main_func = ir.Function(self.module, main_type, name="main")
        self.functions["main"] = main_func

        block = main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)

        # 全文をコード生成
        for stmt in program.statements:
            self._gen_statement(stmt)

        # return 0 (もし最後のブロックが終端されていなければ)
        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(self.int32_type, 0))

        return self.module

    def _gen_statement(self, stmt: Statement) -> None:
        """文のコード生成"""
        if isinstance(stmt, Comment):
            return  # コメントは IR に含めない

        if isinstance(stmt, ProgramStart):
            return  # 特に何もしない（main 関数は既に開始済み）

        if isinstance(stmt, ProgramEnd):
            self.builder.call(self.exit_func, [ir.Constant(self.int32_type, 0)])
            self.builder.ret(ir.Constant(self.int32_type, 0))
            return

        if isinstance(stmt, DeclareStatement):
            self._gen_declare(stmt)
            return

        if isinstance(stmt, AssignStatement):
            self._gen_assign(stmt)
            return

        if isinstance(stmt, PrintStatement):
            self._gen_print(stmt)
            return

        if isinstance(stmt, InputStatement):
            self._gen_input(stmt)
            return

        if isinstance(stmt, IncrementStatement):
            self._gen_increment(stmt)
            return

        if isinstance(stmt, DecrementStatement):
            self._gen_decrement(stmt)
            return

        if isinstance(stmt, IfStatement):
            self._gen_if(stmt)
            return

        if isinstance(stmt, WhileStatement):
            self._gen_while(stmt)
            return

        if isinstance(stmt, FnStatement):
            self._gen_function(stmt)
            return

        if isinstance(stmt, ThrowStatement):
            # exit(1) で代用
            self.builder.call(self.exit_func, [ir.Constant(self.int32_type, 1)])
            self.builder.ret(ir.Constant(self.int32_type, 1))
            return

        raise CodeGenError(f"未対応の文: {type(stmt).__name__}", stmt.line)

    def _gen_declare(self, stmt: DeclareStatement) -> None:
        """変数宣言: alloca で領域を確保し 0 で初期化"""
        alloca = self.builder.alloca(self.int_type, name=stmt.name)
        self.builder.store(ir.Constant(self.int_type, 0), alloca)
        self.variables[stmt.name] = alloca

    def _gen_assign(self, stmt: AssignStatement) -> None:
        """代入"""
        value = self._gen_expression(stmt.value)
        if stmt.name not in self.variables:
            alloca = self.builder.alloca(self.int_type, name=stmt.name)
            self.variables[stmt.name] = alloca
        self.builder.store(value, self.variables[stmt.name])

    def _gen_print(self, stmt: PrintStatement) -> None:
        """出力"""
        value = stmt.value
        if isinstance(value, StringLiteral):
            # 文字列の場合: printf("%s\n", str)
            fmt = self._create_global_string("%s\n")
            fmt_ptr = self._get_string_ptr(fmt)
            str_val = self._create_global_string(value.value)
            str_ptr = self._get_string_ptr(str_val)
            self.builder.call(self.printf, [fmt_ptr, str_ptr])
        else:
            # 数値の場合: printf("%lld\n", val)
            val = self._gen_expression(value)
            fmt = self._create_global_string("%lld\n")
            fmt_ptr = self._get_string_ptr(fmt)
            self.builder.call(self.printf, [fmt_ptr, val])

    def _gen_input(self, stmt: InputStatement) -> None:
        """入力: scanf で整数を読み込む"""
        if stmt.name not in self.variables:
            alloca = self.builder.alloca(self.int_type, name=stmt.name)
            self.variables[stmt.name] = alloca
        fmt = self._create_global_string("%lld")
        fmt_ptr = self._get_string_ptr(fmt)
        self.builder.call(self.scanf, [fmt_ptr, self.variables[stmt.name]])

    def _gen_increment(self, stmt: IncrementStatement) -> None:
        """インクリメント"""
        if stmt.name not in self.variables:
            raise CodeGenError(f"未定義の変数: {stmt.name}", stmt.line)
        current = self.builder.load(self.variables[stmt.name])
        new_val = self.builder.add(current, ir.Constant(self.int_type, 1))
        self.builder.store(new_val, self.variables[stmt.name])

    def _gen_decrement(self, stmt: DecrementStatement) -> None:
        """デクリメント"""
        if stmt.name not in self.variables:
            raise CodeGenError(f"未定義の変数: {stmt.name}", stmt.line)
        current = self.builder.load(self.variables[stmt.name])
        new_val = self.builder.sub(current, ir.Constant(self.int_type, 1))
        self.builder.store(new_val, self.variables[stmt.name])

    def _gen_if(self, stmt: IfStatement) -> None:
        """条件分岐"""
        func = self.builder.function

        # 基本ブロック
        then_bb = func.append_basic_block("if.then")
        merge_bb = func.append_basic_block("if.merge")

        # elif / else ブロックを先に作成
        elif_bbs = []
        for i, (cond, body) in enumerate(stmt.elif_clauses):
            elif_cond_bb = func.append_basic_block(f"elif.cond.{i}")
            elif_body_bb = func.append_basic_block(f"elif.body.{i}")
            elif_bbs.append((elif_cond_bb, elif_body_bb, cond, body))

        else_bb = None
        if stmt.else_body:
            else_bb = func.append_basic_block("if.else")

        # 最初の分岐先（elif がなければ else、else もなければ merge）
        first_false_target = elif_bbs[0][0] if elif_bbs else (else_bb if else_bb else merge_bb)

        # if 条件評価
        cond_val = self._gen_expression(stmt.condition)
        cond_bool = self.builder.icmp_signed("!=", cond_val, ir.Constant(self.int_type, 0))
        self.builder.cbranch(cond_bool, then_bb, first_false_target)

        # then ブロック
        self.builder.position_at_start(then_bb)
        for s in stmt.then_body:
            self._gen_statement(s)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)

        # elif ブロック
        for i, (cond_bb, body_bb, cond, body) in enumerate(elif_bbs):
            next_target = elif_bbs[i + 1][0] if i + 1 < len(elif_bbs) else (else_bb if else_bb else merge_bb)

            self.builder.position_at_start(cond_bb)
            elif_cond_val = self._gen_expression(cond)
            elif_cond_bool = self.builder.icmp_signed("!=", elif_cond_val, ir.Constant(self.int_type, 0))
            self.builder.cbranch(elif_cond_bool, body_bb, next_target)

            self.builder.position_at_start(body_bb)
            for s in body:
                self._gen_statement(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)

        # else ブロック
        if else_bb:
            self.builder.position_at_start(else_bb)
            for s in stmt.else_body:
                self._gen_statement(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)

        # merge ブロック
        self.builder.position_at_start(merge_bb)

    def _gen_while(self, stmt: WhileStatement) -> None:
        """ループ"""
        func = self.builder.function
        cond_bb = func.append_basic_block("while.cond")
        body_bb = func.append_basic_block("while.body")
        merge_bb = func.append_basic_block("while.merge")

        # 条件チェックへジャンプ
        self.builder.branch(cond_bb)

        # 条件ブロック
        self.builder.position_at_start(cond_bb)
        cond_val = self._gen_expression(stmt.condition)
        cond_bool = self.builder.icmp_signed("!=", cond_val, ir.Constant(self.int_type, 0))
        self.builder.cbranch(cond_bool, body_bb, merge_bb)

        # ボディブロック
        self.builder.position_at_start(body_bb)
        for s in stmt.body:
            self._gen_statement(s)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_bb)

        # merge
        self.builder.position_at_start(merge_bb)

    def _gen_function(self, stmt: FnStatement) -> None:
        """関数定義（簡易版: int64 引数・戻り値）"""
        param_types = [self.int_type] * len(stmt.params)
        func_type = ir.FunctionType(self.int_type, param_types)
        func = ir.Function(self.module, func_type, name=stmt.name)
        self.functions[stmt.name] = func

        block = func.append_basic_block("entry")
        saved_builder = self.builder
        saved_vars = self.variables.copy()

        self.builder = ir.IRBuilder(block)
        self.variables = {}

        # 引数を alloca にコピー
        for param, arg in zip(stmt.params, func.args):
            arg.name = param
            alloca = self.builder.alloca(self.int_type, name=param)
            self.builder.store(arg, alloca)
            self.variables[param] = alloca

        # ボディ
        for s in stmt.body:
            self._gen_statement(s)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(self.int_type, 0))

        # 復帰
        self.builder = saved_builder
        self.variables = saved_vars

    def _gen_expression(self, expr: Expression) -> ir.Value:
        """式のコード生成"""
        if isinstance(expr, IntLiteral):
            return ir.Constant(self.int_type, expr.value)

        if isinstance(expr, FloatLiteral):
            return ir.Constant(self.int_type, int(expr.value))

        if isinstance(expr, Identifier):
            if expr.name not in self.variables:
                raise CodeGenError(f"未定義の変数: {expr.name}", expr.line)
            return self.builder.load(self.variables[expr.name])

        if isinstance(expr, BinaryOp):
            left = self._gen_expression(expr.left)
            right = self._gen_expression(expr.right)

            if expr.op == "==":
                result = self.builder.icmp_signed("==", left, right)
                return self.builder.zext(result, self.int_type)
            elif expr.op == "!=":
                result = self.builder.icmp_signed("!=", left, right)
                return self.builder.zext(result, self.int_type)
            elif expr.op == ">":
                result = self.builder.icmp_signed(">", left, right)
                return self.builder.zext(result, self.int_type)
            elif expr.op == "<":
                result = self.builder.icmp_signed("<", left, right)
                return self.builder.zext(result, self.int_type)
            elif expr.op == "%":
                return self.builder.srem(left, right)
            else:
                raise CodeGenError(f"未対応の演算子: {expr.op}", expr.line)

        if isinstance(expr, StringLiteral):
            # 文字列は直接値としては使えないため、ポインタを返す
            str_val = self._create_global_string(expr.value)
            return self._get_string_ptr(str_val)

        raise CodeGenError(f"未対応の式: {type(expr).__name__}", expr.line)
