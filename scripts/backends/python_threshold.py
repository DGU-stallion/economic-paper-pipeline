# Python backend — Hansen (1999) panel threshold regression.
# Grid search over threshold variable, PanelOLS per candidate, RSS minimization.
# Produces .tex table matching Stata output.
#
# Optional external: thrreg (github.com/mlkremer/thrreg) — R package.
# If installed via rpy2, can delegate to thrreg::thr_reg() for verified Hansen 2000.
# Benefits: more mature implementation, likelihood ratio test for threshold significance.
# Current: pure Python grid search (works without R).

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np
from linearmodels.panel import PanelOLS


# ── Optional thrreg bridge (R package) ──
HAS_THRREG = False
try:
    import rpy2.robjects as ro
    from rpy2.robjects.packages import importr
    importr("thrreg")
    HAS_THRREG = True
except (ImportError, Exception):
    pass


# ── Public API ──


def run_threshold_regression(
    data_path: Path,
    y_var: str,
    d_var: str,
    threshold_var: str,
    controls: Optional[List[str]] = None,
    fe_entity: str = "id",
    fe_time: str = "year",
    cluster_entity: str = "id",
    n_grid: int = 100,
    drop_range: tuple[float, float] = (0.05, 0.95),
    project_dir: Optional[Path] = None,
) -> dict:
    """Hansen (1999) panel threshold regression.

    Grid search → optimal threshold → full-sample FE + subsample regressions.

    Returns:
        dict: threshold, full_model (PanelResults), low_subsample, high_subsample, tex_path.
    """
    df = _load_data(data_path)
    required = [y_var, d_var, threshold_var, fe_entity, fe_time, cluster_entity] + (controls or [])
    _validate_columns(df, required)
    df = df.dropna(subset=[y_var, d_var, threshold_var])

    ctrl_list = controls or []

    # ── 1. Grid search ──
    q_lo = df[threshold_var].quantile(drop_range[0])
    q_hi = df[threshold_var].quantile(drop_range[1])
    step = (q_hi - q_lo) / n_grid
    candidates = [q_lo + i * step for i in range(1, n_grid + 1)]

    best_rss, best_gamma = float("inf"), None
    for gamma in candidates:
        pdf = df.copy().set_index([fe_entity, fe_time])
        pdf["_low"] = (df[threshold_var].values <= gamma).astype(float)
        pdf["_D_low"] = pdf[d_var] * pdf["_low"]
        pdf["_D_high"] = pdf[d_var] * (1 - pdf["_low"])

        formula = f"{y_var} ~ 1 + _D_low + _D_high + EntityEffects + TimeEffects"
        if ctrl_list:
            formula += " + " + " + ".join(ctrl_list)

        try:
            mod = PanelOLS.from_formula(formula, pdf, drop_absorbed=True).fit(cov_type="unadjusted")
            rss = float(mod.resids.pow(2).sum())
            if rss < best_rss:
                best_rss = rss
                best_gamma = gamma
        except Exception:
            continue

    if best_gamma is None:
        raise RuntimeError("Threshold grid search failed — no candidate converged.")

    # ── 2. Full-sample threshold model ──
    pdf = df.copy().set_index([fe_entity, fe_time])
    pdf["_low"] = (df[threshold_var].values <= best_gamma).astype(float)
    pdf["_D_low"] = pdf[d_var] * pdf["_low"]
    pdf["_D_high"] = pdf[d_var] * (1 - pdf["_low"])

    formula_full = f"{y_var} ~ 1 + _D_low + _D_high + EntityEffects + TimeEffects"
    if ctrl_list:
        formula_full += " + " + " + ".join(ctrl_list)

    mod_full = PanelOLS.from_formula(formula_full, pdf, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=cluster_entity
    )

    # ── 3. Subsample regressions ──
    low_mask = df[threshold_var].values <= best_gamma
    high_mask = ~low_mask

    def run_subsample(sub_df):
        if len(sub_df) < 10:
            return None
        sub = sub_df.copy().set_index([fe_entity, fe_time])
        formula = f"{y_var} ~ 1 + {d_var} + EntityEffects + TimeEffects"
        if ctrl_list:
            formula += " + " + " + ".join(ctrl_list)
        try:
            return PanelOLS.from_formula(formula, sub, drop_absorbed=True).fit(
                cov_type="clustered", cluster_entity=cluster_entity
            )
        except Exception:
            return None

    mod_low = run_subsample(df[low_mask])
    mod_high = run_subsample(df[high_mask])

    # ── 4. Structure results ──
    all_vars = ["_D_low", "_D_high", d_var] + ctrl_list

    def extract_row(mod, vname, label):
        if mod is None or vname not in mod.params:
            return {"label": label, "coef": "", "se": "", "sig": ""}
        coef = float(mod.params[vname])
        se = float(mod.std_errors[vname])
        pval = float(mod.pvalues[vname])
        return {
            "label": label,
            "coef": f"{coef:.3f}",
            "se": f"{se:.3f}",
            "sig": _sig_stars(pval),
        }

    def label_var(v):
        """Display label for a variable (raw name, no LaTeX escaping)."""
        return v

    full_rows = []
    # D_low always first
    full_rows.append(extract_row(mod_full, "_D_low", f"{_tex_name(d_var)} $\\times$ 低门槛组"))
    # D_high always second
    full_rows.append(extract_row(mod_full, "_D_high", f"{_tex_name(d_var)} $\\times$ 高门槛组"))
    # Controls in full model
    for c in ctrl_list:
        full_rows.append(extract_row(mod_full, c, c))

    low_rows = []
    low_rows.append(extract_row(mod_low, d_var, d_var))
    for c in ctrl_list:
        low_rows.append(extract_row(mod_low, c, c))

    high_rows = []
    high_rows.append(extract_row(mod_high, d_var, d_var))
    for c in ctrl_list:
        high_rows.append(extract_row(mod_high, c, c))

    result = {
        "threshold": round(best_gamma, 4),
        "full_model": {"rows": full_rows, "n": int(mod_full.nobs),
                       "r_squared": round(float(mod_full.rsquared), 4)},
        "low_subsample": {"rows": low_rows,
                          "n": int(mod_low.nobs) if mod_low else 0},
        "high_subsample": {"rows": high_rows,
                           "n": int(mod_high.nobs) if mod_high else 0},
        "threshold_var": threshold_var,
        "d_var": d_var,
    }

    if project_dir:
        tex = _generate_threshold_tex(result)
        tex_path = project_dir / "analysis" / "output" / "03_threshold.tex"
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


