#!/usr/bin/env python3
"""文献助手核心逻辑

从候选论文列表到完整文献综述 + .bib。
LLM 在对话中驱动筛选/脉络梳理/综述撰写流程，core.py 负责结构化产出。
"""

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
        "screened_papers": [],
        "key_theories": [],
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
    total = result.get("total_papers", 0)
    key_theories = result.get("key_theories", [])

    theories_text = ""
    if key_theories:
        theories_text = "## 核心理论框架\n\n"
        for t in key_theories:
            if isinstance(t, dict):
                theories_text += f"- **{t.get('name', '')}**: {t.get('desc', '')}\n"
            else:
                theories_text += f"- {t}\n"
        theories_text += "\n"

    content = f"""\
# 文献综述

研究问题: {research_question}
生成时间: {now}
涵盖论文: {total} 篇

{theories_text}"""
    if review_text:
        content += f"""\
## 综述正文

{review_text}

"""
    content += f"""\
## 研究空白

{gap if gap else '（待识别）'}

---
*由文献助手 (Literature) 自动生成*
"""
    review_file = lit_dir / "04_review_final.md"
    review_file.write_text(content, encoding="utf-8")


def commit_bib(
    bib_entries: List[dict],
    project_dir: Path,
):
    """将文献引用写入 .bib 文件

    bib_entries: [{cite_key, authors, title, journal, year, volume, pages, url}]
    """
    paper_dir = project_dir / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)

    lines = []
    for entry in bib_entries:
        key = entry.get("cite_key", f"ref{len(lines)+1}")
        authors = entry.get("authors", "")
        title = entry.get("title", "")
        journal = entry.get("journal", "")
        year = entry.get("year", "")
        volume = entry.get("volume", "")
        pages = entry.get("pages", "")
        url = entry.get("url", "")

        lines.append(f"@article{{{key},")
        if authors:
            lines.append(f"  author = {{{authors}}},")
        if title:
            lines.append(f"  title = {{{title}}},")
        if journal:
            lines.append(f"  journal = {{{journal}}},")
        if year:
            lines.append(f"  year = {{{year}}},")
        if volume:
            lines.append(f"  volume = {{{volume}}},")
        if pages:
            lines.append(f"  pages = {{{pages}}},")
        if url:
            lines.append(f"  url = {{{url}}},")
        lines.append("}\n")

    bib_path = paper_dir / "erjref.bib"
    bib_path.write_text("\n".join(lines), encoding="utf-8")


ENTRY_PROMPT = """\
你好，我是文献助手。调研助手已经帮你搜到了候选论文列表（共 {paper_count} 篇）。

接下来我会帮你：
1. 筛选高相关文献
2. 梳理研究脉络
3. 撰写综述正文
4. 生成 .bib 参考文献文件

从筛选开始——你觉得哪些论文和你的研究问题最相关？
"""
