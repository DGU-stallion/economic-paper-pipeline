---
name: topic-explorer
description: Explore research topics using 5W1H framework — from vague idea to precise research question with Y/D variables and identification strategy.
version: 6.0.0a1
triggers:
  - "我有个想法"
  - "帮我选题"
  - "research topic"
consumes: []
produces:
  - research_question
  - y_var
  - d_var
  - identification
  - hypotheses
  - control_vars
output_dir: topics/
---

# Topic Explorer

## What It Does

Guides the researcher from a vague idea to a precise, testable research question through structured 5W1H dialogue.

## Process

```
What → Why → Who → When → Where → How
→ Gap identification → SMART refinement → Hypothesis generation
```

## Outputs

| Key | Type | Description |
|-----|------|-------------|
| research_question | str | Precise research question statement |
| y_var | str | Dependent variable name |
| d_var | str | Core independent variable name |
| identification | str | Causal identification strategy (FE/DID/IV/RDD) |
| hypotheses | list[str] | Testable hypotheses |
| control_vars | list[str] | Control variable candidates |

## Files Written

```
papers/<project>/topics/00_research_proposal.md
```

## Agent Guide Output

```json
{
  "completed": "topic-explorer",
  "artifacts": ["topics/00_research_proposal.md"],
  "context_written": ["research_question", "y_var", "d_var", "identification"],
  "next_steps": [
    {"skill": "literature-survey", "reason": "研究问题已明确，需要检索相关文献", "ready": true},
    {"skill": "data-collector", "reason": "可以并行搜索可用数据源", "ready": true}
  ],
  "warnings": []
}
```

## Behavior

- Ask one high-information question at a time
- Do not assume identification strategy — let the researcher confirm
- All outputs are `user_supplied` evidence status (researcher's decisions)
