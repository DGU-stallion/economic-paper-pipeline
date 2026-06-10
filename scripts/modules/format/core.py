#!/usr/bin/env python3
"""格式助手核心逻辑：LaTeX 编译、AI 痕迹检测"""
from __future__ import annotations
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


def run(
    tex_path: Optional[str] = None,
    project_dir: Optional[Path] = None,
) -> dict:
    return {"pdf_path": ""}


def compile_tex(tex_path: Path, project_dir: Path) -> dict:
    """执行 xelatex → biber → xelatex → xelatex 编译管线"""
    log_file = project_dir / "paper" / "compile.log"
    pdf_path = project_dir / "paper" / "main.pdf"

    # 删除旧 PDF 避免锁定
    if pdf_path.exists():
        pdf_path.unlink()

    steps = [
        (["xelatex", "-interaction=nonstopmode", tex_path.name], "xelatex 第 1 次"),
        (["biber", tex_path.stem], "biber"),
        (["xelatex", "-interaction=nonstopmode", tex_path.name], "xelatex 第 2 次"),
        (["xelatex", "-interaction=nonstopmode", tex_path.name], "xelatex 第 3 次"),
    ]

    success = True
    for cmd, desc in steps:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                result = subprocess.run(
                    cmd, cwd=str(tex_path.parent),
                    stdout=f, stderr=subprocess.STDOUT,
                    timeout=120,
                )
            if result.returncode != 0:
                success = False
                break
        except subprocess.TimeoutExpired:
            success = False
            break

    return {
        "pdf_path": str(pdf_path) if success else "",
        "compile_success": success,
        "log_path": str(log_file),
    }


def detect_texlive() -> bool:
    """检测 TeX Live 是否安装"""
    try:
        result = subprocess.run(
            ["xelatex", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
