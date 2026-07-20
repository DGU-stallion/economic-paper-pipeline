#!/usr/bin/env python3
"""验证助手 — 独立运行入口"""

import argparse
import json

from scripts.shared.paths import PAPERS_DIR


def main():
    parser = argparse.ArgumentParser(description="验证助手")
    parser.add_argument("--project", "-p", help="项目名")
    parser.add_argument("--data", help="清洗后数据路径")
    parser.add_argument("--y", help="被解释变量 Y")
    parser.add_argument("--d", help="核心解释变量 D")
    parser.add_argument("--controls", nargs="*", help="控制变量")
    args = parser.parse_args()

    from scripts.modules.verify.core import run

    project_dir = PAPERS_DIR / args.project if args.project else None
    result = run(
        y_var=args.y or "",
        d_var=args.d or "",
        clean_data_path=args.data or "",
        controls=args.controls,
        project_dir=project_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
