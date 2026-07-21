---
name: literature-survey
description: Search, screen, and synthesize academic literature — produces candidate list, structured review, and BibTeX bibliography.
version: 6.0.0a1
triggers:
  - "帮我搜文献"
  - "写文献综述"
  - "literature review"
consumes:
  - research_question
produces:
  - candidate_papers
  - literature_review_path
  - bib_path
  - research_gap
output_dir: literature/
---

# Literature Survey

## What It Does

Two-phase literature work:
1. **Search** — find candidate papers from multiple sources
2. **Synthesize** — screen, organize by theme, write review, generate .bib

## Search Backends (auto-detected)

Priority: Tavily → Semantic Scholar API → Agent built-in web search → manual guidance

## Process

```
Research question → Multi-source search → Candidate list
→ Screen (relevance + recency) → Theme clustering
→ Review narrative → BibTeX generation → Gap identification
```

## Outputs

| Key | Type | Description |
|-----|------|-------------|
| candidate_papers | list | Titles, authors, abstracts, URLs |
| literature_review_path | str | Path to review markdown |
| bib_path | str | Path to .bib file |
| research_gap | str | Identified gap statement |

## Files Written

```
papers/<project>/literature/00_candidate_papers.md
papers/<project>/literature/04_review_final.md
papers/<project>/paper/references.bib
```

## Agent Guide Output

```json
{
  "completed": "literature-survey",
  "artifacts": ["literature/00_candidate_papers.md", "literature/04_review_final.md", "paper/references.bib"],
  "context_written": ["candidate_papers", "literature_review_path", "bib_path", "research_gap"],
  "next_steps": [
    {"skill": "data-collector", "reason": "文献已梳理，需要获取数据支撑实证", "ready": true},
    {"skill": "integrity-auditor", "reason": "验证引用真实性", "ready": true}
  ],
  "warnings": ["引用真实性建议通过 integrity-auditor 验证"]
}
```

## Behavior

- Every citation must come from a source the agent actually accessed (no memory-only citations)
- Mark unverified citations explicitly
- Do not fabricate paper titles, authors, or publication venues
