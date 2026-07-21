---
name: integrity-auditor
description: Audit research integrity — verify citations via OpenAlex/Semantic Scholar, check numerical consistency, detect AI writing patterns, validate data-to-paper traceability.
version: 6.0.0a1
triggers:
  - "检查引用"
  - "审查论文"
  - "verify citations"
  - "integrity check"
consumes: []
produces:
  - audit_report
output_dir: audit/
---

# Integrity Auditor

## What It Does

Multi-dimensional research integrity audit:

1. **Citation verification** — validate each .bib entry against OpenAlex / Semantic Scholar
2. **Numerical consistency** — check that numbers in paper match analysis output
3. **AI writing detection** — Humanizer-ZH patterns (dashes, repetition, euroization)
4. **Data traceability** — verify every table/figure has a source artifact

## Citation Verification Backends

| Backend | API Key Required | Coverage |
|---------|-----------------|----------|
| OpenAlex | No (free, rate-limited) | 250M+ works |
| Semantic Scholar | No (free tier) | 200M+ papers |
| CrossRef | No | DOI resolution |

## Process

```
Paper artifacts → Citation check → Numerical audit
→ Writing style check → Traceability check
→ Evidence grading (verified / unverified / suspicious / fabricated)
→ Audit report
```

## Outputs

| Key | Type | Description |
|-----|------|-------------|
| audit_report | dict | Findings by category, evidence grades |

## Files Written

```
papers/<project>/audit/citation_verification.json
papers/<project>/audit/integrity_report.md
```

## Agent Guide Output

```json
{
  "completed": "integrity-auditor",
  "artifacts": ["audit/integrity_report.md", "audit/citation_verification.json"],
  "context_written": ["audit_report"],
  "next_steps": [
    {"skill": "paper-writer", "reason": "修复发现的问题后重新生成", "ready": true}
  ],
  "warnings": ["发现 3 条引用无法验证", "第 4 节有 2 处数字与回归输出不一致"]
}
```

## Evidence Grades

| Grade | Meaning |
|-------|---------|
| verified | Confirmed via API — title, authors, year all match |
| unverified | Could not confirm (API timeout / not found) |
| suspicious | Partial match with discrepancies |
| fabricated | No matching work found in any database |

## Behavior

- Never auto-delete citations — only report and recommend
- Rate-limit API calls (max 1 req/sec for free tiers)
- Can audit external papers (given a PDF or .bib path)
