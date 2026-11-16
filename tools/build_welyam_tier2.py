"""读取当前 Anbennar 君主制二级改革列表，生成只替换该层的任务效果。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pdx_script import parse

ROOT = Path(__file__).resolve().parent.parent
TARGET = "empower_magnate_council"
OUTPUT = "common/scripted_effects/gcd_welyam_tier2_reform_effect.txt"


def build(anb: Path):
    source = anb / "common/governments/00_governments.txt"
    monarchy = parse(source.read_text(encoding="utf-8-sig")).children("monarchy")[0]
    level = monarchy.children("reform_levels")[0].children()[1]
    reforms = [n.key for n in level.children("reforms")[0].children()]
    assert len(reforms) == len(set(reforms)) and TARGET in reforms
    lines = [
        "# 生成：tools/build_welyam_tier2.py；更新 Anbennar 后从当前君主制二级列表重建。",
        "# 修正：仅替换第二层现有选项，不使用 lose_reforms，不移除其他层或扣改革点数。",
        "gcd_welyam_normalize_tier2_effect = {",
        f"    if = {{ limit = {{ NOT = {{ has_reform = {TARGET} }} }}",
    ]
    for reform in reforms:
        if reform != TARGET:
            lines.append(f"        if = {{ limit = {{ has_reform = {reform} }} remove_government_reform = {reform} }}")
    lines.extend([f"        add_government_reform = {TARGET}", "    }", "}", ""])
    content = "\n".join(lines).encode("utf-8")
    metadata = {
        "source": "common/governments/00_governments.txt",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "level": 2, "level_key": level.key, "reforms": reforms,
        "generated_sha256": hashlib.sha256(content).hexdigest(),
    }
    return content, metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("anb_root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content, metadata = build(args.anb_root)
    if args.check:
        assert (ROOT / OUTPUT).read_bytes() == content, "二级改革列表已变更，需要重建"
    else:
        (ROOT / OUTPUT).write_bytes(content)
        (ROOT / "制作源文件/改革二级政改基线.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Tier 2 reform {'checked' if args.check else 'generated'}: {len(metadata['reforms'])} choices.")
