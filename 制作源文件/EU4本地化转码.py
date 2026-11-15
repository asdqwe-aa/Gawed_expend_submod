"""将中文本地化转换为 EU4 双字节补丁使用的特殊转义格式。"""

from __future__ import annotations

import argparse
from pathlib import Path

# 游戏会把这些字节用于分隔符或文本标记；碰到时须调整对应字节并更换前导码。
# 采用 EU4 1.26 之后的低字节偏移量；额外转义已知的 #、/、: 和 !。
_RESERVED = frozenset({
    0x00, 0x0A, 0x0D, 0x20, 0x21, 0x22, 0x23, 0x24,
    0x2F, 0x3A, 0x3B, 0x3D, 0x40, 0x5B, 0x5C, 0x5D,
    0x5F, 0x7B, 0x7D, 0x7E, 0x80, 0xA3, 0xA4, 0xA7, 0xBD,
})


def _file_character(byte: int) -> str:
    """把 CP1252 扩展区的字节表示为可写入 UTF-8 文件的字符。"""
    try:
        return bytes((byte,)).decode("cp1252")
    except UnicodeDecodeError:
        # CP1252 未定义的五个字节沿用原字节的码点。
        return chr(byte)


def escape_text(text: str) -> str:
    """只转换非 Latin1 字符，保留键名、引号、格式控制符及换行。"""
    result: list[str] = []
    for character in text:
        codepoint = ord(character)
        if codepoint < 0x100:
            result.append(character)
            continue
        if codepoint > 0xFFFF:
            raise ValueError(f"超出 EU4 双字节编码范围的字符：{character!r}")

        low = codepoint & 0xFF
        high = codepoint >> 8
        escape_low = low in _RESERVED
        escape_high = high in _RESERVED
        marker = 0x10 + int(escape_low) + 2 * int(escape_high)
        if escape_low:
            low += 14
        if escape_high:
            high -= 9
        result.extend((chr(marker), _file_character(low), _file_character(high)))
    return "".join(result)


def convert_file(source: Path, destination: Path) -> None:
    """读入便于编辑的中文原文，输出带 UTF-8 BOM 的游戏用本地化。"""
    text = source.read_text(encoding="utf-8-sig")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(escape_text(text), encoding="utf-8-sig")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="未经转码的中文 .yml 原文")
    parser.add_argument("destination", type=Path, help="游戏 localisation 目录内的 .yml 路径")
    arguments = parser.parse_args()
    convert_file(arguments.source, arguments.destination)
