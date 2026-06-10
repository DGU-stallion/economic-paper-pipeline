#!/usr/bin/env python3
"""论文助手核心逻辑"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Optional


def run(
    context: Optional[dict] = None,
    project_dir: Optional[Path] = None,
) -> dict:
    if project_dir:
        paper_dir = project_dir / "paper"
        paper_dir.mkdir(parents=True, exist_ok=True)
        (paper_dir / "sections").mkdir(exist_ok=True)
    return {"tex_path": ""}


def commit_tex(tex_content: str, project_dir: Path) -> dict:
    tex_path = project_dir / "paper" / "main.tex"
    tex_path.write_text(tex_content, encoding="utf-8")
    return {"tex_path": str(tex_path)}
