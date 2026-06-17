#!/usr/bin/env python3
"""
Python analysis backend.

Runs panel regressions via linearmodels, generates LaTeX tables.
Zero Stata dependency. Works on any OS with Python.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS
from linearmodels.panel.results import PanelResults


# ── Public API ──


def run_panel_ols(
    data_path: Path,
    y_var: str,
    d_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    project_dir: Optional[Path] = None,
) -> dict:
    """Run PanelOLS with entity+time FE, clustered SE.

    Supports two models:
      M1: y ~ D (baseline)
      M2: y ~ D + controls

    Returns structured results dict + writes .tex table.

    Args:
        data_path: Path to CSV/Parquet/Stata file.
        y_var: Dependent variable name.
        d_var: Core explanatory variable.
        controls: Control variable names.
        fe_entity: Entity FE column name.
        fe_time: Time FE column name.
        cluster_entity: Cluster SE column name.
        project_dir: If set, write table file to analysis/output/.

    Returns:
        dict with keys: variables, r_squared, n, caption, tex_path, models.
    """
    df = _load_data(data_path)
    _validate_columns(df, [y_var, d_var, fe_entity, fe_time, cluster_entity]
                      + (controls or []))

    # Set panel index (dropna first to avoid index-column conflict)
    df = df.dropna(subset=[y_var, d_var]).set_index([fe_entity, fe_time])

    # De-meaning formula (EntityEffects + TimeEffects for FE)
    base_formula = f"{y_var} ~ 1 + {d_var} + EntityEffects + TimeEffects"
    full_formula = base_formula
    if controls:
        full_formula = f"{y_var} ~ 1 + {d_var} + " + " + ".join(controls) + " + EntityEffects + TimeEffects"

    # M1: baseline
    m1 = PanelOLS.from_formula(
        base_formula, df,
        drop_absorbed=True,
    ).fit(cov_type='clustered', cluster_entity=cluster_entity)

    # M2: with controls
    m2 = None
    if controls:
        m2 = PanelOLS.from_formula(
            full_formula, df,
            drop_absorbed=True,
        ).fit(cov_type='clustered', cluster_entity=cluster_entity)

    # Build structured results
    variables = _extract_vars(m1, m2, d_var, controls)
    models = {
        "m1": _model_to_dict(m1),
    }
    if m2 is not None:
        models["m2"] = _model_to_dict(m2)

    result = {
        "variables": variables,
        "r_squared": round(float(m1.rsquared), 4),
        "n": int(m1.nobs),
        "caption": "基准回归结果",
        "models": models,
    }

    # Write .tex
    if project_dir:
        tex = _generate_baseline_tex(result)
        tex_path = project_dir / "analysis" / "output" / "02_baseline_regression.tex"
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(tex, encoding="utf-8")
        result["tex_path"] = str(tex_path)

    return result


def run_heterogeneity(
    data_path: Path,
    y_var: str,
    d_var: str,
    group_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    project_dir: Optional[Path] = None,
) -> dict:
    """Run PanelOLS per group for heterogeneity analysis.

    Args:
        data_path: Path to data file.
        group_var: Categorical column to split by.
        others: Same as run_panel_ols.

    Returns:
        dict with groups (list of per-group results) and optional tex_path.
    """
    df = _load_data(data_path)
    _validate_columns(df, [y_var, d_var, group_var, fe_entity, fe_time, cluster_entity]
                      + (controls or []))

    groups = []
    for group_name, group_df in df.groupby(group_var):
        if len(group_df) < 10:
            continue
        group_df = group_df.dropna(
            subset=[y_var, d_var]).set_index([fe_entity, fe_time])
        formula = f"{y_var} ~ 1 + {d_var} + EntityEffects + TimeEffects"
        if controls:
            formula = f"{y_var} ~ 1 + {d_var} + " + " + ".join(controls) + " + EntityEffects + TimeEffects"

        try:
            mod = PanelOLS.from_formula(
                formula, group_df,
                drop_absorbed=True,
            ).fit(cov_type='clustered', cluster_entity=cluster_entity)

            coef = float(mod.params.get(d_var, 0))
            se = float(mod.std_errors.get(d_var, 0))
            pval = float(mod.pvalues.get(d_var, 1))
            groups.append({
                "name": str(group_name),
                "coef": f"{coef:.4f}",
                "se": f"{se:.4f}",
                "sig": _sig_stars(pval),
                "pval": pval,
                "n": int(mod.nobs),
            })
        except Exception:
            groups.append({
                "name": str(group_name),
                "coef": "N/A",
                "se": "",
                "sig": "",
                "pval": 1.0,
                "n": 0,
            })

    result = {"groups": groups, "caption": "异质性分析"}

    if project_dir:
        tex = _generate_heterogeneity_tex(result)
        tex_path = project_dir / "analysis" / "output" / "03_heterogeneity.tex"
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(tex, encoding="utf-8")
        result["tex_path"] = str(tex_path)

    return result


def run_did(
    data_path: Path,
    y_var: str,
    treat_var: str,
    post_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    project_dir: Optional[Path] = None,
) -> dict:
    """Run DID (interaction of treat×post) using PanelOLS.

    Formula: y ~ 1 + treat:post + treat + post + controls
    Entity FE + Time FE + clustered SE.

    Returns structured results dict.
    """
    df = _load_data(data_path)
    _validate_columns(df, [y_var, treat_var, post_var, fe_entity, fe_time, cluster_entity]
                      + (controls or []))

    df = df.dropna(subset=[y_var, treat_var, post_var])

    # Create interaction term before set_index (post_var may be fe_time)
    df["_did_interact"] = df[treat_var] * df[post_var]
    df = df.set_index([fe_entity, fe_time])

    # DID formula: interaction is identified; treat/post absorbed by FEs
    formula = f"{y_var} ~ 1 + _did_interact + EntityEffects + TimeEffects"
    if controls:
        formula = f"{y_var} ~ 1 + _did_interact + " + " + ".join(controls) + " + EntityEffects + TimeEffects"

    mod = PanelOLS.from_formula(
        formula, df,
        drop_absorbed=True,
    ).fit(cov_type='clustered', cluster_entity=cluster_entity)

    coef = float(mod.params.get("_did_interact", 0))
    se = float(mod.std_errors.get("_did_interact", 0))
    pval = float(mod.pvalues.get("_did_interact", 1))

    result = {
        "did_coef": f"{coef:.4f}",
        "did_se": f"{se:.4f}",
        "did_sig": _sig_stars(pval),
        "did_pval": pval,
        "r_squared": round(float(mod.rsquared), 4),
        "n": int(mod.nobs),
    }

    if project_dir:
        tex = _generate_did_tex(result)
        tex_path = project_dir / "analysis" / "output" / "02_did.tex"
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(tex, encoding="utf-8")
        result["tex_path"] = str(tex_path)

    return result


# ── Internal helpers ──


def _load_data(data_path: Path) -> pd.DataFrame:
    """Load CSV / Parquet / Stata / Excel into DataFrame."""
    ext = Path(data_path).suffix.lower()
    if ext == ".csv":
        return pd.read_csv(data_path)
    elif ext == ".parquet":
        return pd.read_parquet(data_path)
    elif ext == ".dta":
        return pd.read_stata(data_path)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(data_path)
    else:
        raise ValueError(f"Unsupported data format: {ext}")


def _validate_columns(df: pd.DataFrame, columns: List[str]):
    """Raise ValueError if any column is missing."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Columns not found in data: {missing}")


