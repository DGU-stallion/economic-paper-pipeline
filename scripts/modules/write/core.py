#!/usr/bin/env python3
"""论文助手核心逻辑

大纲 → 各章节撰写 → LaTeX 组装 → 质量检测。
LLM 在对话中驱动，core.py 负责 LaTeX 模板渲染和文件输出。
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def run(
    research_question: str = "",
    y_var: str = "",
    d_var: str = "",
    project_dir: Optional[Path] = None,
) -> dict:
    """启动论文撰写流程"""
    if project_dir:
        (project_dir / "paper" / "sections").mkdir(parents=True, exist_ok=True)
        (project_dir / "paper" / "tables").mkdir(parents=True, exist_ok=True)
        (project_dir / "paper" / "figures").mkdir(parents=True, exist_ok=True)
    return {"tex_path": ""}


def commit_outline(outline: str, project_dir: Path) -> str:
    """写入论文大纲"""
    outline_path = project_dir / "paper" / "outline.md"
    outline_path.write_text(outline, encoding="utf-8")
    return str(outline_path)


def commit_section(section_name: str, tex_content: str, project_dir: Path) -> str:
    """写入单个章节的 .tex 文件

    section_name: 'introduction', 'literature', 'model', 'results', 'robustness', 'conclusion'
    """
    name_map = {
        "introduction": "01_introduction",
        "literature": "02_literature",
        "model": "03_model",
        "results": "04_empirical_results",
        "robustness": "05_robustness",
        "conclusion": "06_conclusion",
    }
    filename = name_map.get(section_name, section_name)
    section_path = project_dir / "paper" / "sections" / f"{filename}.tex"
    section_path.write_text(tex_content, encoding="utf-8")
    return str(section_path)


def commit_main_tex(
    project_dir: Path,
    title: str = "",
    authors: str = "",
    abstract: str = "",
    template: str = "economic-research",
    sections: Optional[List[str]] = None,
) -> str:
    """生成主文件 main.tex 并组装各章节"""
    if sections is None:
        sections = ["introduction", "literature", "model", "results", "robustness", "conclusion"]

    include_lines = []
    for s in sections:
        include_lines.append(f"\\input{{sections/{s}}}")

    includes = "\n".join(include_lines)

    cls_map = {
        "economic-research": "chinese-erj",
        "qje": "chinese-erj",
        "aer": "article",
    }
    cls = cls_map.get(template, "chinese-erj")

    tex = f"""\
% 主文件 (自动生成 {datetime.now().isoformat(timespec='minutes')})
% 模板: {template}
\\documentclass{{{cls}}}

\\usepackage{{ctex}}
\\usepackage{{booktabs}}
\\usepackage{{dcolumn}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}

\\title{{{title}}}
\\author{{{authors}}}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
{abstract}
\\end{{abstract}}

{includes}

\\bibliographystyle{{chinese-erj}}
\\bibliography{{erjref}}

\\end{{document}}
"""
    tex_path = project_dir / "paper" / "main.tex"
    tex_path.write_text(tex, encoding="utf-8")
    return str(tex_path)


def commit_qc_report(report: str, project_dir: Path) -> str:
    """写入质量检测报告（humanizer-zh 输出）"""
    report_path = project_dir / "paper" / "humanizer_report.md"
    report_path.write_text(report, encoding="utf-8")
    return str(report_path)
