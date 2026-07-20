# 论文助手 — Paper Assistant for Coding Agents

> 面向经济学与社会科学实证研究、运行于 Claude Code、Codex、Kiro、Cursor、OpenCode 等 Coding Agent 的主动式研究协作 Skill。

论文助手会读取项目中的研究问题、文献、数据、实证结果和论文草稿，判断当前完成度、阻塞项与风险，并协助推进选题灵感、方向验证、文献搜索、数据搜集、实证分析和论文写作。

## 一句话安装

将下面这段话完整复制给你的 Coding Agent：

```text
请为我安装并初始化“论文助手”：https://github.com/DGU-stallion/economic-paper-pipeline

请先读取仓库中的 AGENT_INSTALL.md，检测我的操作系统、Agent 类型和现有环境；安装或更新论文助手及 Standard 实证分析环境；检测可用的搜索、MCP 和 LaTeX 能力；最后运行 Doctor 和安装测试，并向我报告已启用能力、未启用能力及原因。未经我确认，不要安装大型系统软件，不要修改全局配置，不要上传我的论文、数据或密钥，也不要让我手动执行你能够安全完成的命令。
```

Agent 安装完成后，你可以直接说：

```text
检查我当前的论文状态，告诉我最应该推进的三件事。
```

详细安装安全边界和验证步骤见 [`AGENT_INSTALL.md`](AGENT_INSTALL.md)。

