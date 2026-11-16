"""检查 EU4 运行脚本和本地化的 BOM 规则；不修改文件。"""
from pathlib import Path
import sys


def errors(root: Path) -> list[str]:
    result = []
    # 新增：事件脚本也遵循无 BOM 规则，防止新增事件被首行编码破坏。
    for folder in ["common", "missions", "interface", "events"]:
        for file in (root / folder).rglob("*"):
            if file.is_file() and file.suffix in {".txt", ".gui", ".gfx"}:
                data = file.read_bytes()
                if data.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")):
                    result.append(f"{file.relative_to(root)}: 运行脚本不可带 BOM")
    for file in (root / "localisation").rglob("*.yml"):
        if not file.read_bytes().startswith(b"\xef\xbb\xbf"):
            result.append(f"{file.relative_to(root)}: 本地化必须保留 UTF-8 BOM")
    return result


if __name__ == "__main__":
    problems = errors(Path(__file__).resolve().parent.parent)
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print("Encoding checks passed: scripts have no BOM; localisation retains BOM.")
