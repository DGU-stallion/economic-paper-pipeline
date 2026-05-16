# 经济学实证论文自动化工作流

> **Claude Code Plugin** — 纯对话式 AI 协作工具，覆盖选题、文献综述、Stata 实证、稳健性检验、LaTeX 论文撰写全流程。

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/DGU-stallion/economic-paper-pipeline)
[![Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-purple)](https://claude.ai/install.sh)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🚀 安装

### 前提条件
- [Claude Code](https://claude.ai/install.sh)（最新版）
- 可选：StataMP 18（用于实证回归）、TeX Live（用于本地 LaTeX 编译）

---

### 安装方式一：全局安装（推荐）

作为 Claude Code 全局插件安装，任何目录下都可使用：

```text
/plugin marketplace add DGU-stallion/economic-paper-pipeline
/plugin install economic-paper-pipeline
```

**文件存放**：论文项目创建在你**启动 Claude Code 时的目录**下的 `papers/` 文件夹。

---

### 安装方式二：本地开发模式

直接克隆仓库，在项目目录内启动 Claude Code，自动识别为本地插件：

```bash
git clone https://github.com/DGU-stallion/economic-paper-pipeline.git
cd economic-paper-pipeline
claude .  # 在项目目录内启动 Claude Code
```

**文件存放**：论文项目创建在仓库根目录的 `papers/` 文件夹内。

---

### 验证是否成功
输入 `/econ-help`，能看到命令列表即安装成功。

---

## 📂 文件存放位置

| 模式 | 论文项目路径 | 配置路径 |
|------|-------------|---------|
| **全局安装插件** | `./papers/你的项目/`（Claude Code 当前工作目录） | `./.config/current_project.json` |
| **本地开发模式** | `./papers/你的项目/`（插件目录内） | `./config/current_project.json` |

> 💡 全局安装时，所有论文项目创建在你**启动 Claude Code 时的目录**下，不会污染插件安装目录。

---

## 🗣️ 纯对话式，零命令

用户永远不说 Python 命令，只说自然语言：

| 你说一句话 | Agent 自动做的事 |
|-----------|----------------|
| "帮我创建一篇关于最低工资与企业就业的论文" | 创建项目，进入选题引导 |
| "我有哪些论文项目？" | 列出所有项目进度表格 |
| "切换到数字经济那篇论文" | 激活对应项目，显示当前阶段 |
| "现在进展到哪了？" | 展示当前项目进度 |
| "跑回归" | 自动生成 .do 文件、执行 Stata、提取系数 |
| "写论文" | 按《经济研究》格式生成完整 LaTeX 论文 |

也可以精确使用 `/econ-*` 命令：`/econ-status`、`/econ-stata`、`/econ-paper` 等。

---

## 📊 工作流

```
选题研究 → 文献综述 → 数据清洗 → Stata实证 → 稳健性检验 → 结论验证 → LaTeX论文撰写
```

| 阶段 | 自动化程度 | 人机协作点 |
|------|-----------|-----------|
| 1. 选题研究 | 半自动 | 5W1H 逐维引导 |
| 2. 文献综述 | 自动+确认 | 自动检索，关键文献确认 |
| 3. 数据清洗 | 自动 | 数据源无法获取时反馈 |
| 4. Stata 实证 | 自动 | 模型设定、变量选择可确认 |
| 5. 稳健性检验 | 自动 | 结果异常时反馈 |
| 6. 结论验证 | 自动+确认 | 对比假设与结果 |
| 7. LaTeX 论文 | 自动 | 偏好采集、编译方式选择 |

---

## 📁 目录结构

```
economic-paper-pipeline/
├── .claude-plugin/
│   └── plugin.json              # 插件清单（Plugin 入口）
├── commands/                    # /econ-* 斜杠命令（共 9 个，核心操作）
│   ├── econ-help.md
│   ├── econ-status.md
│   ├── econ-new.md
│   ├── econ-use.md
│   ├── econ-list.md
│   ├── econ-paper.md
│   ├── econ-paper.md
│   ├── econ-advance.md
│   ├── econ-reset.md
│   └── econ-compile.md
├── skills/                      # 子 Skill（自动发现）
│   ├── coordinator/SKILL.md     #   意图识别与路由
│   ├── topic/SKILL.md           #   选题研究
│   ├── literature/SKILL.md      #   文献综述
│   ├── stata/SKILL.md           #   Stata 实证
│   ├── latex/SKILL.md           #   LaTeX 论文
│   └── shared/interfaces/       #   跨 Skill 接口规范
├── hooks/
│   └── hooks.json               # SessionStart 钩子
├── scripts/
│   ├── pipeline.py              #   状态机引擎（29 微状态）
│   ├── memory.py                #   对话记忆持久化
│   └── announce-plugin-loaded.sh#   SessionStart 钩子
├── .mcp.json                    # MCP 服务器配置
├── .gitignore
├── CLAUDE.md                    # AI 协作主协议
├── config/                      # 项目配置
├── papers/                      # 你的所有论文项目
├── templates/                   # 论文模板
└── docs/                        # 文档
```

---

## 📦 使用自有数据与模板

### 自定义数据放置

将你的数据文件放入项目的 `data/raw/` 目录：

```
papers/你的项目/
└── data/
    ├── raw/                    ✅ 放这里，支持 .dta/.csv/.xlsx
    │   ├── 面板数据_2025.dta
    │   └── 宏观控制变量.csv
    ├── clean/                  ← 清洗后输出
    └── scripts/                ← 清洗脚本（自动生成）
```

**告诉 Agent 使用你的数据**：
> "使用 `data/raw/面板数据_2025.dta` 作为主数据"
> "核心解释变量是 `digital`，被解释变量是 `emp_tertiary`"

### 自定义 LaTeX 模板

将你的 `.cls` 文档类文件放入项目的 `paper/` 目录，并在项目创建时指定：

```
papers/你的项目/
└── paper/
    ├── 期刊投稿.cls            ✅ 放你的模板
    ├── main.tex                ← 自动生成时引用你的模板
    ├── sections/
    └── ...
```

**告诉 Agent 使用你的模板**：
> "创建新项目时使用 `paper/经济研究.cls` 作为文档类"
> "参考文献格式按 GB/T 7714-2015 顺序编码制"

### 覆盖全局模板

如果你想为所有新项目使用自定义模板，替换根目录：
- `templates/paper/chinese-erj.cls` — 默认文档类
- `templates/paper/main.tex` — 默认主文档结构

---

## 🎓 演示项目

内置演示论文：**数字经济发展对省际就业结构的影响——基于面板门槛模型的实证研究**

| 维度 | 内容 |
|------|------|
| **研究问题** | 数字经济发展如何影响中国省际就业结构？是否存在门槛效应？ |
| **方法** | 双向固定效应 + 面板门槛模型 (Hansen, 1999) |
| **数据** | 31 省份 × 2011–2023 年，403 观测值 |
| **状态** | ✅ 全部 7 阶段完成，论文已撰写 |

查看演示项目：`/econ-use demo-paper` → `/econ-status`

---

## 🔧 技术栈

| 工具 | 用途 |
|------|------|
| **Python 3.12+** | 数据获取、清洗、状态管理 |
| **StataMP 18** | 计量回归分析 |
| **LaTeX (XeLaTeX)** | 论文排版 |
| **MCP 协议** | 与 Stata、学术搜索引擎集成 |

### MCP 服务器

| 服务器 | 用途 |
|--------|------|
| [stata-mcp](https://github.com/SepineTam/stata-mcp) | 操作本地 StataMP 18 |
| [paper-search-mcp](https://github.com/openags/paper-search-mcp) | 搜索 Google Scholar / arXiv |

---

## 📝 论文偏好

进入论文撰写阶段时，Agent 主动询问字数、参考文献格式、语言、期刊模板等偏好，保存到项目记忆供后续使用。

---

## 📄 许可

[MIT License](LICENSE)

## 🙏 致谢

- [EthanDeng/Chinese-ERJ](https://github.com/EthanDeng/Chinese-ERJ) — 《经济研究》LaTeX 模板
- [SepineTam/stata-mcp](https://github.com/SepineTam/stata-mcp) — Stata MCP 集成
- [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) — Claude Code Plugin 结构参考
