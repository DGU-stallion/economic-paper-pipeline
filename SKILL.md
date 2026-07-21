# PaperPilot — Skill Manifest

**Version:** 6.0.0a1 (source of truth: `scripts/__init__.__version__`)
**Protocol:** CLI + JSON over stdout
**Runtime:** Python ≥ 3.11 (no mandatory external services)

## What This Skill Does

Guides an empirical economics paper from topic ideation through PDF output.
Works inside any coding agent (Claude Code, Codex, Kiro, Cursor, OpenCode, etc.)
that can run Python and read files.

## Capabilities

| ID | Name | Requires | Produces |
|----|------|----------|----------|
| conceptualize | 概念引导 | — | research_question, y_var, d_var, identification |
| research | 文献搜索 | web_search | candidate_papers, data_sources |
| literature | 文献综述 | candidate_papers | literature_review, bib |
| data | 数据清洗 | raw data files | clean_data_path, quality_report |
| analyze | 实证分析 | clean_data + vars | baseline, heterogeneity |
| verify | 稳健性 | baseline | robustness_results |
| write | 论文写作 | all upstream | tex_path |
| format | 编译 | tex_path + texlive | pdf_path |

## Agent Interaction Protocol

### 1. Install

```bash
python3 install/bootstrap.py --check --profile standard --json
```

If not installed:
```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[standard]"
```

### 2. Diagnose

```bash
pp doctor --json        # environment capabilities
pp inspect <dir> --json # paper project state
```

### 3. Execute Workflow

```bash
pp workflow plan <module> [description]
# ... agent runs module logic ...
pp workflow commit <module>
pp workflow verify <module>
```

### 4. Recover

```bash
pp workflow recover
pp workflow revisions
```

## Agent Capability Declaration

On first load, the agent adapter should declare available host capabilities
by writing to the project's `pipeline_state.json`:

```json
{
  "agent_capabilities": {
    "agent_type": "claude-code | codex | kiro | cursor | generic",
    "web_search": true,
    "mcp_servers": ["tavily", "paper-search"],
    "file_edit": true,
    "shell_exec": true,
    "texlive": false
  }
}
```

The skill reads this to enable/disable capabilities gracefully.

## Evidence Status Contract

Every result in `context_store` carries an `evidence_status`:

| Status | Meaning |
|--------|---------|
| `planned` | Module scheduled but not yet run |
| `user_supplied` | Value provided by researcher (not machine-verified) |
| `executed` | Code ran and produced this result |
| `verified` | Result passed validation checks |

Transitions: `planned → executed`, `planned → user_supplied`, `user_supplied → executed`, `executed → verified`.

## Golden Path

The canonical research workflow:

```
conceptualize → research → literature → data → analyze → verify → write → format
```

Each step checks upstream readiness via the contract system.
Steps can be skipped if evidence is already present (e.g., importing an existing project).

## Non-Goals

- This skill does NOT implement IV, RDD, or synthetic control (only FE/DID currently).
- Agent adapters must NOT duplicate core research logic.
- LLM-generated content must NOT be marked as `executed` or `verified`.

## File Layout

```
SKILL.md              ← this file (agent-neutral manifest)
CLAUDE.md             ← Claude Code specific behavior rules
AGENT_INSTALL.md      ← installation contract
adapters/             ← thin agent-specific adapters
  claude_code.md      ← Claude Code adapter
  codex.md            ← OpenAI Codex adapter
  kiro.md             ← AWS Kiro adapter
scripts/              ← core logic (shared across all agents)
  workflow.py         ← plan/commit/verify lifecycle
  paper_state.py      ← read-only project scanner
  pipeline.py         ← unified CLI entry point
  orchestrator.py     ← state machine
  modules/            ← 8 capability modules
  backends/           ← analysis backends
```
