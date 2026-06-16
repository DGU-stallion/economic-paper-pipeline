#!/usr/bin/env python3
"""格式助手 — 独立运行入口"""
import argparse
from scripts.shared.paths import PAPERS_DIR
from scripts.modules.format.core import run, compile_tex, detect_texlive


def main():
    parser = argparse.ArgumentParser(description="格式助手")
    parser.add_argument("--project", "-p", help="项目名")
    parser.add_argument("--compile", action="store_true", help="编译 LaTeX")
    parser.add_argument("--check-texlive", action="store_true", help="检测 TeX Live")
    args = parser.parse_args()

    if args.check_texlive:
        if detect_texlive():
            print("✅ TeX Live 已安装")
        else:
            print("❌ TeX Live 未安装")
        return

    project_dir = PAPERS_DIR / args.project if args.project else None

    if args.compile and project_dir:
        tex_path = project_dir / "paper" / "main.tex"
        if not tex_path.exists():
            print(f"❌ 未找到 {tex_path}")
            return
        result = compile_tex(tex_path, project_dir)
        if result["compile_success"]:
            print(f"✅ 编译成功: {result['pdf_path']}")
        else:
            print(f"❌ 编译失败，日志: {result['log_path']}")
    else:
        result = run(project_dir=project_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
