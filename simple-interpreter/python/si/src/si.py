#!/usr/bin/env python3
import argparse
import ctypes
import importlib.util
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

# ----------------------------- Lexer -----------------------------

@dataclass
class Token:
    kind: str
    value: Any
    line: int
    col: int

KEYWORDS = {
    "let", "func", "return", "if", "else", "while", "true", "false", "null",
}

TWO_CHAR = {"==", "!=", "<=", ">=", "&&", "||"}
ONE_CHAR = set("+-*/%(){};,=!<>[]")

class SiSyntaxError(Exception): pass
class SiRuntimeError(Exception): pass
class ReturnSignal(Exception):
    def __init__(self, value): self.value = value

class Lexer:
    def __init__(self, source: str):
        self.s = source
        self.i = 0
        self.line = 1
        self.col = 1

    def peek(self, n=0):
        j = self.i + n
        return self.s[j] if j < len(self.s) else "\0"

    def advance(self):
        ch = self.peek()
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_ws_comments(self):
        while True:
            while self.peek().isspace(): self.advance()
            if self.peek() == "/" and self.peek(1) == "/":
                while self.peek() not in ("\n", "\0"): self.advance()
                continue
            if self.peek() == "/" and self.peek(1) == "*":
                self.advance(); self.advance()
                while not (self.peek() == "*" and self.peek(1) == "/"):
                    if self.peek() == "\0": raise SiSyntaxError("Unterminated block comment")
                    self.advance()
                self.advance(); self.advance()
                continue
            break

    def tokenize(self):
        out = []
        while True:
            self.skip_ws_comments()
            line, col = self.line, self.col
            ch = self.peek()
            if ch == "\0":
                out.append(Token("EOF", None, line, col)); return out
            if ch.isalpha() or ch == "_":
                text = ""
                while self.peek().isalnum() or self.peek() == "_": text += self.advance()
                out.append(Token(text if text in KEYWORDS else "IDENT", text, line, col)); continue
            if ch.isdigit():
                text = ""
                while self.peek().isdigit(): text += self.advance()
                if self.peek() == ".":
                    text += self.advance()
                    while self.peek().isdigit(): text += self.advance()
                    out.append(Token("NUMBER", float(text), line, col))
                else:
                    out.append(Token("NUMBER", int(text), line, col))
                continue
            if ch == '"':
                self.advance()
                text = ""
                while self.peek() != '"':
                    if self.peek() == "\0": raise SiSyntaxError(f"Unterminated string at {line}:{col}")
                    if self.peek() == "\\":
                        self.advance(); esc = self.advance()
                        text += {"n":"\n", "t":"\t", "r":"\r", '"':'"', "\\":"\\"}.get(esc, esc)
                    else:
                        text += self.advance()
                self.advance()
                out.append(Token("STRING", text, line, col)); continue
            two = ch + self.peek(1)
            if two in TWO_CHAR:
                self.advance(); self.advance(); out.append(Token(two, two, line, col)); continue
            if ch in ONE_CHAR:
                self.advance(); out.append(Token(ch, ch, line, col)); continue
            raise SiSyntaxError(f"Unexpected character {ch!r} at {line}:{col}")

# ----------------------------- AST -----------------------------

@dataclass
class Program: body: list
@dataclass
class Let: name: str; expr: Any
@dataclass
class Assign: name: str; expr: Any
@dataclass
class ExprStmt: expr: Any
@dataclass
class Block: body: list
@dataclass
class If: cond: Any; then: Any; otherwise: Any
@dataclass
class While: cond: Any; body: Any
@dataclass
class FuncDecl: name: str; params: list; body: Any
@dataclass
class Return: expr: Any
@dataclass
class Literal: value: Any
@dataclass
class Var: name: str
@dataclass
class Unary: op: str; right: Any
@dataclass
class Binary: left: Any; op: str; right: Any
@dataclass
class Call: callee: Any; args: list

# ----------------------------- Parser -----------------------------

