#!/usr/bin/env python3
"""验证助手 — 独立运行入口"""
import argparse, json
from pathlib import Path
from scripts.modules.verify.core import run, commit_results


def main():
    parser = argparse.ArgumentParser(description="验证助手")
    parser.add_argument("--project", "-p", help="项目名")
    parser.add_argument("--results", help="稳健性检验结果 JSON")
    args = parser.parse_args()

    PROJECTS_DIR = Path.cwd() / "papers"
    project_dir = PROJECTS_DIR / args.project if args.project else None

    if args.results and project_dir:
        with open(args.results, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = commit_results(data, project_dir)
        print(f"✅ 稳健性检验表已写入 {result['robustness_tex']}")
    else:
        result = run(project_dir=project_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
