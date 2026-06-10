#!/usr/bin/env python3
"""分析助手核心逻辑"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Optional


def run(
    model_spec: Optional[dict] = None,
    project_dir: Optional[Path] = None,
) -> dict:
    if project_dir:
        (project_dir / "analysis" / "output").mkdir(parents=True, exist_ok=True)
    return {"baseline": {}, "heterogeneity": {}, "mediation": {}}


def commit_baseline(result: dict, project_dir: Path) -> dict:
    now = datetime.now().isoformat(timespec="minutes")
    tex_content = f"""% 基准回归结果 (自动生成 {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{基准回归}}
\\label{{tab:baseline}}
\\begin{{tabular}}{{lcc}}
\\toprule
 & (1) & (2) \\\\
\\midrule
{result.get('d_var', 'D')} & {result.get('coef', '?')}{result.get('sig', '')} & {result.get('coef_2', '?')}{result.get('sig_2', '')} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}"""
    tex_path = project_dir / "analysis" / "output" / "02_baseline_regression.tex"
    tex_path.write_text(tex_content, encoding="utf-8")
    return {"baseline": result, "baseline_tex": str(tex_path)}
