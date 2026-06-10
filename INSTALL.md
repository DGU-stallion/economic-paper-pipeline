# 安装与配置指南

## 前置要求

### 必需软件

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| **Python** | 3.12+ | 数据处理、工作流管理 |
| **StataMP** | 18+ | 实证回归分析 |
| **TeX Live** | 2023+ | LaTeX 论文编译，需安装 `collection-langchinese` 和 `collection-bibtexextra` |
| **uv** | 最新版 | Python 包管理器，用于启动 MCP 服务器 |

### Claude Code 配置

本项目作为 Claude Code Skill 使用，需要配置 MCP 服务器。

---

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/economic-paper-pipeline.git
cd economic-paper-pipeline
```

### 2. 安装 Python 依赖

```bash
pip install pandas numpy requests beautifulsoup4 yfinance openpyxl statsmodels
```

### 3. 配置 MCP 服务器

编辑 `~/.claude/settings.json`（或项目本地 `.claude/settings.json`），添加 MCP 服务器配置：

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    },
    "paper-search-mcp": {
      "command": "uv",
      "args": ["run", "--with", "paper-search-mcp", "python", "-m", "paper_search_mcp.server"]
    }
  }
}
```

### 4. 配置 Stata 路径

编辑 `.statamcp/config.json`：

```json
{
  "stata_path": "D:\\Program Files\\Stata\\StataMP-64.exe"
}
```

Windows 用户注意路径使用双反斜杠。

### 5. 验证安装

在 Claude Code 中打开项目目录，Agent 会自动问候你。

**不要敲任何命令**。直接说：
> "列出所有项目

Agent 会在后台执行并展示给你结果。

---

## 纯对话式工作流

### 你可以说的话（自然语言即可，不限定措辞）

| 当你想说... | Agent 自动执行的操作 |
|-------------|-------------------|
| "创建一篇关于 XXX 的论文" | 从 templates/ 创建新项目，自动切换，进入选题引导 |
| "我有哪些论文项目？" | 列出所有项目的进度表格 |
| "切换到 XXX 项目" | 激活指定项目，显示当前状态 |
| "现在进展到哪了？" | 显示当前项目的阶段和历史 |
| "这个阶段完成了" | 推进到下一阶段，告知你接下来做什么 |
| "看看历史记录" | 展示项目的完成历史 |
| "我想从头开始" | 重置当前项目（会先确认你的意图） |

> 💡 **重要**：你永远不需要敲 `python pipeline.py xxx` 这种命令。有什么需求，直接用自然语言说。Agent 会在后台自动执行。

### 目录结构说明

```
economic-paper-pipeline/
├── scripts/                    # 核心脚本
│   ├── orchestrator.py         # 编排器（状态管理 + 模块路由）
│   ├── pipeline.py             # 后向兼容入口
│   ├── shared/                 # 共享层（契约 / 注册表 / 状态）
│   └── modules/                # 8 个独立模块
│       ├── conceptualize/      # 概念助手
│       ├── research/           # 调研助手
│       ├── literature/         # 文献助手
│       ├── data/               # 数据助手
│       ├── analyze/            # 分析助手
│       ├── verify/             # 验证助手
│       ├── write/              # 论文助手
│       └── format/             # 格式助手
├── docs/                       # 文档
├── config/                     # 配置
├── templates/                  # 新项目模板
├── papers/                     # 你的所有论文项目
│   ├── demo-paper/             # 示例项目
│   └── my-first-paper/         # 你的第一篇论文
│       ├── topics/             # 选题研究
│       ├── literature/         # 文献综述
│       ├── data/               # 数据
│       ├── analysis/           # Stata 实证
│       └── paper/              # LaTeX 论文源码
├── .claude/                    # Claude 配置
└── .mcp.json                   # MCP 服务器配置
```

---

## Stata 包安装

首次使用前，在 Stata 中安装必需包：

```stata
ssc install estout, replace
ssc install coefplot, replace
ssc install outreg2, replace
ssc install reghdfe, replace
ssc install ftools, replace
ssc install boottest, replace
```

也可以使用项目提供的 do 文件：
```bash
# 使用 stata-mcp 执行安装
```

---

## TeX Live 配置

确保安装以下宏包集合：

- `collection-langchinese`（中文支持）
- `collection-bibtexextra`（biblatex-gb7714-2015 等）
- `collection-latexextra`

编译论文：

```bash
cd papers/<your-project>/paper
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
```

---

## 常见问题

### Q: 如何迁移已有论文项目？

将整个项目目录移动到 `papers/` 下，然后：

```bash
python pipeline.py use <your-project-name>
```

### Q: 如何更新框架版本？

```bash
git pull origin main
```

模板更新不会影响已有项目。如需将新模板特性应用到旧项目，手动复制对应文件。

### Q: 如何备份项目？

```bash
# 备份单个项目
tar -czf papers/my-project.tar.gz papers/my-project/

# 或直接提交到 Git（推荐为每个项目创建独立仓库）
```

### Q: Stata 执行乱码？

确保：
1. `.do` 文件使用 UTF-8 编码
2. Stata 设置 `set locale_functions all on`
3. 使用 stata-mcp 的 `read_log` 工具时指定 `encoding="utf-8"`

---

## 卸载

删除整个项目目录即可，所有项目数据保存在 `papers/` 下。
