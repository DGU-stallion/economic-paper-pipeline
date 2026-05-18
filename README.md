# 经济学实证论文自动化工作流

> **Claude Code Plugin** — 纯对话式 AI 协作工具，覆盖选题、文献综述、Stata 实证、稳健性检验、LaTeX 论文撰写全流程。

[![Version](https://img.shields.io/badge/version-3.0.0-blue)](https://github.com/DGU-stallion/economic-paper-pipeline)
[![Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-purple)](https://claude.ai/install.sh)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🚀 安装

### 前提条件
- [Claude Code](https://claude.ai/install.sh)（最新版）
- 可选：StataMP 18（用于实证回归）、TeX Live（用于本地 LaTeX 编译）

### 安装方式一：全局安装（推荐）

作为 Claude Code 全局插件安装，任何目录下都可使用：

```text
/plugin marketplace add DGU-stallion/economic-paper-pipeline
/plugin install economic-paper-pipeline
```

**文件存放**：论文项目创建在你**启动 Claude Code 时的目录**下的 `papers/` 文件夹。

### 安装方式二：本地开发模式

```bash
git clone https://github.com/DGU-stallion/economic-paper-pipeline.git
cd economic-paper-pipeline
claude .  # 在项目目录内启动 Claude Code
```

**文件存放**：论文项目创建在仓库根目录的 `papers/` 文件夹内。

验证安装：输入 `/econ-help`，能看到命令列表即安装成功。

---

## 🗣️ 纯对话式，零命令

用户永远不说 Python 命令，只说自然语言：

| 你说一句话 | Agent 自动做的事 |
|-----------|----------------|
| "帮我创建一篇关于最低工资与企业就业的论文" | 创建项目，进入选题引导 |
| "我有哪些论文项目？" | 列出所有项目进度表格 |
| "切换到数字经济那篇论文" | 激活对应项目，显示当前阶段 |
| "现在进展到哪了？" | 展示分层上下文摘要（已完成 + 待决策 + 最近决策） |
| "跑回归" | 从 `project_config.json` 读取变量映射，生成 .do 文件，执行 Stata |
| "回退到上一步" | 撤销当前状态，回到上一状态，保留中间结果 |
| "写论文" | 从 `context_store` 获取所有上游产出，生成完整 LaTeX 论文 |
| "编译论文" | 健壮编译链 `xelatex → biber → xelatex → xelatex`，日志落地 |

也可以精确使用 `/econ-*` 命令：`/econ-status`、`/econ-stata`、`/econ-paper` 等。

---

## 🧠 分层记忆架构（V3 核心）

管线采用四层记忆模型，LLM **每次只读最少的东西**，用结构化数据替代对话历史：

```
Tier 1: pipeline_state.json  (每次必读, ~200 tokens)
  → 当前阶段 + 一句话摘要

Tier 2: project_config.json + context_store (进入项目时加载, ~500 tokens)
  → 变量映射表 / 假设验证表 / 决策记录 / 实证结果摘要

Tier 3: context/<stage>.md (进入当前阶段时才读, ~300 tokens)
  → 该阶段的输入/已完成/待决策/下游需要

Tier 4: conversation.json (几乎不读, 仅调试用)
```

**结果**：每次 "继续" 从 ~7500 token 降到 ~1000 token，节省 **85%**。

各 Skill 通过 `context_store` 自动传递上下文。Topic 阶段确定的 Y/D/X 变量写入后，Stata 和 LaTeX 阶段直接读取，无需重新询问用户。

---

## 📊 工作流

```
选题研究 → 文献综述 → 数据清洗 → Stata实证 → 稳健性检验 → 结论验证 → LaTeX论文撰写
```

| 阶段 | 自动化程度 | 人机协作点 | Skill 文件 |
|------|-----------|-----------|-----------|
| 1. 选题研究 | 半自动 | 5W1H 逐维引导 → Gap → SMART | `skills/topic/SKILL.md` |
| 2. 文献综述 | 自动+确认 | MCP 检索，关键文献确认 | `skills/literature/SKILL.md` |
| 3. 数据清洗 | 自动 | 数据源确认 | `skills/stata/SKILL.md` |
| 4. Stata 实证 | 自动 | 模型设定、变量选择可确认 | `skills/stata/SKILL.md` |
| 5. 稳健性检验 | 自动 | 结果异常时反馈 | `skills/stata/SKILL.md` |
| 6. 结论验证 | 自动+确认 | 对比假设与结果 | `skills/stata/SKILL.md` |
| 7. LaTeX 论文 | 自动 | 偏好采集、编译方式选择 | `skills/latex/SKILL.md` |

**关键原则**：技术操作自动执行，研究决策节点可请求用户介入。状态机支持决策分支——基准回归不显著时自动引导回到模型设定而非盲目前进。

---

## 📁 目录结构

```
economic-paper-pipeline/
├── .claude-plugin/
│   └── plugin.json              # 插件清单
├── commands/                    # /econ-* 斜杠命令
│   ├── econ-help.md
│   ├── econ-status.md
│   ├── econ-new.md
│   ├── econ-use.md
│   ├── econ-list.md
│   ├── econ-paper.md
│   ├── econ-advance.md
│   ├── econ-reset.md
│   └── econ-compile.md
├── skills/                      # 子 Skill（自动发现）
│   ├── coordinator/SKILL.md     #   意图识别、路由、分层记忆协议
│   ├── topic/SKILL.md           #   选题研究（5W1H → Gap → SMART）
│   ├── literature/SKILL.md      #   文献综述（检索 → 摘要 → 综述 → .bib）
│   ├── stata/SKILL.md           #   Stata 实证（清洗 → 基准 → 中介 → 异质 → 稳健）
│   └── latex/SKILL.md           #   LaTeX 论文（模板 → 章节 → 表格注入 → 编译）
├── hooks/
│   └── hooks.json               # SessionStart 钩子
├── scripts/
│   ├── pipeline.py              #   状态机引擎（35 微状态 + 上下文管理 + 分层记忆）
│   ├── memory.py                #   对话记忆持久化
│   └── announce-plugin-loaded.sh
├── .mcp.json                    # MCP 服务器配置
├── CLAUDE.md                    # AI 协作主协议
├── papers/                      # 你的所有论文项目
│   └── <项目名>/
│       ├── project_config.json  #   变量映射表（Y/D/X/ID）
│       ├── pipeline_state.json  #   状态 + context_store + 决策记录
│       ├── context/             #   Tier 3 阶段上下文文件
│       │   ├── topic.md
│       │   ├── stata.md
│       │   └── paper.md
│       ├── topics/              #   选题产出
│       ├── literature/          #   文献综述产出
│       ├── data/                #   原始数据 + 清洗后数据
│       ├── analysis/            #   do-files + output tables
│       └── paper/               #   LaTeX 源码 + PDF
└── templates/                   # 论文模板（零硬编码，{{PLACEHOLDER}} 系统）
    ├── paper/                   #   LaTeX 模板（main.tex, .cls, sections/）
    ├── data/scripts/            #   数据清洗 do-file 模板
    └── analysis/do-files/       #   实证分析 do-file 模板
```

---

## 🎓 演示项目

内置完整论文：**企业数字化转型对供应链韧性的影响——基于中国A股上市公司的实证研究**

| 维度 | 内容 |
|------|------|
| **研究问题** | 企业数字化转型能否提升供应链韧性？传导机制是什么？ |
| **方法** | 双向固定效应 + 三步法中介效应 (Sobel) + 分组交互项异质性 |
| **数据** | 3,663 家上市公司 × 2015—2024 年，27,510 观测值 |
| **发现** | DT 对 SCR 有显著正向影响（β=0.0016, p<0.01），疫情后效应放大；三条中介路径均不显著——提示直接效应主导 |
| **状态** | ✅ 全部 7 阶段完成，14 页 PDF 已生成 |

查看项目：`/econ-use digital-supply-chain` → `/econ-status`

---

## 🔧 零外部依赖原则

所有 Stata do-file 模板仅使用 **Stata 内置命令**，无需安装任何 ssc 包：

| 替代方案 | 被替代的外部包 |
|---------|-------------|
| `xtreg ..., fe` | `reghdfe` |
| `_pctile` 手动缩尾 | `winsor2` |
| 手动计算 Sobel Z 值 | `sgmediation` |

> 仅 `estout` 为可选推荐（用于 LaTeX 表格输出）。

---

## 🤖 后台命令参考

用户无需手动运行，但了解后台机制有助于理解管线：

```bash
# 项目管理
python scripts/pipeline.py new <name>        # 创建项目
python scripts/pipeline.py use <name>        # 切换项目
python scripts/pipeline.py list              # 列出所有项目

# 状态控制
python scripts/pipeline.py status            # 分层上下文摘要
python scripts/pipeline.py advance           # 推进（支持 --branch <n> 决策分支）
python scripts/pipeline.py jump <stage>      # 跳转
python scripts/pipeline.py undo              # 回退到上一状态

# 上下文管理（分层记忆核心）
python scripts/pipeline.py init-config        # 从 context_store 生成 project_config.json
python scripts/pipeline.py set-context <s> <k> <v>  # 写入上下文
python scripts/pipeline.py get-context [s]    # 读取上下文
python scripts/pipeline.py context-stage [s]  # 生成 Tier 3 阶段上下文文件

# 论文工具
python scripts/pipeline.py compile           # 健壮 LaTeX 编译（日志落地，失败信息可见）
python scripts/pipeline.py wc                # 章节字数统计 + 告警
python scripts/pipeline.py cite-fix          # 纯文本引用自动转 \cite

# Stata 工具
python scripts/pipeline.py gen-do <type>     # 从模板生成 do-file（自动占位符替换）
python scripts/pipeline.py run-all           # 一键全流程（清洗→基准→中介→异质→稳健→编译）
python scripts/pipeline.py check-data        # 数据与代码一致性扫描
```

---

## 📦 使用自有数据

将数据文件放入项目的 `data/raw/` 目录，在选题阶段告诉 Agent：

> "使用 `data/raw/面板数据_2025.dta` 作为主数据，核心解释变量是 `digital`，被解释变量是 `emp_tertiary`"

选题完成后，管线自动生成 `project_config.json`（变量映射表），后续所有 do-file 从该配置自动读取变量名。**无需手动替换任何代码**。

---

## 🔧 技术栈

| 工具 | 用途 |
|------|------|
| **Python 3.12+** | 状态管理、上下文持久化、do-file 生成 |
| **StataMP 18** | 计量回归分析 |
| **LaTeX (XeLaTeX)** | 论文排版 |
| **MCP 协议** | Stata 执行、学术搜索引擎集成 |

### MCP 服务器

| 服务器 | 用途 |
|--------|------|
| [stata-mcp](https://github.com/SepineTam/stata-mcp) | 操作本地 StataMP 18 |
| [paper-search-mcp](https://github.com/openags/paper-search-mcp) | 搜索 Google Scholar / arXiv |

---

## 📄 许可

[MIT License](LICENSE)

## 🙏 致谢

- [EthanDeng/Chinese-ERJ](https://github.com/EthanDeng/Chinese-ERJ) — 《经济研究》LaTeX 模板
- [SepineTam/stata-mcp](https://github.com/SepineTam/stata-mcp) — Stata MCP 集成
- [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) — Claude Code Plugin 结构参考
