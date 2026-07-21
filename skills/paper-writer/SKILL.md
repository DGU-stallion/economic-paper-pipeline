---
name: paper-writer
description: Assemble all upstream artifacts into a complete LaTeX manuscript — introduction through conclusion, with tables and citations injected.
version: 6.0.0a1
triggers:
  - "帮我写论文"
  - "write paper"
  - "整合写作"
consumes:
  - research_question
  - literature_review_path
  - bib_path
  - baseline (optional)
  - robustness_results (optional)
produces:
  - tex_path
  - pdf_path (if texlive available)
output_dir: paper/
---

# Paper Writer

## What It Does

Integrates all upstream skill outputs into a structured LaTeX manuscript:

1. Abstract
2. Introduction (research question + contribution)
3. Literature Review (from literature-survey)
4. Research Design / Methodology
5. Empirical Results (from empirical-analysis)
6. Robustness Checks
7. Conclusion

## Process

```
Upstream artifacts → Section assembly → Table/figure injection
→ Citation injection from .bib → LaTeX generation
→ (optional) XeLaTeX compile → Humanizer quality check
```

## Outputs

| Key | Type | Description |
|-----|------|-------------|
| tex_path | str | Path to main.tex |
| pdf_path | str | Path to compiled PDF (if TeX available) |

## Files Written

```
papers/<project>/paper/main.tex
papers/<project>/paper/sections/01_introduction.tex
papers/<project>/paper/sections/02_literature.tex
papers/<project>/paper/sections/03_methodology.tex
papers/<project>/paper/sections/04_results.tex
papers/<project>/paper/sections/05_robustness.tex
papers/<project>/paper/sections/06_conclusion.tex
papers/<project>/paper/main.pdf (if compiled)
```

## Agent Guide Output

```json
{
  "completed": "paper-writer",
  "artifacts": ["paper/main.tex", "paper/main.pdf"],
  "context_written": ["tex_path", "pdf_path"],
  "next_steps": [
    {"skill": "integrity-auditor", "reason": "论文初稿完成，建议审查引用和数字一致性", "ready": true}
  ],
  "warnings": ["论文由 AI 辅助生成，建议标注并经领域专家审阅"]
}
```

## Behavior

- Every number in the paper must trace back to an artifact with `executed` or `verified` status
- Placeholder content must be explicitly marked (TODO/TBD)
- AI-generated disclosure: recommend adding a note that AI tools were used in drafting
- Humanizer quality check: detect AI-style writing patterns (excessive dashes, repetitive structures)
