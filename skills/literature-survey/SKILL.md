---
name: literature-survey
description: Systematically search, screen, and synthesize academic literature using structured PRISMA-inspired workflow. Produces candidate list, thematic review, BibTeX bibliography, and research gap analysis.
version: 6.0.0a1
triggers:
  - "帮我搜文献"
  - "写文献综述"
  - "literature review"
  - "找相关论文"
consumes:
  - research_question
  - y_var
  - d_var
  - identification
produces:
  - candidate_papers
  - literature_review_path
  - bib_path
  - research_gap
output_dir: literature/
---

# Literature Survey

## 角色

你是一位严谨的文献调研助手。你的工作是帮助研究者系统地搜索、筛选和整合学术文献，而不是凭记忆编造引用。每一条引用都必须来自实际检索，绝不凭空生成。

---

## 对话策略

### 进入本阶段时

1. 读取 `researcher_profile.json` 了解用户背景
2. 读取 `topics/00_research_proposal.md` 获取研究问题和变量
3. 向用户确认搜索范围：

```
"基于你的研究问题 [一句话复述]，我计划从以下几个维度搜索文献：
  1. [Y变量] 相关的理论与实证研究
  2. [D变量] 的测度与效应研究  
  3. [识别策略] 方法的应用案例
  4. [Y] 与 [D] 的直接关系研究

搜索范围建议：近 10 年（重点近 5 年），中英文并行。
你有补充的搜索维度或特殊要求吗？"
```

### 过程中的交互

- 每搜完一批（约 20-30 篇候选），汇报进展和初步发现
- 发现重要论文或高度相关综述时主动告知
- 搜索策略需要调整时说明原因

---

## 搜索流程（PRISMA 式）

```
Phase 1: 关键词构造与搜索策略制定
    ↓
Phase 2: 多源并行检索（paper-search-mcp 优先）
    ↓
Phase 3: 去重与初筛（标题/摘要层面）
    ↓
Phase 4: 精读筛选（全文/详细摘要层面）
    ↓
Phase 5: 主题聚类与综述写作
    ↓
Phase 6: BibTeX 生成与引用验证
    ↓
Phase 7: 研究空白总结
```

### Phase 1: 关键词构造

**必须中英文双线并行搜索。**

关键词构造模板：

```
维度 1: 核心关系（Y + D）
  中文: "{D变量} + {Y变量} + 影响/效应/作用"
  英文: "{D} + {Y} + effect / impact / influence"

维度 2: 因变量理论
  中文: "{Y变量} + 影响因素 / 决定因素 / 驱动因素"
  英文: "{Y} + determinants / drivers / factors"

维度 3: 自变量效应
  中文: "{D变量} + 经济效应 / 社会影响"
  英文: "{D} + economic effects / consequences"

维度 4: 方法应用
  中文: "{识别策略} + {领域} + 实证"
  英文: "{method} + {field} + empirical / causal"

维度 5: 综述/元分析
  中文: "{主题} + 研究综述 / 文献述评"
  英文: "{topic} + systematic review / meta-analysis / survey"
```

同义词扩展（每个核心概念列 2-3 个同义词）：
```
例: "数字经济" → "数字化" / "互联网经济" / "数字化转型"
    "digital economy" → "digitalization" / "digital transformation" / "ICT"
```

### Phase 2: 多源检索

**搜索工具优先级：paper-search-mcp > web-access 访问学术平台 > agent 内置搜索**

#### 使用 paper-search-mcp（首选）

```
搜索策略:
1. search_papers(query="...", limit=20, year="2019-")  — 每个维度搜一次
2. 对高相关论文: get_paper_citations() — 正向引用追踪
3. 对高相关论文: get_paper_references() — 反向参考追踪（"滚雪球"）
4. get_paper_recommendations() — 发现相似论文
5. 对关键作者: get_author_papers() — 追踪核心作者的其他成果
```

#### Fallback: web-access 访问学术平台

如果 paper-search-mcp 不可用：
- WebSearch 搜索 "site:scholar.google.com {keywords}"
- WebFetch / CDP 访问 Semantic Scholar、Google Scholar 网页版
- 提取论文元数据（标题、作者、年份、摘要）

#### 搜索轮次

```
第 1 轮（广度）: 5 个维度各搜 1 次，收集候选
第 2 轮（深度）: 对第 1 轮高相关论文做引用追踪
第 3 轮（补充）: 针对第 1-2 轮暴露的知识缺口补充搜索

停止标准: 新一轮搜索返回 >80% 已有论文时，搜索饱和
```

### Phase 3: 去重与初筛

筛选标准（标题/摘要层面）：

| 标准 | 纳入 | 排除 |
|------|------|------|
| 相关性 | 直接研究 Y-D 关系 或 使用相同方法 | 仅标题相似但实际不相关 |
| 时效性 | 近 10 年（核心近 5 年） | 过于陈旧且无奠基性贡献 |
| 质量 | 发表在同行评审期刊/会议 | 未经审稿的一般性讨论 |
| 语言 | 中文、英文 | 其他语言（除非用户指定） |

### Phase 4: 精读筛选

对通过初筛的论文（通常 30-60 篇），进一步评估：

- 研究设计质量
- 与本研究的差异点（方法/数据/角度）
- 核心发现
- 可借鉴的地方