def _sig_stars(pval: float) -> str:
    return "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""


def _tex_sig(sig: str) -> str:
    return f"\\sym{{{sig}}}" if sig else ""


def _tex_name(name: str) -> str:
    """Escape underscores for LaTeX display."""
    return name.replace("_", "\\_")


def _generate_threshold_tex(result: dict) -> str:
    now = datetime.now().isoformat(timespec="minutes")
    tv_esc = _tex_name(result["threshold_var"])
    full = result["full_model"]
    low = result["low_subsample"]
    high = result["high_subsample"]

    # Build triple-aligned display rows
    # Format: (label, full_coef+se, low_coef+se, high_coef+se)
    t = []

    # 1. Regime interactions (only in full model)
    for r in full["rows"][:2]:
        label = r["label"]  # already has "× 低阈值" / "× 高阈值"
        c = r["coef"] + _tex_sig(r["sig"])
        s = f"({r['se']})" if r["se"] else ""
        t.append((label, c, s, "", "", "", ""))
        t.append(None)  # \addlinespace

    # 2. d_var (only in subsample models)
    dv_label = _tex_name(low["rows"][0]["label"])
    for grp, sgrp in [("low", low), ("high", high)]:
        r = sgrp["rows"][0]
        c = r["coef"] + _tex_sig(r["sig"]) if r["coef"] else ""
        se = f"({r['se']})" if r["se"] else ""
        if grp == "low":
            lc_low, lse_low = c, se
        else:
            lc_high, lse_high = c, se
    t.append((dv_label, "", "", lc_low, lse_low, lc_high, lse_high))
    t.append(None)

    # 3. Controls (in all 3 models)
    # full rows start at index 2 (after 2 regime rows)
    # low/high rows start at index 1 (after 1 d_var row)
    n_ctrl = min(len(full["rows"]) - 2, len(low["rows"]) - 1, len(high["rows"]) - 1)
    for i in range(n_ctrl):
        fr = full["rows"][i + 2]
        lr = low["rows"][i + 1]
        hr = high["rows"][i + 1]
        label = _tex_name(fr["label"])
        fc = fr["coef"] + _tex_sig(fr["sig"]) if fr["coef"] else ""
        fse = f"({fr['se']})" if fr["se"] else ""
        lc = lr["coef"] + _tex_sig(lr["sig"]) if lr["coef"] else ""
        lse = f"({lr['se']})" if lr["se"] else ""
        hc = hr["coef"] + _tex_sig(hr["sig"]) if hr["coef"] else ""
        hse = f"({hr['se']})" if hr["se"] else ""
        t.append((label, fc, fse, lc, lse, hc, hse))

    # Render rows
    R = []
    for item in t:
        if item is None:
            R.append(r"\addlinespace")
            continue
        label, fc, fse, lc, lse, hc, hse = item
        R.append(f"{label} & {fc} & {lc} & {hc} \\\\")
        # Only render SE row if any SE exists
        has_se = any([fse, lse, hse])
        if has_se:
            R.append(f"  & {fse} & {lse} & {hse} \\\\")

    # Model stats
    R.append(r"\midrule")
    R.append(f"样本量 & {full['n']} & {low['n']} & {high['n']} \\\\")
    R.append(f"R² & {full['r_squared']} & & \\\\")

    rows_str = "\n".join(R)

    fn1 = r"\multicolumn{4}{l}{\footnotesize 注：门槛变量为" + tv_esc + r"，最优门槛值为" + str(result['threshold']) + r"。}\\"
    fn2 = r"\multicolumn{4}{l}{\footnotesize 全样本门槛回归同时包含低/高两组数字经济的交互项。}\\"
    fn3 = r"\multicolumn{4}{l}{\footnotesize * $p<0.10$, ** $p<0.05$, *** $p<0.01$}\\"

    return (
        "% 面板门槛回归结果 (Python, " + now + ")\n"
        + r"\begin{table}[htbp]" + "\n"
        + r"\centering" + "\n"
        + r"\caption{面板门槛回归：" + tv_esc + r"的调节效应\label{tab:threshold}}" + "\n"
        + r"\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}" + "\n"
        + r"\begin{tabular}{l*{3}{c}}" + "\n"
        + r"\toprule" + "\n"
        + r"& \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} \\" + "\n"
        + r"& \multicolumn{1}{c}{全样本门槛} & \multicolumn{1}{c}{低" + tv_esc + r"} & \multicolumn{1}{c}{高" + tv_esc + r"} \\" + "\n"
        + r"\midrule" + "\n"
        + rows_str + "\n"
        + r"\bottomrule" + "\n"
        + fn1 + "\n"
        + fn2 + "\n"
        + fn3 + "\n"
        + r"\end{tabular}" + "\n"
        + r"\end{table}"
    )
