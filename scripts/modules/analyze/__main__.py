#!/usr/bin/env python3
"""分析助手 — 独立运行入口"""
import argparse, json
from pathlib import Path
from scripts.modules.analyze.core import run, commit_baseline


def main():
    parser = argparse.ArgumentParser(description="分析助手")
    parser.add_argument("--project", "-p", help="项目名")
    parser.add_argument("--baseline", help="基准回归结果 JSON")
    args = parser.parse_args()

    PROJECTS_DIR = Path.cwd() / "papers"
    project_dir = PROJECTS_DIR / args.project if args.project else None

    if args.baseline and project_dir:
        with open(args.baseline, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = commit_baseline(data, project_dir)
        print(f"✅ 基准回归表已写入 {result['baseline_tex']}")
    else:
        result = run(project_dir=project_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