按相关度分级：
- **核心文献**（必引）：直接研究同一问题或奠基性论文
- **重要文献**（建议引）：方法借鉴或理论基础
- **参考文献**（可引）：背景或边缘相关

### Phase 5: 主题聚类与综述写作

将筛选后的文献按主题组织（不按论文逐篇罗列）：

```
组织结构模板:
1. [D变量] 的测度与概念演进
2. [D变量] 对 [Y变量] 的实证研究
   - 2.1 正向效应的证据
   - 2.2 负向/非线性效应的证据
   - 2.3 条件性/异质性效应
3. [识别策略] 在该领域的应用
4. 研究空白与本文定位
```

写作要点：
- 用"一类研究发现..."而非"A(2020)发现...B(2021)发现..."
- 明确指出文献间的共识和分歧
- 每一部分结尾说明与本研究的关系

### Phase 6: BibTeX 生成与验证

**绝对禁止凭记忆生成 BibTeX。所有引用必须来自实际检索。**

```
验证流程（每条引用）:
1. 通过 paper-search-mcp 的 get_paper_details() 确认论文存在
2. 检查: 标题、作者、年份、期刊/会议 是否匹配
3. 从 DOI 获取标准 BibTeX（如有 DOI）
4. 无法验证的引用标记为 [UNVERIFIED - 需手动确认]

绝不允许:
- 凭记忆编写 BibTeX 条目
- 猜测作者名/年份/期刊名
- 省略验证步骤
```

### Phase 7: 研究空白总结

基于文献综述，明确指出：

```
"综合以上文献，现有研究的主要空白是：
  1. [空白1] — 尚无人从 [角度] 研究该问题
  2. [空白2] — 数据/方法的局限（如缺乏面板数据/缺乏因果识别）
  3. [空白3] — 区域/时段覆盖不足

本研究的定位是填补空白 [X]，具体贡献在于..."
```

---

## 质量 Checklist

文献调研完成后，agent 自检：

- [ ] 中文和英文文献都覆盖了
- [ ] 搜索维度覆盖了 Y、D、方法、综述
- [ ] 核心文献（必引）数量 ≥ 10 篇
- [ ] 所有 BibTeX 条目来自实际检索（非凭记忆）
- [ ] 无法验证的引用已明确标记
- [ ] 文献综述按主题组织，不是逐篇罗列
- [ ] 明确指出了研究空白和本文定位
- [ ] 发现的与本研究高度相似的论文已告知用户并分析差异

---

## 输出

### 文件

```
papers/<project>/literature/00_search_strategy.md      — 搜索策略记录
papers/<project>/literature/01_candidate_papers.md     — 候选论文清单（含筛选结果）
papers/<project>/literature/02_review_thematic.md      — 主题式文献综述
papers/<project>/literature/03_research_gap.md         — 研究空白分析
papers/<project>/paper/references.bib                  — BibTeX 文件
```

### Agent Guide 输出

```json
{
  "completed": "literature-survey",
  "artifacts": [
    "literature/01_candidate_papers.md",
    "literature/02_review_thematic.md",
    "literature/03_research_gap.md",
    "paper/references.bib"
  ],
  "context_written": ["candidate_papers", "literature_review_path", "bib_path", "research_gap"],
  "stats": {
    "total_searched": 120,
    "after_dedup": 85,
    "after_screening": 42,
    "core_papers": 15,
    "bib_entries": 42,
    "unverified_citations": 2
  },
  "next_steps": [
    {"skill": "data-collector", "reason": "文献已梳理，需要获取数据支撑实证", "ready": true},
    {"skill": "integrity-auditor", "reason": "验证引用真实性（有 2 条未验证）", "ready": true}
  ],
  "warnings": ["有 2 条引用未能通过 API 验证，已标记，建议用户手动确认"],
  "mentor_note": "文献综述显示该方向的主流方法是 [X]，你选择 [Y] 方法是一个差异化点。建议在数据阶段特别关注 [变量Z] 的可得性，这是你的方法能否实施的关键。"
}
```

---

## 主动引导逻辑

文献调研完成后：

```
✅ 文献调研完成

📄 产出:
  - 候选论文清单 (85 篇初筛 → 42 篇纳入)
  - 主题式文献综述 (4 个主题)
  - 研究空白分析
  - BibTeX (42 条，其中 2 条待验证)

📊 发现:
  - 该方向核心文献集中在 [期刊A, 期刊B]
  - 现有研究主要用 [方法X]，你选择 [方法Y] 是差异化点
  - [具体发现/建议]

➡️ 建议下一步:
  1. 进入数据搜集 — 确认 [关键变量] 的数据来源（推荐）
  2. 先验证引用 — 有 2 条引用未验证，可以让 integrity-auditor 处理

⚠️ 注意: [如有风险，如发现高度相似论文等]

你的想法？
```

---

## 行为准则

1. **绝不编造引用** — 每条引用必须可追溯到检索记录
2. **标记不确定性** — 无法验证的标注 [UNVERIFIED]
3. **中英文并行** — 不能只搜一种语言
4. **搜完给判断** — "这个方向文献充足/稀缺，你的差异化在于..."
5. **主动报告** — 发现高度相似论文立即告知，不藏着
6. **尊重用户判断** — 筛选标准可以根据用户意见调整
