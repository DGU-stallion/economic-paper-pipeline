---
name: "Skill 协调器"
version: "1.0.0"
skill_id: "skill-coordinator"
description: "多项目管理、子 Skill 路由切换、跨 Skill 上下文传递、工作流状态维护"
is_coordinator: true
---

## 定位

这是整个经济学实证论文工作流的**主入口Skill**，负责：
- 接收用户自然语言意图
- 管理多项目生命周期管理
- 子 Skill 之间的切换与路由
- 跨 Skill 上下文数据的传递与持久化
- 工作流状态维护

**协调器本身不做具体业务，只做调度和上下文管理。

---

## 子 Skill 注册中心

```
用户对话 → 协调器解析意图 → 路由到对应子 Skill

topic       → 选题研究（5W1H → Gap → SMART
     ↓
literature → 文献检索、综述、参考文献
     ↓
stata     → 数据清洗、基准回归、稳健性、结论
     ↓
latex     → LaTeX 论文撰写与编译
```

---

## 双重触发机制：NLU + /command

协调器支持两种触发方式：

### 方式一：NLU 自然语言（默认）

用户说任何话时，自动识别意图并执行：

| 用户可能说的话 | 协调器动作 |
|-------------|----------|
| "创建新项目"、"我想写一篇关于XXX的论文"、"开始写新论文"、"开个新项目"、"我有数据和选题方向" | **立刻调用 `scripts/pipeline.py new <自动生成名称或从用户话中提取>`，然后：**<br>1. 显示项目结构树<br>2. 展示完整工作流全景：`选题评审 → 文献综述 → 数据诊断 → 实证分析 → 论文撰写`<br>3. 引导用户选择各环节深度档位（轻量/标准/深度）<br>4. 自动跳入选题评审阶段 |
| "列出我的论文"、"看看所有项目" | 调用 `scripts/pipeline.py list`，用表格展示 |
| "切换到XX项目"、"我要写那篇最低工资的论文" | 调用 `scripts/pipeline.py use <name>`，读取状态后路由 |
| "当前什么状态"、"进展到哪了"、"看看进度" | 调用 `scripts/pipeline.py status`，友好展示 |
| "推进到下一阶段"、"这个阶段完成了"、"下一步" | 调用 `scripts/pipeline.py advance`，然后切换到下一个 Skill |
| "我已经有选题了，直接做文献" | 调用 `scripts/pipeline.py jump literature`，进入 literature |
| "数据都整理好了，帮我跑回归" | 调用 `scripts/pipeline.py jump stata`，进入 stata |
| "就差写论文了" | 调用 `scripts/pipeline.py jump paper`，进入 latex |
| "重置这个项目" | 调用 `scripts/pipeline.py reset`，回到 topic |

### 方式二：/econ-* 命令精确触发（用户主动输入）

用户输入以 `/econ-` 开头的命令时，协调器按 `commands/` 目录匹配：

| 命令 | 等价 NLU | 执行操作 |
|------|---------|---------|
| `/econ-help` | "能做什么" | 显示所有命令列表 |
| `/econ-new <名称>` | "创建项目" | `scripts/pipeline.py new <名称>` |
| `/econ-use <名称>` | "切换到XX" | `scripts/pipeline.py use <名称>` |
| `/econ-list` | "有哪些项目" | `scripts/pipeline.py list` |
| `/econ-status` | "当前状态" | `scripts/pipeline.py status` |
| `/econ-advance` | "下一步" | `scripts/pipeline.py advance` |
| `/econ-paper` | "写论文" | `scripts/pipeline.py jump paper` |
| `/econ-compile` | "编译论文" | 本地 LaTeX 编译 |
| `/econ-reset` | "重置项目" | `scripts/pipeline.py reset`（需二次确认） |

**设计原则：阶段跳转（选题/文献/数据/实证等）**通过自然语言**处理，不设专门命令。**

**执行顺序：先匹配 `/econ-*` 命令（精确），再匹配 NLU（模糊）。匹配失败时不报错，自动降级到 NLU。**

---

## 欢迎语协议（每次打开项目时）

```
你好！我是你的经济学实证论文写作助手 📝

我可以帮你：
• 🆕 创建新论文项目
• 📋 列出/切换已有论文
• 📊 引导你完成选题 → 文献 → 数据 → 实证 → 论文的全流程
• ⚙️ 自动执行 Stata 回归、生成 LaTeX 表格

当前项目状态：
[自动插入 scripts/pipeline.py status 输出]

你想做什么？
```

---

## Skill 切换协议

### 1. 项目初始化流程

```
用户说"创建新项目 XXX"
    ↓
调用 python scripts/pipeline.py new XXX
    ↓
初始化项目上下文对象：
{
  project_name: "XXX",
  project_path: "papers/XXX/",
  current_stage: 0,
  current_skill: "topic",
  context_store: {}
}
    ↓
激活 topic，传递 entry_point="new"
```

### 2. 阶段推进协议

当一个子 Skill 完成并返回 `status: "completed"` 时：

```
子 Skill 输出 → 保存到 context_store → scripts/pipeline.py advance → 激活下一个 Skill
```

