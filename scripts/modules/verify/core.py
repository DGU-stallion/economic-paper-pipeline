#!/usr/bin/env python3
"""验证助手核心逻辑

稳健性检验策略设计 → 执行 → 结果汇总。
LLM 在对话中驱动，core.py 负责模板渲染和结构化输出。
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def run(
    y_var: str = "",
    d_var: str = "",
    baseline_results: Optional[dict] = None,
    project_dir: Optional[Path] = None,
) -> dict:
    """启动稳健性检验流程"""
    if project_dir:
        (project_dir / "analysis" / "output").mkdir(parents=True, exist_ok=True)
    return {
        "robustness_results": {},
        "tests_performed": [],
        "conclusion": "",
    }


def commit_plan(plan: str, project_dir: Path) -> str:
    """写入稳健性检验方案"""
    plan_path = project_dir / "analysis" / "04_robustness_plan.md"
    plan_path.write_text(plan, encoding="utf-8")
    return str(plan_path)


def commit_robustness_do(
    y_var: str,
    d_var: str,
    controls: List[str],
    project_dir: Path,
) -> str:
    """生成稳健性检验 do-file 模板"""
    controls_str = " ".join(controls) if controls else ""
    now = datetime.now().isoformat(timespec="minutes")
    content = f"""\
* 稳健性检验 (自动生成 {now})
* Y={y_var}, D={d_var}

use "${{DATA}}/clean/panel_clean.dta", clear

* 1. 替换核心变量测度
* replace {d_var}_alt = ...
* reghdfe {y_var} {d_var}_alt {controls_str}, absorb(id year) cluster(id)

* 2. 改变样本窗口
* drop if year < 2015 | year > 2020
* reghdfe {y_var} {d_var} {controls_str}, absorb(id year) cluster(id)

* 3. 安慰剂检验
* 随机分配处理组
* reghdfe {y_var} placebo_{d_var} {controls_str}, absorb(id year) cluster(id)

* 4. 排除极端值
* winsor2 {y_var} {d_var}, cuts(1 99) replace
* reghdfe {y_var} {d_var} {controls_str}, absorb(id year) cluster(id)
"""
    do_path = project_dir / "analysis" / "do-files" / "04_robustness.do"
    do_path.write_text(content, encoding="utf-8")
    return str(do_path)


def commit_results_tex(result: dict, project_dir: Path) -> str:
    """写入稳健性检验 .tex 表格"""
    now = datetime.now().isoformat(timespec="minutes")

    tests = result.get("tests", [])
    rows = []
    for t in tests:
        name = t.get("name", "")
        coef = t.get("coef", "?")
        sig = t.get("sig", "")
        conclusion = t.get("conclusion", "")
        rows.append(f"{name} & {coef}{sig} & {conclusion} \\\\")

    tex = f"""\
% 稳健性检验 (自动生成 {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{{result.get('caption', '稳健性检验')}}}
\\label{{tab:robustness}}
\\begin{{tabular}}{{lcc}}
\\toprule
检验 & 系数 & 结论 \\\\
\\midrule
{chr(10).join(rows) if rows else '  % (待填充)'} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    tex_path = project_dir / "analysis" / "output" / "04_robustness.tex"
    tex_path.write_text(tex, encoding="utf-8")
    return str(tex_path)
