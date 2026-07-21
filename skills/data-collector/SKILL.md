---
name: data-collector
description: Locate, acquire, clean, and validate research data — from raw sources to analysis-ready panel.
version: 6.0.0a1
triggers:
  - "帮我找数据"
  - "洗一下数据"
  - "clean data"
consumes:
  - research_question
  - y_var
  - d_var
produces:
  - clean_data_path
  - data_quality_report
output_dir: data/
---

# Data Collector

## What It Does

End-to-end data pipeline:
1. **Source identification** — find datasets covering required variables
2. **Acquisition guidance** — provide download instructions or API access
3. **Cleaning** — type detection, missing values, outliers, deduplication
4. **Validation** — panel structure verification, quality report

## Requires

- Python pandas (for cleaning/validation execution)
- Without pandas: provides guidance only, marks outputs as `planned`

## Process

```
Variables needed → Source search → Acquire
→ Format detection (csv/xlsx/dta/parquet)
→ Type inference → Missing diagnosis → Outlier treatment
→ Panel structure validation → Quality report → Export clean
```

## Outputs

| Key | Type | Description |
|-----|------|-------------|
| clean_data_path | str | Path to cleaned data file |
| data_quality_report | str | Path to validation report |

## Files Written

```
papers/<project>/data/raw/           ← user provides
papers/<project>/data/clean/panel_clean.csv
papers/<project>/data/00_feasibility_report.md
papers/<project>/data/02_validation_report.md
papers/<project>/data/scripts/01_clean.py
```

## Agent Guide Output

```json
{
  "completed": "data-collector",
  "artifacts": ["data/clean/panel_clean.csv", "data/02_validation_report.md"],
  "context_written": ["clean_data_path", "data_quality_report"],
  "next_steps": [
    {"skill": "empirical-analysis", "reason": "数据已就绪，可以进行实证分析", "ready": true},
    {"skill": "integrity-auditor", "reason": "验证数据面板结构一致性", "ready": true}
  ],
  "warnings": []
}
```

## Behavior

- Never upload user data to external services without confirmation
- Cleaning scripts must be reproducible (saved to `data/scripts/`)
- Report panel dimensions (N entities × T periods) explicitly
