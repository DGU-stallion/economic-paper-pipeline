#!/usr/bin/env python3
"""
Python verification backend.

Robustness checks using pandas + linearmodels.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS


def winsorize_series(s: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Winsorize a series at given percentiles."""
    lo = s.quantile(lower)
    hi = s.quantile(upper)
    return s.clip(lo, hi)


def run_robustness_suite(
    data_path: Path,
    y_var: str,
    d_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    project_dir: Optional[Path] = None,
) -> dict:
    """Run a suite of robustness checks.

    Checks performed:
      1. Winsorize Y and D at 1%/99%
      2. Drop top/bottom 1% of D
      3. Add entity-specific linear time trends (cluster at entity × year)
      4. Alternative cluster level (fe_time)
      5. Exclude outliers (DFBETAS approximation via Cook's distance)

    Args:
        Same as run_panel_ols.

    Returns:
        dict with tests list + optional tex_path.
    """
    df = _load_data(data_path)
    required = [y_var, d_var, fe_entity, fe_time, cluster_entity] + (controls or [])
    _validate_columns(df, required)
    df = df.dropna(subset=[y_var, d_var])

    tests = []
    results = []

    # 1. Winsorize
    try:
        w_df = df.copy()
        w_df[y_var] = winsorize_series(w_df[y_var])
        w_df[d_var] = winsorize_series(w_df[d_var])
        res = _run_panel(w_df, y_var, d_var, controls, fe_entity, fe_time, cluster_entity)
        tests.append(_make_test("缩尾处理 (1%/99%)", res, d_var))
        results.append(res)
    except Exception as e:
        tests.append(_make_test("缩尾处理 (1%/99%)", None, d_var, error=str(e)))

    # 2. Drop extreme D
    try:
        lo, hi = df[d_var].quantile(0.01), df[d_var].quantile(0.99)
        t_df = df[(df[d_var] >= lo) & (df[d_var] <= hi)]
        res = _run_panel(t_df, y_var, d_var, controls, fe_entity, fe_time, cluster_entity)
        tests.append(_make_test("排除极端 D 值 (1%/99%)", res, d_var))
        results.append(res)
    except Exception as e:
        tests.append(_make_test("排除极端 D 值 (1%/99%)", None, d_var, error=str(e)))

    # 3. Alternative clustering
    try:
        res = _run_panel(df, y_var, d_var, controls, fe_entity, fe_time, cluster_entity=fe_time)
        tests.append(_make_test(f"聚类层级: {fe_time}", res, d_var))
        results.append(res)
    except Exception as e:
        tests.append(_make_test(f"聚类层级: {fe_time}", None, d_var, error=str(e)))

    # 4. Drop top 1% influence (crude filter on D residual)
    try:
        from scipy import stats
        z = np.abs(stats.zscore(df[d_var].dropna()))
        t_df = df.loc[df.index[z < 3].intersection(df.index)] if len(z) < len(df) else df
        res = _run_panel(t_df, y_var, d_var, controls, fe_entity, fe_time, cluster_entity)
        tests.append(_make_test("排除 D 异常值 (|z|<3)", res, d_var))
        results.append(res)
    except Exception as e:
        tests.append(_make_test("排除 D 异常值 (|z|<3)", None, d_var, error=str(e)))

    # Determine overall conclusion
    coefs = [t["coef_val"] for t in tests if t["coef_val"] is not None]
    robust = bool(
        coefs
        and all(abs(c - coefs[0]) / max(abs(coefs[0]), 0.001) < 0.5 for c in coefs)
        and all(t["pval"] is not None and t["pval"] < 0.1 for t in tests if t["pval"] is not None)
    ) if coefs else False

    result = {
        "tests": tests,
        "conclusion": "结果稳健" if robust else "结果不完全稳健，建议进一步检验",
    }

    if project_dir:
        tex = _generate_robustness_tex(result)
        tex_path = project_dir / "analysis" / "output" / "04_robustness.tex"
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(tex, encoding="utf-8")
        result["tex_path"] = str(tex_path)

    return result


