#!/usr/bin/env python3
"""调研助手核心逻辑

流程:
  输入 → [LLM 生成搜索策略] → [web-access 执行搜索] → [LLM 整理结果] → 输出

core.py 提供：
  - run() 入口（编排器调用）
  - 数据结构定义
  - 产出文件写入
  - 报告模板

实际搜索由 LLM 使用 web-access 工具在对话层完成。
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json


# ── 数据结构 ──

@dataclass
class PaperEntry:
    """一篇候选论文"""
    title: str = ""
    authors: str = ""
    year: str = ""
    abstract: str = ""
    url: str = ""
    source: str = ""  # google-scholar / arxiv / ssrn / nber


@dataclass
class DataSourceEntry:
    """一个候选数据源"""
    name: str = ""
    description: str = ""
    variables_available: List[str] = field(default_factory=list)
    time_coverage: str = ""
    sample_size: str = ""
    access_method: str = ""  # free / application / purchase
    url: str = ""
    notes: str = ""


# ── 入口 ──

def run(
    research_question: str,
    keywords: Optional[List[str]] = None,
    project_dir: Optional[Path] = None,
    extra_context: Optional[dict] = None,
) -> dict:
    """运行调研助手（准备阶段）

    这个函数负责：
      1. 验证输入完整性
      2. 创建产出目录
      3. 返回初始化的空结构（供 LLM 填充）

    LLM 在对话中实际执行搜索，然后调用 commit_results() 写入产出。

    Args:
      research_question: 研究问题
      keywords: 搜索关键词（可选）
      project_dir: 项目路径（可选，用于写文件）
      extra_context: 额外的上下文（y_var, d_var, time_window 等）

    Returns:
      初始化的 context 更新字典
    """
    if keywords is None:
        keywords = []

    # 创建产出目录
    if project_dir:
        lit_dir = project_dir / "literature"
        data_dir = project_dir / "data"
        lit_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

    return {
        "candidate_papers": [],
        "data_sources": [],
        "feasibility_verdict": "needs_adjustment",
    }


def commit_results(
    result: dict,
    project_dir: Path,
    research_question: str = "",
):
    """将搜索结果写入产出文件

    Args:
      result: LLM 填充好的结果字典
      project_dir: 项目路径
      research_question: 研究问题
    """
    now = datetime.now().isoformat(timespec="minutes")

    # ── 候选论文列表 ──
    papers = result.get("candidate_papers", [])
    lit_dir = project_dir / "literature"
    lit_dir.mkdir(parents=True, exist_ok=True)

    paper_entries = []
    for i, p in enumerate(papers, 1):
        title = p.get("title", "(无标题)")
        authors = p.get("authors", "")
        year = p.get("year", "")
        source = p.get("source", "")
        abstract = p.get("abstract", "")
        url = p.get("url", "")

        entry = f"### {i}. {title}\n\n"
        if authors:
            entry += f"- **作者**: {authors}\n"
        if year:
            entry += f"- **年份**: {year}\n"
        if source:
            entry += f"- **来源**: {source}\n"
        if url:
            entry += f"- **链接**: {url}\n"
        if abstract:
            entry += f"- **摘要**: {abstract[:300]}{'...' if len(abstract) > 300 else ''}\n"
        paper_entries.append(entry)

    paper_content = f"""\
# 候选论文列表

研究问题: {research_question}
生成时间: {now}
总篇数: {len(papers)}

---

{chr(10).join(paper_entries)}
"""
    paper_file = lit_dir / "00_candidate_papers.md"
    paper_file.write_text(paper_content, encoding="utf-8")

    # ── 数据源可行性报告 ──
    data_sources = result.get("data_sources", [])
    verdict = result.get("feasibility_verdict", "needs_adjustment")
    data_dir = project_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    verdict_labels = {
        "feasible": "✅ 数据可行，可以继续",
        "needs_adjustment": "⚠️ 数据部分可行，需要调整研究设计",
        "infeasible": "❌ 数据不可行，建议回退修改研究问题",
    }

    source_entries = []
    for i, ds in enumerate(data_sources, 1):
        name = ds.get("name", "(未命名)")
        desc = ds.get("description", "")
        variables = ds.get("variables_available", [])
        time_cov = ds.get("time_coverage", "")
        sample = ds.get("sample_size", "")
        access = ds.get("access_method", "")
        url = ds.get("url", "")
        notes = ds.get("notes", "")

        entry = f"### {i}. {name}\n\n"
        if desc:
            entry += f"- **说明**: {desc}\n"
        if variables:
            entry += f"- **可用变量**: {', '.join(variables)}\n"
        if time_cov:
            entry += f"- **时间覆盖**: {time_cov}\n"
        if sample:
            entry += f"- **样本量**: {sample}\n"
        if access:
            entry += f"- **获取方式**: {access}\n"
        if url:
            entry += f"- **链接**: {url}\n"
        if notes:
            entry += f"- **备注**: {notes}\n"
        source_entries.append(entry)

    report_content = f"""\
# 数据可行性报告

研究问题: {research_question}
生成时间: {now}

## 结论

{verdict_labels.get(verdict, verdict)}

## 可用数据源

{chr(10).join(source_entries) if source_entries else '(未找到匹配的数据源)'}

## 建议

{_generate_suggestion(verdict, data_sources)}
"""
    report_file = data_dir / "00_feasibility_report.md"
    report_file.write_text(report_content, encoding="utf-8")


def _generate_suggestion(verdict: str, data_sources: list) -> str:
    """根据可行性结论生成建议"""
    if verdict == "feasible":
        return "数据条件满足，可以进入文献综述阶段。"
    elif verdict == "needs_adjustment":
        if data_sources:
            names = [ds.get("name", "") for ds in data_sources if ds.get("name")]
            if names:
                return f"以下数据源部分满足要求：{', '.join(names)}。建议调整时间窗口或变量定义以匹配可用数据。"
        return "建议调整研究问题的范围或变量定义，重新评估数据可行性。"
    else:
        return "当前研究问题在现有数据条件下不可行。建议回到概念助手阶段，调整研究方向或数据来源。"
