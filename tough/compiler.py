"""TOUGH 言語 - コンパイラパイプライン

Lexer → Parser → CodeGen → JIT 実行を統合する。
"""

import sys
from ctypes import CFUNCTYPE, c_int

from llvmlite import ir, binding

from tough.lexer import Lexer, LexerError
from tough.parser import Parser, ParseError
from tough.codegen import CodeGenerator, CodeGenError


class CompileError(Exception):
    """コンパイルエラー"""
    pass


class Compiler:
    """TOUGH コンパイラ"""

    def __init__(self):
        binding.initialize_all_targets()
        binding.initialize_all_asmprinters()

    def compile_source(self, source: str) -> ir.Module:
        """TOUGH ソースコードを LLVM IR モジュールに変換する"""
        # 1. 字句解析
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # 2. 構文解析
        parser = Parser(tokens)
        ast = parser.parse()

        # 3. コード生成
        codegen = CodeGenerator()
        module = codegen.generate(ast)

        return module

    def run(self, source: str) -> int:
        """TOUGH ソースコードをコンパイルして JIT 実行する"""
        module = self.compile_source(source)

        # LLVM IR を文字列化してパース
        llvm_ir = str(module)
        mod = binding.parse_assembly(llvm_ir)
        mod.verify()

        # 最適化 (PassManagerBuilder がない環境向けの対応)
        try:
            pmb = binding.create_pass_manager_builder()
            pmb.opt_level = 2
            pm = binding.create_module_pass_manager()
            pmb.populate(pm)
            pm.run(mod)
        except AttributeError:
            pass  # 新しい llvmlite では PassManagerBuilder が削除されている可能性があるためスキップ

        # JIT 実行エンジン
        target = binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        engine = binding.create_mcjit_compiler(mod, target_machine)

        # main 関数を取得して実行
        main_ptr = engine.get_function_address("main")
        main_func = CFUNCTYPE(c_int)(main_ptr)
        result = main_func()

        return result

    def emit_ir(self, source: str) -> str:
        """TOUGH ソースコードから LLVM IR テキストを取得する"""
        module = self.compile_source(source)
        return str(module)

    def run_file(self, filepath: str) -> int:
        """TOUGH ファイルを読み込んでコンパイル＆実行する"""
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        return self.run(source)

    def emit_ir_file(self, filepath: str) -> str:
        """TOUGH ファイルから LLVM IR テキストを取得する"""
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        return self.emit_ir(source)
