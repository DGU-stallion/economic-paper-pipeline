---
name: paper-agent
description: Meta-skill that orchestrates all PaperPilot skills in order. Contains no research logic of its own — only sequencing, state diagnosis, and next-step recommendations.
version: 6.0.0a1
triggers:
  - "帮我写论文"
  - "开始一篇新论文"
  - "检查论文状态"
  - "research pipeline"
---

# PaperPilot Agent (meta-skill)

## Overview

Top-level entry point for PaperPilot. This skill **contains no research logic** — it only:

1. Diagnoses the current project state (`pp inspect`)
2. Determines which downstream skill to invoke next
3. Passes context between skills via `pipeline_state.json`
4. Returns structured `agent_guide` after each step

## Downstream Skills

```
用户需求
   │
   ▼
[paper-agent] ─── 诊断 + 编排 + agent_guide
   │
   ├──▶ [topic-explorer]        选题探索
   ├──▶ [literature-survey]     文献调研
   ├──▶ [data-collector]        数据搜集与清洗
   ├──▶ [empirical-analysis]    实证分析 (可选，按需安装)
   ├──▶ [paper-writer]          论文写作
   └──▶ [integrity-auditor]     审查
```

## When to Use

- User wants the full research pipeline end-to-end
- User says "检查论文状态" or "下一步做什么"
- Session start / resume — auto-diagnose and recommend

## When NOT to Use

- User explicitly asks for only one stage → invoke that skill directly

## Workflow

### Step 1: Diagnose

Run `pp inspect <project> --json` to get 7-dimension readiness report.

### Step 2: Identify Next Skill

Based on dimensions with lowest readiness and blockers:

| Condition | Invoke |
|-----------|--------|
| No research question | topic-explorer |
| No literature | literature-survey |
| No data | data-collector |
| Data ready, no regression | empirical-analysis |
| Results ready, no paper | paper-writer |
| Paper draft exists | integrity-auditor |

### Step 3: Invoke & Collect Guide

Load the selected skill, execute, then read its `agent_guide` output.

### Step 4: Return Recommendations

```json
{
  "completed_skill": "<skill-name>",
  "project_readiness": 0.65,
  "next_steps": [
    {"skill": "empirical-analysis", "reason": "文献已就绪，数据可用", "ready": true},
    {"skill": "integrity-auditor", "reason": "检查已有引用的真实性", "ready": true}
  ],
  "warnings": []
}
```

## Path Convention

All skills write artifacts to:
```
papers/<project>/<skill-output-dir>/
```

Mapping:
- topic-explorer → `topics/`
- literature-survey → `literature/`
- data-collector → `data/`
- empirical-analysis → `analysis/`
- paper-writer → `paper/`
- integrity-auditor → `audit/`

## Behavior Rules

1. Never execute research logic directly — always delegate to a downstream skill
2. Evidence status rules apply: planned / user_supplied / executed / verified
3. When a skill is not installed (e.g., empirical-analysis without deps), recommend installation rather than failing
4. One recommendation at a time when asking user for research decisions