class Parser:
    def __init__(self, tokens): self.t = tokens; self.i = 0
    def cur(self): return self.t[self.i]
    def match(self, *kinds):
        if self.cur().kind in kinds:
            tok = self.cur(); self.i += 1; return tok
        return None
    def need(self, kind, msg=None):
        tok = self.match(kind)
        if not tok:
            c = self.cur()
            raise SiSyntaxError(msg or f"Expected {kind} at {c.line}:{c.col}, got {c.kind}")
        return tok

    def parse(self):
        body = []
        while self.cur().kind != "EOF": body.append(self.decl())
        return Program(body)

    def decl(self):
        if self.match("func"): return self.func_decl()
        if self.match("let"): return self.let_decl()
        return self.stmt()

    def func_decl(self):
        name = self.need("IDENT", "Expected function name").value
        self.need("(")
        params = []
        if not self.match(")"):
            while True:
                params.append(self.need("IDENT", "Expected parameter name").value)
                if self.match(")"): break
                self.need(",")
        return FuncDecl(name, params, self.block())

    def let_decl(self):
        name = self.need("IDENT", "Expected variable name").value
        self.need("=")
        expr = self.expr()
        self.need(";")
        return Let(name, expr)

    def stmt(self):
        if self.match("if"): return self.if_stmt()
        if self.match("while"): return self.while_stmt()
        if self.match("return"):
            expr = Literal(None) if self.cur().kind == ";" else self.expr()
            self.need(";"); return Return(expr)
        if self.cur().kind == "{": return self.block()
        expr = self.expr()
        if isinstance(expr, Var) and self.match("="):
            val = self.expr(); self.need(";"); return Assign(expr.name, val)
        self.need(";")
        return ExprStmt(expr)

    def block(self):
        self.need("{")
        body = []
        while self.cur().kind != "}": body.append(self.decl())
        self.need("}")
        return Block(body)

    def if_stmt(self):
        self.need("("); cond = self.expr(); self.need(")")
        then = self.stmt()
        otherwise = self.stmt() if self.match("else") else None
        return If(cond, then, otherwise)

    def while_stmt(self):
        self.need("("); cond = self.expr(); self.need(")")
        return While(cond, self.stmt())

    def expr(self): return self.or_expr()
    def or_expr(self):
        node = self.and_expr()
        while self.match("||"): node = Binary(node, "||", self.and_expr())
        return node
    def and_expr(self):
        node = self.equality()
        while self.match("&&"): node = Binary(node, "&&", self.equality())
        return node
    def equality(self):
        node = self.compare()
        while True:
            op = self.match("==", "!=")
            if not op: return node
            node = Binary(node, op.kind, self.compare())
    def compare(self):
        node = self.term()
        while True:
            op = self.match("<", "<=", ">", ">=")
            if not op: return node
            node = Binary(node, op.kind, self.term())
    def term(self):
        node = self.factor()
        while True:
            op = self.match("+", "-")
            if not op: return node
            node = Binary(node, op.kind, self.factor())
    def factor(self):
        node = self.unary()
        while True:
            op = self.match("*", "/", "%")
            if not op: return node
            node = Binary(node, op.kind, self.unary())
    def unary(self):
        op = self.match("!", "-")
        if op: return Unary(op.kind, self.unary())
        return self.call()
    def call(self):
        node = self.primary()
        while self.match("("):
            args = []
            if not self.match(")"):
                while True:
                    args.append(self.expr())
                    if self.match(")"): break
                    self.need(",")
            node = Call(node, args)
        return node
    def primary(self):
        tok = self.cur()
        if self.match("NUMBER"): return Literal(tok.value)
        if self.match("STRING"): return Literal(tok.value)
        if self.match("true"): return Literal(True)
        if self.match("false"): return Literal(False)
        if self.match("null"): return Literal(None)
        if self.match("IDENT"): return Var(tok.value)
        if self.match("("):
            node = self.expr(); self.need(")"); return node
        raise SiSyntaxError(f"Expected expression at {tok.line}:{tok.col}")

# ----------------------------- Runtime -----------------------------

class Env:
    def __init__(self, parent=None): self.parent = parent; self.values = {}
    def define(self, name, val): self.values[name] = val
    def get(self, name):
        if name in self.values: return self.values[name]
        if self.parent: return self.parent.get(name)
        raise SiRuntimeError(f"Undefined name: {name}")
    def set(self, name, val):
        if name in self.values: self.values[name] = val; return
        if self.parent: self.parent.set(name, val); return
        raise SiRuntimeError(f"Undefined name: {name}")

class SiFunction:
    def __init__(self, interp, name, params, body, closure):
        self.interp, self.name, self.params, self.body, self.closure = interp, name, params, body, closure
    def __call__(self, *args):
        if len(args) != len(self.params):
            raise SiRuntimeError(f"{self.name} expected {len(self.params)} args, got {len(args)}")
        env = Env(self.closure)
        for p, a in zip(self.params, args): env.define(p, a)
        try:
            self.interp.exec_block(self.body.body, env)
        except ReturnSignal as r:
            return r.value
        return None
    def __repr__(self): return f"<func {self.name}>"