[![Version](https://img.shields.io/badge/version-4.2.0-blue)](https://github.com/DGU-stallion/economic-paper-pipeline)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Skill](https://img.shields.io/badge/AI%20Skill-portable-orange)](CLAUDE.md)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![PanelOLS](https://img.shields.io/badge/linearmodels-7.0%2B-purple)](https://bashtage.github.io/linearmodels/)

---

## 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [使用方式](#使用方式)
- [工作流详解](#工作流详解)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [内置演示](#内置演示)
- [许可证](#许可证)
- [贡献指南](#贡献指南)

---

## 项目简介

本项目是一套**经济学实证论文写作 AI Skill**，以 `CLAUDE.md` 作为可移植技能契约，定义了 8 项核心能力及其输入输出规范。支持多种使用方式：

| 使用方式 | 说明 |
|---------|------|
| **AI Skill 加载** | 任意支持 Skill 机制的 AI 工具（OpenCode、Claude Code 等）加载 `CLAUDE.md`，获得完整的论文写作能力 |
| **Python 后端** | 内置 Python 分析引擎（linearmodels PanelOLS），自动检测可用依赖，执行真实回归分析并输出 LaTeX 表格 |
| **LLM-only 降级** | 无 Python 环境时自动降级为纯对话引导 + 模板生成，仍然可用 |
| **CLI 直接调用** | `scripts/pipeline.py` 提供 12 个子命令，支持脚本化运行 |

### 设计原则

1. **不绑定特定 AI 工具** — 核心契约是 `CLAUDE.md`，任何支持 skill 的系统均可加载
2. **不假设 Shell 命令** — 所有操作通过自然语言或 Python API 完成
3. **不硬编码路径** — 所有路径从 `PROJECT_ROOT` 派生，适应不同项目布局
4. **后端自动检测** — `scripts/backends/__init__.py` → `detect()` 返回可用能力，AI 据此决策（linearmodels / statsmodels / pandas / pyfixest / thrreg / stata）

---

## 核心特性

### 🗣️ 纯自然语言交互

研究者说中文，AI 自动执行：

| 你说 | 能力 | AI 自动做 |
|------|------|----------|
| "我有个想法" | Conceptualize | 5W1H 逐维引导 → Gap 识别 → SMART 问题 → 研究方案 |
| "帮我搜文献和数据" | Research | 搜索候选论文 + 数据源可行性报告（Tavily search/extract/crawl + paper-search-mcp） |
| "写文献综述" | Literature | 筛选论文 → 脉络梳理 → 综述正文 + .bib |
| "洗一下数据" | Data | 格式识别 → 缺失异常处理 → 清洗验证 → 质量报告 |
| "跑回归" | Analyze | 面板固定效应回归 → .tex 表格输出（linearmodels / pyfixest 双后端） |
| "结果稳不稳" | Verify | 稳健性检验套件（替换变量/改变窗口/安慰剂） |
| "帮我写论文" | Write | 整合所有产出 → 完整 LaTeX 论文（含引用验证 + 写作指南知识库） |
| "编译" | Format | XeLaTeX × 3 + biber + Humanizer 质检 |

### 🧠 分层记忆架构

用结构化状态替代对话历史，大幅节省 token：

```
Tier 1: pipeline_state.json（~200 tokens）
  → 当前阶段 + 一句话摘要
Tier 2: context_store（~500 tokens）
  → Y/D/X 变量映射 / 假设验证 / 决策记录 / 实证摘要
Tier 3: context/<stage>.md（~300 tokens）
  → 该阶段的输入 / 已完成 / 待决策 / 下游需要
```

各阶段通过 `context_store` 自动传递上下文。选题阶段确定的 Y/D/X 变量，分析和 LaTeX 阶段直接读取，无需重复询问。

### 🔐 阶段门禁与健壮性保障

- **前置检查**：进入分析阶段自动检查 Y/D 变量和清洗后数据
- **缺失友好提示**：明确告知缺什么、去哪补
- **增量执行**：数据未变则跳过重跑
- **状态回退**：`undo` 回到上一步，保留中间文件

### 🐍 Python 后端，自动降级

```
detect() → {python_analysis, linearmodels, statsmodels, pandas}
```

- Python 环境就绪 → 真实回归分析，输出 .tex 表格
- 无 Python → LLM-only 降级，纯对话生成结果模板

支持模型：
- 面板固定效应（PanelOLS EntityEffects + TimeEffects，支持 linearmodels 和 pyfixest 双后端）
- 双重差分（DID 交互项法）
- 门槛回归（Hansen 1999 网格搜索）
- 异质性分析（分组回归 / 交互项）
- 稳健性检验（替换变量 / 改变窗口 / 安慰剂 / 排除极端值）

### 🔍 Humanizer-ZH 中文 AI 痕迹检测

- 破折号滥用检测
- 句式单一性检查
- 被动语态 / 欧化句式检测
- 写作中逐节质检 + 最终汇总报告

---

## 快速开始

### 方式一：AI Skill 加载（推荐）

本项目核心交付物是 `CLAUDE.md` — 一份可移植的 AI Skill 契约。支持 Skill 机制的 AI 工具均可加载：

```bash
# 克隆仓库
git clone https://github.com/DGU-stallion/economic-paper-pipeline.git
cd economic-paper-pipeline

# 在你的 AI 工具中加载该目录（工具会自动读取 CLAUDE.md）
# OpenCode:  opencode .
# Claude Code: claude .
```

然后直接用自然语言开始：
```
"帮我创建一篇关于数字经济与就业结构的研究"
```

### 方式二：带 Python 后端（推荐，有回归能力）

```bash
pip install pandas numpy statsmodels linearmodels openpyxl

# 验证后端就绪
python3 -c "
from scripts.backends import detect
caps = detect()
print('Python 分析后端可用' if caps['python_analysis'] else '需安装 linearmodels')
"
```

有 Python 后端时：
- 面板回归自动执行，结果输出 .tex 表格
- 数据清洗自动运行
- 门槛回归、稳健性检验全部自动化

无 Python 后端时自动降级为 LLM-only，仍然可以使用全部 8 项能力，回归结果以模板形式呈现。

### 方式三：CLI 直接调用

不依赖 AI 工具，直接使用 Python 管线：

```bash
python3 scripts/pipeline.py list          # 列出项目
python3 scripts/pipeline.py new my-paper  # 创建项目
python3 scripts/pipeline.py status        # 查看状态
python3 scripts/pipeline.py cleanup       # 清理编译垃圾
```

---

## 使用方式

### 自然语言交互（AI Skill 模式）

加载 `CLAUDE.md` 后，以下自然语言触发对应能力：

| 你说 | 触发能力 | 所需上游 |
|------|---------|---------|
| "我有个想法，想研究 XX" | Conceptualize | — |
| "帮我搜一下相关文献" | Research | research_question |
| "写文献综述" | Literature | candidate_papers |
| "洗一下数据" | Data | raw_data_path |
| "跑回归" | Analyze | clean_data_path, Y/D 变量 |
| "结果稳不稳" | Verify | baseline 结果 |
| "帮我写论文" | Write | 所有上游产出 |
| "编译" | Format | tex_path |

每步进入前自动检查上游字段是否就绪，缺则追问。

### 8 项能力详解

| 能力 | 用户说 | 输入 | 输出 |
|------|--------|------|------|
| **Conceptualize** 概念引导 | "我有个想法" | 模糊想法 | 研究方案 (Y/D/假设) |
| **Research** 调研搜索 | "帮我搜文献和数据" | 研究问题 | 候选论文 + 数据源报告 |
| **Literature** 综述撰写 | "写文献综述" | 候选论文 | 综述 + .bib |
| **Data** 数据清洗 | "洗一下数据" | 原始 csv/xlsx/dta | 清洗后数据 + 质量报告 |
| **Analyze** 实证分析 | "跑回归" | 数据 + 模型设定 | 回归表格 .tex |
| **Verify** 稳健性检验 | "结果稳不稳" | 基准结果 | 稳健性检验套件 |
| **Write** 论文撰写 | "帮我写论文" | 表格 + 综述 | 完整 .tex |
| **Format** 格式编译 | "编译" | .tex 源码 | .pdf |

### 完整示例对话

```
你：我有个想法，想研究数字化转型对企业绩效的影响

→ Conceptualize 能力激活
→ 5W1H 逐维引导
目标产出：research_question, y_var（ROA）, d_var（数字化投入占比）, identification（FE）

你：帮我搜一下相关文献

→ Research 能力激活
→ 搜索论文 + 数据源
目标产出：candidate_papers, data_sources

你：写文献综述

→ Literature 能力激活
→ 筛选 → 脉络梳理 → 综述正文 + .bib
目标产出：literature_review.md, references.bib

你：我这里有数据，data.csv

→ Data 能力激活
→ pandas 清洗 → 描述性统计 → 验证
目标产出：clean_data.csv, data_quality_report.md

你：跑回归

→ Analyze 能力激活
→ PanelOLS 双向固定效应 → .tex 表格
目标产出：analysis/output/baseline.tex

你：结果稳不稳

→ Verify 能力激活
→ 替换变量 / 改变窗口 / 安慰剂检验
目标产出：robustness_summary.tex

你：帮我写论文

→ Write 能力激活
→ 整合所有产出 → 完整 7 章节 LaTeX
目标产出：paper/main.tex

你：编译

→ Format 能力激活
→ XeLaTeX × 3 + biber → Humanizer 质检
目标产出：paper/main.pdf
```

---

## 工作流详解

### 状态机

```
topic → literature → data → analyze → verify → conclusion → paper
```

每个阶段通过 `pipeline_state.json` 跟踪状态，`context_store` 传递上下文变量。

### 阶段 1：概念引导（Conceptualize）

**自动化程度**：半自动（需研究者参与）

5W1H 逐维引导：

| 维度 | 引导问题 | 产出 |
|------|---------|------|
| What | 研究什么具体经济问题？ | 研究问题陈述 |
| Why | 为什么重要？理论/政策意义？ | 研究动机 |
| Who | 研究对象？群体/企业/地区？ | 研究对象 |
| When | 什么时间段？ | 时间窗口 |
| Where | 哪个地域/市场？ | 地域范围 |
| How | 用什么方法识别因果？ | 识别策略 |

**产出**：research_question, y_var, d_var, identification, hypotheses, control_vars

示例：
```
研究问题：数字经济发展对省际就业结构的影响
Y：tertiary_employment_share（第三产业就业占比）
D：digital_economy_index（数字经济发展指数）
识别：面板固定效应 + 门槛回归
假设：
  H1: 数字经济显著提升第三产业就业占比
  H2: 存在人力资本门槛效应
控制：人均 GDP、城镇化率、教育投入、产业结构
```

### 阶段 2：调研搜索（Research）

**自动化**：自动（需 web-access）

文献搜索 + 数据源搜索并行 → 候选论文列表 + 可行性报告

### 阶段 3：文献综述（Literature）

**自动化**：自动 + 确认

筛选 → 脉络梳理 → 综述正文 → BibTeX

### 阶段 4：数据清洗（Data）

**自动化**：自动

```
读取（csv/xlsx/dta）→ 类型检测 → 缺失诊断 → 异常处理 → 描述统计 → 导出
```

### 阶段 5：实证分析（Analyze）

**自动化**：自动

| 分析 | 方法 | 产出 |
|------|------|------|
| 基准回归 | PanelOLS 双向固定效应 | baseline.tex |
| 双重差分 | DID 交互项 | did.tex |
| 门槛回归 | Hansen 1999 网格搜索 | threshold.tex |
| 异质性 | 分组回归 / 交互项 | heterogeneity.tex |

### 阶段 6：稳健性检验（Verify）

**自动化**：自动

| 检验 | 方法 |
|------|------|
| 替换测度 | 替换 Y 或 D 度量方式 |
| 改变窗口 | 缩短/延长样本期间 |
| 安慰剂 | 随机分配处理组 |
| 替换聚类 | 不同层面聚类标准误 |
| 排除极端值 | 剔除 1%-5% 样本 |

### 阶段 7：论文撰写（Write）

**自动化**：自动

整合上游产出 → 生成 7 章节 LaTeX：
1. 摘要
2. 引言
3. 文献综述
4. 研究设计
5. 实证结果
6. 稳健性检验
7. 结论

### 阶段 8：格式编译（Format）

**自动化**：自动

```
XeLaTeX → biber → XeLaTeX → XeLaTeX → Humanizer 质检
```

---

## 项目结构

```
economic-paper-pipeline/
├── CLAUDE.md                         # AI Skill 契约（核心交付物）
│                                      # 8 能力定义 + 后端检测 + 行为准则
│
├── scripts/                          # Python 后端实现
│   ├── pipeline.py                   # CLI 入口（12 子命令）
│   ├── orchestrator.py               # 编排器：状态机 + 模块路由
│   ├── shared/                       # 共享层
│   │   ├── paths.py                  #   路径中心化
│   │   ├── state.py                  #   pipeline_state 读写
│   │   ├── registry.py               #   模块注册表 + 依赖推导
│   │   └── contract.py               #   ModuleContract 契约
│   ├── backends/                     # 后端检测 + 分析引擎
│   │   ├── __init__.py               #   detect() 能力检测（linearmodels/pyfixest/stata/thrreg）
│   │   ├── python_analysis.py        #   PanelOLS / pyfixest / DID / 异质性
│   │   ├── python_verify.py          #   稳健性检验套件
│   │   └── python_threshold.py       #   Hansen 门槛回归（可选 thrreg 桥接）
│   └── modules/                      # 8 模块（对应 CLAUDE.md 8 能力）
│       ├── conceptualize/            #   概念引导
│       ├── research/                 #   调研搜索（Tavily search/extract/crawl/map）
│       ├── literature/               #   文献综述
│       ├── data/                     #   数据清洗
│       ├── analyze/                  #   实证分析
│       ├── verify/                   #   稳健性检验
│       ├── write/                    #   论文撰写
│       │   ├── citation_validate.py  #   引用验证（DOI 格式 + Crossref API + 去重）
│       │   └── writing_guide.md      #   经济学写作指南（Cochrane/McCloskey 等 50+ 指南核要）
│       └── format/                   #   格式编译
│
├── papers/                           # 论文项目（每个独立状态）
│   ├── demo-paper/                   #   内置演示
│   └── <项目名>/
│       ├── pipeline_state.json       #   状态 + context_store
│       ├── project_config.json       #   变量映射
│       ├── topics/                   #   选题产出
│       ├── literature/               #   综述 + .bib
│       ├── data/                     #   raw/clean/scripts
│       ├── analysis/                 #   output/（.tex 表格）
│       └── paper/                    #   .tex + .pdf
│
├── .claude-plugin/                   # Claude Code 集成（可选）
│   └── plugin.json
├── commands/                         # /econ-* 斜杠命令
├── hooks/                            # 生命周期钩子
├── templates/                        # 论文/数据/分析模板
├── tests/                            # E2E 测试
│   ├── run_tests.py
│   └── fixtures/
├── .mcp.json                         # MCP 服务器配置（可选）
└── .config/                          # 当前项目配置
```

### 关键文件说明

| 文件 | 作用 |
|------|------|
| `CLAUDE.md` | **核心交付物**。可移植 AI Skill 契约，定义 8 能力、后端检测、行为准则。任何支持 skill 的 AI 工具读取此文件获得完整能力 |
| `scripts/backends/__init__.py` | `detect()` 返回可用能力字典（linearmodels/pyfixest/stata/thrreg），AI 据此决策 |
| `scripts/backends/python_analysis.py` | 分析后端，支持 linearmodels + pyfixest 双引擎 |
| `scripts/modules/write/citation_validate.py` | 引用验证（DOI 格式校验 + Crossref API + 去重） |
| `scripts/modules/write/writing_guide.md` | 经济学写作指南知识库（Cochrane/McCloskey 等 50+ 指南） |
| `scripts/pipeline.py` | CLI 入口，不依赖 AI 工具时直接调用 |
| `papers/<name>/pipeline_state.json` | 每个项目的持久化状态 + context_store |

---

## 开发指南

### 运行测试

```bash
python3 tests/run_tests.py
```

覆盖：FE 面板回归、DID、LaTeX 编译可用性、cleanup 命令。

### 扩展新能力

`CLAUDE.md` 中定义了 8 项能力。新增能力只需：

1. 在 `scripts/modules/` 下创建模块目录
2. 实现模块（`core.py` + `__init__.py`）
3. 在 `CLAUDE.md` 能力清单中添加一行
4. 在 `shared/registry.py` 注册
5. 在 `orchestrator.py` 状态机中添加阶段

### 后端替换

`scripts/backends/` 下的后端可独立替换：

- 每个后端通过 `detect()` 报告可用性
- 分析后端输出统一为 .tex 表格格式
- 可添加 R、Julia 等后端（需实现对应 `detect()` + 分析函数）

### 适配不同 AI 工具

本项目核心是 `CLAUDE.md` 中定义的 Skill 契约。适配不同 AI 工具：

- **OpenCode**：直接加载目录，自动读取 `CLAUDE.md`
- **Claude Code**：通过 `.claude-plugin/` 插件机制集成
- **其他支持 Skill 的工具**：加载 `CLAUDE.md` 即可获得能力定义
- **纯 CLI 环境**：直接使用 `scripts/pipeline.py`

---

## 内置演示

**数字经济发展对省际就业结构的影响——基于面板门槛模型的实证研究**

| 维度 | 内容 |
|------|------|
| 模型 | 面板固定效应 + Hansen 门槛回归 |
| 数据 | 31 省份 2011-2023，N=403 |
| 基准 | D=0.3374***（t=4.02） |
| 论文 | 完整 7 章节，17 页 PDF，0 编译错误 |

使用：
```
加载目录后直接说：
"看看演示项目"
"编译论文"
```

---

## 许可证

MIT License。详见 [LICENSE](LICENSE)。

---

## 贡献指南

欢迎 Issue 和 PR！优先方向：

- **新增识别策略**：RDD、IV、合成控制法
- **新增数据源接口**：CSMAR、Wind、CNRDS
- **扩展检验套件**：PSM-DID、Bacon decomposition
- **引用验证增强**：完善 Crossref / OpenAlex / Semantic Scholar API 集成
- **分析后端扩展**：Stata MCP、R pyfixest 后端
- **适配更多 AI 工具**：补充其他 AI 平台的 Skill 加载说明

提交 PR 前：
1. `python3 tests/run_tests.py` 确认无回归
2. 更新 `CLAUDE.md` 与实现保持一致
3. 遵循 `ModuleContract` 契约模式
