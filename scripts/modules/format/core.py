#!/usr/bin/env python3
"""格式助手核心逻辑：LaTeX 编译管线、错误解析、AI 痕迹检测。"""

from __future__ import annotations
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def run(
    tex_path: Optional[str] = None,
    project_dir: Optional[Path] = None,
) -> dict:
    """启动格式处理"""
    return {"pdf_path": ""}


# ── 编译管线 ──

def compile_tex(tex_path: Path, project_dir: Path) -> dict:
    """执行 xelatex → biber → xelatex → xelatex 编译管线"""
    log_file = project_dir / "paper" / "compile.log"
    pdf_path = project_dir / "paper" / "main.pdf"

    if pdf_path.exists():
        pdf_path.unlink()

    steps = [
        (["xelatex", "-interaction=nonstopmode", tex_path.name], "xelatex 第 1 次"),
        (["biber", tex_path.stem], "biber"),
        (["xelatex", "-interaction=nonstopmode", tex_path.name], "xelatex 第 2 次"),
        (["xelatex", "-interaction=nonstopmode", tex_path.name], "xelatex 第 3 次"),
    ]

    step_results = []
    for cmd, desc in steps:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                result = subprocess.run(
                    cmd, cwd=str(tex_path.parent),
                    stdout=f, stderr=subprocess.STDOUT,
                    timeout=120,
                )
            ok = result.returncode == 0
            step_results.append({"step": desc, "ok": ok})
            if not ok:
                break
        except subprocess.TimeoutExpired:
            step_results.append({"step": desc, "ok": False, "error": "超时"})
            break

    success = all(s["ok"] for s in step_results)

    errors = parse_compile_errors(log_file) if not success else []

    return {
        "pdf_path": str(pdf_path) if success else "",
        "compile_success": success,
        "log_path": str(log_file),
        "steps": step_results,
        "errors": errors,
    }


def parse_compile_errors(log_path: Path) -> List[dict]:
    """从编译日志中提取错误信息"""
    if not log_path.exists():
        return []
    content = log_path.read_text(encoding="utf-8", errors="replace")
    errors = []
    for m in re.finditer(r'^! (.*?)$', content, re.MULTILINE):
        errors.append({"message": m.group(1).strip()})
        # 上下文 3 行
        lines = content.split("\n")
        pos = lines.index(m.group(0)) if m.group(0) in lines else -1
        if pos >= 0:
            context = lines[pos + 1 : pos + 4]
            for c in context:
                if c.strip():
                    errors[-1].setdefault("context", []).append(c.strip())
    return errors[:20]


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


# ── 编译辅助 ──

def clean_aux_files(project_dir: Path):
    """清理 LaTeX 编译辅助文件"""
    paper_dir = project_dir / "paper"
    aux_extensions = [
        ".aux", ".bbl", ".bcf", ".blg", ".log", ".out",
        ".toc", ".lof", ".lot", ".run.xml", ".synctex.gz",
        ".fdb_latexmk", ".fls",
    ]
    count = 0
    for ext in aux_extensions:
        for f in paper_dir.glob(f"*{ext}"):
            try:
                f.unlink()
                count += 1
            except OSError:
                pass
    return count


# ── Humanizer ──

def run_humanizer(project_dir: Path) -> dict:
    """运行 AI 痕迹检测，返回检测结果"""
    sections_dir = project_dir / "paper" / "sections"
    if not sections_dir.exists():
        return {"ok": False, "error": "sections 目录不存在"}

    issues = []
    for tex_file in sorted(sections_dir.glob("*.tex")):
        content = tex_file.read_text(encoding="utf-8")
        file_issues = []

        # 1. 连续短破折号检测
        long_dash = re.findall(r'-{3,}', content)
        if long_dash:
            file_issues.append(f"连续短破折号: {len(long_dash)} 处")

        # 2. 规则三句式检测
        sentences = re.findall(r'[^。]+。', content)
        pattern_count = 0
        for i in range(len(sentences) - 2):
            if all(len(s.strip()) < 80 for s in sentences[i:i+3]):
                pattern_count += 1
        if pattern_count > 3:
            file_issues.append(f"可能的三句式模式: {pattern_count} 处相邻短句")

        # 3. 重复开头词检测
        starts = [s.strip()[:6] for s in sentences if s.strip()]
        from collections import Counter
        common = Counter(starts).most_common(3)
        for word, count in common:
            if count > 2 and len(word) > 1:
                file_issues.append(f"重复开头 '{word}': {count} 次")

        if file_issues:
            issues.append({"file": tex_file.name, "issues": file_issues})

    return {
        "ok": True,
        "total_files": len(list(sections_dir.glob("*.tex"))),
        "files_with_issues": len(issues),
        "issues": issues,
    }
