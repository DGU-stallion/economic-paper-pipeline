---
name: "文献综述 Skill"
version: "1.0.0"
skill_id: "skill-literature"
description: "自动检索学术文献、生成摘要、撰写文献综述、管理参考文献"
stages_handled: [literature]
required_mcp: [paper-search-mcp]
---

## Skill 定位

专门负责**学术文献的自动检索、摘要、综述撰写和参考文献管理**。

**不负责**：选题确认、实证分析、论文撰写

---

## 输入输出接口

### 输入 (来自协调器)

```json
{
  "project_name": "项目名称",
  "project_path": "papers/<project-name>/",
  "entry_point": "new|resume|jump",
  "topic_context": {
    "research_question": "研究问题",
    "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
    "identification_strategy": "DID|FE|IV|RDD|OLS",
    "y_var": "被解释变量",
    "d_var": "核心解释变量"
  }
}
```

### 输出 (传递给下一个 Skill)

```json
{
  "status": "completed|partial",
  "stage": "literature",
  "literature_summary": {
    "total_papers": 50,
    "core_papers": 15,
    "chinese_papers": 20,
    "recent_papers_ratio": 0.65,
    "key_findings": ["发现1", "发现2", "发现3"],
    "research_gaps": ["空白1", "空白2"]
  },
  "artifacts": [
    "literature/literature_review.md",
    "literature/references.bib"
  ],
  "next_skill": "stata"
}
```

---

## 工作流程

### Step 1: 检索策略生成

基于研究问题和关键词，自动生成检索策略：

**英文文献**（Google Scholar）：
- 关键词组合：`Y D`、`Y D identification`、`mechanism`
- 检索时间范围根据用户偏好调整
- 高引文献回溯

**中文文献**（用户补充或 CNKI）：
- 对应中文关键词
- 《经济研究》《管理世界》《经济学季刊》优先

### Step 2: 批量检索与筛选

使用 `paper-search-mcp`：
1. `search_google_scholar` - 英文核心文献
2. `search_arxiv` - 最新工作论文

对检索结果自动筛选：
- 被引量排序前 30
- 期刊等级筛选（JCR Q1、中文权威）
- 标题/摘要相关性筛选

### Step 3: 关键文献摘要

对筛选出的 Top 15 篇核心文献，生成结构化摘要：

```markdown
## [文献序号] 标题

**作者**：XXX et al.
**年份**：2023
**期刊**：Journal Name
**核心贡献**：一句话
**识别策略**：方法简述
**关键发现**：核心系数及显著性
**与本文关系**：基准/对比/机制
```

### Step 4: 文献综述撰写

按以下结构自动生成综述：

1. **研究脉络梳理**：该领域的发展阶段和里程碑
2. **三支文献分支**：按理论视角或方法分类
3. **研究空白定位**：本文的边际贡献位置
4. **文献总结表格**：核心文献对比表

### Step 5: 参考文献管理

- 自动生成 `.bib` 文件（BibTeX 格式）
- 根据用户偏好检查参考文献（语言、时效性等要求）
- 自动补全缺失字段

---

## 人机协作点

✅ **需要用户确认**：
1. 检索策略确认（关键词是否合适）
2. 关键文献清单确认（是否需要补充特定文献）
3. 文献综述整体结构确认
4. 是否需要对某篇文献做精读解读

---

## 约束条件（按用户偏好检查）

| 检查项 | 数据来源 | 不满足时处理 |
|------|---------|-------------|
| 语言要求 | `preferences.paper_lang_requirement` | 提示用户补充对应语种文献 |
| 参考文献风格 | `preferences.paper_ref_style` | 按用户要求调整 |
| 核心文献 | 至少 15 篇高质量文献 | 补充检索或降低门槛 |
| .bib 完整性 | 所有条目有 author/title/journal/year | 自动补全或标记待填 |

---

## 产出文件规范

所有文件写入 `papers/<project-name>/literature/` 目录：

| 文件 | 内容 | 格式要求 |
|------|------|---------|
| `search_results.json` | 原始检索结果（中间产物） | JSON |
| `paper_summaries.md` | Top 15 核心文献摘要 | 每篇结构化 |
| `literature_review.md` | 完整文献综述 | 4 部分结构 |
| `references.bib` | BibTeX 参考文献 | 规范格式，中英双语 |

---

## 快速入口（跳转）

如果用户跳过选题直接进入文献阶段，确认：
1. 研究问题一句话
2. 关键词 3-5 个
3. 是否需要补充特定文献