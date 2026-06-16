#!/usr/bin/env python3
"""验证助手核心逻辑

稳健性检验策略设计 → 执行 → 结果汇总。
Python 后端自动运行稳健性检验套件并生成 .tex 表格。
Stata do-file 模板保留为旧版兼容 (docstring 标记 [旧版兼容])。
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from scripts.backends import detect
from scripts.backends.python_verify import (
    run_robustness_suite,
    run_placebo_test,
)


def run(
    y_var: str = "",
    d_var: str = "",
    baseline_results: Optional[dict] = None,
    project_dir: Optional[Path] = None,
    clean_data_path: str = "",
    controls: Optional[List[str]] = None,
) -> dict:
    """启动稳健性检验流程（自动检测后端）"""
    if project_dir:
        (project_dir / "analysis" / "output").mkdir(parents=True, exist_ok=True)

    caps = detect()
    backend = "python" if caps["python_analysis"] else "llm"
    result = {"robustness_results": {}, "tests_performed": [], "conclusion": "",
              "backend": backend}

    if backend == "python" and y_var and d_var and clean_data_path and project_dir:
        result["robustness_results"] = run_robustness_suite(
            data_path=Path(clean_data_path),
            y_var=y_var,
            d_var=d_var,
            controls=controls or [],
            project_dir=project_dir,
        )
        result["tests_performed"] = [
            t["name"] for t in result["robustness_results"].get("tests", [])
        ]
        result["conclusion"] = result["robustness_results"].get("conclusion", "")

    return result


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
    """[旧版兼容] 生成稳健性检验 do-file 模板"""
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
    """[旧版兼容] 写入稳健性检验 .tex 表格（Python 后端自动生成）"""
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


# ── Python 后端显式调用入口 ──


def run_robustness_python(
    clean_data_path: str,
    y_var: str,
    d_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    project_dir: Optional[Path] = None,
) -> dict:
    """显式调用 Python 后端跑稳健性检验套件。"""
    return run_robustness_suite(
        data_path=Path(clean_data_path),
        y_var=y_var,
        d_var=d_var,
        controls=controls,
        fe_entity=fe_entity,
        fe_time=fe_time,
        cluster_entity=cluster_entity,
        project_dir=project_dir,
    )


def run_placebo_python(
    clean_data_path: str,
    y_var: str,
    d_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    n_permutations: int = 100,
    project_dir: Optional[Path] = None,
) -> dict:
    """显式调用 Python 后端跑安慰剂检验。"""
    return run_placebo_test(
        data_path=Path(clean_data_path),
        y_var=y_var,
        d_var=d_var,
        controls=controls,
        fe_entity=fe_entity,
        fe_time=fe_time,
        cluster_entity=cluster_entity,
        n_permutations=n_permutations,
        project_dir=project_dir,
    )