def _extract_vars(
    m1: PanelResults,
    m2: Optional[PanelResults],
    d_var: str,
    controls: Optional[List[str]],
) -> List[dict]:
    """Build variable rows for side-by-side model LaTeX table.

    Each entry has keys: name, m1 (dict or None), m2 (dict or None).
    Per-model dict: {coef, se, sig}.
    """
    variables = []
    all_names = [d_var] + (controls or [])

    for name in all_names:
        entry: dict = {"name": name, "m1": None, "m2": None}
        for model_key, mod in [("m1", m1), ("m2", m2)]:
            if mod is not None and name in mod.params:
                entry[model_key] = {
                    "coef": f"{float(mod.params[name]):.4f}",
                    "se": f"{float(mod.std_errors[name]):.4f}",
                    "sig": _sig_stars(float(mod.pvalues[name])),
                }
        variables.append(entry)

    return variables


def _model_to_dict(mod: PanelResults) -> dict:
    """Convert PanelResults to serializable dict."""
    return {
        "params": {k: float(v) for k, v in mod.params.items()},
        "se": {k: float(v) for k, v in mod.std_errors.items()},
        "pvalues": {k: float(v) for k, v in mod.pvalues.items()},
        "r_squared": float(mod.rsquared),
        "n": int(mod.nobs),
    }