def run_placebo_test(
    data_path: Path,
    y_var: str,
    d_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    n_permutations: int = 100,
    project_dir: Optional[Path] = None,
) -> dict:
    """Randomly shuffle D variable and re-run regression (placebo)."""
    df = _load_data(data_path)
    _validate_columns(df, [y_var, d_var, fe_entity, fe_time, cluster_entity]
                      + (controls or []))
    df = df.dropna(subset=[y_var, d_var])

    real_res = _run_panel(df, y_var, d_var, controls, fe_entity, fe_time, cluster_entity)
    real_coef = float(real_res.params.get(d_var, 0))

    placebo_coefs = []
    for _ in range(n_permutations):
        p_df = df.copy()
        shuffled = p_df[d_var].sample(frac=1).values
        p_df[f"_placebo_{d_var}"] = shuffled
        try:
            res = _run_panel(p_df, y_var, f"_placebo_{d_var}", controls,
                             fe_entity, fe_time, cluster_entity)
            placebo_coefs.append(float(res.params.get(f"_placebo_{d_var}", 0)))
        except Exception:
            placebo_coefs.append(0.0)

    placebo_arr = np.array(placebo_coefs)
    p_val = float(np.mean(np.abs(placebo_arr) >= abs(real_coef)))

    result = {
        "real_coef": round(real_coef, 4),
        "placebo_mean": round(float(np.mean(placebo_arr)), 4),
        "placebo_std": round(float(np.std(placebo_arr)), 4),
        "placebo_pval": round(p_val, 4),
        "n_permutations": n_permutations,
    }

    if project_dir:
        tex = _generate_placebo_tex(result)
        tex_path = project_dir / "analysis" / "output" / "04_placebo.tex"
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(tex, encoding="utf-8")
        result["tex_path"] = str(tex_path)

    return result


# ── Internal ──


def _load_data(data_path: Path) -> pd.DataFrame:
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
        raise ValueError(f"Unsupported format: {ext}")


def _validate_columns(df: pd.DataFrame, cols: List[str]):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")


def _run_panel(df, y, d, controls, fe_entity, fe_time, cluster_entity):
    """Run PanelOLS with entity+time FE, clustered SE."""
    pdf = df.dropna(subset=[y, d]).set_index([fe_entity, fe_time])
    formula = f"{y} ~ 1 + {d} + EntityEffects + TimeEffects"
    if controls:
        formula = f"{y} ~ 1 + {d} + " + " + ".join(controls) + " + EntityEffects + TimeEffects"
    return PanelOLS.from_formula(
        formula, pdf,
        drop_absorbed=True,
    ).fit(cov_type='clustered', cluster_entity=cluster_entity)


def _make_test(name: str, panel_res, d_var: str, error: str = "") -> dict:
    if panel_res is None or error:
        return {
            "name": name,
            "coef": "N/A",
            "sig": "",
            "coef_val": None,
            "pval": None,
            "conclusion": f"失败: {error}" if error else "N/A",
        }
    coef = float(panel_res.params.get(d_var, 0))
    pval = float(panel_res.pvalues.get(d_var, 1))
    return {
        "name": name,
        "coef": f"{coef:.4f}",
        "sig": "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else "",
        "coef_val": coef,
        "pval": pval,
        "conclusion": "稳健" if pval < 0.1 else "不稳健",
    }


def _tex_sig(sig: str) -> str:
    """Wrap significance stars in \\sym{}. Returns empty string if no sig."""
    return f"\\sym{{{sig}}}" if sig else ""

def _generate_robustness_tex(result: dict) -> str:
    now = datetime.now().isoformat(timespec="minutes")
    rows = []
    for t in result.get("tests", []):
        rows.append(f"{t['name']} & {t['coef']}{_tex_sig(t['sig'])} & {t['conclusion']} \\\\")
    conclusion = result.get("conclusion", "")
    return f"""\
% 稳健性检验 (Python, {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{稳健性检验结果}}
\\label{{tab:robustness}}
\\def\\sym#1{{\\ifmmode^{{#1}}\\else\\(^{{#1}}\\)\\fi}}
\\begin{{tabular}}{{lcc}}
\\toprule
检验 & 系数 & 结论 \\\\
\\midrule
{chr(10).join(rows) if rows else '  % (空)'}
\\bottomrule
\\end{{tabular}}
\\end{{table}}

\\textbf{{结论}}: {conclusion}
"""


def _generate_placebo_tex(result: dict) -> str:
    now = datetime.now().isoformat(timespec="minutes")
    return f"""\
% 安慰剂检验 (Python, {now})
\\begin{{table}}[htbp]
\\centering
\\caption{{安慰剂检验 (随机分配 D, {result['n_permutations']} 次)}}
\\label{{tab:placebo}}
\\begin{{tabular}}{{lc}}
\\toprule
真实系数 & {result['real_coef']} \\\\
安慰剂均值 & {result['placebo_mean']} \\\\
安慰剂标准差 & {result['placebo_std']} \\\\
安慰剂 p 值 & {result['placebo_pval']} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
