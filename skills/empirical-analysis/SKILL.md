---
name: empirical-analysis
description: Execute empirical analysis — baseline regression, robustness checks, heterogeneity, and mediation. Optional skill with multiple backend tiers.
version: 6.0.0a1
triggers:
  - "跑回归"
  - "做实证"
  - "run regression"
  - "DID"
  - "工具变量"
consumes:
  - y_var
  - d_var
  - identification
  - clean_data_path
  - control_vars (optional)
produces:
  - baseline
  - heterogeneity
  - robustness_results
output_dir: analysis/
optional: true
---

# Empirical Analysis

## What It Does

Executes quantitative empirical analysis based on the identification strategy defined in topic-explorer.

## Backend Tiers (installed separately)

| Tier | Package | Methods |
|------|---------|---------|
| **builtin** | linearmodels + statsmodels | FE, DID (interaction), Threshold (Hansen grid) |
| **diff-diff** | `pip install diff-diff` | Callaway-Sant'Anna, Staggered DID, Synthetic DID, Honest DID |
| **statspai** | `pip install statspai` | IV, RDD, Synthetic Control, Double ML, full causal suite |

## Installation

This skill works in **guidance mode** without any backend installed.
To execute real regressions, install at least the builtin tier:

```bash
pip install paperpilot[standard]  # builtin: linearmodels + statsmodels
```

For advanced methods:
```bash
pip install diff-diff     # Staggered DID / Synthetic DID
pip install statspai      # IV / RDD / SC / Double ML
```

## Process

```
Identification strategy → Model specification
→ Baseline regression → Robustness checks
→ Heterogeneity analysis → (optional) Mediation
→ .tex table generation
```

## Outputs

| Key | Type | Description |
|-----|------|-------------|
| baseline | dict | Coefficients, SE, significance, N, R² |
| heterogeneity | dict | Group-level results |
| robustness_results | dict | Multiple robustness test outcomes |

## Files Written

```
papers/<project>/analysis/output/00_model_spec.md
papers/<project>/analysis/output/02_baseline_regression.tex
papers/<project>/analysis/output/03_heterogeneity.tex
papers/<project>/analysis/output/04_robustness.tex
```

## Agent Guide Output

```json
{
  "completed": "empirical-analysis",
  "artifacts": ["analysis/output/02_baseline_regression.tex", "analysis/output/04_robustness.tex"],
  "context_written": ["baseline", "robustness_results"],
  "next_steps": [
    {"skill": "paper-writer", "reason": "实证结果已就绪，可以整合写作", "ready": true},
    {"skill": "integrity-auditor", "reason": "验证数字一致性", "ready": true}
  ],
  "warnings": [],
  "backend_used": "linearmodels"
}
```

## Behavior

- All regression results are `executed` evidence — never mark LLM estimates as executed
- Record random seeds for any stochastic process (placebo tests)
- If the needed method is not installed, return `{"ready": false, "install_hint": "pip install diff-diff"}`