def _sig_stars(pval: float) -> str:
    if pval < 0.01:
        return "***"
    elif pval < 0.05:
        return "**"
    elif pval < 0.1:
        return "*"
    return ""

def _tex_sig(sig: str) -> str:
    """Wrap significance stars in \\sym{}. Returns empty string if no sig."""
    return f"\\sym{{{sig}}}" if sig else ""


def _tex_name(name: str) -> str:
    """Sanitize variable names for LaTeX (escape underscores)."""
    return name.replace("_", "\\_")

def _generate_baseline_tex(result: dict) -> str:
    """Generate LaTeX table from baseline results (side-by-side models)."""
    now = datetime.now().isoformat(timespec="minutes")
    # Determine number of models
    model_keys = [k for k in ("m1", "m2") if result.get("models", {}).get(k)]
    n_models = len(model_keys)
    col_spec = "l" + "c" * n_models
    col_headers = " & " + " & ".join(f"({i+1})" for i in range(n_models))

    rows = []
    for v in result.get("variables", []):
        name = v.get("name", "")
        # Coefficient row
        coefs = []
        for mk in model_keys:
            entry = v.get(mk)
            if entry:
                coefs.append(f"{entry['coef']}{_tex_sig(entry['sig'])}")
            else:
                coefs.append("")
        rows.append(f"{_tex_name(name)} & " + " & ".join(coefs) + " \\\\")
        # SE row (skip if all blank)
        ses = []
        for mk in model_keys:
            entry = v.get(mk)
            if entry and entry.get("se"):
                ses.append(f"({entry['se']})")
            else:
                ses.append("")
        if any(ses):
            rows.append("  & " + " & ".join(ses) + " \\\\")

    return f"""\
% 基准回归结果 (Python PanelOLS, {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{{result.get('caption', '基准回归结果')}}}
\\label{{tab:main}}
\\def\\sym#1{{\\ifmmode^{{#1}}\\else\\(^{{#1}}\\)\\fi}}
\\begin{{tabular}}{{{col_spec}}}
\\toprule
{col_headers} \\\\
\\midrule
{chr(10).join(rows) if rows else '  % (待填充)'}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""


def _generate_heterogeneity_tex(result: dict) -> str:
    """Generate LaTeX table from heterogeneity results."""
    now = datetime.now().isoformat(timespec="minutes")
    rows = []
    for g in result.get("groups", []):
        name = g.get("name", "")
        coef = g.get("coef", "?")
        sig = g.get("sig", "")
        n = g.get("n", "")
        rows.append(f"{_tex_name(name)} & {coef}{_tex_sig(sig)} & {n} \\\\")
        se = g.get("se", "")
        if se:
            rows.append(f"  & ({se}) & \\\\")

    return f"""\
% 异质性分析 (Python PanelOLS, {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{{result.get('caption', '异质性分析')}}}
\\label{{tab:heterogeneity}}
\\def\\sym#1{{\\ifmmode^{{#1}}\\else\\(^{{#1}}\\)\\fi}}
\\begin{{tabular}}{{lcc}}
\\toprule
 分组 & 系数 & 样本量 \\\\
\\midrule
{chr(10).join(rows) if rows else '  % (待填充)'}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""


def _generate_did_tex(result: dict) -> str:
    """Generate LaTeX table from DID results."""
    now = datetime.now().isoformat(timespec="minutes")
    return f"""\
% DID 双重差分结果 (Python PanelOLS, {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{双重差分 (DID) 结果}}
\\label{{tab:did}}
\\def\\sym#1{{\\ifmmode^{{#1}}\\else\\(^{{#1}}\\)\\fi}}
\\begin{{tabular}}{{lc}}
\\toprule
DID (Treat×Post) & {result.get('did_coef', '?')}{_tex_sig(result.get('did_sig', ''))} \\\\
  & ({result.get('did_se', '?')}) \\\\
R² & {result.get('r_squared', '?')} \\\\
N & {result.get('n', '?')} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
