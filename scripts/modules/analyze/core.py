#!/usr/bin/env python3
"""分析助手核心逻辑

模型设定 → 基准回归 → 异质性分析 → 中介效应。
LLM 在对话中驱动，core.py 负责 do-file 模板渲染和结果表格输出。
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def run(
    y_var: str = "",
    d_var: str = "",
    control_vars: Optional[List[str]] = None,
    identification: str = "",
    clean_data_path: str = "",
    project_dir: Optional[Path] = None,
) -> dict:
    """启动分析流程"""
    if project_dir:
        (project_dir / "analysis" / "do-files").mkdir(parents=True, exist_ok=True)
        (project_dir / "analysis" / "output").mkdir(parents=True, exist_ok=True)
    return {
        "baseline": {},
        "heterogeneity": {},
        "mediation": {},
    }


def commit_model_spec(spec: str, project_dir: Path) -> str:
    """写入模型设定文档"""
    spec_path = project_dir / "analysis" / "do-files" / "00_model_spec.md"
    spec_path.write_text(spec, encoding="utf-8")
    return str(spec_path)


def commit_baseline_do(
    y_var: str,
    d_var: str,
    controls: List[str],
    fe: str,
    cluster: str,
    project_dir: Path,
) -> str:
    """生成基准回归 do-file"""
    controls_str = " ".join(controls) if controls else ""
    content = f"""\
* 基准回归 (自动生成 {datetime.now().isoformat(timespec='minutes')})
* Y={y_var}, D={d_var}, FE={fe}, Cluster={cluster}

use "${{DATA}}/clean/panel_clean.dta", clear

* M1: 仅核心变量
reghdfe {y_var} {d_var}, absorb({fe}) cluster({cluster})
estadd local FE "Yes"
est store m1

* M2: 加控制变量
reghdfe {y_var} {d_var} {controls_str}, absorb({fe}) cluster({cluster})
estadd local FE "Yes"
est store m2

* 输出表格
esttab m1 m2 using "${{OUTPUT}}/02_baseline_regression.tex", ///
  replace label b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) ///
  scalars("FE Fixed Effects") ///
  title("基准回归结果") ///
  nomtitles nogaps compress
"""
    do_path = project_dir / "analysis" / "do-files" / "01_baseline.do"
    do_path.write_text(content, encoding="utf-8")
    return str(do_path)


def commit_baseline_tex(result: dict, project_dir: Path) -> str:
    """写入基准回归 .tex 表格（LLM 解析 Stata 输出后生成）"""
    now = datetime.now().isoformat(timespec="minutes")

    rows = []
    variables = result.get("variables", [])
    for v in variables:
        coef = v.get("coef", "?")
        se = v.get("se", "")
        sig = v.get("sig", "")
        name = v.get("name", "")
        rows.append(f"{name} & {coef}{sig} \\\\")
        if se:
            rows.append(f"  & ({se}) \\\\")

    tex = f"""\
% 基准回归结果 (自动生成 {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{{result.get('caption', '基准回归结果')}}}
\\label{{tab:baseline}}
\\begin{{tabular}}{{lcc}}
\\toprule
 & (1) & (2) \\\\
\\midrule
{chr(10).join(rows) if rows else '  % (待填充)'} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    tex_path = project_dir / "analysis" / "output" / "02_baseline_regression.tex"
    tex_path.write_text(tex, encoding="utf-8")
    return str(tex_path)


def commit_heterogeneity_tex(result: dict, project_dir: Path) -> str:
    """写入异质性分析 .tex 表格"""
    now = datetime.now().isoformat(timespec="minutes")

    groups = result.get("groups", [])
    group_rows = []
    for g in groups:
        name = g.get("name", "")
        coef = g.get("coef", "?")
        sig = g.get("sig", "")
        n = g.get("n", "")
        group_rows.append(f"{name} & {coef}{sig} & {n} \\\\")

    tex = f"""\
% 异质性分析 (自动生成 {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{{result.get('caption', '异质性分析')}}}
\\label{{tab:heterogeneity}}
\\begin{{tabular}}{{lcc}}
\\toprule
分组 & 系数 & 样本量 \\\\
\\midrule
{chr(10).join(group_rows) if group_rows else '  % (待填充)'} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    tex_path = project_dir / "analysis" / "output" / "03_heterogeneity.tex"
    tex_path.write_text(tex, encoding="utf-8")
    return str(tex_path)
