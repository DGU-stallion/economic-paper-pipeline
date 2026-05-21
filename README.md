# 经济学实证论文自动化工作流

> **Claude Code Plugin** — 纯对话式 AI 协作工具，覆盖选题、文献综述、Stata 实证、稳健性检验、LaTeX 论文撰写全流程。让你专注于研究问题，而不是工具操作。

[![Version](https://img.shields.io/badge/version-4.1.0-blue)](https://github.com/DGU-stallion/economic-paper-pipeline)
[![Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-purple)](https://claude.ai/install.sh)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## ✨ 核心特性

### 🗣️ 纯对话式，零命令
永远只说自然语言，不需要记住任何命令：

| 你说一句话 | Agent 自动做的事 |
|-----------|----------------|
| "帮我创建一篇关于最低工资与企业就业的论文" | 创建项目，进入选题引导 |
| "我有哪些论文项目？" | 列出所有项目进度表格 |
| "切换到数字经济那篇论文" | 激活对应项目，显示当前阶段 |
| "现在进展到哪了？" | 展示分层上下文摘要 |
| "跑回归" | 读取变量映射，生成 .do 文件，执行 Stata |
| "回退到上一步" | 撤销当前状态，保留中间结果 |
| "写论文" | 自动整合所有上游产出，生成完整 LaTeX |
| "编译论文" | 健壮编译链，日志自动落地 |

也可以精确使用 `/econ-*` 命令：`/econ-status`、`/econ-stata`、`/econ-paper` 等。

---

### 🧠 分层记忆架构
LLM 每次只读最少的东西，用结构化数据替代对话历史：

```
Tier 1: pipeline_state.json  (每次必读, ~200 tokens)
  → 当前阶段 + 一句话摘要

Tier 2: project_config.json + context_store (进入项目时加载, ~500 tokens)
  → 变量映射表 / 假设验证表 / 决策记录 / 实证结果摘要

Tier 3: context/<stage>.md (进入当前阶段时才读, ~300 tokens)
  → 该阶段的输入/已完成/待决策/下游需要

Tier 4: conversation.json (几乎不读, 仅调试用)
```

**效果**：每次 "继续" 从 ~7500 token 降到 ~1000 token，节省 **85%**。

各阶段通过 `context_store` 自动传递上下文。选题阶段确定的 Y/D/X 变量，Stata 和 LaTeX 阶段直接读取，无需重复询问。

---

### 🔐 阶段门禁与健壮性保障
不让你"跑了半小时才发现第一步少了个变量"：

- **进入 Stata 阶段**：自动检查 Y/D 变量是否定义、清洗后数据是否存在
- **进入 Paper 阶段**：自动检查回归表格、参考文献文件是否齐全
- 缺东西友好提示，确认没问题可加 `--force` 强行推进
- **增量执行**：do-file 和数据没变就自动跳过重跑，节省 70% 调试时间
- **状态回退**：`undo` 命令回到上一步，保留所有中间文件

---

### 🧹 项目全生命周期管理
从创建到归档的完整支持：

- **清道夫清理**：`cleanup` 命令一键删除 LaTeX 编译垃圾、Stata 运行日志、版本化 PDF
- **多项目并行**：任意切换项目，每个项目独立状态
- **决策记录**：每个阶段的关键选择自动记录，方便后续回顾和修改

---

### 🔍 Humanizer-ZH 中文 AI 痕迹检测
论文写作过程中自动质检，让 AI 产出更像人写的：
- 破折号滥用检测、句式单一性检查
- 中文写作规范检查、被动语态滥用检测
- LaTeX 写作中自动逐节检测，最终 QC 汇总报告

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

## 📊 标准工作流

```
选题研究 → 文献综述 → 数据清洗 → Stata实证 → 稳健性检验 → 结论验证 → LaTeX论文撰写
```

| 阶段 | 自动化程度 | 人机协作点 |
|------|-----------|-----------|
| 1. 选题研究 | 半自动 | 5W1H 逐维引导 → Gap 识别 → SMART 问题 |
| 2. 文献综述 | 自动+确认 | MCP 检索 Google Scholar，关键文献可人工确认 |
| 3. 数据清洗 | 自动 | 数据格式自动识别，缺失值异常值处理 |
| 4. Stata 实证 | 自动 | 模型设定、变量选择可确认，基准/中介/异质性自动跑 |
| 5. 稳健性检验 | 自动 | 替换变量/改变样本/安慰剂检验，结果异常自动反馈 |
| 6. 结论验证 | 自动+确认 | 对比假设与结果，边际贡献梳理 |
| 7. LaTeX 论文 | 自动 | 所有表格自动注入，参考文献自动排版，一键编译 PDF |

**关键原则**：技术操作自动执行，研究决策节点可请求用户介入。状态机支持决策分支——基准回归不显著时自动引导回到模型设定而非盲目前进。

---

## 📁 项目目录结构

```
economic-paper-pipeline/
├── .claude-plugin/
│   └── plugin.json              # 插件清单
├── commands/                     # /econ-* 斜杠命令
│   ├── econ-help.md
│   ├── econ-status.md
│   ├── econ-new.md
│   ├── econ-use.md
│   ├── econ-list.md
│   ├── econ-paper.md
│   ├── econ-advance.md
│   ├── econ-reset.md
│   └── econ-compile.md
├── skills/                       # 子 Skill（自动发现）
│   ├── coordinator/SKILL.md      #   意图识别、路由、分层记忆协议
│   ├── topic/SKILL.md            #   选题研究（5W1H → Gap → SMART）
│   ├── literature/SKILL.md       #   文献综述（检索 → 摘要 → 综述 → .bib）
│   ├── stata/SKILL.md            #   Stata 实证（清洗 → 基准 → 中介 → 异质 → 稳健）
│   ├── latex/SKILL.md            #   LaTeX 论文（模板 → 章节 → 表格注入 → 编译）
│   └── humanizer-zh/SKILL.md     #   中文 AI 痕迹检测与质量优化
├── hooks/
│   └── hooks.json                # SessionStart 钩子
├── scripts/
│   ├── pipeline.py               #   状态机引擎（微状态 + 上下文管理 + 分层记忆）
│   ├── memory.py                 #   对话记忆持久化
│   └── announce-plugin-loaded.sh
├── .mcp.json                     # MCP 服务器配置
├── CLAUDE.md                     # AI 协作主协议
├── templates/                    # 论文模板（零硬编码，{{PLACEHOLDER}} 系统）
│   ├── paper/                    #   LaTeX 模板（main.tex, .cls, sections/）
│   ├── data/scripts/             #   数据清洗 do-file 模板
│   └── analysis/do-files/        #   实证分析 do-file 模板
├── tests/                        # 测试套件
│   ├── run_tests.py              #   一键运行所有测试
│   └── fixtures/                 #   测试数据
└── papers/                       # 你的所有论文项目
    └── <项目名>/
        ├── project_config.json   #   变量映射表（Y/D/X/ID）
        ├── pipeline_state.json   #   状态 + context_store + 决策记录
        ├── context/              #   阶段上下文文件
        ├── topics/               #   选题产出
        ├── literature/           #   文献综述产出
        ├── data/                 #   原始数据 + 清洗后数据
        ├── analysis/             #   do-files + output tables
        └── paper/                #   LaTeX 源码 + PDF
```

---

## 🎓 演示项目

内置演示论文：**数字经济发展对省际就业结构的影响——基于面板门槛模型的实证研究**

| 维度 | 内容 |
|------|------|
| 模型 | FE 固定效应 + 面板门槛模型 |
| 数据 | 2015-2020 年省级面板 |
| 表格 | 描述性统计 + 基准回归 + 门槛检验 + 异质性 + 稳健性 |
| 论文 | 完整 7 章节，含摘要、引言、文献、模型、结论、参考文献 |

---

## 🧪 开发测试

内置最小测试用例，改代码后一键回归：
```bash
python tests/run_tests.py
```

测试覆盖：
- FE 面板回归全流程
- DID 双重差分
- LaTeX 编译环境
- 清道夫清理功能

---

## 📄 License

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 PR！核心改进方向：
- 更多高校的学位论文模板
- 更多识别策略的自动化支持（RDD、IV、合成控制等）
- 更多数据来源的自动接入（CSMAR、Wind、CNRDS 等）
