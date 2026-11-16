"""小型 Clausewitz 语法读取器：保留位置，供兼容补丁和静态检查使用。"""
from __future__ import annotations

from dataclasses import dataclass
import re

TOKEN = re.compile(r'#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}]|[<>!]?=|[<>]|[^\s{}=<>!"#]+')


@dataclass
class Node:
    key: str
    value: str | list["Node"] | None
    start: int
    end: int
    brace: int | None = None
    op: str | None = "="

    def children(self, key: str | None = None) -> list["Node"]:
        nodes = self.value if isinstance(self.value, list) else []
        return [n for n in nodes if key is None or n.key == key]

    def scalar(self, key: str, default=None):
        nodes = self.children(key)
        return nodes[0].value if nodes else default

    def walk(self):
        yield self
        for child in self.children():
            yield from child.walk()


def parse(text: str) -> Node:
    tokens = [m for m in TOKEN.finditer(text) if not m[0].startswith("#")]
    pos = 0

    def body(nested=False):
        nonlocal pos
        nodes = []
        while pos < len(tokens):
            token = tokens[pos]
            if token[0] == "}":
                if not nested:
                    raise ValueError(f"多余的闭括号，字符 {token.start()}")
                pos += 1
                return nodes, token.end()
            if token[0] in {"{", "=", ">", "<", ">=", "<=", "!="}:
                raise ValueError(f"意外的 {token[0]}，字符 {token.start()}")
            pos += 1
            key = token[0].strip('"')
            if pos >= len(tokens) or tokens[pos][0] not in {"=", ">", "<", ">=", "<=", "!="}:
                nodes.append(Node(key, None, token.start(), token.end(), op=None))
                continue
            op = tokens[pos][0]
            pos += 1
            if pos >= len(tokens):
                raise ValueError(f"{key} 缺少值")
            value = tokens[pos]
            pos += 1
            if value[0] == "{":
                children, end = body(True)
                nodes.append(Node(key, children, token.start(), end, value.start(), op))
            elif value[0] in {"}", "=", "{", ">", "<"}:
                raise ValueError(f"{key} 的值无效")
            else:
                nodes.append(Node(key, value[0].strip('"'), token.start(), value.end(), op=op))
        if nested:
            raise ValueError("缺少闭括号")
        return nodes, len(text)

    children, _ = body()
    return Node("ROOT", children, 0, len(text))