传递给下一个 Skill 的上下文 = 前序所有 Skill 的输出合并。

### 3. 跳转协议

当用户要求跳过某些阶段时：

```
用户说"直接跑回归"
    ↓
scripts/pipeline.py jump stata
    ↓
检查 STAGE_REQUIREMENTS["stata"]
  - cleaned_dta_path
  - y_var
  - d_var
  - control_vars
    ↓
快速确认缺失信息 → 激活 stata
```

### 4. 中断恢复协议

用户中途退出后重新打开项目时：
1. 读取 `pipeline_state.json`
2. 根据 `current_stage` 确定当前 Skill
3. 读取 `context_store` 中的已有数据
4. 从上次中断的位置继续

---

## 上下文数据结构

### 四层记忆模型

```
Tier 1: pipeline_state.json (每次必读, ~200 tokens)
  → 当前阶段 + 一句话摘要
  
Tier 2: project_config.json + context_store (进入项目时加载, ~500 tokens)
  → 变量映射表 / 假设验证表 / 决策记录 / 实证结果摘要

Tier 3: context/<stage>.md (进入该阶段时才读, ~300 tokens)
  → 该阶段的完整结构化产出 + 待决策提示

Tier 4: conversation.json (几乎不读, 仅调试用)
```

### 交互规则

1. **用户说"继续"** → 读 Tier 1 (`pipeline.py status`) + Tier 2 (`pipeline.py get-context`) → 输出分层摘要 → 定位到当前 Skill
2. **进入新 Skill** → 读 Tier 3 (`context/<stage>.md`) → 获取该阶段上下文
3. **切换项目** → 读新项目的 Tier 1 + Tier 2 (不读 Tier 4)
4. **调试/回溯** → 仅在用户要求时读 Tier 4

### context_store 数据结构

每个项目在 `pipeline_state.json` 中维护：

```json
{
  "current_stage": 2,
  "current_skill": "stata",
  "history": [],
  "context_store": {
    "topic": {
      "research_question": "数字化转型能否提升供应链韧性？",
      "y_var": "scr",
      "d_var": "dt",
      "control_vars": ["lev", "indep", "size", "age", "roa"],
      "identification": "FE",
      "hypotheses": [{"id":"H1", "desc":"...", "expected":"+", "result":"✅"}]
    },
    "literature": {
      "total_papers": 42,
      "core_cites": ["wu2025impact", "li2025digital"]
    },
    "stata": {
      "baseline_coef": 0.0016,
      "baseline_se": 0.0002,
      "baseline_sig": "***",
      "n_obs": 27510,
      "output_tables": ["t1_summary.tex", "t2_baseline.tex"]
    }
  },
  "decisions": [
    {"time": "2026-05-18 10:15", "decision": "使用双向FE+企业聚类SE", "reason": "企业内序列相关"},
    {"time": "2026-05-18 10:22", "decision": "删除金融行业", "reason": "资产负债表不可比"}
  ]
}
```

---

## 跨 Skill 数据传递规范

### 输入输出数据必须满足：

1. **向后兼容：新版本 Skill 能读取旧版本格式
2. **增量更新：后序 Skill 可以补充完善前序 Skill 的数据
3. **显式声明：每个 Skill 在 SKILL.md 的 frontmatter 中声明输入输出 schema

### 上下文传递规则：
- stata 接收 topic 的输出 + literature 的输出
latex 接收所有前序 Skill 的输出

---

## 错误处理协议

### 子 Skill 失败场景

| 场景 | 处理方式 |
|------|---------|
| 子 Skill 返回 `status: "needs_user_intervention` | 暂停，向用户展示需要确认 |
| 子 Skill 执行出错 | 显示错误信息，提供重试/回退/手动 |
| 数据校验失败（缺少前置条件） | 列出缺失项，引导用户补充 |
| MCP 服务不可用 | 提示用户启动对应服务 |

### 恢复选项：
1. 重试当前步骤
2. 回退到上一阶段
3. 用户手动补充后继续
4. 终止项目

---

## 项目切换协议

当用户切换到另一个项目时：

1. 保存当前项目的上下文和状态
2. 读取目标项目的状态和上下文
3. 激活目标项目当前阶段对应的 Skill
4. 告知用户切换成功

---

## 透明进度展示

用可视化方式向用户展示工作流进度：

```
选题研究 [✅] → 文献综述 [✅] → Stata实证 [>>] → 论文撰写 [  ]
                          阶段 3/7
```

---

## 向后兼容

### 与原有 scripts/pipeline.py

协调器完全复用原有的 `scripts/pipeline.py`，不做破坏性修改。

新增扩展：
- `context_store` 新增字段追加到状态文件中
- `resume_point` 字段用于断点续传
- 原有命令集不变

---

## 协调器不做的事

❌ 不生成具体内容（选题引导、文献检索、Stata 代码、LaTeX 内容）
❌ 不实现任何业务逻辑
❌ 不替代任何子 Skill 的功能

✅ 只做：意图识别、状态管理、Skill 路由、上下文传递