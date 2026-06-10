#!/usr/bin/env python3
"""论文助手 — 独立运行入口"""
import argparse
from pathlib import Path
from scripts.modules.write.core import run, commit_tex


def main():
    parser = argparse.ArgumentParser(description="论文助手")
    parser.add_argument("--project", "-p", help="项目名")
    parser.add_argument("--tex", help="LaTeX 源码文件路径")
    args = parser.parse_args()

    PROJECTS_DIR = Path.cwd() / "papers"
    project_dir = PROJECTS_DIR / args.project if args.project else None

    if args.tex and project_dir:
        with open(args.tex, "r", encoding="utf-8") as f:
            content = f.read()
        result = commit_tex(content, project_dir)
        print(f"✅ 论文已写入 {result['tex_path']}")
    else:
        result = run(project_dir=project_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
