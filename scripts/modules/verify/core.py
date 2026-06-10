#!/usr/bin/env python3
"""验证助手核心逻辑"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Optional


def run(
    baseline: Optional[dict] = None,
    project_dir: Optional[Path] = None,
) -> dict:
    if project_dir:
        (project_dir / "analysis" / "output").mkdir(parents=True, exist_ok=True)
    return {"robustness_results": {}}


def commit_results(result: dict, project_dir: Path) -> dict:
    now = datetime.now().isoformat(timespec="minutes")
    tests = result.get("tests", [])
    test_entries = "\n".join(f"- {t}" for t in tests) if tests else "(未记录具体检验)"
    content = f"""% 稳健性检验结果 (自动生成 {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{稳健性检验}}
\\label{{tab:robustness}}
\\begin{{tabular}}{{lc}}
\\toprule
检验 & 结论 \\\\
\\midrule
{test_entries}
\\bottomrule
\\end{{tabular}}
\\end{{table}}"""
    tex_path = project_dir / "analysis" / "output" / "04_robustness.tex"
    tex_path.write_text(content, encoding="utf-8")
    return {"robustness_results": result, "robustness_tex": str(tex_path)}
