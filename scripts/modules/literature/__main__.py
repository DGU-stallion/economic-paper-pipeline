#!/usr/bin/env python3
"""文献助手 — 独立运行入口"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from scripts.modules.literature.core import run, commit_review, commit_bib, ENTRY_PROMPT


def main():
    parser = argparse.ArgumentParser(description="文献助手")
    parser.add_argument("--project", "-p", help="项目名")
    parser.add_argument("--standalone", action="store_true", help="输出入口话术")
    parser.add_argument("--papers", help="候选论文 JSON 文件")
    parser.add_argument("--review", help="综述正文 JSON 文件")
    parser.add_argument("--bib", help="参考文献 JSON 文件")
    parser.add_argument("--paper-count", type=int, default=0, help="候选论文数")
    args = parser.parse_args()

    if args.standalone:
        print(ENTRY_PROMPT.format(paper_count=args.paper_count))
        return

    PROJECTS_DIR = Path.cwd() / "papers"
    project_dir = PROJECTS_DIR / args.project if args.project else None

    papers = []
    if args.papers:
        with open(args.papers, "r", encoding="utf-8") as f:
            papers = json.load(f)

    result = run(candidate_papers=papers, project_dir=project_dir)

    if args.review and project_dir:
        with open(args.review, "r", encoding="utf-8") as f:
            review_data = json.load(f)
        result.update(review_data)
        commit_review(result, project_dir, result.get("research_question", ""))
        print(f"✅ 文献综述已写入 {project_dir / 'literature' / '04_review_final.md'}")

    if args.bib and project_dir:
        with open(args.bib, "r", encoding="utf-8") as f:
            bib_data = json.load(f)
        commit_bib(bib_data, project_dir)
        print(f"✅ 参考文献已写入 {project_dir / 'paper' / 'erjref.bib'}")

    if not args.project:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
