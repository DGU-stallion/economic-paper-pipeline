#!/usr/bin/env python3
"""数据助手核心逻辑"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def run(
    variables: Optional[dict] = None,
    project_dir: Optional[Path] = None,
) -> dict:
    if project_dir:
        (project_dir / "data" / "clean").mkdir(parents=True, exist_ok=True)
    return {"clean_data_path": "", "data_quality_report": ""}


def commit_report(quality_report: str, project_dir: Path):
    now = datetime.now().isoformat(timespec="minutes")
    report_path = project_dir / "data" / "01_quality_report.md"
    report_path.write_text(f"# 数据质量报告\n生成时间: {now}\n\n{quality_report}", encoding="utf-8")
    return {"data_quality_report": str(report_path)}
