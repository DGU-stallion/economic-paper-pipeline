---
name: "选题研究 Skill"
version: "1.0.0"
skill_id: "skill-topic"
description: "引导用户完成从模糊研究兴趣到精确研究问题的结构化选题推演"
stages_handled: [topic]
required_mcp: []
---

## Skill 定位

专门负责**引导用户完成从模糊研究兴趣到精确研究问题**的全流程选题推演。

**不负责**：文献检索、实证分析、论文写作等后续阶段

---

## 输入输出接口

### 输入 (来自协调器)

```json
{
  "project_name": "项目名称",
  "project_path": "papers/<project-name>/",
  "entry_point": "new|resume|jump",
  "user_intent": "用户初始意图描述",
  "resume_context": {
    "last_step": "5w1h_what|gap_analysis|...",
    "partial_results": {}
  }
}
```

### 输出 (传递给下一个 Skill)

```json
{
  "status": "completed|partial|user_intervention",
  "stage": "topic",
  "research_proposal": {
    "title": "研究题目",
    "research_question": "SMART 精确研究问题",
    "hypotheses": ["H1", "H2"],
    "variables": {
      "y_var": {"name": "", "definition": "", "expected_sign": ""},
      "d_var": {"name": "", "definition": "", "expected_sign": ""},
      "control_vars": []
    },
    "identification_strategy": "DID|FE|IV|RDD|OLS",
    "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"]
  },
  "artifacts": [
    "topics/01_5w1h.md",
    "topics/02_gap_analysis.md",
    "topics/03_research_question.md",
    "topics/00_research_proposal.md"
  ],
  "next_skill": "literature"
}
```

---

## 工作流程

### Step 0: 入口判断

根据协调器传入的 `entry_point` 决定入口：

- **new**：全新项目 → 从 5W1H What 开始
- **resume**：恢复项目 → 从 `last_step` 继续
- **jump**：跳转进入 → 执行快速确认清单

### Step 1: 5W1H 逐维引导（必须逐维，不能一次问完）

**What** → **Why** → **Who** → **When** → **Where** → **How**

每一步用户回答后，保存对话记录到 `topics/01_5w1h.md`，然后进入下一维度。

全部完成后，生成 **5W1H 推演摘要表**。

### Step 2: 研究空白分析 (Gap Analysis)

自动评估 5 类空白：
- 文献空白（基于关键词初步检索）
- 方法空白（内生性问题）
- 数据空白（数据可得性）
- 政策空白（准自然实验）
- 跨学科空白（交叉领域）

生成**决策矩阵**（重要性/新颖性/可行性 1-5 分），保存到 `topics/02_gap_analysis.md`。

### Step 3: SMART 研究问题精确化

逐项引导用户确认：
- S (Specific): 总体、D、Y、方法具体明确
- M (Measurable): 变量可量化，数据可得
- A (Achievable): 方法在能力范围内
- R (Relevant): 有学术/政策价值
- T (Time-bound): 数据频率明确

明确研究假设、核心变量、识别策略，保存到 `topics/03_research_question.md`。

### Step 4: 整合选题分析报告

自动生成完整研究方案到 `topics/00_research_proposal.md`，让用户确认后通知协调器切换到 `literature`。

**⚠️ 确认后必须执行以下操作将产出持久化到 context_store：**

```bash
# 写入核心变量
python ../scripts/pipeline.py set-context topic research_question "研究问题一句话"
python ../scripts/pipeline.py set-context topic y_var "变量名"
python ../scripts/pipeline.py set-context topic d_var "变量名"
python ../scripts/pipeline.py set-context topic y_label "中文标签"
python ../scripts/pipeline.py set-context topic d_label "中文标签"
python ../scripts/pipeline.py set-context topic control_vars "v1 v2 v3"
python ../scripts/pipeline.py set-context topic identification "FE/DID/IV"
python ../scripts/pipeline.py set-context topic id_var "企业ID变量"
python ../scripts/pipeline.py set-context topic year_var "年份变量"

# 写入中介变量（如有）
python ../scripts/pipeline.py set-context topic m1_var "中介变量1"
python ../scripts/pipeline.py set-context topic m2_var "中介变量2"

# 初始化项目配置（生成 project_config.json）
python ../scripts/pipeline.py init-config
```

这样后续的 literature/stata/latex Skill 都可以直接从 context_store 获取变量映射，无需重新询问用户。

---

## 人机协作点

✅ **必须用户确认后才能继续** 的节点：
1. 5W1H 推演摘要表确认
2. Gap Analysis 决策矩阵确认
3. 最终研究问题和假设确认
4. 选题分析报告整体确认

💬 **对话规则**：
- 每次只问一个问题，聚焦当前维度
- 追问不超过 3 句话
- 用表格展示结构化结果

---

## 产出文件规范

所有文件写入 `papers/<project-name>/topics/` 目录：

| 文件 | 内容 | 格式要求 |
|------|------|---------|
| `01_5w1h.md` | 5W1H 对话记录 + 推演摘要表 | Markdown，含原始对话 |
| `02_gap_analysis.md` | 5 类空白评估 + 决策矩阵 + 推荐方向 | 矩阵必须是 Markdown 表格 |
| `03_research_question.md` | SMART 逐项确认 + 研究假设 + 变量定义 | 变量必须明确预期符号 |
| `00_research_proposal.md` | 完整研究方案 | 结构：动机→5W1H→空白→问题→识别→数据→贡献 |

---

## 快速入口（从其他阶段跳转过来）

如果用户跳过选题直接开始，必须先问 **2 个问题**：
1. "你的核心研究问题是什么？一句话描述"
2. "3-5 个关键词是什么？"

获得回答后，生成最简版 `00_research_proposal.md`，然后通知协调器切换。