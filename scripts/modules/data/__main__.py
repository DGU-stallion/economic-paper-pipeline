#!/usr/bin/env python3
"""数据助手 — 独立运行入口"""
import argparse, json
from pathlib import Path
from scripts.modules.data.core import run, commit_report


def main():
    parser = argparse.ArgumentParser(description="数据助手")
    parser.add_argument("--project", "-p", help="项目名")
    parser.add_argument("--report", help="质量报告文本")
    args = parser.parse_args()

    PROJECTS_DIR = Path.cwd() / "papers"
    project_dir = PROJECTS_DIR / args.project if args.project else None

    if args.report and project_dir:
        result = commit_report(args.report, project_dir)
        print(f"✅ 数据质量报告已写入 {result['data_quality_report']}")
    else:
        result = run(project_dir=project_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