class Interpreter:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.getcwd()
        self.globals = Env()
        self.loaded_libs = []
        self.add_builtin("print", lambda *xs: print(*xs))
        self.add_builtin("clock", lambda: time.time())
        self.add_builtin("len", lambda x: len(x))
        self.add_builtin("str", lambda x: str(x))
        self.add_builtin("int", lambda x: int(x))
        self.add_builtin("float", lambda x: float(x))
        self.add_builtin("plugin", self.load_plugin)
        self.add_builtin("native", self.bind_native)

    def add_builtin(self, name: str, func: Callable): self.globals.define(name, func)

    def resolve_path(self, path):
        return path if os.path.isabs(path) else os.path.join(self.base_dir, path)

    def load_plugin(self, path):
        full = self.resolve_path(path)
        spec = importlib.util.spec_from_file_location("si_plugin_" + os.path.basename(full).replace('.', '_'), full)
        if spec is None or spec.loader is None:
            raise SiRuntimeError(f"Could not load plugin: {path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "register"):
            raise SiRuntimeError("Plugin must define register(si)")
        mod.register(self)
        return None

    def ctype_for(self, name):
        return {
            "int": ctypes.c_int,
            "double": ctypes.c_double,
            "string": ctypes.c_char_p,
            "void": None,
        }.get(name)

    def bind_native(self, lib_path, symbol, si_name, ret_type, *arg_types):
        full = self.resolve_path(lib_path)
        lib = ctypes.CDLL(full)
        fn = getattr(lib, symbol)
        ret = self.ctype_for(ret_type)
        args = [self.ctype_for(a) for a in arg_types]
        if any(a is None for a in args):
            raise SiRuntimeError("Native args cannot be void")
        fn.restype = ret
        fn.argtypes = args
        self.loaded_libs.append(lib)
        def wrapper(*vals):
            if len(vals) != len(args): raise SiRuntimeError(f"{si_name} expected {len(args)} args")
            cooked = []
            for val, typ in zip(vals, arg_types):
                cooked.append(val.encode() if typ == "string" and isinstance(val, str) else val)
            result = fn(*cooked)
            if ret_type == "string" and isinstance(result, bytes): return result.decode()
            return result
        self.add_builtin(si_name, wrapper)
        return None

    def run(self, program):
        for stmt in program.body: self.exec(stmt, self.globals)

    def exec_block(self, body, env):
        for stmt in body: self.exec(stmt, env)

    def exec(self, node, env):
        if isinstance(node, Let): env.define(node.name, self.eval(node.expr, env)); return
        if isinstance(node, Assign): env.set(node.name, self.eval(node.expr, env)); return
        if isinstance(node, ExprStmt): self.eval(node.expr, env); return
        if isinstance(node, Block): self.exec_block(node.body, Env(env)); return
        if isinstance(node, If):
            if self.truthy(self.eval(node.cond, env)): self.exec(node.then, env)
            elif node.otherwise: self.exec(node.otherwise, env)
            return
        if isinstance(node, While):
            while self.truthy(self.eval(node.cond, env)): self.exec(node.body, env)
            return
        if isinstance(node, FuncDecl): env.define(node.name, SiFunction(self, node.name, node.params, node.body, env)); return
        if isinstance(node, Return): raise ReturnSignal(self.eval(node.expr, env))
        raise SiRuntimeError(f"Unknown statement: {node}")

    def eval(self, node, env):
        if isinstance(node, Literal): return node.value
        if isinstance(node, Var): return env.get(node.name)
        if isinstance(node, Unary):
            r = self.eval(node.right, env)
            return -r if node.op == "-" else (not self.truthy(r))
        if isinstance(node, Binary):
            if node.op == "&&":
                return self.truthy(self.eval(node.left, env)) and self.truthy(self.eval(node.right, env))
            if node.op == "||":
                return self.truthy(self.eval(node.left, env)) or self.truthy(self.eval(node.right, env))
            l = self.eval(node.left, env); r = self.eval(node.right, env)
            if node.op == "+": return l + r
            if node.op == "-": return l - r
            if node.op == "*": return l * r
            if node.op == "/": return l / r
            if node.op == "%": return l % r
            if node.op == "==": return l == r
            if node.op == "!=": return l != r
            if node.op == "<": return l < r
            if node.op == "<=": return l <= r
            if node.op == ">": return l > r
            if node.op == ">=": return l >= r
            raise SiRuntimeError(f"Unknown operator: {node.op}")
        if isinstance(node, Call):
            fn = self.eval(node.callee, env)
            args = [self.eval(a, env) for a in node.args]
            if not callable(fn): raise SiRuntimeError(f"Not callable: {fn}")
            return fn(*args)
        raise SiRuntimeError(f"Unknown expression: {node}")

    def truthy(self, v): return False if v is None else bool(v)

def run_source(source, filename="<stdin>"):
    base = os.path.dirname(os.path.abspath(filename)) if filename != "<stdin>" else os.getcwd()
    program = Parser(Lexer(source).tokenize()).parse()
    Interpreter(base).run(program)

def main(argv=None):
    ap = argparse.ArgumentParser(prog="si", description="si: a tiny C-like interpreter")
    ap.add_argument("file", nargs="?", help=".si source file. Reads stdin when omitted.")
    ns = ap.parse_args(argv)
    try:
        if ns.file:
            with open(ns.file, "r", encoding="utf-8") as f: src = f.read()
            run_source(src, ns.file)
        else:
            run_source(sys.stdin.read())
    except (SiSyntaxError, SiRuntimeError, OSError, AttributeError) as e:
        print(f"si error: {e}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
