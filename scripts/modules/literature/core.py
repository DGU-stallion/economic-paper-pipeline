#!/usr/bin/env python3
"""文献助手核心逻辑"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def run(
    candidate_papers: Optional[List[dict]] = None,
    research_question: str = "",
    project_dir: Optional[Path] = None,
) -> dict:
    """启动文献梳理流程"""
    if project_dir:
        lit_dir = project_dir / "literature"
        lit_dir.mkdir(parents=True, exist_ok=True)
    return {
        "literature_review_path": "",
        "bib_path": "",
        "research_gap": "",
        "total_papers": len(candidate_papers) if candidate_papers else 0,
    }


def commit_review(
    result: dict,
    project_dir: Path,
    research_question: str = "",
):
    """将文献综述结果写入产出文件"""
    now = datetime.now().isoformat(timespec="minutes")
    lit_dir = project_dir / "literature"
    lit_dir.mkdir(parents=True, exist_ok=True)

    review_text = result.get("review_text", "")
    gap = result.get("research_gap", "")

    content = f"""\
# 文献综述

研究问题: {research_question}
生成时间: {now}
涵盖论文: {result.get('total_papers', 0)} 篇

## 研究空白

{gap}

## 综述正文

{review_text}
"""
    review_file = lit_dir / "04_review_final.md"
    review_file.write_text(content, encoding="utf-8")


ENTRY_PROMPT = """\
你好，我是文献助手。调研助手已经帮你搜到了候选论文列表。

接下来我会帮你：
1. 筛选高相关文献
2. 梳理研究脉络
3. 撰写综述正文
4. 生成 .bib 参考文献文件

候选论文共 {paper_count} 篇，我从筛选开始。"""
