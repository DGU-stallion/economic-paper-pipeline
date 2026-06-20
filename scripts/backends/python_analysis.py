#!/usr/bin/env python3
"""
Python analysis backend.

Runs panel regressions via linearmodels or pyfixest, generates LaTeX tables.
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

# ── Optional pyfixest backend (faster for large panels) ──
HAS_PYFIXEST = False
try:
    import pyfixest as pf
    HAS_PYFIXEST = True
except ImportError:
    pass


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
    backend: str = "auto",
) -> dict:
    """Run panel FE regression with clustered SE.

    Supports two backends:
      - "linearmodels": PanelOLS (default, always available)
      - "pyfixest": feols (faster for large panels, pip install pyfixest)
      - "auto": try pyfixest if N*T > 10000, fallback linearmodels

    Returns dict with keys: variables, r_squared, n, caption, tex_path, models, backend_used.
    """
    df = _load_data(data_path)
    _validate_columns(df, [y_var, d_var, fe_entity, fe_time, cluster_entity]
                      + (controls or []))
    df = df.dropna(subset=[y_var, d_var]).set_index([fe_entity, fe_time])

    # Select backend
    use_pyfixest = False
    if backend == "pyfixest" and HAS_PYFIXEST:
        use_pyfixest = True
    elif backend == "auto" and HAS_PYFIXEST and len(df) > 10000:
        use_pyfixest = True

    if use_pyfixest:
        m1, m2 = _run_panel_ols_pyfixest(df, y_var, d_var, controls, fe_entity, fe_time, cluster_entity)
        backend_used = "pyfixest"
    else:
        m1, m2 = _run_panel_ols_linearmodels(df, y_var, d_var, controls, fe_entity, fe_time, cluster_entity)
        backend_used = "linearmodels"

    variables = _extract_vars(m1, m2, d_var, controls)
    models = {"m1": _model_to_dict(m1)}
    if m2 is not None:
        models["m2"] = _model_to_dict(m2)

    result = {
        "variables": variables,
        "r_squared": round(float(m1.rsquared), 4),
        "n": int(m1.nobs),
        "caption": "基准回归结果",
        "models": models,
        "backend_used": backend_used,
    }

    if project_dir:
        tex = _generate_baseline_tex(result)
        tex_path = project_dir / "analysis" / "output" / "02_baseline_regression.tex"
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(tex, encoding="utf-8")
        result["tex_path"] = str(tex_path)

    return result


# ── Backend wrappers ──


def _run_panel_ols_linearmodels(df, y_var, d_var, controls, fe_entity, fe_time, cluster_entity):
    """Run PanelOLS via linearmodels (default)."""
    base_formula = f"{y_var} ~ 1 + {d_var} + EntityEffects + TimeEffects"
    full_formula = base_formula
    if controls:
        full_formula = f"{y_var} ~ 1 + {d_var} + " + " + ".join(controls) + " + EntityEffects + TimeEffects"

    m1 = PanelOLS.from_formula(base_formula, df, drop_absorbed=True).fit(
        cov_type='clustered', cluster_entity=cluster_entity)
    m2 = PanelOLS.from_formula(full_formula, df, drop_absorbed=True).fit(
        cov_type='clustered', cluster_entity=cluster_entity) if controls else None
    return m1, m2


def _run_panel_ols_pyfixest(df, y_var, d_var, controls, fe_entity, fe_time, cluster_entity):
    """Run fixed effects via pyfixest (faster for large panels)."""
    base_fml = f"{y_var} ~ {d_var} | {fe_entity} + {fe_time}"
    full_fml = base_fml
    if controls:
        full_fml = f"{y_var} ~ {d_var} + " + " + ".join(controls) + f" | {fe_entity} + {fe_time}"

    m1 = pf.feols(base_fml, data=df.reset_index(), vcov={"CRV1": cluster_entity})
    m2 = pf.feols(full_fml, data=df.reset_index(), vcov={"CRV1": cluster_entity}) if controls else None
    return m1, m2


# ── DID ──


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


# ── Heterogeneity ──


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
    """Build variable rows for side-by-side model LaTeX table."""
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
    return f"\\sym{{{sig}}}" if sig else ""


def _tex_name(name: str) -> str:
    return name.replace("_", "\\_")


def _generate_baseline_tex(result: dict) -> str:
    """Generate publication-quality baseline table with model stats."""
    now = datetime.now().isoformat(timespec="minutes")
    model_keys = [k for k in ("m1", "m2") if result.get("models", {}).get(k)]
    n_models = len(model_keys)
    col_spec = "l" + "c" * n_models
    col_headers = " & " + " & ".join(f"({i+1})" for i in range(n_models))

    rows = []
    for v in result.get("variables", []):
        name = v.get("name", "")
        coefs = []
        ses = []
        for mk in model_keys:
            entry = v.get(mk)
            if entry:
                coefs.append(f"{entry['coef']}{_tex_sig(entry['sig'])}")
                ses.append(f"({entry['se']})" if entry.get("se") else "")
            else:
                coefs.append("")
                ses.append("")
        rows.append(f"{_tex_name(name)} & " + " & ".join(coefs) + " \\\\")
        if any(ses):
            rows.append("  & " + " & ".join(ses) + " \\\\")

    rows.append(r"\midrule")
    r2_parts = ["R²"]
    n_parts = ["样本量"]
    for mk in model_keys:
        m = result["models"][mk]
        r2_parts.append(f"{m['r_squared']:.4f}")
        n_parts.append(str(m["n"]))
    rows.append(" & ".join(r2_parts) + " \\\\")
    rows.append(" & ".join(n_parts) + " \\\\")

    ncols = n_models + 1
    fn1 = r"\multicolumn{" + str(ncols) + r"}{l}{\footnotesize 括号内为聚类稳健标准误（省份层面）。}\\"
    fn2 = r"\multicolumn{" + str(ncols) + r"}{l}{\footnotesize * $p<0.10$, ** $p<0.05$, *** $p<0.01$}\\"

    return (
        "% 基准回归结果 (Python, " + now + ")\n"
        + r"\begin{table}[htbp]" + "\n"
        + r"\centering" + "\n"
        + r"\caption{" + result.get("caption", "基准回归结果") + "}" + "\n"
        + r"\label{tab:main}" + "\n"
        + r"\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}" + "\n"
        + r"\begin{tabular}{" + col_spec + "}" + "\n"
        + r"\toprule" + "\n"
        + col_headers + r" \\" + "\n"
        + r"\midrule" + "\n"
        + ("\n".join(rows) if rows else "  % (待填充)") + "\n"
        + r"\bottomrule" + "\n"
        + fn1 + "\n"
        + fn2 + "\n"
        + r"\end{tabular}" + "\n"
        + r"\end{table}"
    )


def _generate_heterogeneity_tex(result: dict) -> str:
    """Generate publication-quality heterogeneity table."""
    now = datetime.now().isoformat(timespec="minutes")
    groups = result.get("groups", [])
    n_groups = len(groups)
    col_spec = "l" + "c" * n_groups if n_groups > 0 else "lc"

    if n_groups <= 1:
        rows = []
        for g in groups:
            name = g.get("name", "")
            coef = g.get("coef", "?")
            sig = g.get("sig", "")
            n = g.get("n", "")
            rows.append(f"{_tex_name(name)} & {coef}{_tex_sig(sig)} & {n} \\\\")
            se = g.get("se", "")
            if se:
                rows.append(f"  & ({se}) & \\\\")
        return (
            "% 异质性分析 (Python, " + now + ")\n"
            + r"\begin{table}[htbp]" + "\n"
            + r"\centering" + "\n"
            + r"\caption{" + result.get("caption", "异质性分析") + "}" + "\n"
            + r"\label{tab:heterogeneity}" + "\n"
            + r"\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}" + "\n"
            + r"\begin{tabular}{lcc}" + "\n"
            + r"\toprule" + "\n"
            + r" 分组 & 系数 & 样本量 \\" + "\n"
            + r"\midrule" + "\n"
            + ("\n".join(rows) if rows else "  % (待填充)") + "\n"
            + r"\bottomrule" + "\n"
            + r"\multicolumn{3}{l}{\footnotesize 括号内为聚类稳健标准误。}\\" + "\n"
            + r"\multicolumn{3}{l}{\footnotesize * $p<0.10$, ** $p<0.05$, *** $p<0.01$}\\" + "\n"
            + r"\end{tabular}" + "\n"
            + r"\end{table}"
        )

    header_parts = [""]
    for g in groups:
        header_parts.append(f"\\multicolumn{{1}}{{c}}{{{g['name']}}}")
    col_header = " & ".join(header_parts)

    coef_parts = [_tex_name(result.get('coef_label', '系数'))]
    se_parts = ["标准误"]
    n_parts = ["样本量"]
    for g in groups:
        coef_parts.append(f"{g['coef']}{_tex_sig(g['sig'])}")
        se_parts.append(f"({g['se']})" if g.get("se") else "")
        n_parts.append(str(g["n"]))
    rows = [
        " & ".join(coef_parts) + " \\\\",
        " & ".join(se_parts) + " \\\\",
        " & ".join(n_parts) + " \\\\",
    ]

    fn1 = r"\multicolumn{" + str(n_groups + 1) + r"}{l}{\footnotesize 括号内为聚类稳健标准误。}\\"
    fn2 = r"\multicolumn{" + str(n_groups + 1) + r"}{l}{\footnotesize * $p<0.10$, ** $p<0.05$, *** $p<0.01$}\\"
    return (
        "% 异质性分析 (Python, " + now + ")\n"
        + r"\begin{table}[htbp]" + "\n"
        + r"\centering" + "\n"
        + r"\caption{" + result.get("caption", "异质性分析") + "}" + "\n"
        + r"\label{tab:heterogeneity}" + "\n"
        + r"\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}" + "\n"
        + r"\begin{tabular}{" + col_spec + "}" + "\n"
        + r"\toprule" + "\n"
        + col_header + r" \\" + "\n"
        + r"\midrule" + "\n"
        + "\n".join(rows) + "\n"
        + r"\bottomrule" + "\n"
        + fn1 + "\n"
        + fn2 + "\n"
        + r"\end{tabular}" + "\n"
        + r"\end{table}"
    )


def _generate_did_tex(result: dict) -> str:
    """Generate LaTeX table from DID results."""
    now = datetime.now().isoformat(timespec="minutes")
    return f"""\
% DID 双重差分结果 (Python, {now})
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
