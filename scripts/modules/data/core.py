#!/usr/bin/env python3
"""数据助手核心逻辑

原始数据诊断 → 清洗方案 → Python pandas 清洗 → 数据验证。
Python 后端优先；Stata do-file 保留为旧版兼容 (docstring 标记 [旧版兼容])。
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def run(
    raw_data_path: Optional[str] = None,
    y_var: str = "",
    d_var: str = "",
    control_vars: Optional[List[str]] = None,
    project_dir: Optional[Path] = None,
) -> dict:
    """启动数据流程（检测后端，可用则自动做描述性统计）"""
    from scripts.backends import detect
    caps = detect()

    if project_dir:
        (project_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (project_dir / "data" / "clean").mkdir(parents=True, exist_ok=True)
        (project_dir / "data" / "scripts").mkdir(parents=True, exist_ok=True)

    result = {
        "clean_data_path": "",
        "data_quality_report": "",
        "diagnosis_summary": "",
        "variables_found": [],
        "variables_missing": [],
        "backend": "python" if caps["pandas"] else "llm",
    }

    if caps["pandas"] and raw_data_path:
        desc = run_describe_python(raw_data_path)
        result.update(desc)

    return result


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
    """[旧版兼容] 写入 Stata 清洗 do-file（Python 后端使用 run_clean_python）"""
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


# ── Python 后端函数 ──


def run_describe_python(data_path: str) -> dict:
    """用 pandas 读取数据并返回诊断信息。"""
    import pandas as pd

    p = Path(data_path)
    ext = p.suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(p)
    elif ext == ".parquet":
        df = pd.read_parquet(p)
    elif ext == ".dta":
        df = pd.read_stata(p)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(p)
    else:
        return {"diagnosis_summary": f"unsupported format: {ext}"}

    # 基本信息
    n_obs = len(df)
    n_vars = len(df.columns)
    missing = df.isnull().sum().to_dict()
    missing_vars = {k: v for k, v in missing.items() if v > 0}

    # 数值变量描述性统计
    num_cols = df.select_dtypes(include="number").columns.tolist()
    desc_rows = []
    for c in num_cols[:10]:  # limit to 10
        desc_rows.append(
            f"{c}: mean={df[c].mean():.3f}, sd={df[c].std():.3f}, "
            f"min={df[c].min():.3f}, max={df[c].max():.3f}, missing={int(df[c].isnull().sum())}"
        )

    summary = (
        f"Rows: {n_obs}, Cols: {n_vars}. "
        f"Missing: {len(missing_vars)}/{n_vars} vars have nulls. "
        f"Numeric: {len(num_cols)} columns."
    )

    return {
        "diagnosis_summary": summary,
        "variables_found": df.columns.tolist(),
        "variables_missing": list(missing_vars.keys()),
        "descriptive_table": "\n".join(desc_rows),
        "observations": n_obs,
    }


def run_clean_python(
    raw_data_path: str,
    project_dir: Path,
    drop_cols: Optional[List[str]] = None,
    rename_map: Optional[Dict[str, str]] = None,
    drop_na: bool = False,
    output_format: str = "parquet",
) -> dict:
    """通用 pandas 清洗管道。

    Args:
        raw_data_path: 原始数据路径。
        project_dir: 项目目录（clean 数据和 scripts 写至此）。
        drop_cols: 要删除的列。
        rename_map: {旧名: 新名} 重命名字典。
        drop_na: 是否删除含任何缺失的行。
        output_format: "parquet" (默认) 或 "csv"。

    Returns:
        dict with clean_data_path 和 descriptive stats。
    """
    import pandas as pd

    p = Path(raw_data_path)
    ext = p.suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(p)
    elif ext == ".parquet":
        df = pd.read_parquet(p)
    elif ext == ".dta":
        df = pd.read_stata(p)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(p)
    else:
        raise ValueError(f"unsupported: {ext}")

    # 清洗
    if drop_cols:
        df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    if rename_map:
        df = df.rename(columns=rename_map)

    if drop_na:
        before = len(df)
        df = df.dropna()
        print(f"drop_na: {before} -> {len(df)} rows")

    # 清洗脚本保存
    script_path = project_dir / "data" / "scripts" / "01_clean.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        f"# Auto-generated clean script\n# {datetime.now().isoformat(timespec='minutes')}\n"
        f"# input: {raw_data_path}\n"
        f"# drops: {drop_cols or []}\n"
        f"# rename: {rename_map or {}}\n",
        encoding="utf-8",
    )

    # 保存清洗后数据
    clean_dir = project_dir / "data" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    if output_format == "parquet":
        clean_path = clean_dir / "panel_clean.parquet"
        df.to_parquet(clean_path, index=False)
    else:
        clean_path = clean_dir / "panel_clean.csv"
        df.to_csv(clean_path, index=False)

    return {
        "clean_data_path": str(clean_path),
        "observations": len(df),
        "variables_found": df.columns.tolist(),
    }
