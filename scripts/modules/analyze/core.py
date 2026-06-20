#!/usr/bin/env python3
"""分析助手核心逻辑

模型设定 → 基准回归 → 异质性分析 → 中介效应。
Python 后端 (linearmodels) 自动运行回归并生成 .tex 表格。
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional

from scripts.backends import detect
from scripts.backends.python_analysis import (
    run_panel_ols,
    run_heterogeneity,
    run_did,
)


def run(
    y_var: str = "",
    d_var: str = "",
    control_vars: Optional[List[str]] = None,
    identification: str = "",
    clean_data_path: str = "",
    project_dir: Optional[Path] = None,
) -> dict:
    """启动分析流程（自动检测后端，Python 可用则直接运行回归）"""
    if project_dir:
        (project_dir / "analysis" / "output").mkdir(parents=True, exist_ok=True)

    caps = detect()
    backend = "python" if caps["python_analysis"] else "llm"

    result = {"baseline": {}, "heterogeneity": {}, "mediation": {}, "backend": backend}

    if backend == "python" and y_var and d_var and clean_data_path and project_dir:
        result["baseline"] = run_panel_ols(
            data_path=Path(clean_data_path),
            y_var=y_var,
            d_var=d_var,
            controls=control_vars or [],
            project_dir=project_dir,
        )

    return result


def commit_model_spec(spec: str, project_dir: Path) -> str:
    """写入模型设定文档"""
    spec_path = project_dir / "analysis" / "output" / "00_model_spec.md"
    spec_path.write_text(spec, encoding="utf-8")
    return str(spec_path)


# ── Python 后端显式调用入口 ──


def run_baseline_python(
    clean_data_path: str,
    y_var: str,
    d_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    project_dir: Optional[Path] = None,
) -> dict:
    """显式调用 Python 后端跑基准回归 (PanelOLS)。"""
    return run_panel_ols(
        data_path=Path(clean_data_path),
        y_var=y_var,
        d_var=d_var,
        controls=controls,
        fe_entity=fe_entity,
        fe_time=fe_time,
        cluster_entity=cluster_entity,
        project_dir=project_dir,
    )


def run_heterogeneity_python(
    clean_data_path: str,
    y_var: str,
    d_var: str,
    group_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    project_dir: Optional[Path] = None,
) -> dict:
    """显式调用 Python 后端跑异质性分析。"""
    return run_heterogeneity(
        data_path=Path(clean_data_path),
        y_var=y_var,
        d_var=d_var,
        group_var=group_var,
        controls=controls,
        fe_entity=fe_entity,
        fe_time=fe_time,
        cluster_entity=cluster_entity,
        project_dir=project_dir,
    )


def run_did_python(
    clean_data_path: str,
    y_var: str,
    treat_var: str,
    post_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    project_dir: Optional[Path] = None,
) -> dict:
    """显式调用 Python 后端跑 DID (Treat×Post)。"""
    return run_did(
        data_path=Path(clean_data_path),
        y_var=y_var,
        treat_var=treat_var,
        post_var=post_var,
        controls=controls,
        fe_entity=fe_entity,
        fe_time=fe_time,
        cluster_entity=cluster_entity,
        project_dir=project_dir,
    )
