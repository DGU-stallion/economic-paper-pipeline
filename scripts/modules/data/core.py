#!/usr/bin/env python3
"""数据助手核心逻辑

原始数据诊断 → 清洗方案 → Stata 清洗执行 → 数据验证。
LLM 在对话中驱动流程，core.py 负责结构化产出和模板渲染。
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def run(
    raw_data_path: Optional[str] = None,
    y_var: str = "",
    d_var: str = "",
    control_vars: Optional[List[str]] = None,
    project_dir: Optional[Path] = None,
) -> dict:
    """启动数据清洗流程"""
    if project_dir:
        (project_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (project_dir / "data" / "clean").mkdir(parents=True, exist_ok=True)
        (project_dir / "data" / "scripts").mkdir(parents=True, exist_ok=True)
    return {
        "clean_data_path": "",
        "data_quality_report": "",
        "diagnosis_summary": "",
        "variables_found": [],
        "variables_missing": [],
    }


def commit_diagnosis(report: str, summary: str, project_dir: Path) -> str:
    """写入数据诊断报告"""
    now = datetime.now().isoformat(timespec="minutes")
    content = f"""\
# 数据质量诊断

生成时间: {now}

## 诊断摘要

{summary}

## 详细报告

{report}
"""
    report_path = project_dir / "data" / "00_diagnosis_report.md"
    report_path.write_text(content, encoding="utf-8")
    return str(report_path)


def commit_clean_plan(plan: str, project_dir: Path) -> str:
    """写入清洗方案"""
    now = datetime.now().isoformat(timespec="minutes")
    content = f"""\
# 数据清洗方案

生成时间: {now}

{plan}
"""
    plan_path = project_dir / "data" / "01_clean_plan.md"
    plan_path.write_text(content, encoding="utf-8")
    return str(plan_path)


def commit_clean_script(do_content: str, project_dir: Path) -> str:
    """写入 Stata 清洗 do-file"""
    script_path = project_dir / "data" / "scripts" / "01_clean.do"
    script_path.write_text(do_content, encoding="utf-8")
    return str(script_path)


def commit_validation(
    result: dict,
    project_dir: Path,
    y_var: str = "",
    d_var: str = "",
) -> dict:
    """写入清洗后数据验证结果"""
    now = datetime.now().isoformat(timespec="minutes")
    descriptive = result.get("descriptive_table", "")
    obs = result.get("observations", "")
    vars_found = result.get("variables_found", [])

    content = f"""\
# 清洗后数据验证

生成时间: {now}
观测数: {obs}
变量数: {len(vars_found)}

## 变量清单

{vars_found}

## 描述性统计

{descriptive}
"""
    report_path = project_dir / "data" / "02_validation_report.md"
    report_path.write_text(content, encoding="utf-8")

    # 写入最终的清洗后数据路径
    clean_path = project_dir / "data" / "clean" / "panel_clean.dta"

    return {
        "clean_data_path": str(clean_path),
        "data_quality_report": str(report_path),
    }
